# Authentication and roles

## Authentication endpoints

| Method | Endpoint | Authentication | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/auth/login/` | Public | Exchange username/password for a token |
| `GET` | `/api/auth/me/` | Token | Return the current user's safe profile |
| `POST` | `/api/auth/password-change/` | Token | Validate password, rotate token, clear required-change flag |
| `POST` | `/api/auth/logout/` | Token | Revoke the current token and clear media cookie |
| `GET` | `/api/auth/media/authorize/` | HTTP-only cookie | Validate media-request identity |

Send the API token in a header:

```text
Authorization: Token 0123456789abcdef...
```

Example login body:

```json
{
  "username": "annotator",
  "password": "the-user-password"
}
```

The response contains the token and a safe user representation. It never
returns the password. Login also sets `webann_media_token` as an HTTP-only,
SameSite `Strict` cookie. JavaScript uses the response token for API headers;
the browser can attach the inaccessible cookie to later protected media
requests. HTTPS environments must set `WEBANN_SECURE_COOKIES=true` (the
default). Local HTTP Compose explicitly sets it to false.

## Roles and least privilege

Django user flags map to application roles:

| Role | `is_staff` | `is_superuser` | Configuration read | Configuration write |
| --- | --- | --- | --- | --- |
| Annotator | false | false | Allowed | Forbidden |
| Manager | true | false | Allowed | Forbidden |
| Administrator | true | true | Allowed | Allowed |

Anonymous access is rejected with 401. An authenticated user lacking permission
receives 403. Hiding a button in React later improves usability but is never an
authorization control; the backend permission remains authoritative.

## Password and token lifecycle

The login response's `must_change_password` value comes from the user's
`UserSecurity` record. If that record is absent, the API returns `true` for a
regular user or manager, and `false` for a superuser. This allows a local
superuser created with `createsuperuser` to sign in without a forced change.
An explicit record takes precedence for every role, so a
superuser given a temporary password can also be required to change it.

When provisioning an account with a temporary password, set the flag
explicitly. For the local SQLite backend, run:

```bash
DJANGO_SECRET_KEY=insecure-local-development-key DJANGO_DEBUG=true \
  .venv/bin/python backend/manage.py shell
```

Then, replacing `new_username` with the account's username:

```python
from django.contrib.auth import get_user_model
from annotations.models import UserSecurity

user = get_user_model().objects.get(username="new_username")
UserSecurity.objects.update_or_create(
    user=user, defaults={"must_change_password": True}
)
```

This sets policy for the existing account; it does not create the user. The
frontend shows the change form when the API returns `true`. The current API
does not enforce the flag on every protected endpoint, so the form is guidance
rather than a complete access restriction.

Password changes require the current password, matching new-password fields,
and Django's configured password validators. On success, Django hashes the new
password, clears `must_change_password`, deletes the old token, and issues a new
one. Logout deletes the active token. A stolen or logged token acts as a
credential until revoked, so never commit, print, or place tokens in URLs.

From Lesson 10, React keeps the API token only in component memory and sends
it in an `Authorization: Token ...` header. It does not save the token in
`localStorage`, `sessionStorage`, a URL, or a JavaScript-readable cookie.
Refreshing the page therefore requires signing in again to use the React UI,
but it does not revoke the old server token or clear the media cookie. The separate
HTTP-only media cookie is set and cleared by Django through the same-origin
frontend API proxy; React never reads it. The UI's required-password-change
screen is guidance, not server-side enforcement of that policy.

Lesson 7 demonstrates the boundary but is not the final production security
posture. Login throttling, audit events, resource-specific media authorization,
and production proxy controls are introduced with the systems they require.

For further study, start with PortSwigger's
[XSS explanation and learning material](https://portswigger.net/web-security/cross-site-scripting),
then use the [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
when reviewing frontend defenses.

For CSRF, use PortSwigger's
[CSRF explanation and examples](https://portswigger.net/web-security/csrf) to
understand how automatically sent credentials can authorize an unwanted
request. Follow it with the
[OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
for defense-in-depth guidance. In particular, remember that `HttpOnly` prevents
JavaScript from reading a cookie but does not prevent the browser from sending
it, and `SameSite` should not be the only protection for cookie-authenticated
state-changing requests.
