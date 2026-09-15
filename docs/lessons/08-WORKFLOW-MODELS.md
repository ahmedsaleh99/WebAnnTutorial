# Lesson 8 — Workflow models and assignment boundaries

## Goal

Build the objects that turn project configuration into work an annotator can
perform. By the end of this lesson, a manager can prepare a task and assign a
job, while an annotator can see only assigned work, move it through valid
states, and save one result.

**Branch:** `lesson/08-workflow-models`

**Pull request title:** `Lesson 8: add workflow models and assignments`

## What you will learn

- how to identify an aggregate boundary instead of treating every table alone;
- when to use `ForeignKey`, `ManyToManyField`, and `OneToOneField`;
- how conditional uniqueness constraints describe business rules;
- why cross-project relationships require application validation;
- how a state machine controls lifecycle changes;
- how queryset scoping prevents data disclosure;
- the difference between role permission and object permission; and
- how to test database, serializer, API, and authorization boundaries.

## Part 1 — Begin from the reviewed checkpoint

Finish and merge Lesson 7 before starting:

```bash
git switch main
git pull --ff-only
git switch -c lesson/08-workflow-models
make check
```

`git switch main` changes the current branch without changing it. `git pull
--ff-only` downloads commits and advances local `main` only when no merge commit
is required. The new lesson branch therefore starts from reviewed history.

## Part 2 — Understand the workflow domain

The existing models define project configuration, including the subjects
available to a project. They do not yet select a subset of those subjects for a
particular recording, connect that recording to video views, assign the work,
or store its result.

```text
Project
├── Subject [0..many]                 available project subjects
├── VideoAsset [0..many]              reusable project media
└── Task [0..many]
    ├── subjects [0..many] ────────── selected subset of Project subjects
    ├── VideoView [0..many]
    │   ├── asset ─────────────────── one VideoAsset from the same Project
    │   └── subject [0..1] ────────── optional selected Task subject
    └── AnnotationJob [0..many] ───── one parent assignment per annotator
        ├── assigned_to ───────────── one User
        └── AnnotationWorkItem [1..many]
            ├── task_subject ──────── one selected Task subject
            └── AnnotationResult [0..1]
```

This diagram shows stored database relationships. Indentation means ownership;
the connecting lines identify references. It does **not** mean that a job owns a
copied subject list.

- `Task` is one unit of annotation work inside a project.
- `VideoAsset` represents reusable source media owned by a project.
- `VideoView` gives an asset a role inside a task: main, back, or subject.
- `TaskSubject` makes each selected task subject an explicit subtask.
- `AnnotationJob` is the parent assignment of a task to an annotator.
- `AnnotationWorkItem` connects the assignment to one `TaskSubject` and owns
  its independent lifecycle.
- `AnnotationResult` is the optional result for one work item.

Think of the task as an **aggregate boundary**: its selected subjects, video
views, and jobs together describe one unit of work. The project is the wider
ownership boundary. Every subject and asset used by the task must come from
that same project.

### Follow the subject inheritance chain

Subject scope is narrowed at the task level and then inherited by a normal job:

```text
Project defines the available subjects
                  ↓
Task selects a subset of those project subjects
                  ↓
Creating AnnotationJob creates one work item per TaskSubject
```

For example:

```text
Project: Classroom study
Available subjects: Alice, Bob, Carla, David

Task: Morning recording
Selected subjects: Alice, Carla

Job: Morning recording assigned to Annotator 1
Work item 1: Alice
Work item 2: Carla
```

`TaskSubject` is the source of truth for task membership. Work items reference
those rows rather than copying arbitrary subject IDs. This tutorial deliberately
normalizes the original repository's `subject=NULL` convention: every inherited
subject now has a database row while one parent job still groups the assignment.

This makes partial progress explicit. Alice can be completed while Carla is
still in progress, and each can have its own result and review state.

## Part 3 — Write invariant tests first (red)

Extend `backend/annotations/tests/test_models.py`. Write one test per rule:

1. a task rejects subjects owned by another project;
2. a video view rejects an asset owned by another project;
3. a subject video requires a subject included in the task;
4. a task has at most one main view and one back view;
5. one job creates exactly one work item per selected task subject;
6. a work item has at most one result;
7. an annotator sees only their own assignments; and
8. invalid work-item status jumps return `400 Bad Request`.

Run the test file:

```bash
DJANGO_SECRET_KEY=test-only-not-a-production-secret \
  .venv/bin/python backend/manage.py test annotations.tests.test_models
```

It should fail because the classes do not exist. This is TDD's red stage. The
failures describe behavior before implementation decisions influence the tests.
Test observable rules, not Django itself. Do not test that a `ForeignKey` stores
an ID; test that it cannot connect objects across project boundaries.

## Part 4 — Add readable test builders

Extend `backend/annotations/tests/builders.py` with `create_task`,
`create_video_asset`, `create_video_view`, `create_job`, `create_work_item`, and
`create_result`.

A builder creates a valid default object and accepts only relevant differences:

```python
job = create_job(assigned_to=annotator)
```

This reads as domain language. Builders are test helpers, not production
shortcuts: make values explicit when they affect the rule being tested.

## Part 5 — Implement the relationship types

Add the seven models to `backend/annotations/models.py`.

Use a `ForeignKey` when many children may reference one parent:

```python
project = models.ForeignKey(
    Project,
    related_name="tasks",
    on_delete=models.CASCADE,
)
```

Use an explicit through model because a selected task subject is now a
first-class subtask:

```python
subjects = models.ManyToManyField(
    Subject,
    related_name="tasks",
    through="TaskSubject",
    blank=True,
)
```

Django always stores many-to-many relationships in an intermediate table.
Naming it `TaskSubject` gives each selected subject an identity that work items
can reference. Save the task before calling `.subjects.set(...)`.

Use `OneToOneField` because a work item has zero or one result:

```python
work_item = models.OneToOneField(
    AnnotationWorkItem,
    related_name="result",
    on_delete=models.CASCADE,
)
```

A foreign key would allow several competing results for one subject work item.

Choose deletion behavior deliberately. Projects own tasks/assets and tasks own
views/jobs, so those relationships cascade. Assigned users use `PROTECT` so an
assignment cannot silently lose its identity. A view protects its reusable
asset from accidental deletion.

## Part 6 — Express database-enforceable rules

Scope task keys to a project:

```python
models.UniqueConstraint(
    fields=["project", "key"],
    name="unique_task_key_per_project",
)
```

A conditional constraint applies only to matching rows:

```python
models.UniqueConstraint(
    fields=["task"],
    condition=models.Q(role="main"),
    name="one_main_video_per_task",
)
```

This permits several views but only one main view. Add corresponding back-view
and `(task, subject)` rules. Add a check so a subject role requires a subject,
while main/back roles forbid one.

Add check constraints for task and work-item statuses. `TextChoices` helps
Python and serializers; database checks also reject bad values written outside
those paths.

Constraints are the concurrency-safe boundary. Two requests may both pass an
earlier existence check, but the database arbitrates simultaneous inserts.

## Part 7 — Validate cross-object scope

SQL constraints cannot conveniently state that several related rows all belong
to the same project. Implement those rules in model `clean()` and serializers.

For a video view, validate:

```text
asset.project == task.project
subject.project == task.project
subject is in task.subjects
```

Validate that every `TaskSubject.subject` belongs to the task's project and that
every work item's `task_subject.task` equals its parent job's task. A task
request must reject every selected subject from another project.

`model.save()` does not automatically call `full_clean()`. Direct model tests
must call it explicitly. API serializers must validate before saving so bad
requests become readable `400` responses rather than corrupt relationships.
The model documents the rule for Python callers; the serializer gives API
clients a stable error contract.

## Part 8 — Model each work-item status as a state machine

A status choice does not allow every movement between choices:

| Current status | Allowed next status | Meaning |
| --- | --- | --- |
| `assigned` | `in_progress` | Annotator starts work |
| `in_progress` | `completed` | Annotator submits work |
| `completed` | `reviewed` | Manager completes review |
| `reviewed` | — | Terminal state |

Reject skips such as `assigned → completed`, backward movement, and movement
out of `reviewed`. A transition is an edge, not just a valid destination.

## Part 9 — Build serializers and APIs

Add serializers and register these router endpoints:

```text
/api/tasks/
/api/video-assets/
/api/video-views/
/api/jobs/
/api/work-items/
/api/results/
```

Set `created_by` from `request.user`. Create the parent job and every child work
item inside `transaction.atomic()`, so a failure rolls back the whole assignment.

Managers (`is_staff=True`) manage workflow and assignments. Annotators read
assigned workflow, advance their own work items, and maintain their work-item
results. They cannot reassign or delete parent jobs.

Creating one parent job requires only the task and annotator:

```json
{
  "task": "<task UUID>",
  "assigned_to": 17
}
```

The server reads the task's `TaskSubject` rows and creates one work item for
each. The React form does not recreate a separate subject list.

## Part 10 — Scope querysets before object lookup

For an annotator, start the jobs queryset with:

```python
AnnotationJob.objects.filter(assigned_to=request.user)
```

Derive related task, view, and asset querysets through that assignment. Managers
use the complete queryset.

DRF uses `get_queryset()` for list and detail lookups. An unassigned UUID is
outside the visible set and returns `404`, without revealing its existence.
Filtering after serialization would still expose detail endpoints and load data
the request must never access.

Use `select_related()` for foreign keys and `prefetch_related()` for many-valued
relationships. Use `.distinct()` when joins through jobs could repeat a task or
asset. These choices improve query count without weakening authorization.

### Why use `AssignedWorkflowQuerysetMixin`?

Every workflow endpoint applies the same high-level rule:

```text
manager   → may query every workflow object
annotator → may query only objects reachable from their assignment
```

Without a shared helper, each viewset would repeat the role check and filtering:

```python
user = self.request.user
if not user.is_staff:
    queryset = queryset.filter(jobs__assigned_to=user).distinct()
return queryset
```

Repeated authorization code is easy to make inconsistent. A future endpoint
might forget `.distinct()`, check the wrong role, or omit filtering entirely.
The mixin centralizes the shared policy while allowing each resource to supply
its own relationship path:

```python
class AssignedWorkflowQuerysetMixin:
    def scope_to_user(self, queryset, assignment_path):
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(**{assignment_path: user}).distinct()
```

A **mixin** is a small class that contributes reusable behavior to another
class. It is not used by itself. A viewset inherits it before `ModelViewSet`:

```python
class TaskViewSet(AssignedWorkflowQuerysetMixin, viewsets.ModelViewSet):
    ...
```

That makes `self.scope_to_user(...)` available inside the viewset. The mixin
does not define a model, serializer, URL, or complete view; it supplies only the
queryset-scoping behavior shared by workflow resources.

### How `assignment_path` works

Django uses double underscores to traverse relationships. The path differs
depending on how far a resource is from `AnnotationJob.assigned_to`:

| Resource being queried | Assignment path | Relationship traversal |
| --- | --- | --- |
| `AnnotationJob` | `assigned_to` | job → user |
| `Task` | `jobs__assigned_to` | task → jobs → user |
| `VideoView` | `task__jobs__assigned_to` | view → task → jobs → user |
| `VideoAsset` | `video_views__task__jobs__assigned_to` | asset → views → task → jobs → user |
| `AnnotationWorkItem` | `job__assigned_to` | work item → job → user |
| `AnnotationResult` | `work_item__job__assigned_to` | result → work item → job → user |

This call:

```python
self.scope_to_user(queryset, "task__jobs__assigned_to")
```

constructs keyword arguments dynamically:

```python
{"task__jobs__assigned_to": request.user}
```

The `**` operator passes that dictionary to `filter()`, making it equivalent to:

```python
queryset.filter(task__jobs__assigned_to=request.user).distinct()
```

The path is supplied by backend code, never by request input. Accepting an
arbitrary relationship path from a client would make the security rule
untrustworthy.

### Why call `.distinct()`?

A SQL join can produce repeated rows. If one task has two jobs assigned to the
same user, joining `Task` through `jobs` can return that task twice. `distinct()`
asks the database to return each resource once, keeping pagination counts and
API results correct.

### Why the mixin does not replace permissions

Queryset scoping answers:

> Which existing objects may this user discover?

Permission classes answer:

> May this user perform this HTTP action?

Both are required. The mixin hides an unassigned object from list and detail
queries, usually producing `404`. Permission classes separately prevent actions
such as an annotator creating a task or deleting a parent job. Creation also
needs serializer/view validation because a new object is not yet present in a
queryset.

Use this mixin only for resources whose visibility is derived from an
annotation assignment. Project configuration endpoints intentionally use their
separate `IsAdminOrReadOnly` policy.

## Part 11 — Complete security and lifecycle tests

Test the matrix with different real users:

```text
manager   → create workflow objects and jobs; see all
annotator → see assigned work; advance own work items; edit own results
other     → cannot retrieve another annotator's job/result
anonymous → 401 from every workflow endpoint
```

Prefer readable intermediate responses:

```python
response = self.client.get(f"/api/jobs/{job.pk}/")

self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
```

Test a full work-item transition sequence and an invalid jump. One successful
status update does not prove forbidden transitions are rejected.

## Part 12 — Generate and inspect the migration

Generate rather than hand-number the migration:

```bash
DJANGO_SECRET_KEY=insecure-local-development-key DJANGO_DEBUG=true \
  .venv/bin/python backend/manage.py makemigrations annotations
```

Read it. Confirm all models, relationship fields, conditional constraints, and
checks exist. Then run:

```bash
make backend-test
make check
make container-test
git diff --check
```

If `python3` is not Python 3.12, activate the Lesson 2 environment or pass the
documented Python 3.12 command to Make. Do not delete the runtime check.

## Part 13 — Open the pull request

Update the data-model and API references, README index, repository validation,
and container migration assertion. Include in the PR:

- invariant tests written during red;
- model and migration choices made during green;
- the role/object permission matrix;
- one rejected transition and its response;
- `make check` and `make container-test` evidence; and
- intentionally deferred media-processing behavior.

## Acceptance criteria

- All seven workflow models and their migration exist.
- Tasks select only subjects available in their project.
- A parent job creates exactly one work item per selected task subject.
- Each work item has an independent status, result, and review state.
- View and assignment duplicates are database constrained.
- Each work item has at most one result.
- Managers create workflow/assignment objects; creator identity is trusted.
- Annotators see only assigned tasks, media, jobs, and results.
- Unassigned detail URLs do not disclose object existence.
- Annotators cannot reassign or delete jobs.
- Work-item transitions follow the documented state machine.
- Invalid relationships and transitions return clear `400` responses.
- Local and PostgreSQL tests pass without migration drift.

## Gold-standard implementation

Read this after your implementation and first review. The checkpoint is
`lesson-08`:

```bash
git fetch --tags
git diff lesson-08 -- . ':!docs/lessons/08-WORKFLOW-MODELS.md'
```

The reference uses relational ownership, conditional constraints, explicit
cross-project validation, forward-only transitions, server-controlled creator
fields, and SQL-level queryset scoping. Internal structure may differ, but the
same observable rules and security boundaries must pass.

## What you should now be able to explain

- the workflow aggregate and each model's responsibility;
- foreign key versus many-to-many versus one-to-one;
- ordinary versus conditional uniqueness;
- why some invariants belong in SQL and others in validation;
- why `save()` and `full_clean()` differ;
- a state versus a state transition;
- role, object, and queryset permissions;
- why hidden objects return 404; and
- `select_related`, `prefetch_related`, and `distinct`.
