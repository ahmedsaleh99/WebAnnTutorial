# Lesson 7 — Authentication, roles, and permissions

## Goal

Replace Lesson 6's temporary public API with token authentication and
backend-enforced role permissions. Implement login, current-user,
password-change, logout, and media-cookie authorization through tests first.

**Branch:** `lesson/07-auth-rbac`

**Prerequisite:** Lesson 6 is merged and tagged; `make check` and
`make container-test` pass.

## Deliverables

- Django authentication and DRF token applications and migrations;
- authenticated-by-default API settings;
- annotator, manager, and administrator role mapping;
- an administrator-write/authenticated-read permission class;
- login, current-user, password-change, and logout endpoints;
- an HTTP-only media identity cookie and authorization endpoint;
- per-user required-password-change state;
- token rotation and revocation;
- authentication and permission-matrix tests; and
- documented API security contracts.

## Conceptual foundation

Read this section before implementing the lesson. Security code is difficult to
evaluate if authentication, authorization, credentials, roles, and browser
security are treated as interchangeable ideas.

### Identity, credentials, authentication, and authorization

An **identity** is an application account, such as the Django user named
`annotator`. A **credential** is evidence presented to prove control of that
identity. Passwords, API tokens, and browser cookies can all carry credentials,
but they are not the identity itself.

**Authentication** verifies a credential and establishes an identity:

```text
present token
    → find matching token record
    → confirm its user is active
    → request.user becomes that user
```

**Authorization** evaluates the established identity, requested action, and
sometimes the requested object:

```text
authenticated manager + GET templates  → allow
authenticated manager + POST template  → deny
authenticated admin   + POST template  → allow
```

**Validation** checks the proposed data after access is allowed:

```text
authenticated admin + POST invalid status
    → authentication succeeds
    → authorization succeeds
    → serializer validation fails with 400
```

This order matters. The server should not reveal validation details for a
protected operation to a caller who is not allowed to perform it.

### Authentication is request-scoped

Logging in does not cause the server to remember a connection permanently.
HTTP requests are independent. Login issues a credential, and the client must
present that credential on later requests:

```text
POST /api/auth/login/ + username/password
    → server verifies password hash
    → server returns token T

GET /api/projects/ + Authorization: Token T
    → DRF verifies T again
    → request.user is established for this request
    → permission check runs
```

The login endpoint does not authorize future operations by itself. It only
creates or returns a token that can authenticate later requests.

### How DRF processes a protected request

For `POST /api/templates/`, the relevant pipeline is:

```text
Django URL resolver
    → DRF ViewSet dispatch
    → authentication classes
    → permission classes
    → serializer validation
    → ViewSet action and database write
    → serializer output
    → HTTP response
```

If token authentication fails, processing stops with 401. If authentication
succeeds but the role permission fails, it stops with 403. The serializer and
database write are reached only after both gates pass.

DRF stores the results on the request:

- `request.user`: the authenticated Django user;
- `request.auth`: the credential object, which is a DRF `Token` here.

The logout and password-change views use `request.auth` to revoke exactly the
credential used for the request.

### Token authentication versus session authentication

Django commonly authenticates browser applications with a session cookie. DRF
also supports token authentication. They have different mechanics:

| Concern | Session authentication | DRF token authentication |
| --- | --- | --- |
| Credential sent as | Cookie | `Authorization` header |
| Server-side record | Session | Token |
| Browser sends automatically | Yes | No; JavaScript/client adds header |
| CSRF protection normally required | Yes, for unsafe cookie-authenticated requests | Not for a token sent only in a custom header |
| Revocation | Delete session | Delete token |

This lesson chooses DRF tokens because they make API authentication explicit
and are simple to inspect while learning. DRF's built-in token model generally
stores a long-lived token record for each user. It is not a complete replacement
for OAuth, short-lived access tokens, refresh-token rotation, device sessions,
or centralized identity systems. Those would be justified by different
production requirements, not added only for complexity.

A token is a **bearer credential**: possession is enough to use it. Therefore it
must be handled like a password. HTTPS is required outside local development;
tokens must not appear in URLs, logs, analytics, screenshots, or commits.

### Passwords are verified, not decrypted

Django does not need to recover a user's original password. `set_password()`
generates a salted, computationally expensive one-way hash and stores the
encoded result. During login, `authenticate()` hashes the supplied candidate
using the recorded algorithm and parameters and compares it safely.

```text
raw password → password hasher + unique salt → encoded hash stored in database
```

A salt prevents users with the same password from having identical stored
hashes and makes precomputed lookup attacks more expensive. A slow password
hash is intentional: a small cost during legitimate login creates a large cost
for offline guessing.

Never do this:

```python
user.password = new_password
```

It bypasses Django's hashing format. Use:

```python
user.set_password(new_password)
```

Password **validators** are a separate layer from hashing. Hashing safely stores
whatever password it receives; validators reject weak, overly similar, common,
or entirely numeric choices. Django does not automatically run password
validators every time `set_password()` is called, so this lesson explicitly
calls `validate_password()` in the password-change flow.

### Authentication state versus account policy state

Django's user model owns general identity fields and the password hash. WebAnn's
`UserSecurity` model owns application-specific policy state:

```text
Django User 1 ─── 0..1 UserSecurity
                       └── must_change_password
```

`must_change_password=True` does not mean the current password is invalid. It
means the account is authenticated but application policy requires a password
change before normal use. The backend returns the flag so the future frontend
can guide the user. Sensitive endpoints must ultimately enforce such policy on
the backend too; a frontend redirect alone is not security enforcement.

The one-to-one relationship avoids modifying Django's built-in user model at
this stage and guarantees at most one security-policy record per user.

### RBAC and least privilege

Role-based access control (RBAC) assigns permissions to roles and roles to
users. It avoids scattering username checks through views:

```text
user → role → permitted actions
```

The Lesson 7 policy is intentionally small:

```text
annotator → read configuration
manager   → read configuration
admin     → read and modify configuration
```

This follows **least privilege**: grant only the capabilities currently needed.
A manager does not receive configuration writes merely because that role is
more trusted than an annotator. Later lessons can add narrowly justified manager
operations without granting blanket administrator access.

The project maps roles to Django flags for now. `is_staff` normally means access
to Django's administrative site; this tutorial also interprets it as manager.
`is_superuser` represents application administrator. This is a deliberate
course convention that must remain centralized and tested. If future role rules
become more complex or users need multiple roles, a dedicated role/permission
model would be clearer than accumulating flag combinations.

### View-level and object-level authorization

`IsAdminOrReadOnly.has_permission()` is a **view-level** permission. It answers
whether the role may use an HTTP method on that resource type. It does not
inspect a particular project.

DRF can also call `has_object_permission()` after retrieving an object. That is
needed for rules such as “an annotator may read only projects assigned to them.”
Another essential technique is queryset scoping: omit objects the user may not
see from `get_queryset()` so list and detail access use the same boundary.

Lesson 7 has no assignments yet, so it enforces view-level role permissions.
Lesson 8 introduces assignment-bearing objects and can add object/queryset
scope. Do not invent object authorization without the relationships required to
express it correctly.

### Why both 401 and 403 matter

These responses communicate different failures:

| Status | Meaning in this lesson | Example |
| --- | --- | --- |
| 401 Unauthorized | No acceptable authentication credential was established | Missing or invalid token |
| 403 Forbidden | Identity was established, but the operation is not permitted | Manager tries to create template |

Despite its historical name, 401 means “authentication required or failed.” A
401 response should identify the supported authentication scheme without
revealing account secrets. A 403 response tells an authenticated client that
retrying with the same identity will not make that action valid.

The difference is useful to clients: a 401 may trigger sign-in, while a 403
should display an insufficient-permission message.

### Header token versus HTTP-only media cookie

The course uses two transports for the same token because the consumers differ:

```text
React/API request → Authorization header
browser media request → HTTP-only cookie → authorization endpoint
```

JavaScript can read a token returned in JSON and add it to an API header. That
also means an XSS vulnerability could steal it, so frontend output escaping,
dependency safety, and careful storage still matter.

Before continuing, read PortSwigger Web Security Academy's
[What is cross-site scripting (XSS) and how to prevent it?](https://portswigger.net/web-security/cross-site-scripting).
It explains reflected, stored, and DOM-based XSS with concrete examples. Then
use the [OWASP Cross-Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
as the defensive reference for context-aware output encoding, safe browser APIs,
HTML sanitization, and Content Security Policy as defense in depth. The first
resource teaches the vulnerability; the second is a practical implementation
checklist. Do not test attack payloads against systems you do not own or have
explicit permission to assess.

An HTTP-only cookie cannot be read through ordinary JavaScript, reducing token
theft through XSS. However, the browser attaches cookies automatically, which
creates cross-site request risks. `SameSite=Strict` reduces cross-site sending,
and `Secure` prevents transmission over plain HTTP. `HttpOnly` does not stop
CSRF, `SameSite` does not repair XSS, and none of these flags replace HTTPS.
Each flag addresses a different threat.

CSRF, or cross-site request forgery, happens when an attacker causes a signed-in
browser to send an unwanted request to another site. If authentication depends
on a cookie, the browser may attach that cookie automatically; the server can
then mistake the attacker's request for an intentional request from the user.
`HttpOnly` does not prevent this because the attacker does not need to read the
cookie. They only need the browser to send it.

Read PortSwigger Web Security Academy's
[CSRF explanation and examples](https://portswigger.net/web-security/csrf) for
the attack conditions and request flow. Then use the
[OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
as the implementation reference. Important defenses include framework-provided
CSRF tokens, appropriate `SameSite` cookies, origin verification, and custom
request headers. These defenses should be layered; `SameSite` alone is not a
complete CSRF strategy.

The distinction in this lesson is important:

- browsers attach matching cookies automatically, so cookie-authenticated
  state-changing requests need explicit CSRF protection;
- another website cannot normally make the browser add WebAnn's token to a
  JavaScript-controlled `Authorization` header, so the general JSON API is not
  exposed in the same way; and
- the cookie-backed media authorization endpoint is a read-only `GET` that only
  reports authorization status. It must never change application state.

If a later lesson authenticates `POST`, `PUT`, `PATCH`, or `DELETE` requests
with cookies, add and test CSRF protection at that point. Only practise CSRF
attacks in intentionally vulnerable labs or systems you are authorized to test.

The media authorization endpoint returns only a status. It does not return the
token or media bytes. In this lesson it proves that the cookie maps to an active
identity. Later resource authorization must additionally ask whether that user
may access the exact requested media object.

### Secure defaults and narrow exceptions

The global DRF default is `IsAuthenticated`. A developer adding a new ViewSet
therefore gets protection without remembering to opt in. Public access requires
an explicit, reviewable `AllowAny`, currently limited to login and media-cookie
validation.

This pattern is safer than globally allowing requests and attempting to protect
each endpoint individually. Security should fail closed: missing configuration,
unknown credentials, and unrecognized roles should deny access.

### How to test security boundaries

Security tests should cover the matrix, not only one successful administrator:

```text
anonymous × read
annotator × read/write
manager   × read/write
admin     × read/write
```

Use real tokens for authentication tests and permission-matrix tests so token
parsing and lookup are included. `force_authenticate()` is appropriate in the
existing CRUD contract tests: those tests need an authorized identity but are
not responsible for retesting the authentication mechanism.

Also test credential lifecycle transitions:

- valid and invalid login;
- inactive account;
- old token before and after rotation;
- token before and after logout;
- cookie missing, valid, and tied to an inactive user;
- wrong current password, mismatched confirmation, and weak new password.

Tests should assert observable responses and persisted state without printing
raw credentials. A passing UI test cannot prove backend authorization, because
an attacker can call the API without using the UI.

## Part 1 — Create the branch and threat model

```bash
git switch main
git pull --ff-only
make check
make container-test
git switch -c lesson/07-auth-rbac
```

Before coding, list the boundaries being protected:

- authentication answers **who is making the request?**
- authorization answers **may that identity perform this operation?**
- validation answers **is the requested data acceptable?**

These are separate checks. A valid token does not make every operation allowed,
and a valid request body does not make an anonymous request authenticated.

## Part 2 — Write failing security tests (red)

Create `annotations/tests/test_auth.py`. Specify these contracts before adding
auth routes:

1. anonymous configuration reads return 401;
2. annotator, manager, and administrator tokens may read configuration;
3. annotator and manager writes return 403;
4. administrator writes succeed;
5. valid login returns a token and safe user data but never a password;
6. invalid credentials and inactive users receive the same generic error;
7. `/auth/me/` requires a valid token;
8. password change rotates the token and clears the required-change flag;
9. logout revokes the current token;
10. media authorization requires a valid cookie for an active user.

Run `make backend-test`. The meaningful red result is that anonymous access
still returns 200 or auth routes return 404. Record those contract failures.

Update Lesson 6 API test classes to authenticate an administrator in `setUp()`.
Those tests describe valid CRUD behavior, not permission behavior; the new
permission matrix owns authorization cases.

## Part 3 — Enable Django users and token authentication

Add these applications to `INSTALLED_APPS`:

```python
"django.contrib.auth",
"django.contrib.contenttypes",
"rest_framework.authtoken",
```

Configure DRF globally:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated"
    ],
    # existing pagination settings
}
```

Every DRF endpoint now requires authentication unless it explicitly declares a
different permission. This secure default prevents a newly added ViewSet from
accidentally becoming public.

Token authentication expects:

```text
Authorization: Token <token-key>
```

DRF looks up the token, assigns its user to `request.user`, and assigns the token
to `request.auth`. Missing or invalid credentials return 401 before the ViewSet
action runs.

## Part 4 — Define roles and the permission matrix

For this application, map Django's existing flags rather than creating a second
role field:

```text
is_superuser=True                 → administrator
is_staff=True, is_superuser=False → manager
both false                        → annotator
```

Create `IsAdminOrReadOnly`. Its `has_permission()` should require an
authenticated user and then allow either a safe method or a superuser:

```text
GET, HEAD, OPTIONS → every authenticated role
POST, PUT, PATCH, DELETE → administrator only
```

Apply it to every configuration ViewSet. `SAFE_METHODS` expresses read intent
more clearly than manually comparing only `GET`.

The expected denial codes differ:

- 401: the server does not know a valid identity;
- 403: identity is known, but that role cannot perform the operation.

Test the matrix using real tokens and `subTest()` so failures name the affected
role. Frontend visibility in Lesson 10 will mirror this policy for usability,
but the server remains the enforcement point.

## Part 5 — Add required-password-change state

Create `UserSecurity` with a one-to-one relationship to Django's user and a
`must_change_password` Boolean. One-to-one means each user has zero or one
security record and each record belongs to exactly one user.

Generate and review `0002_usersecurity.py`:

```bash
DJANGO_SECRET_KEY=test-only-not-a-secret \
  .venv/bin/python backend/manage.py makemigrations annotations
```

Do not store password text in this model. Django's user stores a salted password
hash produced by `set_password()`.

## Part 6 — Implement login and safe user data

Expose `POST /api/auth/login/` with `AllowAny`; login is the intentional public
exception to the global policy. Read username/password, call Django
`authenticate()`, and reject an invalid password, unknown user, or inactive
user with the same generic message:

```json
{"detail": "Invalid username or password."}
```

The generic response avoids revealing whether a username exists. On success,
get or create the user's token and return:

```json
{
  "token": "...",
  "user": {
    "id": 1,
    "username": "annotator",
    "email": "annotator@example.com",
    "role": "annotator",
    "must_change_password": true
  }
}
```

Create user data by allowlisting safe fields. Never serialize a password hash,
raw password, token in logs, or permission internals unnecessarily.

## Part 7 — Understand the media cookie

Login also sets `webann_media_token` with:

- `HttpOnly`: browser JavaScript cannot read it;
- `SameSite=Strict`: cross-site requests normally do not include it;
- `Secure`: transmit only over HTTPS when `WEBANN_SECURE_COOKIES=true`;
- bounded `Max-Age`: do not create an indefinite browser credential.

Normal JSON API requests continue using the `Authorization` header. The cookie
exists because browser media elements and a future Nginx authorization
subrequest cannot always attach a custom authorization header conveniently.

Compose uses local HTTP and explicitly sets `WEBANN_SECURE_COOKIES=false`.
Secure cookies default to true everywhere else. Do not derive this decision
implicitly from debug mode.

`GET /api/auth/media/authorize/` validates that the cookie identifies an active
user and returns 204 or 401. There are no media objects yet, so this lesson proves
identity only. Resource-specific media access is added when tasks and media
relationships exist; do not claim this endpoint currently authorizes a file.

## Part 8 — Current user, password change, and logout

`GET /api/auth/me/` returns the same safe user representation for the token's
identity. It is protected by the global default.

`POST /api/auth/password-change/` must:

1. verify the current password with `check_password()`;
2. require matching new password and confirmation;
3. run Django's configured password validators;
4. hash through `set_password()` and save;
5. clear `must_change_password`;
6. delete the old token;
7. create and return a replacement token and cookie.

Rotating the token invalidates an existing credential after a sensitive account
change. Directly assigning `user.password = value` would store unusable and
unsafe text; always call `set_password()`.

`POST /api/auth/logout/` deletes `request.auth`, returns 204, and expires the
media cookie. Token authentication is otherwise stateless at the HTTP layer;
deleting the database token is what makes the credential unusable.

## Part 9 — Register routes and run the matrix

Add named routes before the router URLs:

```text
POST /api/auth/login/
GET  /api/auth/me/
POST /api/auth/password-change/
POST /api/auth/logout/
GET  /api/auth/media/authorize/
```

Run:

```bash
make backend-test
make check
make container-test
git diff --check
```

The container smoke test must now expect 401 from anonymous
`/api/templates/`. The previous Lesson 6 `results` response would represent a
security regression. It also verifies both annotations migrations and runs the
30-test suite against PostgreSQL.

## Part 10 — Review limitations and open the PR

Update `docs/API.md` and create `docs/AUTHENTICATION.md` with endpoints, header
format, cookie behavior, role matrix, and credential handling.

Open `Lesson 7: add authentication and role permissions`. Include red/green
evidence and the complete matrix. Confirm that test output, screenshots, commits,
and PR text contain no real password or token.

This lesson does not yet implement login throttling, audit trails, user
administration APIs, resource-level media checks, or production TLS/proxy
configuration. Documenting a security boundary includes saying what it does not
yet protect.

## Acceptance criteria

- APIs authenticate with the token header and reject anonymous access with 401.
- All three roles have tested allowed and forbidden configuration operations.
- Only administrators may modify configuration.
- Login errors do not reveal account existence and never return passwords.
- Inactive users cannot log in or authorize media identity.
- Current-user data is explicitly allowlisted.
- Password validation, hashing, required-change state, and token rotation work.
- Logout revokes the token and expires the media cookie.
- Cookie flags and secure-by-default configuration have tests.
- Both migrations apply and all tests pass against PostgreSQL.

## Gold-standard implementation

Read this after your first PR review. The reference checkpoint is `lesson-07`:

```bash
git fetch --tags
git diff lesson-07 -- . ':!docs/lessons/07-AUTH-RBAC.md'
```

The gold implementation uses secure global defaults, narrow public exceptions,
real token requests in the permission matrix, one shared backend permission,
generic credential errors, explicit safe user output, Django password hashing
and validators, credential rotation, and a purpose-specific HTTP-only cookie.

A different role representation is acceptable only if every boundary remains
server-enforced, denial codes are meaningful, credentials are handled safely,
and the same matrix is fully tested.

## What you should now be able to explain

- authentication versus authorization versus validation;
- 401 versus 403;
- token lookup and `request.user`/`request.auth`;
- secure default versus endpoint exception;
- role matrix and least privilege;
- password hashing and validation;
- token rotation and revocation;
- HTTP-only, Secure, and SameSite cookies; and
- identity authorization versus resource authorization.
