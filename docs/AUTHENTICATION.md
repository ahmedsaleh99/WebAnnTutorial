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

Password changes require the current password, matching new-password fields,
and Django's configured password validators. On success, Django hashes the new
password, clears `must_change_password`, deletes the old token, and issues a new
one. Logout deletes the active token. A stolen or logged token acts as a
credential until revoked, so never commit, print, or place tokens in URLs.

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
