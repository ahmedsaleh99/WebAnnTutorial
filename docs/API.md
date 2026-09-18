# REST API

Lesson 6 exposes the configuration domain beneath `/api/`.

| Resource | Collection endpoint | Supported filter |
| --- | --- | --- |
| Project templates | `/api/templates/` | — |
| Projects | `/api/projects/` | `status` |
| Annotation dimensions | `/api/dimensions/` | `project` UUID |
| Annotation labels | `/api/labels/` | `dimension` UUID |
| Subjects | `/api/subjects/` | `project` UUID |
| Tasks | `/api/tasks/` | `project` UUID |
| Video assets | `/api/video-assets/` | — |
| Video views | `/api/video-views/` | — |
| Annotation jobs | `/api/jobs/` | — |
| Annotation work items | `/api/work-items/` | — |
| Annotation results | `/api/results/` | — |

Collection endpoints support `GET` and `POST`. Detail endpoints append a UUID
and support `GET`, `PUT`, `PATCH`, and `DELETE`:

```text
/api/projects/2ad65f20-2c4c-4ed1-86a6-d1be3b177292/
```

List responses always use the pagination envelope:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": []
}
```

Successful creation returns `201`, reads and updates return `200`, successful
deletion returns `204`, invalid input returns `400`, and an unknown object
returns `404`. Deleting a template still used by a project returns `409` with a
`detail` message.

Except for login and media-cookie authorization, API endpoints require:

```text
Authorization: Token <token-key>
```

From Lesson 10, the React frontend calls relative `/api/` URLs. Vite forwards
them to local Django during development; `frontend/server.mjs` forwards them
inside Compose. The browser therefore stays on the frontend origin. A proxied
401 is still Django's authentication decision, not a frontend permission
check. The `webann_media_token` cookie remains HTTP-only and is forwarded
through the same-origin proxy when Django sets or clears it.

All authenticated roles may read configuration. Only administrators may create,
update, or delete it. See [Authentication and roles](AUTHENTICATION.md).

Workflow endpoints are assignment-scoped. Managers create tasks, media
relationships, and jobs. Annotators see only objects reachable through their
jobs, may move their job through allowed states, and may maintain only their own
result. An unassigned detail lookup returns `404` so it does not reveal whether
another user's object exists.

Projects define available subjects and a task selects a subset represented by
`TaskSubject` rows. Creating one parent job from `task` and `assigned_to`
atomically creates one work item per selected task subject. Each work item has
its own status and result.

Work-item transitions are forward-only:

```text
assigned → in_progress → completed → reviewed
```

Skipping or reversing a state returns `400`. An annotator cannot change or
delete the parent assignment.
