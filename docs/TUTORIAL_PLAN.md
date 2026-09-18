# Tutorial plan: build EngAnnWeb from scratch

## 1. Course goal

By the end of this tutorial, a student will have built and deployed a
multi-camera video annotation platform modeled on EngAnnWeb. More importantly,
the student will understand why the system is designed as it is and will have
practiced delivering every change through tests, code review, continuous
integration, and small pull requests.

The finished application will let administrators configure projects, subjects,
annotation dimensions, and labels; let managers ingest video, create tasks,
synchronize camera views, and assign annotation jobs; and let annotators create
frame-accurate timeline segments, notes, and bounding boxes. It will also cover
exports, audit/security controls, background media processing, authenticated
video streaming, and annotation analytics.

This is a from-scratch learning path, not a line-by-line copy of the finished
repository. Each concept is introduced before the application depends on it.
As frontend features appear, their navigation, page structure, and user
journeys should match EngAnnWeb's corresponding screens. After the shared login
and app header, each frontend lesson builds or extends **one page only**. A
page lesson includes that page's loading, empty, success, error, and permission
states, plus any small API changes it needs. Shared backend or deployment
lessons may support several future pages, but do not introduce several page UIs
at once. Unbuilt destinations remain clearly labeled placeholders. A smaller
checkpoint may omit later features, but should not invent a competing product
layout that students must eventually undo.

WebAnnTutorial is the course and reference repository. Every student creates a
separate empty GitHub repository and implements the lessons there. The student's
repository accumulates the same capabilities and essential content through the
student's own branches, pull requests, tests, and commits. See
[Student repository workflow](STUDENT_WORKFLOW.md).

## 2. Technology map

| Area | Technology | What the student will learn |
| --- | --- | --- |
| Source control | Git and GitHub | Branches, commits, pull requests, reviews, and protected branches |
| Automation | GitHub Actions | CI jobs, quality gates, artifacts, dependency caching, and deployment gates |
| Backend | Python, Django 5, Django REST Framework | Models, migrations, validation, APIs, authentication, permissions, and tests |
| Frontend | React, TypeScript, Vite | Components, hooks, state, typed API access, routing, forms, and production builds |
| Frontend testing | Vitest | Unit, component, domain-policy, and scenario tests |
| Data | PostgreSQL | Relational modeling, constraints, indexes, transactions, and persistence |
| Containers | Docker and Docker Compose | Images, services, networks, volumes, health checks, and isolated environments |
| Async work | Celery and Redis | Queues, workers, retries, idempotency, and observable background jobs |
| Production API | Gunicorn | Worker configuration and production Django serving |
| Web/media serving | Nginx | Static SPA delivery, reverse proxying, `auth_request`, and HTTP byte ranges |
| Media | FFmpeg and ffprobe | Metadata extraction, frame/time conversion, fixtures, and proxy generation |
| Object storage | boto3 and S3-compatible MinIO | Safe discovery, preview/apply imports, credentials, and object downloads |
| Security | Django/DRF and Nginx controls | Token auth, HTTP-only media cookies, RBAC, throttling, audit logs, and secrets |
| Analytics | Python statistics/domain logic | Work metrics and inter-annotator agreement |

## 3. How every lesson works

Each lesson represents one pull request. The student should:

1. read the goal and prerequisite notes;
2. create the named feature branch from the current `main` branch;
3. turn the acceptance criteria into one or more failing tests;
4. run the tests and record the expected failure (red);
5. implement the smallest change that passes (green);
6. refactor without changing behavior;
7. update relevant documentation;
8. push the branch and open a pull request using the lesson checklist;
9. respond to review and merge only after every required check passes.

Documentation-only or infrastructure lessons may use executable validation,
linters, smoke tests, or intentionally failing workflow demonstrations instead
of application unit tests. The red-green-refactor loop should still be used
whenever behavior is added.

Every lesson includes a gold-standard implementation after the student steps.
Students should attempt the work and open their pull request before reading it,
then compare implementations, explain meaningful differences, and improve their
work where appropriate. The reference is a model solution, not a requirement to
produce identical code.

The reference repository should be tagged after each completed lesson (for
example, `lesson-01`) so the instructor can publish the exact expected
checkpoint without exposing work from later lessons.

### Definition of done for every pull request

- The lesson's deliverables and acceptance criteria are satisfied.
- New behavior has tests at the lowest useful level.
- Existing backend and frontend tests pass.
- Formatting, linting, type checking, builds, and container validation pass as
  applicable.
- No credentials, generated dependencies, build output, database data, or
  uploaded media are committed.
- User-facing behavior and architectural decisions are documented.
- A frontend lesson builds or extends one page; unrelated page UI waits for its
  own lesson and pull request.
- The pull request explains the red-green-refactor evidence and includes manual
  verification steps where automation is insufficient.
- In instructor-led use, at least one independent review is completed before
  merge once branch protection is enabled. Solo-study pull requests document a
  self-review when no separate reviewer is available.

## 4. Course roadmap

The frontend page sequence is explicit. The Annotation workspace is one page
expanded across several lessons; each of those lessons changes that page only.

| Page | Lesson checkpoint |
| --- | --- |
| Sign-in and password change | 10 |
| Project templates | 11 |
| Projects | 12; portability controls in 27 |
| Tasks | 13; portability controls in 28 |
| Users | 14 |
| Jobs / My jobs | 15; portability controls in 29 |
| Videos | 19 |
| Annotation workspace | 21–25 |
| Logs | 31 |
| Analytics | 33 |
| Agreement | 34 |

### Phase A — Delivery foundations

#### Lesson 1 — Repository workflow and CI/CD foundation

**Branch:** `lesson/01-ci-cd-foundation`

**Goal:** Turn an empty repository into a safe collaborative workspace in which
every later lesson is delivered through a verifiable pull request.

**Concepts:** Git history, feature branches, pull requests, CI versus CD,
workflow triggers, jobs and steps, least-privilege workflow permissions,
required checks, branch protection, secrets, dependency automation, and the
difference between build artifacts and deployments.

**Deliverables:**

- repository README, license decision, `.gitignore`, `.editorconfig`, and
  contribution guide;
- pull request template with test evidence and lesson acceptance checklists;
- GitHub Actions CI workflow triggered for pull requests and `main`;
- an initial repository validation script/check that works before application
  code exists;
- documented required-check and protected-branch setup;
- a staged CD workflow skeleton with environments and manual approval, but no
  production credentials or live deployment yet;
- dependency/security update configuration.

**Acceptance criteria:** A deliberately invalid documentation or repository
change makes CI fail; correcting it makes CI pass. CI has read-only permissions
unless a job documents why it needs more. Pull requests cannot be merged until
the required check passes. Instructor-led repositories also require approval
from a reviewer with write access; solo-study repositories document a
self-review. The CD skeleton cannot deploy from an unreviewed pull request and
clearly identifies where environment secrets will eventually live.

#### Lesson 2 — Local developer tooling and quality gates

**Branch:** `lesson/02-developer-tooling`

**Goal:** Create one repeatable interface for local and CI checks.

**Concepts:** reproducible commands, formatting versus linting, static analysis,
pre-commit checks, version pinning, and fast feedback.

**Deliverables:** Python and Node runtime version files, task commands in a
Makefile, dependency-pinned pre-commit automation, shell syntax checks, and
documentation for setup and troubleshooting. Language-specific linting and type
checking are added when the Django and React source trees are introduced.

**Acceptance criteria:** one command runs every check available at this stage;
CI invokes the same commands rather than duplicating their logic; an introduced
format or lint violation is detected locally and in CI.

#### Lesson 3 — Docker fundamentals and Compose architecture

**Branch:** `lesson/03-docker-compose`

**Goal:** Learn containers before using them to host the application stack.

**Concepts:** images, layers, containers, build context, networks, volumes,
health checks, environment variables, Compose dependencies, and development
versus production configuration.

**Deliverables:** minimal backend and frontend Dockerfiles, Compose services,
health checks, `.dockerignore` files, and container smoke tests.

**Acceptance criteria:** the stack builds from a clean checkout, services become
healthy, source changes use the documented development loop, and Compose config
validation runs in CI.

### Phase B — Learn the backend by building the core domain

#### Lesson 4 — Django fundamentals and the first test

**Branch:** `lesson/04-django-foundations`

**Goal:** Create the Django project and understand its request lifecycle.

**Concepts:** Python environments, projects versus apps, settings, URLs, views,
management commands, Django's test runner, and red-green-refactor.

**Deliverables:** `backend/config`, the annotation app, a health endpoint, and
backend CI.

**Acceptance criteria:** a health-endpoint test is seen failing before the view
is implemented; it then passes locally and in CI; configuration comes from the
environment rather than committed secrets.

#### Lesson 5 — PostgreSQL, models, and migrations

**Branch:** `lesson/05-postgres-domain-model`

**Goal:** Model project templates, projects, dimensions, labels, and subjects.

**Concepts:** relational design, foreign keys, many-to-many relationships, JSON
fields, constraints, indexes, transactions, migrations, and test databases.

**Deliverables:** PostgreSQL Compose service, initial models/migrations, factories
or builders, and model tests.

**Acceptance criteria:** invalid and duplicate domain states are rejected at the
appropriate layer; migrations apply to an empty database; tests use an isolated
database; a short data-model diagram is documented.

#### Lesson 6 — REST APIs, serialization, and validation

**Branch:** `lesson/06-drf-api`

**Goal:** Expose the configuration domain through a consistent JSON API.

**Concepts:** DRF serializers, viewsets, routers, status codes, pagination,
filtering, API contracts, and boundary validation.

**Deliverables:** CRUD endpoints for templates, projects, dimensions, labels,
and subjects plus API tests.

**Acceptance criteria:** success, validation failure, not-found, and deletion
rules are tested; responses have stable shapes; `makemigrations --check` and
backend tests run in CI.

#### Lesson 7 — Authentication, roles, and permissions

**Branch:** `lesson/07-auth-rbac`

**Goal:** Protect the API for annotator, manager, and administrator roles.

**Concepts:** Django users, DRF token authentication, authorization at the API
boundary, password lifecycle, cookies, and least privilege.

**Deliverables:** login/current-user/password-change/logout endpoints, role
policies, media authorization endpoint, and permission-matrix tests.

**Acceptance criteria:** anonymous access fails securely; every role is tested
for allowed and forbidden operations; credentials never appear in logs or test
snapshots; backend enforcement does not rely on the UI.

#### Lesson 8 — Tasks, video assets, views, and annotation jobs

**Branch:** `lesson/08-workflow-models`

**Goal:** Complete the main work-assignment domain.

**Concepts:** aggregate boundaries, state machines, scoped queries, uniqueness,
and safe lifecycle transitions.

**Deliverables:** task, task-subject, video asset, video view, parent annotation
job, per-subject work item, and result models; migrations; APIs; and tests.

**Acceptance criteria:** each task has valid project-scoped media/subjects;
duplicate assignments are prevented; annotators see only assigned work;
work-item status transitions follow documented rules.

### Phase C — Learn the frontend and connect the stack

#### Lesson 9 — React, TypeScript, Vite, and Vitest fundamentals

**Branch:** `lesson/09-react-foundations`

**Goal:** Build a tested browser application shell.

**Concepts:** components, props, state, hooks, effects, TypeScript types, Vite,
the DOM, accessible markup, and Vitest.

**Deliverables:** Vite React application, dashboard shell, navigation policy,
error boundary, basic styling, and frontend CI.

**Acceptance criteria:** navigation is driven by a tested pure policy; the app
type-checks, tests, and builds; a component failure is handled by the error
boundary; keyboard and semantic HTML basics are verified.

#### Lesson 10 — Typed API client and authentication UI

**Branch:** `lesson/10-frontend-api-auth`

**Goal:** Connect React to Django without weakening the API contract.

**Concepts:** `fetch`, typed DTOs, async state, error handling, authentication
state, CORS, proxy configuration, and safe token handling.

**Deliverables:** typed API module, sign-in/password-change flows, auth gate,
role-aware navigation, and tests with mocked network boundaries.

**Acceptance criteria:** loading, success, validation, unauthorized, and network
failure paths are tested; role-hidden controls match backend policy but do not
replace it; local proxying works through Compose.

#### Lesson 11 — Project templates page

**Branch:** `lesson/11-project-admin`

**Goal:** Build the Project templates page beneath the established login and
app header.

**Concepts:** forms, controlled inputs, reusable components, optimistic versus
pessimistic updates, API integration tests, and accessible feedback.

**Deliverables:** template search, status/type filters, cards, create/edit/delete
dialog, and the API fields those controls need. Projects, Tasks, and Jobs
remain later workflows.

**Acceptance criteria:** an administrator can create, filter, edit, and delete
templates; edits increment version; invalid input is explained without losing
form state; backend and frontend tests cover the template journey.

#### Lesson 12 — Projects page

**Branch:** `lesson/12-projects-page`

**Goal:** Match the EngAnnWeb Projects page and its project settings dialog.

**Concepts:** dependent data, scoped forms, tabs, and read-only role states.

**Deliverables:** project cards, search/status/template filters, project creation,
and General, Dimensions & labels, and Subjects settings sections. Keep all
project setup inside this page; do not build the Tasks page here.

**Acceptance criteria:** an administrator can create and configure a project
from a template; managers can inspect setup without write controls; invalid
relationships are rejected by the API and explained in the dialog.

#### Lesson 13 — Tasks page

**Branch:** `lesson/13-tasks-page`

**Goal:** Match the task list and task editor for configured projects.

**Concepts:** project-scoped choices, task state, and list filtering.

**Deliverables:** task cards, search/project/status filters, task creation and
editing, and subject selection. Media synchronization actions can remain
placeholders until their backend lessons.

**Acceptance criteria:** a manager can create and find a task for one project;
subjects from other projects cannot be selected or submitted; annotators do
not receive task-management controls.

#### Lesson 14 — Users page

**Branch:** `lesson/14-users-page`

**Goal:** Build the administrator's user-management page before job assignment.

**Concepts:** account provisioning, role changes, and password lifecycle.

**Deliverables:** user list and filters, create/edit controls, role display, and
first-login password-change handling using the existing auth policy.

**Acceptance criteria:** an administrator can provision an annotator and
verify its role and password-change state; managers and annotators cannot
modify users through either the page or API.

#### Lesson 15 — Jobs page

**Branch:** `lesson/15-jobs-page`

**Goal:** Match the staff and annotator assignment views.

**Concepts:** assignment boundaries, role-scoped lists, and work-item status.

**Deliverables:** job cards, search/task/status/annotator filters, assignment
creation for managers, and an annotator's My jobs view. Opening the annotation
workspace remains a later lesson.

**Acceptance criteria:** managers can assign eligible tasks to annotators;
annotators see only their own jobs; duplicate or invalid assignments return
useful errors without inventing a finished annotation workspace.

### Phase D — Media and asynchronous systems

#### Lesson 16 — Celery, Redis, and reliable background jobs

**Branch:** `lesson/16-celery-redis`

**Goal:** Move slow media work outside HTTP requests.

**Concepts:** brokers, workers, task states, retries, idempotency, timeouts,
failure reporting, and testing tasks synchronously.

**Deliverables:** Redis and worker services, Celery configuration, a demonstrator
task, media-processing state transitions, and worker tests.

**Acceptance criteria:** submitting work returns promptly; repeated delivery
does not corrupt state; failures are visible and retry policy is bounded; the
API remains usable when a worker is temporarily unavailable.

#### Lesson 17 — FFmpeg/ffprobe media pipeline

**Branch:** `lesson/17-media-pipeline`

**Goal:** Safely inspect video and prepare browser-compatible media.

**Concepts:** codecs/containers, FPS, frame count, duration, subprocess safety,
temporary files, checksums, fixtures, and proxy generation.

**Deliverables:** generated tiny test videos, metadata parser, processing task,
video status/log API, and media-pipeline tests.

**Acceptance criteria:** metadata is stable for known fixtures; frame/time
conversion handles boundaries; commands do not interpolate untrusted shell
text; failed processing leaves an actionable error and no false `ready` state.

#### Lesson 18 — Secure uploads, remote sources, and MinIO

**Branch:** `lesson/18-media-ingestion`

**Goal:** Ingest reusable project media from controlled sources.

**Concepts:** multipart upload, SSRF risk, allowlists, size limits, TLS choices,
S3 APIs, pagination, credentials, and preview/apply workflows.

**Deliverables:** upload and remote-import APIs, boto3/MinIO discovery, a
side-effect-free batch preview, explicit apply action, and tests with fakes.

**Acceptance criteria:** unsupported schemes/hosts and oversized downloads are
rejected; preview writes nothing; apply is idempotent; credentials and signed
query strings do not enter filenames or logs.

#### Lesson 19 — Videos page

**Branch:** `lesson/19-videos-page`

**Goal:** Match the media list and ingestion controls on the Videos page.

**Concepts:** upload progress, processing states, preview/apply, and retry UX.

**Deliverables:** searchable video cards, status feedback, upload and remote
source controls, and MinIO preview/apply actions using Lessons 16–18 APIs.

**Acceptance criteria:** a manager can ingest and find media without leaving
the Videos page; failed processing is visible and retryable; preview performs
no writes; later annotation controls are not added to this page.

#### Lesson 20 — Nginx, authenticated range requests, and Gunicorn

**Branch:** `lesson/20-production-serving`

**Goal:** Serve the SPA, API, and large media efficiently in a production-like
stack.

**Concepts:** reverse proxies, SPA fallback, HTTP ranges, `auth_request`, caching,
Gunicorn workers/threads, static builds, and read-only mounts.

**Deliverables:** production frontend image, Nginx configs, Gunicorn command,
authenticated media cookie flow, and HTTP smoke tests.

**Acceptance criteria:** direct unauthorized media access fails; an authorized
range request returns correct partial-content headers; the SPA and `/api`
routes work behind one origin; media is mounted read-only in Nginx.

### Phase E — The annotation engine

#### Lesson 21 — Frame-accurate playback as tested domain logic

**Branch:** `lesson/21-frame-playback`

**Goal:** Begin the Annotation workspace page with frame-accurate playback.
Frame number, not floating-point video time, is the source of truth.

**Concepts:** pure domain functions, browser media events, rounding/clamping,
adapters, deterministic tests, and keyboard controls.

**Deliverables:** video component, playback adapter, frame/time policies,
controls, shortcuts, and unit tests.

**Acceptance criteria:** frame conversion and edge cases are deterministic;
stale media events cannot overwrite a newer seek; shortcuts do not fire while
editing text; manual verification works on generated fixtures.

#### Lesson 22 — Multi-camera synchronization

**Branch:** `lesson/22-synchronization`

**Goal:** Extend the Annotation workspace page with synchronized camera views
on one committed frame.

**Concepts:** checkpoint interpolation, timestamp mapping, coordinator state
machines, readiness barriers, seek generations, buffering, and bounded recovery.

**Deliverables:** checkpoint models/APIs, project-type synchronization policies,
synchronization workspace, coordinator, and scenario tests.

**Acceptance criteria:** mappings interpolate and clamp correctly; hidden views
cannot block playback; late seek events are ignored; buffering pauses all active
views and resumes only when the readiness barrier opens.

#### Lesson 23 — Timeline segments with red-green-refactor

**Branch:** `lesson/23-timeline-annotations`

**Goal:** Add continuous, frame-accurate tracks to the Annotation workspace page.

**Concepts:** temporal invariants, transaction boundaries, client/server
validation, command modeling, undo/redo, autosave, and race conditions.

**Deliverables:** timeline models/APIs, interactive timeline, label selection,
boundary editing, notes, history, autosave, and tests.

**Acceptance criteria:** tracks obey start/continuity/end rules; concurrent or
invalid edits cannot silently corrupt a track; undo/redo preserves explicit
boundaries and notes; completed jobs are read-only.

#### Lesson 24 — Bounding-box tracks and keyframes

**Branch:** `lesson/24-bounding-boxes`

**Goal:** Add subject-position tracks to the Annotation workspace page.

**Concepts:** normalized coordinates, pointer geometry, interpolation,
keyframes, visibility states, overlays, and zoom transforms.

**Deliverables:** box-track/keyframe models and APIs, drawing/editing overlay,
interpolation policies, synchronization-box propagation, and tests.

**Acceptance criteria:** geometry remains within 0–100 percent; reverse-direction
dragging works; hidden states and interpolation are deterministic; a sync box is
copied/updated for applicable annotation jobs.

#### Lesson 25 — Resilience, caching, and annotation UX

**Branch:** `lesson/25-resilient-workspace`

**Goal:** Make long sessions on the Annotation workspace page safe and efficient.

**Concepts:** local persistence, service workers/browser storage, cache
validation, quota policy, recovery, error notifications, accessibility, and
performance measurement.

**Deliverables:** optional bounded media cache, recovery flows, fullscreen
workspace, shortcuts reference, and consistent notifications.

**Acceptance criteria:** missing/corrupt cache data falls back to authenticated
streaming; cache use is explicit and capped; refresh/retry does not lose saved
work; errors are visible, dismissible, and do not expose secrets.

### Phase F — Operations, security, and insight

#### Lesson 26 — Exports, imports, and durable data contracts

**Branch:** `lesson/26-data-portability`

**Goal:** Produce self-describing research data and safely restore annotations.

**Concepts:** schema versioning, serialization, validation, authorization,
streaming downloads, compatibility, and round-trip tests.

**Deliverables:** backend project/task/job JSON exports and validated annotation
import. Page controls are added in separate Projects, Tasks, and Jobs lessons.

**Acceptance criteria:** exports contain configuration and annotation context;
an export/import round trip preserves supported data; malformed or unauthorized
imports make no partial changes; schema/version is documented.

#### Lesson 27 — Projects page portability controls

**Branch:** `lesson/27-projects-portability`

**Goal:** Add project export/import actions to the existing Projects page.

**Deliverables:** project-scoped controls, confirmation, progress and error
states, and tests for protected or malformed requests.

**Acceptance criteria:** project actions use Lesson 26 contracts and do not
change the Tasks or Jobs pages.

#### Lesson 28 — Tasks page portability controls

**Branch:** `lesson/28-tasks-portability`

**Goal:** Add task export/import actions to the existing Tasks page.

**Deliverables:** task-scoped controls, validation feedback, and page tests.

**Acceptance criteria:** task actions use Lesson 26 contracts and leave the
Projects and Jobs pages unchanged.

#### Lesson 29 — Jobs page portability controls

**Branch:** `lesson/29-jobs-portability`

**Goal:** Add assignment export/import actions to the existing Jobs page.

**Deliverables:** job-scoped controls, protected import feedback, and tests.

**Acceptance criteria:** a user can only export or import permitted jobs;
invalid imports leave existing annotations intact.

#### Lesson 30 — Security hardening and auditability

**Branch:** `lesson/30-security-audit`

**Goal:** Add layered, testable protections for an internet-facing service.

**Concepts:** threat modeling, database-backed login throttling, proxy rate
limits, content-free audit events, secure headers/cookies, dependency scanning,
and secret management.

**Deliverables:** threat model, escalating login throttle, audit middleware and
admin event API, Nginx burst protection, and security CI checks. The Logs page
is a separate lesson.

**Acceptance criteria:** throttling works across API workers without revealing
account existence; mutation/auth/error events exclude bodies and credentials;
only administrators can read audit events; dependency and secret scans gate PRs.

#### Lesson 31 — Logs page

**Branch:** `lesson/31-logs-page`

**Goal:** Build the administrator's audit-log page from Lesson 30's event API.

**Deliverables:** event list, filters, pagination, and content-free detail view.

**Acceptance criteria:** administrators can investigate activity without
exposing request bodies or credentials; other roles cannot read the page or API.

#### Lesson 32 — Metrics and agreement APIs

**Branch:** `lesson/32-metrics-agreement-api`

**Goal:** Derive useful, privacy-conscious quality and efficiency measures.

**Concepts:** heartbeat sampling, aggregation boundaries, Cohen's kappa,
Krippendorff's alpha with label distances, gamma agreement, sampling, and
statistical edge cases.

**Deliverables:** work/operation/segment metrics and agreement APIs, with tests
based on hand-calculated examples. Their pages come next, one at a time.

**Acceptance criteria:** known fixtures produce expected statistics; incomplete
overlap and empty data are handled explicitly; annotators cannot access admin
analytics; collected work metrics avoid annotation content.

#### Lesson 33 — Analytics page

**Branch:** `lesson/33-analytics-page`

**Goal:** Present Lesson 32's work and quality metrics on the Analytics page.

**Deliverables:** filters, summaries, charts, loading and empty states, and
tests against known metric responses.

**Acceptance criteria:** administrators can inspect useful metrics without
seeing annotation content; this lesson does not build the Agreement page.

#### Lesson 34 — Agreement page

**Branch:** `lesson/34-agreement-page`

**Goal:** Present inter-annotator agreement on its own page.

**Deliverables:** comparison controls, scores, method explanations, and
insufficient-data states using Lesson 32's agreement API.

**Acceptance criteria:** known comparisons match backend fixtures; incomplete
overlap is explained; no Analytics page UI is changed in this lesson.

#### Lesson 35 — Production CD, observability, and capstone release

**Branch:** `lesson/35-production-release`

**Goal:** Promote a reviewed commit safely from CI to a production environment.

**Concepts:** immutable artifacts, image tags/digests, environments, approvals,
database migration strategy, backups, health checks, rollback, logs, and release
notes.

**Deliverables:** complete CI/CD workflow, image build/publish stage, protected
staging/production deployment jobs, smoke test, backup/restore runbook, rollback
procedure, and tagged course release.

**Acceptance criteria:** deployment uses the exact artifact tested by CI;
production requires protected-environment approval; migrations and rollback are
documented and rehearsed in staging; failed health checks stop promotion; no
server credential is exposed to pull-request workflows.

## 5. Pull request contract

Every lesson pull request should contain:

```markdown
## Lesson goal

## Deliverables
- [ ] ...

## TDD evidence
- Failing test/check and why it failed:
- Passing test/check after implementation:
- Refactoring performed:

## Verification
- [ ] Local quality command passes
- [ ] CI passes
- [ ] Manual checks (if any) are documented

## Security/data considerations

## Screenshots or API examples (when useful)
```

Keep a lesson focused. If its pull request becomes too large to review, split
it into numbered parts such as `lesson/23a-timeline-domain` and
`lesson/23b-timeline-ui`; each part must still leave `main` working. A split
must not combine multiple page UIs to save lesson numbers.

## 6. Teaching and review strategy

Each lesson document should include prerequisites, a concept explanation, an
architecture sketch where useful, setup steps, the first failing test,
incremental implementation checkpoints, common failure modes, acceptance
criteria, review questions, optional extensions, and a gold-standard solution
with its design reasoning. Solutions should explain tradeoffs, not merely
provide code to paste.

Review should emphasize observable behavior and maintainability:

- Does the test describe the requirement rather than the implementation?
- Is validation enforced at the system boundary closest to the invariant?
- Does authorization remain correct if the UI is bypassed?
- Can the change be operated, diagnosed, and rolled back?
- Is the pull request small enough for a reviewer to understand confidently?

## 7. Planned repository structure

As the course grows, the tutorial repository will use this structure:

```text
.github/                   workflows and pull request template
backend/                   Django/DRF application and worker code
frontend/                  React/TypeScript/Vite application
docs/
  lessons/                 one detailed guide per lesson
  architecture/            evolving diagrams and decisions
  TUTORIAL_PLAN.md          this roadmap
nginx/                     application and media-serving configuration
scripts/                   validation, fixtures, and deployment helpers
test-videos/               generated, redistributable media fixtures
docker-compose.yml         local integrated stack
```

The next new checkpoint after the current Project templates lesson is
**Lesson 12 — Projects page**. Lessons 1–11 remain the foundation for students
starting from an empty repository.
