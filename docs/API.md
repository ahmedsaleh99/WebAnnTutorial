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

Authentication is deliberately not implemented in this lesson. The API is
explicitly public for local learning; Lesson 7 replaces `AllowAny` with tested
authentication and role permissions. Do not deploy the Lesson 6 checkpoint.
