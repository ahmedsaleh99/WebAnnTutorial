# Lesson 10 — Typed API client and authentication UI

## Goal and checkpoint

Connect the React shell from Lesson 9 to Django's Lesson 7 authentication
endpoints. A student can sign in, must change a password when Django requests
it, can enter the dashboard afterward, and can log out. Both the local Vite
server and the Compose frontend must send `/api/` requests to Django.

**Branch:** `lesson/10-frontend-api-auth`

**Pull request:** `Lesson 10: connect React authentication to Django`

This lesson assumes no previous experience with `fetch` or asynchronous
JavaScript. It does **not** build project administration; that begins in
Lesson 11.

## Part 1 — Start from Lesson 9

After Lesson 9 has been reviewed and merged in your own repository:

```bash
git switch main
git pull --ff-only
git switch -c lesson/10-frontend-api-auth
make check
```

When the frontend changes are ready, check its current package version:

```bash
npm --prefix frontend pkg get version
```

In a student repository starting from the Lesson 9 checkpoint, this should
report `"0.9.0"`. If so, update both `frontend/package.json` and the
npm-generated lockfile to `0.10.0`:

```bash
npm --prefix frontend version 0.10.0 --no-git-tag-version
```

If the check already reports `"0.10.0"`, **skip** `npm version`: npm reports
`Version not changed` when asked to set the current version again. This is
not a build failure. In either case, verify the manifest and lockfile agree:

```bash
npm --prefix frontend ci
```

`npm version` updates package metadata without creating a Git commit or tag
because of `--no-git-tag-version`; it does not change locked dependency
versions. `npm ci` installs exactly the lockfile and rejects a mismatch.

Read `backend/annotations/auth_views.py`, `backend/annotations/api_urls.py`,
and `docs/AUTHENTICATION.md` before writing frontend code. Record the real
contract, not an imagined one:

| Request | Success | Important failure |
| --- | --- | --- |
| `POST /api/auth/login/` | `{token, user}` and media cookie | 400 for invalid credentials |
| `GET /api/auth/me/` | current user | 401 for missing/invalid token |
| `POST /api/auth/password-change/` | new `{token, user}` | 400 for password validation; 401 for invalid token |
| `POST /api/auth/logout/` | 204 with no body | 401 for invalid token |

The backend role strings are exactly `"annotator"`, `"manager"`, and
`"admin"`. Lesson 9 used `"administrator"` inside a frontend-only policy;
change the frontend type and tests to `"admin"` now. An API data type should
match the API, not force Django's response into a different spelling.

## Part 2 — Learn the network boundary

`fetch(url, options)` sends an HTTP request and returns a **Promise**: a value
representing work that will finish later. `await` waits inside an `async`
function without freezing the entire browser:

```typescript
const response = await fetch("/api/auth/me/", {
  headers: { Authorization: `Token ${token}` },
});
```

`response` contains a status and body. A `401` or `400` response does **not**
make `fetch` reject its Promise. Check `response.ok` and inspect the status.
By contrast, a network failure such as a disconnected server normally makes
`fetch` reject. These are different user experiences and deserve different
error messages.

`await response.json()` yields a JavaScript value, but that value arrived
from outside TypeScript. A declaration such as `const user: AuthUser = ...`
cannot prove the server sent the expected fields at runtime. The API module
must check the response before handing it to components.

Write the tests in `src/api.test.ts` first. Require at least:

1. a login request with JSON body and same-origin credentials;
2. a valid response mapped to a typed session;
3. malformed success data rejected instead of trusted;
4. a 400 validation error shown by name;
5. a network failure distinguished from an HTTP error;
6. the token sent in `Authorization`, never in the URL; and
7. the new token returned after a password change.

Run `make frontend-test` and verify that the first test fails for the intended
missing function. This is the red stage. Implement the smallest API module
that makes it green, then continue one behavior at a time.

### Read the testing features in `api.test.ts`

The tests call the real API-client functions, such as `signIn`, but replace
the browser's `fetch` with a controlled fake. No Django server or database
is needed. Each test chooses the server response and checks how the client
handles it.

`describe` groups related tests, `it` defines one test, and `expect` makes an
assertion. `vi` provides Vitest's mocking utilities. A **mock function** is a
replacement function whose return value you control and whose calls you can
inspect.

```typescript
const fetchMock = vi.fn().mockResolvedValue(
  response(200, { token: "secret", user: user }),
);
vi.stubGlobal("fetch", fetchMock);

await expect(signIn("amina", "password")).resolves.toEqual({
  token: "secret", user: user,
});
```

Here, `fetchMock` is just a variable name chosen by the test author, not a
built-in API. `vi.fn()` creates the mock and records its calls.
`.mockResolvedValue(value)` makes it return a Promise that succeeds with
`value`. `vi.stubGlobal("fetch", fetchMock)` installs it as the global
`fetch`, so the real `signIn` function uses this fake when it sends a request.
The `user` object is a **fixture**: reusable example data for the tests.
`{ token: "secret", user: user }` explicitly names the property and its value.
In `user: user`, the left `user` is the property name; the right `user` is the
fixture variable containing the user object. These tokens and passwords are
test-only strings.

The local `response` helper builds the small part of an HTTP response that
`api.ts` actually reads:

```typescript
const response = (status: number, data: unknown) => ({
  ok: status >= 200 && status < 300,
  status,
  text: async () => data === null ? "" : JSON.stringify(data),
});
```

The parentheses in `=> ({ ... })` let an arrow function return an object
directly. `status: number` and `data: unknown` are TypeScript parameter
annotations; `unknown` permits both valid and deliberately malformed data.
`ok` is true for status codes 200–299. The `async` method `text()` returns a
Promise containing the body string, just like the method used by the client.
The conditional expression `condition ? a : b` chooses an empty string for
`null`, or JSON text otherwise. This lets `response(204, null)` simulate an
empty logout response. This helper is a partial fake, not a full browser
`Response` object.

The assertions check both the returned result and the outgoing request:

| Feature | Meaning in these tests |
| --- | --- |
| `await expect(promise).resolves.toEqual(value)` | Wait for success and compare the returned object's contents. |
| `await expect(promise).rejects.toMatchObject({ kind: "server" })` | Require a rejected Promise and check the listed error properties; other properties may exist. |
| `expect(fetchMock).toHaveBeenCalledWith(url, options)` | Check that a recorded call used the expected URL and request options. |
| `expect.objectContaining({ ... })` | Match only the listed properties inside an argument, allowing additional fields. |
| `expect(session.token).toBe("new-secret")` | Check the exact token string returned after password change. |
| `.resolves.toBeUndefined()` | Check that logout succeeds without returning a value. |

Always `await` the `.resolves` and `.rejects` assertions so the test waits for
them. `toEqual` compares object contents; `toBe` checks exact equality and is
used here for a string. Nested `expect.objectContaining` calls let the token
test check `headers.Authorization` while allowing headers such as `Accept`.
`JSON.stringify` converts the login object into the JSON string expected in
the request body.

The login test also checks the JSON headers with a nested partial match:

```typescript
headers: expect.objectContaining({
  "Content-Type": "application/json",
  Accept: "application/json",
}),
```

`Content-Type` tells Django that the request body is JSON; `Accept` asks for
a JSON response. Checking these properties catches a missing or incorrect
header while allowing additional headers. The outer `objectContaining`
alone would not check headers unless we explicitly included them.

HTTP errors and network failures need different mock behavior:

```typescript
// The server replied with an HTTP error; fetch itself still succeeds.
vi.fn().mockResolvedValue(response(400, { detail: "Invalid credentials." }));

// No HTTP response arrived; fetch rejects its Promise.
vi.fn().mockRejectedValue(new Error("offline"));
```

The malformed-data test supplies an invalid user object with status 200 to
exercise runtime validation. The HTML test supplies a successful response
whose text cannot be parsed as JSON. Both should become client errors even
though the HTTP status indicates success.

`.mockResolvedValueOnce(...)` queues a response for just one call. In the
last test, the first `fetch` call receives 401 for `currentUser("expired")`;
the second receives an empty 204 for `signOut("secret")`. The order of the
queued responses follows the order of calls to the mock.

The password-change fixture uses `{ ...user, must_change_password: false }`.
The object spread `...user` copies the fixture's properties into a new object,
then overrides that one flag without changing the shared fixture.

Finally, `afterEach(() => vi.unstubAllGlobals())` restores globals after every
test, including a failed test. This prevents one test's fake `fetch` from
leaking into the next. Each test creates its own mock and response setup.
These tests verify client behavior; they do not verify real browser cookie
handling or Django authentication. For example, checking the
`credentials` option proves that the client passes it to `fetch`, not that
a browser actually sends a cookie.

## Part 3 — Build the typed API module

Create `src/api.ts` with `AuthUser`, `AuthSession`, and `ApiError`. `AuthUser`
needs the fields this UI actually reads: numeric ID, username, one of the
three backend role strings, and `must_change_password`. An `AuthSession`
contains the token and validated user.

Use a single request helper for `fetch`, JSON encoding, status handling, and
error conversion. Expose small functions named `signIn`, `currentUser`,
`changePassword`, and `signOut`. Their names express business intent, while
the request helper handles repetitive HTTP details.

At the trust boundary, first treat JSON as `unknown`. A type guard can check
that it is an object before reading properties:

```typescript
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
```

Then check required fields and known role values. If validation fails, report
an invalid server response; do not silently turn an unknown role into
`"annotator"`. The API client is small enough to validate manually here.
These data shapes are **DTOs (Data Transfer Objects)**: structures carrying
data between the backend API and frontend, such as the login response's
token and user. Later lessons can compare schema-validation libraries if
the number or complexity of DTOs grows.

Send JSON with `Content-Type: application/json`; send tokens as
`Authorization: Token <value>`. A logout response is `204 No Content`, so
the request helper must accept an empty body. Handle `401` (unauthorized),
`403` (forbidden), `400` (validation), other server responses, and rejected
network requests distinctly. Do not include the token or password in error
messages, URLs, logs, or test snapshots.

## Part 4 — Understand token and cookie safety

Store the API token in React state **only**. Do not use `localStorage`,
`sessionStorage`, a URL parameter, or a JavaScript-readable cookie. Storage
that persists across page loads is convenient but makes stolen credentials
easier to reuse after an XSS bug. This lesson chooses the smaller exposure:
a page refresh loses the API token and requires signing in again for the
React app. This is an explicit tradeoff, not an accidental broken login.

Django also sets an HTTP-only media cookie at login and password change and
clears it at logout. JavaScript cannot read that cookie; the browser manages
it. The client uses `credentials: "same-origin"` so same-origin cookies can
be accepted and sent when needed. The current API still authenticates with
the explicit token header, not with that cookie. Never treat the media cookie
as a replacement for the API token or as a CSRF defense.

> **Hint:** `credentials: "same-origin"` is the default for `fetch()`. It lets
> the browser send cookies only when the request matches the page's protocol,
> hostname, and port. For a page at `https://example.com`, `/api/auth/login/`
> matches, but `https://api.example.com` or `http://example.com` does not.
> A different port also counts as a different origin.

Importantly, losing the in-memory API token on refresh does **not** revoke
the server token or clear the media cookie. The cookie can remain valid until
its configured expiry or an explicit logout. Do not call a page refresh a
secure logout; use the logout endpoint to revoke the token and clear the
cookie. A complete production session design must address this lifecycle.

## Part 5 — Write the auth-gate tests (red)

Create `src/AuthGate.test.tsx` and replace the Lesson 9 placeholder behavior
with tests for the actual journey. Mock `fetch` at the network boundary;
do not start Django for these fast component tests. Keep the mocked response
shape faithful to the backend contract.

Test the visible states separately:

- an unauthenticated visitor sees a labeled sign-in form;
- a successful login opens the dashboard and displays the username;
- invalid credentials keep the form available and show the server message;
- a network failure gives a retryable message;
- `must_change_password: true` shows only the password-change form, not the
  dashboard;
- password-change validation errors do not discard the form;
- a successful password change uses the rotated token and opens the app; and
- logout revokes the token and returns to sign-in.

Use `userEvent` to type and click, `findByRole` for elements that appear after
an asynchronous request, and `getByRole` for elements already present. Restore
the mocked global `fetch` after every test so cases do not affect each other.
The component tests check frontend behavior; Django's own tests still check
the actual password rules and token revocation.

## Part 6 — Implement the gate and update the shell

Create `src/AuthGate.tsx`. It owns either `null` (not signed in) or an
`AuthSession`, plus a pending-action value and an error message. Render exactly
one of these views:

```text
No session → Sign-in form
Session with must_change_password → Password-change form
Session allowed into app → App dashboard
```

On form submit, call `event.preventDefault()` so the browser does not reload
the page. Read the labeled form values and call the matching API function.
Type a React submit handler as `SubmitEvent<HTMLFormElement>` (imported from
`react`), so `event.currentTarget` is known to be the form. The installed
React type definitions mark the older `FormEvent` name as deprecated because
it does not identify a specific kind of event.
Disable the submit button while a request is pending to avoid duplicate
requests. Use `role="alert"` for an error that should be announced by
assistive technology. Keep the password as short-lived form input, not in a
global store.

Use `current-password` and `new-password` autocomplete values to identify the
password fields. Give the sign-in and change forms different React `key`
values so React mounts fresh inputs when it
switches forms; otherwise it may reuse the sign-in password input and carry
its typed value into the change form. The app leaves those password inputs
empty when the form first appears. A browser or password
manager may still fill them according to the user's saved-password settings,
so users should check any filled values before submitting.

If password change succeeds, **replace the entire session** with Django's
new token and user. The old token has been revoked. If an authenticated
request returns 401, discard the session and return to sign-in. For a logout
network failure, retain the session and explain that logout could not be
confirmed; do not claim a successful revocation.

Update `main.tsx` to mount `AuthGate` inside the existing error boundary.
Update `App` to receive a validated user and an `onLogout` callback. Show
the username; enable the logout button; keep a future account-menu button
disabled until it has a real action. Change `navigationFor` to accept the
backend's exact role strings. Hiding Configuration from an annotator is only
a usability policy—Django's permissions remain the security boundary.

The password-change gate is likewise user guidance. As Lesson 7 explains,
the backend does not yet enforce that flag against every sensitive endpoint.
Do not describe the frontend gate as a security control.

## Part 7 — Make `/api/` work in both environments

The browser should request relative paths such as `/api/auth/login/`. Relative
paths keep browser requests on the frontend's **same origin** (same scheme,
host, and port). A server-side proxy forwards them to Django:

```text
Browser → /api/auth/login/ on frontend origin
        → development: Vite proxy to localhost:8002
        → Compose: server.mjs proxy to api:8000
        → Django authentication view
```

The Vite proxy already routes `/api` to local Django at port 8002. Confirm it
works by starting `make backend-run` and `npm --prefix frontend run dev` in
separate terminals. If the backend is not running, the UI should show a
network/server error instead of pretending login succeeded.

The production-like Compose image does **not** run Vite. Extend
`frontend/server.mjs` with an explicit `/api/` proxy, set `API_ORIGIN` to
`http://api:8000` in Compose, and forward the Authorization header, JSON
body, HTTP status, response body, and Django's `Set-Cookie` headers. Do not
proxy arbitrary destinations from a browser-supplied URL. Keep `/health/`
and `/api-health/` working.

This same-origin design avoids browser CORS configuration for this lesson.
**CORS** is a browser rule controlling whether a page may read responses from
a different origin. It is not authentication or authorization. Do not enable
permissive `Access-Control-Allow-Origin: *` merely to make local login work.
The proxy is a development/deployment routing decision; Django still decides
who may access data.

Add a container smoke assertion that `GET /api/auth/me/` through the
frontend returns 401 for an anonymous user. If the old static fallback
returned `index.html` with 200 instead, this test would catch it.

## Part 8 — Verify the PR

```bash
make frontend-test
make frontend-check
make check
make container-test
git diff --check
```

For a manual Compose check, start the stack and create a local administrator
using `docker compose exec api python manage.py createsuperuser`. Enter the
password at the prompt; never put it in a command or commit it. Open the
frontend address from `docs/DOCKER.md`, sign in, confirm the admin sees
Configuration, log out, and confirm the sign-in form returns. Stop the stack
with `docker compose down` when finished. A normal user with
`must_change_password: true` is needed to manually inspect the forced-change
path; set this flag explicitly as shown in `docs/AUTHENTICATION.md`. The mocked
UI test and backend tests cover it automatically. An interactive superuser
without a `UserSecurity` record receives `must_change_password: false`.

In the PR description, include red/green test evidence, the request/response
contract, screenshots of sign-in, validation, password change, and dashboard,
and output from the full checks. Explain why no token is persisted and why
the frontend role policy does not authorize API requests.

## Acceptance criteria

- The frontend role type exactly matches Django's role values.
- Typed auth DTOs are checked against runtime JSON before use.
- Tests cover login success, validation, malformed responses, 401, network
  failure, forced password change, rotated token, and logout.
- The auth gate never renders the dashboard before successful login or while
  the password-change flag remains true.
- The token stays in memory and is sent only in the Authorization header.
- The HTTP-only media cookie remains browser-managed and is forwarded through
  the same-origin proxy.
- The user and logout controls reflect real authenticated state.
- Vite and Compose both reach Django through `/api/`; an anonymous proxied
  API request returns 401, not the SPA HTML page.
- Frontend, backend, repository, and Compose checks pass.

## Gold-standard implementation

Only read the reference after implementing and receiving the first review.
The intended checkpoint tag is `lesson-10`:

```bash
git fetch --tags
git diff lesson-10 -- . ':!docs/lessons/10-FRONTEND-API-AUTH.md'
```

Compare your implementation with the gold standard by tracing one request
from the form through `api.ts`, the same-origin proxy, and Django, then trace
the response back to the visible UI. Note any differences in error handling,
runtime validation, token lifetime, password-change rotation, and test
coverage. Record what you would change in your PR before merging.

### Gold implementation walkthrough

1. **Contract first:** `api.ts` defines `AuthUser`, `AuthSession`, and
   `ApiError`. The role union uses `"admin"`, matching Django exactly. The
   parser checks `unknown` JSON field by field before returning a session.
   `api.test.ts` proves malformed data is rejected rather than trusted.
2. **One HTTP boundary:** `request()` adds JSON and token headers, uses
   relative URLs, accepts a 204 empty response, and turns status and network
   failures into understandable error kinds. The UI does not repeat `fetch`
   options in each form.
3. **One auth state owner:** `AuthGate` owns the in-memory session. With no
   session it renders sign-in; with the required-change flag it renders the
   password form; otherwise it renders `App`. Each form has explicit pending
   and error states. A successful password change replaces the old token.
4. **Presentational shell:** `App` receives a validated user and logout
   callback. It displays the username and role-based links, but does not
   decide whether a request is authorized. `navigationFor` remains a pure
   function and is tested independently.
5. **Same-origin routing:** Vite proxies `/api` during local development.
   In Compose, `server.mjs` forwards `/api/` to the fixed `API_ORIGIN`,
   including JSON request bodies and `Set-Cookie` response headers. The
   container smoke test requires 401 for anonymous `/api/auth/me/` and 400
   for invalid JSON login through the frontend port.
6. **Separate proof levels:** mocked frontend tests cover visible states and
   API-client parsing; Django tests cover credentials, roles, and token
   rotation; Compose smoke proves the built images and network work together.

This is a reference solution, not the only acceptable structure. A different
implementation is sound if it preserves the same backend contract, security
boundaries, user-visible behavior, and verification evidence.
