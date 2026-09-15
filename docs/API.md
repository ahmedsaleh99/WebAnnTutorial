# REST API

Lesson 6 exposes the configuration domain beneath `/api/`.

| Resource | Collection endpoint | Supported filter |
| --- | --- | --- |
| Project templates | `/api/templates/` | — |
| Projects | `/api/projects/` | `status` |
| Annotation dimensions | `/api/dimensions/` | `project` UUID |
| Annotation labels | `/api/labels/` | `dimension` UUID |
| Subjects | `/api/subjects/` | `project` UUID |

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

All authenticated roles may read configuration. Only administrators may create,
update, or delete it. See [Authentication and roles](AUTHENTICATION.md).
