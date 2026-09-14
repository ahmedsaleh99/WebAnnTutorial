# Lesson 6 — REST APIs, serialization, and validation

## Goal

Expose the Lesson 5 configuration domain as a consistent JSON API using Django
REST Framework (DRF). Specify observable HTTP contracts with failing tests
before implementing serializers, viewsets, routing, pagination, filtering, and
deletion behavior.

**Branch:** `lesson/06-drf-api`

**Prerequisite:** Lesson 5 is merged and tagged; both quality gates pass.

## Deliverables

- pinned Django REST Framework dependency;
- serializers for all five configuration models;
- CRUD viewsets and router-generated URLs;
- stable paginated collection responses;
- explicit project, dimension, and subject filters;
- API-boundary validation and status codes;
- protected-template deletion represented as HTTP 409;
- API contract tests and reference documentation; and
- an API assertion in the PostgreSQL container smoke test.

## Part 1 — Start the branch

```bash
git switch main
git pull --ff-only
make check
make container-test
git switch -c lesson/06-drf-api
```

## Part 2 — Design the HTTP contract first

Create `docs/API.md` before the implementation. Define these collections:

```text
GET, POST   /api/templates/
GET, POST   /api/projects/
GET, POST   /api/dimensions/
GET, POST   /api/labels/
GET, POST   /api/subjects/
```

A detail URL appends the object's UUID and supports `GET`, `PUT`, `PATCH`, and
`DELETE`. Define status codes before writing views:

- `200 OK` for successful reads and updates;
- `201 Created` for successful creation;
- `204 No Content` for successful deletion;
- `400 Bad Request` for invalid client data;
- `404 Not Found` for an unknown UUID;
- `409 Conflict` when a template is valid but cannot be deleted because a
  project references it.

HTTP is part of the application contract. A database `IntegrityError` or Python
traceback is not a client-facing API design.

## Part 3 — Write API tests first (red)

Create `annotations/tests/test_api.py` with DRF's `APITestCase`. Test:

1. template creation returns 201 and the documented fields;
2. list results have exactly `count`, `next`, `previous`, and `results`;
3. duplicate template key/version returns 400;
4. deletion of an in-use template returns 409;
5. project create, retrieve, patch, and delete use the expected codes;
6. invalid status and unknown template return field errors with 400;
7. an unknown project returns 404;
8. project status filtering returns only matching objects;
9. dimensions, labels, and subjects can be created and filtered;
10. invalid label color returns 400.

Run `make backend-test`. The meaningful red result is a 404 because `/api/`
routes do not exist—not an import failure caused by forgetting to install DRF.

## Part 4 — Add DRF and understand serializers

Pin `djangorestframework` in `backend/requirements.txt`, run `make bootstrap`,
and add `rest_framework` to `INSTALLED_APPS`.

Create one `ModelSerializer` per model. A serializer has two directions:

```text
incoming JSON → validation → validated Python values → model
model → primitive values → outgoing JSON
```

### Why serializers are needed

A Django model describes Python objects and database storage. HTTP clients send
and receive JSON-compatible values. Those are different boundaries:

```text
HTTP JSON                         Django/Python
"2ad65f20-..."                   UUID object
"2026-09-14T15:20:00Z"           datetime object
{"cohort": "A"}                 dictionary
template UUID                     ProjectTemplate instance
```

A serializer is the explicit translator and gatekeeper between them. Without a
serializer, each view would need to manually parse request bodies, check
required fields, convert UUIDs, find related objects, format timestamps, build
error responses, save models, and choose which fields are safe to return. That
logic would be repeated across create and update endpoints and would easily
become inconsistent.

Serializers provide four important protections:

1. **Input shape:** Only declared fields participate in the API contract.
2. **Type conversion:** JSON strings and numbers become appropriate Python
   values and related model objects.
3. **Validation:** Missing, malformed, unknown-choice, relationship, validator,
   and uniqueness errors become structured HTTP 400 details before saving.
4. **Output representation:** Model instances become stable JSON-safe values
   without exposing every database field automatically.

The serializer is not a replacement for model or database constraints. It gives
clients useful early feedback, while database constraints remain the final
protection against invalid data and concurrent requests.

### Reading incoming JSON

Consider a project creation body:

```json
{
  "name": "Classroom study",
  "key": "classroom-study",
  "status": "draft",
  "template": "2ad65f20-2c4c-4ed1-86a6-d1be3b177292"
}
```

DRF follows this lifecycle:

```python
serializer = ProjectSerializer(data=request.data)
serializer.is_valid(raise_exception=True)
project = serializer.save()
```

Before validation, `serializer.initial_data` contains untrusted request values.
After `is_valid()`, `serializer.validated_data` contains converted, trusted
values. For example, `template` is now the referenced `ProjectTemplate` object,
not merely an unchecked string. If validation fails, `serializer.errors`
contains field-keyed messages and `raise_exception=True` produces HTTP 400.

Do not read `validated_data` or call `save()` before `is_valid()`. Validation is
the step that establishes whether incoming data is safe to use.

For a new object, `save()` calls the serializer's `create(validated_data)`.
For an existing object, it calls `update(instance, validated_data)`. A
`ModelSerializer` supplies suitable default implementations using the model
manager and model `save()`. Override them only when creation or update genuinely
requires additional domain behavior.

### Producing outgoing JSON

When initialized with a model instance:

```python
serializer = ProjectSerializer(project)
response_body = serializer.data
```

`.data` contains primitive values that DRF's renderer can encode as JSON. The
serializer converts the UUID and timestamps and represents `template` by its
primary-key UUID. It does not return a Python model object to the client.

For a collection, DRF uses `many=True` internally:

```python
serializer = ProjectSerializer(projects, many=True)
```

Pagination wraps the resulting list in `count`, `next`, `previous`, and
`results`.

### Why fields are listed explicitly

List every API field explicitly; do not use `fields = "__all__"`:

```python
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "key",
            "description",
            "status",
            "template",
            "configuration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
```

The explicit list is an allowlist and a reviewable API contract. If a sensitive
model field is added later, it does not silently appear in responses. It also
makes removal or renaming of an API field a deliberate compatibility decision.

`read_only_fields` means a value may appear in responses but clients cannot set
or replace it. IDs and timestamps are server-owned, so requests attempting to
supply them are ignored rather than controlling stored identity or audit data.

### Validation inherited from the model

`ModelSerializer` examines model metadata to construct serializer fields.
Examples in this lesson include:

- `TextChoices` becomes a choice field, so `status="unknown"` returns a status
  error;
- `RegexValidator` checks label colors;
- a foreign key becomes a related field that checks whether the UUID exists;
- `unique=True` and supported compound uniqueness constraints produce duplicate
  validation errors; and
- maximum lengths and required/blank behavior become request rules.

This automatic mapping is useful, but it is not magic. Inspect the generated
behavior through API tests. Add explicit `validate_<field>()` or `validate()`
methods when an API rule cannot be expressed clearly by model metadata, and
retain database constraints for durable invariants.

### Full updates and partial updates

For `PUT`, the serializer normally requires every writable required field
because the request represents a complete replacement. For `PATCH`, the ViewSet
constructs it with `partial=True`, so omitted fields retain their current values:

```python
serializer = ProjectSerializer(
    project,
    data={"status": "active"},
    partial=True,
)
```

Fields that are present are still validated. Partial does not mean unvalidated.

In short, models define how the application stores valid domain state;
serializers define how external clients are allowed to describe and observe
that state.

## Part 5 — Add viewsets and router URLs

A **view** receives one request and returns one response. A **ViewSet** groups
the related views for one resource into a single class. Instead of writing six
separate project view functions, a `ModelViewSet` supplies six standard actions:

| HTTP request | ViewSet action | Purpose | Normal success status |
| --- | --- | --- | --- |
| `GET /api/projects/` | `list()` | Return a collection | 200 |
| `POST /api/projects/` | `create()` | Validate and create one object | 201 |
| `GET /api/projects/<uuid>/` | `retrieve()` | Return one object | 200 |
| `PUT /api/projects/<uuid>/` | `update()` | Replace all editable fields | 200 |
| `PATCH /api/projects/<uuid>/` | `partial_update()` | Change selected fields | 200 |
| `DELETE /api/projects/<uuid>/` | `destroy()` | Delete one object | 204 |

These methods come from DRF's mixins through `ModelViewSet`; they are not
methods we need to copy into every class. A minimal ViewSet connects two things:

```python
class ProjectTemplateViewSet(viewsets.ModelViewSet):
    queryset = ProjectTemplate.objects.all()
    serializer_class = ProjectTemplateSerializer
```

`queryset` describes which objects the ViewSet may operate on.
`serializer_class` describes how those objects cross the HTTP boundary. DRF
uses both for every standard action.

### How a request moves through a ViewSet

For a creation request:

```text
POST /api/projects/
  → router selects ProjectViewSet.create
  → serializer parses and validates request JSON
  → serializer saves Project
  → serializer renders the saved Project
  → Response returns JSON with status 201
```

For a detail read:

```text
GET /api/projects/<uuid>/
  → router selects ProjectViewSet.retrieve
  → get_queryset() supplies the allowed Project query
  → DRF looks up the UUID
  → missing object becomes 404
  → serializer renders the found object
  → Response returns JSON with status 200
```

This explains why the test client can call a URL without invoking a ViewSet
method directly: the router and Django URL dispatcher choose the correct action.

### `queryset` versus `get_queryset()`

Use a class-level `queryset` when every request begins with the same query:

```python
queryset = ProjectTemplate.objects.all()
```

Override `get_queryset()` when the query depends on the request or needs query
optimization:

```python
def get_queryset(self):
    queryset = Project.objects.select_related("template")
    if project_status := self.request.query_params.get("status"):
        queryset = queryset.filter(status=project_status)
    return queryset
```

`self.request` is the current DRF request. The example reads `?status=active`
and adds a database filter. `select_related("template")` retrieves each
project and its template in one joined query, avoiding an extra template query
for every project in a list.

Later, authentication will also use `get_queryset()` to restrict records to
what the current user is authorized to see. Returning a correctly scoped
queryset is therefore both a performance and security responsibility.

### What the default actions do

The inherited `create()` action roughly performs:

```python
serializer = self.get_serializer(data=request.data)
serializer.is_valid(raise_exception=True)
serializer.save()
return Response(serializer.data, status=201)
```

The actual DRF implementation also handles response headers and framework
hooks. This simplified version shows the important collaboration: the ViewSet
coordinates the request, while the serializer validates and saves data.

The inherited `list()` action obtains `get_queryset()`, applies filtering and
pagination, serializes the selected page with `many=True`, and returns the
pagination envelope. The inherited detail actions call `get_object()`, which
uses the queryset and URL UUID and raises a 404 when no permitted object exists.

### Override behavior only when the contract differs

Keep inherited actions when their behavior already matches the API contract.
Override the smallest relevant method when domain behavior differs. For
example, template deletion translates a known `ProtectedError` into HTTP 409:

```python
def destroy(self, request, *args, **kwargs):
    try:
        return super().destroy(request, *args, **kwargs)
    except ProtectedError:
        return Response(
            {"detail": "Templates used by projects cannot be deleted."},
            status=status.HTTP_409_CONFLICT,
        )
```

Calling `super().destroy(...)` preserves DRF's normal object lookup and 204
response. The override changes only the expected conflict. Avoid rewriting the
whole CRUD implementation or catching every exception.

Other useful extension points include:

- `perform_create(serializer)` to supply server-owned values while retaining
  the normal create flow;
- `perform_update(serializer)` for behavior immediately around saving updates;
- `get_serializer_class()` when different actions intentionally use different
  representations;
- `permission_classes` or `get_permissions()` for access control; and
- `@action` for a resource operation that is not ordinary CRUD.

Do not add a custom action merely to avoid designing a normal REST operation.
For example, changing a project name belongs in `PATCH`, not a custom
`rename_project` endpoint.

### How the router creates URLs

Register viewsets with `DefaultRouter` in `annotations/api_urls.py`, then include
those URLs at `/api/` in `config/urls.py`. The router produces consistent
collection/detail routes and names from one declaration.

```python
router.register("projects", ProjectViewSet, basename="project")
```

This registration connects the prefix `projects` to the ViewSet and generates
route names including `project-list` and `project-detail`. `basename` names the
resource for URL reversal; it is not a database table name.

The router decides which action handles each HTTP method based on whether the
URL is a collection or detail URL. The ViewSet itself does not define URL path
strings.

Do not confuse responsibilities:

- model: stored data and durable invariants;
- serializer: external fields and boundary validation;
- viewset: request behavior and queryset selection;
- router: URL mapping;
- test: observable contract.

## Part 6 — Pagination and filtering

Configure `PageNumberPagination` and a page size in `REST_FRAMEWORK`. Pagination
prevents a growing table from returning an unbounded response and gives every
collection the same envelope.

Implement only documented filters:

```text
/api/projects/?status=active
/api/dimensions/?project=<project-uuid>
/api/labels/?dimension=<dimension-uuid>
/api/subjects/?project=<project-uuid>
```

Explicit filters are easier to secure and document than passing arbitrary query
parameters into the ORM.

## Part 7 — Translate protected deletion

The model correctly raises `ProtectedError` when an in-use template is deleted.
At the HTTP boundary, catch that expected domain conflict and return:

```json
{"detail": "Templates used by projects cannot be deleted."}
```

with status 409. Do not catch every exception: unexpected defects should remain
visible to developers rather than being mislabeled as client errors.

## Part 8 — Make temporary public access explicit

DRF normally integrates with Django's authentication user model. Authentication
and auth migrations are taught in Lesson 7. For this checkpoint, configure no
authentication classes, `AllowAny`, and `UNAUTHENTICATED_USER = None`.

This is a visible temporary policy, not production security. Document that the
Lesson 6 checkpoint must not be deployed. Lesson 7 replaces it with tested
authentication and role permissions.

## Part 9 — Green, refactor, and container verification

Run:

```bash
make backend-test
make check
make container-test
git diff --check
```

Extend the smoke test to request `/api/templates/` and verify the `results`
array. This proves routing, DRF, migrations, PostgreSQL, and JSON rendering work
together in the built image. One representative endpoint is intentional: the
API suite tests all resources and is itself run inside the container. Repeating
every CRUD scenario in Bash would duplicate stronger tests. Read
[Quality and smoke tests](../DOCKER.md#quality-and-smoke-tests) for the complete
execution flow, test-layer boundaries, cleanup strategy, and best practices.

Refactor repeated setup into builders, but keep the action under test explicit.
For example, builders may create a valid project while the test shows the exact
invalid POST body.

## Part 10 — Open the pull request

Open `Lesson 6: add configuration REST API`. Include red and green evidence, an
example paginated response, the filtering contract, status-code reasoning, and
an explicit note that authentication arrives in Lesson 7.

## Acceptance criteria

- All five resources expose collection and UUID detail CRUD routes.
- Serializer fields and read-only values are explicit.
- Collections return the stable pagination envelope.
- Documented filters work and have tests.
- Invalid status, foreign key, color, and uniqueness input returns 400.
- Unknown detail objects return 404.
- Protected template deletion returns 409; normal deletion returns 204.
- Migration drift, all API/model tests, and container smoke tests pass.
- The temporary public-access policy is explicit and documented.

## Gold-standard implementation

Read this after opening your PR. The reference checkpoint is tag `lesson-06`:

```bash
git fetch --tags
git diff lesson-06 -- . ':!docs/lessons/06-DRF-API.md'
```

The gold implementation uses explicit serializers, small viewsets, router URLs,
stable pagination, allow-listed filters, and deliberate error translation. It
keeps database invariants in models while presenting useful HTTP errors at the
API boundary. Contract tests assert both status codes and response shapes.

A different abstraction is acceptable only if clients observe the same stable
contract, invalid states remain impossible, query behavior is bounded, and all
acceptance tests pass.

## What you should now be able to explain

- serializer versus model validation;
- viewset action versus router route;
- collection versus detail endpoint;
- `PUT` versus `PATCH`;
- 400 versus 404 versus 409;
- why pagination response shape is a contract;
- why foreign-key query optimization matters; and
- why authentication is explicitly temporary rather than accidentally absent.
