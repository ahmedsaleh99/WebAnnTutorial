# Lesson 9 — React, TypeScript, Vite, and Vitest foundations

## Goal

Replace the placeholder frontend server page with a typed, tested React
application shell. The shell provides semantic navigation, a dashboard, a pure
role-navigation policy, responsive styling, and a recovery boundary. It does
not call Django yet; Lesson 10 introduces that integration.

An **application shell** is the persistent outer interface shared by the
application's pages. It commonly contains the global layout, header,
main-content area, styling, and top-level error handling. It is
called a *shell* because it surrounds the feature-specific content that changes
as the user moves between pages.

```text
Error boundary (wraps the application shell)
└── Application shell (remains present)
    ├── Header: brand → horizontal navigation → account controls
    └── Main-content area
        └── Current page (changes during navigation)
```

The **header** is one horizontal area. It begins with the WebAnn brand, then
shows the primary navigation links, and ends with the user and logout buttons.
The `<nav>` element is the link group *inside* `<header>`: the header is the
whole area, while navigation is one part of it. On narrow screens the items
can wrap, but they remain in the same header. The error boundary surrounds the
shell; it is not a visible part of the header.

Lesson 9 does not implement authentication. The user and logout buttons are
disabled placeholders, not working account controls. Their labels show the
intended layout; a later authentication lesson must connect them to real user
data and logout behavior. Never show an enabled logout button that does
nothing.

Lesson 9 builds this common outer structure, not the complete WebAnn frontend.
Later lessons place project lists, task workflows, and annotation tools inside
the main-content area and connect them to Django.

This lesson assumes no React experience and only a small amount of JavaScript
experience. Every JavaScript, TypeScript, and React construct needed by the
application is introduced before it is used. Basic HTML and CSS familiarity is
helpful, but the lesson does not assume prior frontend framework knowledge.

**Branch:** `lesson/09-react-foundations`

**Pull request title:** `Lesson 9: build the tested React application shell`

## What you will learn

- how the browser, DOM, React, and ReactDOM divide responsibilities;
- how components, JSX, props, state, and effects work;
- how TypeScript checks component and domain contracts;
- how Vite serves source code and creates production assets;
- how npm manifests and lockfiles make installations reproducible;
- how CSS selectors, the box model, Flexbox, and media queries style the shell;
- how Vitest, jsdom, and Testing Library test behavior;
- why semantic HTML and keyboard access are requirements;
- what an error boundary can and cannot recover from; and
- how frontend checks join the local, CI, and container quality gates.

## Part 1 — Start from the reviewed Lesson 8 checkpoint

```bash
git switch main
git pull --ff-only
git switch -c lesson/09-react-foundations
make check
```

Do not start while Lesson 8 remains an unreviewed branch. The frontend will
eventually depend on the workflow API contract established there.

## Part 2 — Install and verify Node.js 22

Python executes Django; Node.js executes frontend build and test tools. The
browser executes the final JavaScript bundle. These are different runtimes.

The repository already contains:

```text
.nvmrc → 22
```

Verify the active runtime:

```bash
node --version
npm --version
```

If Node is not version 22, use a Node version manager such as `nvm`:

```bash
nvm install 22
nvm use 22
```

The new `scripts/check-node-runtime.sh` fails early with a readable error rather
than allowing modern Vite or Vitest syntax to fail later. A major-version file
lets local tools and CI select a current compatible Node 22 release.

## Part 3 — Understand the frontend toolchain

The tools solve separate problems:

```text
TypeScript source and JSX
          ↓
TypeScript checks types
          ↓
Vite transforms and bundles modules
          ↓
dist/ contains browser assets
          ↓
server.mjs serves those assets in the container
```

- **React** describes the interface as components.
- **ReactDOM** mounts the component tree into a browser DOM element.
- **TypeScript** checks value shapes before execution.
- **Vite** runs the development server and builds optimized browser files.
- **Vitest** runs tests using Vite's module transformation.
- **jsdom** supplies a lightweight DOM inside Node for component tests.
- **Testing Library** queries the interface as a user would perceive it.

Vite is not React, and TypeScript is not a runtime. Production browsers receive
ordinary HTML, CSS, and JavaScript.

## Part 3A — Learn the browser and JavaScript essentials

A web page begins as HTML. The browser parses that HTML into an in-memory tree
called the **Document Object Model**, or DOM. CSS controls its presentation,
while JavaScript can respond to events and change the DOM.

```text
HTML       → structure and meaning
CSS        → presentation and layout
JavaScript → behavior and interaction
DOM        → the browser's object tree representing the page
```

React does not replace these browser technologies. It gives us a structured
way to describe which DOM should exist for the application's current data.

Read the following JavaScript before continuing:

```javascript
const user = { name: "Amina", role: "annotator" };
const pages = ["Dashboard", "Assigned work"];

function greeting(name) {
  return `Welcome, ${name}`;
}

const pageLabels = pages.map((page) => page.toUpperCase());
```

The syntax means:

- `const` creates a variable that cannot be assigned a different value;
- an object such as `user` groups named properties;
- an array such as `pages` stores an ordered list;
- a function receives inputs and can return a result;
- a template literal uses backticks and `${...}` to insert a value into text;
- an arrow function such as `(page) => page.toUpperCase()` is a shorter
  function expression; and
- `map` calls that function once for every array item and returns a new array.

Use `let` only when the variable itself must be reassigned:

```javascript
let attempts = 0;
attempts = attempts + 1;
```

`const` does not make an object immutable. It prevents reassignment of the
variable. In React, create new arrays and objects instead of mutating existing
state. The spread syntax copies existing values:

```javascript
const updatedUser = { ...user, role: "manager" };
const updatedPages = [...pages, "Workflow"];
```

JavaScript modules split a program into files. `export` makes a value available
to other modules, and `import` brings it into the current module:

```javascript
// navigation.js
export function navigationFor(role) {
  return role === "administrator" ? ["Dashboard", "Configuration"] : ["Dashboard"];
}

// app.js
import { navigationFor } from "./navigation.js";
```

The function supplied to `map`, an event handler, or a test helper is a
**callback**: code passed to other code to be invoked later. For example,
`onClick={() => setOpen(true)}` passes a function; it does not call
`setOpen` while rendering.

Before continuing, make sure you can identify the object, array, function,
callback, and returned value in these examples. You do not need to memorize all
JavaScript syntax. You need a working mental model and should look up unfamiliar
syntax when it appears.

## Part 3B — Add TypeScript to JavaScript

TypeScript is JavaScript plus static type checking. It finds many mistakes
before the browser runs the program, then Vite removes the type syntax when it
builds ordinary JavaScript.

TypeScript often infers a type without an annotation:

```typescript
const projectName = "Interview annotation"; // inferred as string
const itemCount = 3;                         // inferred as number
```

Add an explicit type where it communicates a contract:

```typescript
type UserRole = "annotator" | "manager" | "administrator";

interface NavigationItem {
  label: string;
  href: string;
}

function navigationFor(role: UserRole): NavigationItem[] {
  // Return an array of objects matching NavigationItem.
  return [{ label: "Dashboard", href: "/" }];
}
```

Here:

- `UserRole` is a union: only one of the three exact strings is valid;
- `interface` describes the required shape of an object;
- `role: UserRole` types a function parameter;
- `: NavigationItem[]` types the returned array; and
- a property written as `role?: UserRole` is optional.

TypeScript checks source code; it does not validate untrusted data at runtime.
If an API returns `"unknown"`, a type annotation cannot make that value safe.
Lesson 10 will validate the assumptions made at the network boundary.

Avoid `any`: it disables useful checking for the value. When a value is truly
unknown, use `unknown`, inspect it, and narrow its type before using it.

## Part 3C — Read JSX and understand React rendering

A React component is usually a function whose name begins with a capital
letter. It returns **JSX**, an HTML-like syntax embedded in JavaScript:

```tsx
interface WelcomeProps {
  name: string;
  pages: string[];
}

function Welcome({ name, pages }: WelcomeProps) {
  return (
    <section className="welcome">
      <h1>Welcome, {name}</h1>
      <ul>
        {pages.map((page) => (
          <li key={page}>{page}</li>
        ))}
      </ul>
    </section>
  );
}
```

Read it from the outside inward:

- `WelcomeProps` defines the component's input contract;
- `{ name, pages }` destructures those properties into local variables;
- lowercase JSX names such as `<section>` represent browser elements;
- capitalized JSX names such as `<Welcome />` represent components;
- `{...}` switches from JSX markup into a JavaScript expression;
- `className` is the JSX property used for an HTML `class` attribute;
- `map` creates one `<li>` for every page; and
- `key` gives React a stable identity for each item in a rendered list.

JSX is not a string and is not sent directly to the browser. Vite transforms it
into JavaScript calls that produce React elements—plain descriptions of the
desired interface.

Use this render model throughout the lesson:

```text
React calls component function
            ↓
component reads props and current state
            ↓
component returns a React element tree
            ↓
React updates only the necessary browser DOM
            ↓
an event may request a state update and start another render
```

Rendering must remain pure: given the same props and state, a component should
describe the same interface. Do not perform network requests, modify the DOM,
or set state directly while rendering. Event handlers respond to user actions;
effects synchronize with external systems after React commits a render.

## Part 4 — Define a reproducible npm project

Create `frontend/package.json` with exact dependency versions and scripts:

```json
{
  "name": "webann-tutorial-frontend",
  "private": true,
  "version": "0.9.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc -b && vite build",
    "test": "vitest run",
    "check": "npm test && npm run build"
  },
  "dependencies": {
    "react": "19.3.0",
    "react-dom": "19.3.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "7.0.1",
    "@testing-library/react": "16.3.3",
    "@testing-library/user-event": "14.6.7",
    "@types/react": "19.3.0",
    "@types/react-dom": "19.3.0",
    "@vitejs/plugin-react": "6.1.1",
    "jsdom": "30.0.1",
    "typescript": "7.0.2",
    "vite": "8.3.0",
    "vitest": "5.0.1"
  }
}
```

`package.json` is the frontend project's manifest. The names under `scripts`
are commands the team agrees to use. For example, `npm run build` looks up and
runs the `build` value; `npm test` is npm's conventional shortcut for the
`test` value. The `--prefix frontend` option tells npm to work in the
`frontend/` directory even when the command is run from the repository root.

The top-level fields have these purposes:

- `name` identifies this npm project;
- `private: true` prevents accidentally publishing the tutorial application as
  a public npm package;
- `version` identifies this lesson's application checkpoint; and
- `type: "module"` makes `.js` files use modern `import` and `export` syntax.

The scripts provide stable project commands:

- `dev` starts Vite's development server and makes it reachable from outside a
  development container;
- `build` first checks TypeScript and then creates production assets;
- `test` runs the test suite once and exits, which is suitable for CI; and
- `check` runs both the behavioral tests and production build.

`dependencies` are needed by the running application, such as React.
`devDependencies` are needed to build or test it, such as TypeScript and
Vitest. The container build needs both groups, but the final static server does
not copy `node_modules`.

The packages have distinct responsibilities:

- `react` defines components, elements, state, effects, and other React APIs;
- `react-dom` connects React's element tree to the browser DOM;
- `typescript` performs static type checking;
- `@types/react` and `@types/react-dom` provide TypeScript declarations;
- `vite` provides the development server and production build;
- `@vitejs/plugin-react` teaches Vite how to transform React JSX;
- `vitest` is the test runner;
- `jsdom` supplies a simulated browser DOM while tests run in Node;
- `@testing-library/react` renders components and queries their output;
- `@testing-library/user-event` simulates realistic user interaction; and
- `@testing-library/jest-dom` adds readable DOM assertions such as
  `toBeInTheDocument()`.

Generate and commit `package-lock.json`. The manifest says what versions the
project requests; the lockfile records the exact resolved dependency graph.
After creating `package.json`, generate the initial lockfile from the repository
root:

```bash
npm --prefix frontend install --package-lock-only
```

Commit both `frontend/package.json` and `frontend/package-lock.json`. Do not
manually write or edit the lockfile; npm generates it from the manifest.
Use this in a repository with a lockfile:

```bash
npm --prefix frontend ci
```

`npm ci` installs exactly the lock, fails when it disagrees with `package.json`,
and does not rewrite it. That makes it appropriate for CI and Docker.

Run the course wrapper:

```bash
make frontend-bootstrap
```

Never commit `node_modules/`, `dist/`, or `coverage/`.

## Part 5 — Write the behavior tests first (red)

### What is a test?

A test is a small program that checks whether application code produces an
expected result. Each test starts from a known situation, performs an action if
one is needed, and checks an observable outcome.

Use the **Arrange–Act–Assert** structure:

```text
Arrange → prepare the component, data, and simulated user
Act     → render it or perform a user action
Assert  → check the result visible to the user
```

For example:

```tsx
test("shows the dashboard heading", () => {
  // Arrange and Act: render the application with a known role.
  render(<App role="annotator" />);

  // Assert: check an outcome a user can observe.
  expect(
    screen.getByRole("heading", { name: "Dashboard" }),
  ).toBeInTheDocument();
});
```

`test` registers one example with Vitest. Its first argument describes the
expected behavior. Its second argument is the function Vitest executes. A test
passes when every assertion succeeds and no unexpected error is thrown.

### What does “test behavior” mean?

Test the contract that matters to a user or another part of the program, not
the component's private implementation. For example, test that an annotator
can see the “Assigned work” link. Do not test the name of an internal variable
or whether a particular helper was called unless that call is itself the
contract.

```text
Prefer:  “the user sees Assigned work”
Avoid:   “the component has a variable named annotatorLinks”
```

A behavior-focused test remains useful if the component is refactored but its
user-visible behavior stays the same.

### Why write the test before the implementation?

This lesson follows test-driven development using the
**red–green–refactor** cycle:

1. **Red:** write one test for the next required behavior and see it fail for
   the expected reason.
2. **Green:** write the smallest clear implementation that makes it pass.
3. **Refactor:** improve names or structure while keeping every test green.

Seeing the test fail first is important. It proves the test can detect the
missing behavior. A test that passes before the feature exists may be testing
the wrong thing.

Do not write all application code and then attempt to add tests at the end.
Work in small steps: one behavior, one expected failure, one implementation,
and then the next behavior.

### How the test suite is divided

Before building the shell, specify behavior in three files:

```text
src/navigation.test.ts
src/App.test.tsx
src/ErrorBoundary.test.tsx
```

Each file tests a different responsibility:

- `navigation.test.ts` tests a pure TypeScript function. It supplies a role and
  checks the navigation items returned. It does not need to render React.
- `App.test.tsx` renders the application and checks what a user can find or do,
  including landmarks, links, headings, and keyboard focus.
- `ErrorBoundary.test.tsx` deliberately renders a failing child and checks that
  the recovery interface replaces it.

Keeping these responsibilities separate makes failures easier to understand.
If a role rule is wrong, the navigation policy test identifies it directly. If
the returned links are correct but the page does not display them, the App test
identifies the rendering problem.

These are mostly **unit and component tests**. They are intentionally fast and
do not start Django, PostgreSQL, or a real browser. Later lessons add tests for
frontend–API integration and complete user workflows. No single test level can
prove the whole application works.

### The behaviors to implement

The first red tests should require:

1. annotators **see** Dashboard and Assigned work;
2. managers additionally **see** Workflow;
3. only administrators **see** Configuration;
4. the header contains the brand, primary navigation, and disabled account
   controls, while the page exposes a main landmark and dashboard heading;
5. the brand link receives keyboard focus first; and
6. a rendering failure shows a recovery message.

### Check keyboard focus order

Pressing `Tab` moves keyboard focus through links and buttons. With no skip
link in this lesson, the WebAnn brand link is the first interactive element in
the header. Test the actual focus order:

```tsx
const user = userEvent.setup();

render(<App />);
await user.tab();

expect(
  screen.getByRole("link", { name: "WebAnn home" }),
).toHaveFocus();
```

The brand and navigation links must keep visible focus styles so keyboard
users can see where they are. This lesson deliberately postpones a shortcut
past repeated navigation; that means keyboard users must currently Tab through
the header links to reach later page controls. Revisit this accessibility
tradeoff when the application grows beyond the foundation shell.

### Why a rendering failure must show a recovery message

A component can throw an error while React is trying to render it. Without an
error boundary, the affected interface may disappear and leave the user with
an unexplained blank area. The application shell therefore wraps its content
in `ErrorBoundary` and replaces a failed subtree with a clear fallback such as
“Something went wrong.”

Test this by deliberately rendering a broken child:

```tsx
function BrokenPage() {
  throw new Error("The page cannot be rendered");
}

render(
  <ErrorBoundary>
    <BrokenPage />
  </ErrorBoundary>,
);

expect(
  screen.getByRole("heading", { name: "Something went wrong" }),
).toBeInTheDocument();
```

The recovery message does not repair the underlying defect. It gives the user
a controlled explanation and a next action instead of silently showing a
broken interface. Error boundaries catch descendant errors during rendering
and React lifecycle processing. They do not normally catch errors in event
handlers, network requests, timers, other asynchronous callbacks, or the error
boundary's own rendering code; those require separate error handling.

Run:

```bash
make frontend-test
```

Run the command after adding the first test. At the beginning, it may fail
because an imported module does not exist. After creating an empty module, it
may fail because the expected link or heading is absent. Read the failure and
confirm it matches the behavior you have not implemented yet.

Keep the red output in the PR description, then implement only enough behavior
to turn that test green. Run the tests again after every small change. A
different, unexpected failure—such as a syntax error or incorrect import—is
not useful red-stage evidence; fix that problem until the test fails for the
intended missing behavior.

Read this first component test line by line:

```tsx
render(<App role="annotator" />);

expect(
  screen.getByRole("heading", { name: "Dashboard" }),
).toBeInTheDocument();
```

- `render` mounts the component in jsdom for this test;
- `role="annotator"` supplies a prop to `App`;
- `screen` provides queries over the rendered page;
- `getByRole` finds an accessible heading with the given name;
- `expect` creates an assertion; and
- `toBeInTheDocument` is the required observable outcome.

The test describes behavior without inspecting component variables. A failure
should tell the student which user-visible contract is missing. This is the
frontend form of the red-green-refactor cycle used in earlier lessons.

When a user action is asynchronous, mark the test function `async` and wait for
the action:

```tsx
test("focuses the brand link first", async () => {
  const user = userEvent.setup();
  render(<App />);

  await user.tab();

  expect(
    screen.getByRole("link", { name: "WebAnn home" }),
  ).toHaveFocus();
});
```

`user.tab()` returns a Promise because the simulated interaction completes
asynchronously. `await` pauses this test function until that interaction is
finished; it does not freeze the entire computer. Without `await`, the
assertion could run before focus changes and produce an unreliable result.

### Walk through the complete `App.test.tsx`

After the first small test passes, grow it into the component tests in
`frontend/src/App.test.tsx`. The `.tsx` extension is needed because the test
file contains JSX such as `<App />`.

```tsx
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders semantic dashboard landmarks", () => {
    render(<App role="annotator" />);

    const header = screen.getByRole("banner");
    const headerContent = within(header);

    expect(headerContent.getByRole("link", { name: "WebAnn home" })).toBeInTheDocument();
    expect(headerContent.getByRole("navigation", { name: "Primary navigation" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dashboard", level: 1 })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Configuration" })).not.toBeInTheDocument();
    expect(headerContent.getByRole("button", { name: "User: annotator" })).toBeDisabled();
    expect(headerContent.getByRole("button", { name: "Log out" })).toBeDisabled();
  });

  it("starts keyboard focus at the brand link", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.tab();

    expect(screen.getByRole("link", { name: "WebAnn home" })).toHaveFocus();
  });
});
```

Read the imports first:

- `render` places a React component into the test DOM; `screen` searches that
  DOM; `within` limits a search to one part of it.
- `userEvent` simulates a person's keyboard or pointer interaction.
- `describe` groups related tests, `it` defines one test case, and `expect`
  starts an assertion. Vitest runs each `it` independently.
- `App` is the component being tested. `./App` means the module in the same
  directory, not an installed package.

In the first test, `render(<App role="annotator" />)` fixes the input so the
expected navigation is predictable. The word `role` in this JSX is WebAnn's
**user role prop**. It is different from the **accessibility role** in
`getByRole("link")`: an accessibility role describes what an HTML element is
to users and assistive technology.

`screen.getByRole("banner")` finds the page's `<header>` landmark. Then
`within(header)` searches only inside that header. This proves that the brand,
navigation, and account controls are **in the header**, not merely somewhere
else on the page. A `<nav>` has the `navigation` role; `<main>` has the `main`
role; and `<h1>` has the `heading` role with level 1. The `{ name: ... }`
option checks an element's **accessible name**, normally the text or label a
user would hear or see.

How do you know which word to pass to `getByRole`? Start with the HTML element
that expresses the meaning you want, then look up its **implicit accessibility
role**. Do not invent a role name or add a `role` attribute just to satisfy a
test. Common mappings in this lesson are:

| HTML element | Accessibility role |
| --- | --- |
| Page-level `<header>` | `banner` |
| `<nav>` | `navigation` |
| `<main>` | `main` |
| `<button>` | `button` |
| `<h1>` | `heading` with `level: 1` |
| `<a href="...">` | `link` |

The page-level `<header>` is called `banner` in accessibility terminology;
this does not mean an advertisement. Context matters: a `<header>` inside an
article or section may not have the `banner` role. For less familiar elements,
use the [W3C HTML-to-ARIA mapping](https://www.w3.org/TR/html-aria/) rather
than guessing.

If a test cannot find an element, temporarily print the roles that Testing
Library sees:

```tsx
import { logRoles, render } from "@testing-library/react";

const { container } = render(<App />);
logRoles(container);
```

Read the output to find the actual role and accessible name, then inspect the
HTML if they are not what you expected. Remove this diagnostic code after
debugging. See Testing Library's [accessibility utilities](https://testing-library.com/docs/dom-testing-library/api-accessibility/)
for `logRoles` and its other tools. Prefer correcting the HTML semantics to
changing an assertion until it passes.

Use `getByRole` when the element **must exist**: it fails immediately if no
match is found. Use `queryByRole` when asserting an element **must not exist**:
it returns `null` when absent, which can then be checked with
`not.toBeInTheDocument()`. The Configuration link must be absent for an
annotator; this is a user-interface rule, not server authorization. The final
two assertions confirm the future account buttons are visible but disabled
because Lesson 9 has no login or logout behavior yet.

In the second test, `<App />` uses its default `annotator` prop. `user.tab()`
simulates one press of the Tab key. `toHaveFocus()` checks the element that
would receive the next keyboard action. Its `async`/`await` syntax ensures the
assertion runs after the simulated key press finishes. The test does not prove
the entire keyboard experience; also inspect focus visibility and order in a
real browser.

The `src/test/setup.ts` file runs Testing Library's `cleanup()` after each
test, so DOM left by the first case cannot make the second case pass or fail.
Run `make frontend-test` after each small behavior is added. If one assertion
fails, read its expected role and name, inspect the rendered markup, and fix
the behavior rather than changing the assertion merely to make it green.

## Part 6 — Create the TypeScript configuration

### What TypeScript configuration does

TypeScript checks `.ts` and `.tsx` files before the browser runs them. A
`tsconfig.json` file tells the TypeScript compiler (`tsc`) which files belong
to a project, which JavaScript and browser features those files may use, and
how strictly to check them. It does **not** start React, run tests, or create
the final browser bundle. Vite handles the bundle in Part 13.

This frontend contains code for two different environments:

- `src/` contains the React application and tests. Application code runs in a
  browser and may use `document`, HTML elements, and DOM events. The component
  tests run in Node with jsdom providing a simulated DOM.
- `vite.config.ts` configures Vite and Vitest. That file runs in Node while
  developing, testing, or building; it is not a page delivered to users.

Give those environments separate configurations so browser-only assumptions
do not silently become assumptions about tool code:

```text
frontend/
├── tsconfig.json       project entry point
├── tsconfig.app.json   src/ browser and React code
└── tsconfig.node.json  vite.config.ts tool code
```

### Create the project entry point

Create `frontend/tsconfig.json`:

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

This file does not list source files directly. `"files": []` prevents the
entry point from compiling the same files again. `references` tells `tsc -b`
to check both child projects. Here `-b` means **build mode**; it follows the
references. It is not the Vite production build. The npm `build` script runs
the TypeScript check first, then runs `vite build`.

### Configure the browser application

Create `frontend/tsconfig.app.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "Bundler",
    "allowImportingTsExtensions": false,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["src"]
}
```

Read the important settings in groups:

- `include` says which files this project checks. It includes components,
  tests, and declaration files under `src/`.
- `target` and `lib` describe the JavaScript features and built-in APIs that
  types may refer to. `DOM` provides types such as `Document` and
  `HTMLButtonElement`; `DOM.Iterable` covers iterable DOM collections. These
  settings do not add browser features at runtime.
- `module: "ESNext"` keeps modern `import`/`export` syntax for Vite to
  process. `moduleResolution: "Bundler"` makes package and import resolution
  match a bundler-oriented project.
- `jsx: "react-jsx"` tells TypeScript how to understand `.tsx` JSX. It works
  with the modern React JSX transform, so most components need not import
  `React` solely to use JSX.
- `noEmit: true` means TypeScript checks code without writing JavaScript
  output. Vite produces the browser files instead.
- `strict: true` enables a collection of stricter checks. For example, if
  `document.getElementById("root")` might return `null`, TypeScript requires
  you to handle that possibility before using the element.
- `noUnusedLocals` and `noUnusedParameters` report declared values that are
  never used. This catches leftovers and some accidental mistakes.
- `verbatimModuleSyntax` preserves the distinction between runtime imports
  and type-only imports. For example, write `import type { UserRole }` when
  only the type is needed.
- `skipLibCheck` skips checking the internals of installed declaration files;
  it does not turn off checking your application code.
- `useDefineForClassFields`, `moduleDetection`, and
  `allowImportingTsExtensions` keep class-field and module behavior explicit
  and compatible with this Vite setup. You do not need to memorize them now;
  leave them as shown while learning the component code.

### Configure the tool file

Create `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "allowImportingTsExtensions": false,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

Most settings have the same purpose as in the app configuration. The key
differences are `include`, which selects only `vite.config.ts`, and
`composite: true`, which permits this configuration to participate in the
referenced-project build. Unlike the app configuration, this file does not
explicitly request DOM or JSX types because the Vite configuration is tool
code, not a React component. This separation is organizational, not a security
boundary: TypeScript types alone cannot prevent runtime access to browser or
Node APIs.

### Add Vite's client declarations

Add `src/vite-env.d.ts`:

```typescript
/// <reference types="vite/client" />
```

The `.d.ts` extension means **declaration file**: it supplies types but does
not create runtime code. Read the line in three parts:

- `/// <reference ... />` is a special TypeScript **triple-slash directive**.
  It looks like a comment, but the TypeScript compiler interprets it.
- `types="vite/client"` asks the compiler to load the client-side type
  declarations supplied by Vite.
- Placing the directive in `src/vite-env.d.ts` makes those declarations
  available while TypeScript checks the application source under `src/`.

For example, Vite understands a CSS import in `main.tsx`:

```tsx
import "./styles.css";
```

TypeScript needs a declaration explaining that this import is allowed. Vite's
client types provide it. They also describe Vite-specific browser features
such as `import.meta.env`. The directive does **not** import Vite into the
running application or add JavaScript to the final bundle; it affects only
type checking.

### Verify the configuration

From the repository root, after `make frontend-bootstrap`, run:

```bash
npm --prefix frontend run build
```

This first executes `tsc -b`. If a type error is reported, read the file and
line number, correct the source or configuration, and run the command again.
Only after type checking succeeds does Vite build the browser assets. For a
type-check-only run from the repository root, pass the configuration path
explicitly:

```bash
npm --prefix frontend exec -- tsc -b frontend/tsconfig.json
```

Here, `npm --prefix frontend exec` finds the TypeScript executable installed
in `frontend/node_modules/`, but `tsc` still resolves a configuration path
relative to your current directory. If you omit `frontend/tsconfig.json` while
standing at the repository root, TypeScript looks for a nonexistent root-level
`tsconfig.json` and reports `TS6053`. Alternatively, change into `frontend/`
first and run `npm exec -- tsc -b` there. The `npm run build` script does not
have this problem because npm runs package scripts from the package directory.

A passing type check does not prove behavior is correct: it cannot tell
whether the right links appear or whether a keyboard user can navigate the
page. That is why Part 5's behavior tests and Part 13's production build are
both required. TypeScript also cannot validate data received from the API at
runtime; that boundary needs explicit handling in a later lesson.

## Part 7 — Mount the React component tree

`index.html` contains the browser entry point:

```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

`main.tsx` obtains that element and mounts React:

```tsx
createRoot(rootElement).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
```

The DOM is the browser's object representation of HTML. React manages the
subtree mounted at `#root`. `StrictMode` adds development checks and may run
certain logic more than once in development to reveal unsafe side effects.

Fail explicitly if `#root` is absent. A non-null assertion would silence
TypeScript without protecting the runtime.

## Part 8 — Learn components, props, state, and effects

A component is a function or class that returns React elements. **Props** is
short for **properties**: the named inputs a parent passes to a component.
For example, in `<App role="manager" />`, `role` is a property and
`"manager"` is its value. React gives the component those properties as one
object. A **typed prop** is a property whose allowed values are described by
TypeScript.

`App` describes its properties with an interface:

```tsx
interface AppProps {
  role?: UserRole;
}

export function App({ role = "annotator" }: AppProps) {
  ...
}
```

`AppProps` is the type of the entire properties object. The `?` means `role`
is optional; when provided, it must be a `UserRole`. If it is omitted, the
default value `"annotator"` is used. The `{ role = "annotator" }` syntax is
**object destructuring**: it extracts `role` from the properties object. The
same idea without destructuring would be:

```tsx
export function App(props: AppProps) {
  const role = props.role ?? "annotator";
  return <p>Current role: {role}</p>;
}
```

For comparison, `<App role="manager" />` and `<App />` are valid, but
`<App role="visitor" />` is a TypeScript error because `"visitor"` is not a
`UserRole`. Type checking happens during development; it does not validate
untrusted data arriving from an API at runtime.

Props are supplied by a parent and should be treated as immutable. A child
component reads them; it does not change the parent's values. 

State is component-owned data that may change and trigger another render:

```tsx
const [ready, setReady] = useState(false);
```

`useState` is a React **hook** that lets a function component remember a value
between renders. The argument `false` is the initial value, used on the first
render. The hook returns a two-item array:

```text
[current value, function that requests an update]
```

JavaScript array destructuring gives those items names: `ready` is the value
for the current render and `setReady` is its setter function. The conventional
name of a setter is `set` followed by the state name.

Here is a small example independent of WebAnn:

```tsx
function Counter() {
  const [count, setCount] = useState(0);

  return (
    <button type="button" onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
```

On the first render, `count` is `0`, so the button says “Count: 0.” The
`onClick` property receives a callback to run when the user clicks; it does
not call `setCount` while the component renders. After a click,
`setCount(count + 1)` asks React to update the state. React calls `Counter`
again with `count` equal to `1`, and the button now says “Count: 1.”

Calling a setter does **not** immediately change the local variable in the
current function call. It schedules a new render with the new value. A normal
`let` variable would not work the same way: React would not know to render
again, and the value would be recreated when the component function runs.

Use state for data that changes and must affect the interface. If a value can
be calculated from existing props or state, use a normal `const` instead of
creating another piece of state. For example:

```tsx
const isManager = role === "manager";
```

This derived value needs no `useState`.

### Understand `useEffect`

React calls a component to calculate what the page should show. After React
updates the browser page, it can run an **effect**: code that synchronizes the
component with something outside that calculation. Examples include changing
the browser tab title, subscribing to browser events, or maintaining a
connection to another system.

Lesson 9's `App` contains:

```tsx
useEffect(() => {
  document.title = "WebAnn · Dashboard";
  setReady(true);
}, []);
```

Read it in this order:

1. `useEffect` registers the function inside it as an effect.
2. React first renders `App` and updates the page.
3. React runs the effect. `document.title` changes the browser tab title,
   which is outside the component's rendered JSX.
4. `setReady(true)` requests another render. The next render displays the
   ready message. Calling a setter inside an effect is possible, but it
   creates an extra render and should have a real reason in production code.

The second argument, `[]`, is the **dependency array**. It says the effect
uses no changing values from the component. React associates this effect with
the component mounting; it does not rerun it merely because `ready` changes.
If the title depended on a `projectName` prop, include that value so the title
stays synchronized when the prop changes:

```tsx
useEffect(() => {
  document.title = `WebAnn · ${projectName}`;
}, [projectName]);
```

An effect can return a **cleanup function**. This is important when setup
registers a listener or starts a subscription:

```tsx
useEffect(() => {
  function handleResize() {
    console.log(window.innerWidth);
  }

  window.addEventListener("resize", handleResize);

  return () => {
    window.removeEventListener("resize", handleResize);
  };
}, []);
```

The returned function removes the listener when the component is removed.
React also runs cleanup before rerunning an effect whose dependencies changed.
Without cleanup, repeated setup could leave duplicate listeners or keep
resources alive after the component is gone.

In development, `StrictMode` may run setup and cleanup an extra time to expose
mistakes. Do not assume an effect runs exactly once. Its setup should be safe
to repeat, and any external resource it creates should have a matching
cleanup.

Do not use an effect merely to calculate data from props or state. For
example, `const isManager = role === "manager"` can be calculated directly
during rendering. The lesson's `ready` flag demonstrates how an effect can
request a state update after mounting; a production feature should introduce
such state only when it represents a genuine loading or readiness condition.

The dependency array tells React which values the effect depends on. An empty
array says this effect has no changing component values. In development,
`StrictMode` may run setup again to expose missing cleanup, so effects must be
safe to repeat. A function returned from an effect is its cleanup function.

## Part 9 — Extract and test a pure navigation policy

Create `navigationFor(role)` separately from React. It receives a role and
returns navigation data without reading the DOM, network, or global state.

Pure functions are valuable because the same input always produces the same
output and tests need no environment setup. The component maps that result into
links.

For example, if `navigationFor("annotator")` returns two navigation objects,
the JSX `items.map(...)` produces two links. Test the returned data separately
from testing how React displays it. A small pure policy test is faster and makes
role rules easier to understand.

This frontend policy improves usability, but it is not authorization. Hiding
Configuration from an annotator does not stop a crafted HTTP request. Django's
permissions from Lesson 7 remain the security boundary.

## Part 10 — Use semantic and keyboard-accessible markup

Prefer elements that communicate purpose:

```text
header → brand, primary navigation, and account controls
nav    → primary navigation links inside the header
main   → primary page content
h1/h2  → document hierarchy
a      → navigation action
```

An `aria-label` distinguishes the primary navigation landmark. The brand link
is the first focusable control in this lesson. Visible focus styles are part
of the feature, not decoration.

Testing Library uses queries such as `getByRole()` because these encourage the
same semantic information used by assistive technologies. A role query is more
resilient than selecting `.topbar > nav > ul > li:first-child`.

Automated tests do not prove full accessibility. They provide regression
coverage; keyboard exploration, screen-reader testing, contrast review, and
appropriate automated auditing remain necessary.

## Part 10A — Style the shell with CSS

React decides **what elements exist**; CSS decides **how those elements look
and fit on a screen**. CSS does not replace semantic HTML. Keep the `<header>`,
`<nav>`, `<main>`, headings, links, and buttons meaningful even before styles
load.

Create `frontend/src/styles.css` and import it once in `src/main.tsx`:

```tsx
import "./styles.css";
```

Vite understands the CSS import and includes the styles in development and in
the production build. This is why Part 6 added Vite's client type
declarations: TypeScript also needs to accept the import.

### Read a CSS rule

```css
.brand {
  font-size: 1.25rem;
  font-weight: 750;
  text-decoration: none;
}
```

`.brand` is a **class selector**. It selects an element whose JSX has
`className="brand"`. Each `property: value;` pair is a **declaration**.
`font-size` changes text size; `font-weight` changes its weight; and
`text-decoration: none` removes the link underline. `1rem` is based on the
root text size, so it scales with a user's text settings.

Selectors can target an element, a class, a descendant, or a state:

```css
body                 /* every body element */
.topbar              /* any element with class="topbar" */
.topbar nav a        /* links inside nav inside .topbar */
.topbar nav a:hover  /* those links while pointed at */
```

When multiple rules apply, the browser uses the **cascade**: origin,
importance, selector specificity, and then source order decide which
declaration wins. Start with simple selectors; do not add `!important` to
solve a rule you have not understood.

### Establish page defaults and the box model

Start with the page background, text, and predictable sizing:

```css
:root {
  color: #172033;
  background: #f4f6fb;
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
}

* { box-sizing: border-box; }
body { margin: 0; min-width: 320px; min-height: 100vh; }
```

`:root` targets the document's root element. The font list contains fallbacks:
this lesson does not download `Inter`, so the browser uses an installed
alternative if necessary. `box-sizing: border-box` means an element's declared
width includes its padding and border. `margin: 0` removes the browser's
default outer body margin. `100vh` means the full viewport height.

The **box model** is content surrounded by padding, border, and margin.
Padding is space *inside* an element's border; margin is space *outside* it.
For example, the dashboard card uses padding so its text does not touch its
border, and `margin-top` to separate it from earlier content.

### Lay out the three-part header

Use Flexbox for the header's left-to-right arrangement:

```css
.topbar {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1rem 1.5rem;
  color: white;
  background: #172033;
}

.topbar nav { flex: 1; }
.topbar ul { display: flex; flex-wrap: wrap; gap: .25rem; }
.account-actions { display: flex; gap: .5rem; }
```

The header's children appear in DOM order: brand, navigation, account
controls. `display: flex` places them on one row. `gap` adds space between
them; `align-items: center` aligns them vertically. `nav { flex: 1; }` lets
navigation take the remaining horizontal room, pushing the account buttons
to the right. The navigation's own list is another flex row. Reset the list's
default margin, padding, and bullets in the final stylesheet.

Do not use CSS `order` to make a visually reordered desktop header while
leaving keyboard focus in another order. Keep visual and DOM order aligned.

### Make the layout responsive and focus visible

At narrow widths, a media query changes the layout:

```css
@media (max-width: 640px) {
  .topbar { flex-wrap: wrap; gap: .75rem; }
  .topbar nav { flex-basis: 100%; }
  .account-actions { margin-left: auto; }
}
```

`@media` applies its rules only when the viewport is at most 640 CSS pixels
wide. `flex-wrap` allows a second row. `flex-basis: 100%` gives navigation
its own row, and the account controls follow it. This is a **layout
breakpoint**, not a test for a particular device. The visual order and the
keyboard focus order both remain brand, navigation, then account controls.

Keyboard users need a visible indication of focus. The navigation links use:

```css
.topbar nav a:hover,
.topbar nav a:focus-visible {
  color: #172033;
  background: #ece9ff;
  outline: 2px solid #b9a8ff;
}
```

`:hover` responds to a pointer; `:focus-visible` normally responds to
keyboard focus. Do not remove the browser's focus outline unless you replace
it with an equally visible one. Disabled account buttons should also look
unavailable; CSS appearance alone does not disable them—the `disabled`
attribute in JSX does that.

### Inspect your result

Run `npm --prefix frontend run dev` and view the page at desktop and narrow
widths using your browser's responsive-design tools. Check that the three
header parts are readable, navigation does not overflow, the card has space
around its content, and focus remains visible while pressing `Tab`. Browser
Developer Tools can show which CSS rule affects an element and which rule won
the cascade. Component tests check the DOM behavior, but visual layout also
needs inspection in a real browser.

## Part 11 — Add an error boundary

An error boundary catches errors thrown while descendants render or execute
lifecycle logic and replaces the broken subtree with a fallback.

React error boundaries are class components because the boundary API uses
`getDerivedStateFromError` and `componentDidCatch`:

```text
child throws
    ↓
getDerivedStateFromError marks the boundary failed
    ↓
fallback UI renders
    ↓
componentDidCatch records diagnostic information
```

It does not catch errors in event handlers, arbitrary asynchronous callbacks,
server rendering, or the boundary's own render method. Those need appropriate
local error handling.

The test deliberately renders a component that throws, suppresses expected
console noise, and asserts the recovery heading rather than internal state.

## Part 12 — Configure Vitest and DOM cleanup

Configure Vitest in `vite.config.ts`:

```typescript
test: {
  environment: "jsdom",
  setupFiles: ["./src/test/setup.ts"],
}
```

Import jest-dom matchers in the setup file and clean the rendered DOM after
each test. Without cleanup, elements from an earlier test can remain and cause
false failures such as “Found multiple elements.” Tests must be isolated so
their result does not depend on execution order.

Test behavior:

- use `userEvent` rather than manually dispatching low-level events;
- prefer role, name, and label queries;
- assert what the user can observe;
- avoid testing React implementation details; and
- restore mocks after use.

## Part 13 — Build and serve production assets

### Preview the application in a browser

After creating the React source and installing dependencies, use the Vite
development server to see your work. From the repository root, with Node 22
active, run:

```bash
npm --prefix frontend run dev
```

Leave that terminal running. Vite prints the address it selected, normally
`http://localhost:5173/`. Open that address in a browser on the same machine.
Editing a source file normally updates the page automatically. Press `Ctrl+C`
in the terminal when you are finished. The Lesson 9 shell does not request
Django data yet, so the backend need not be running just to view this page.

If the repository is on a remote server accessed through SSH, `localhost` in
your laptop's browser means your **laptop**, not the server. In another terminal
on your laptop, forward a local port to Vite on the server:

```bash
ssh -L 15173:127.0.0.1:5173 assale02@engagesrv1
```

Keep the SSH session open and visit `http://localhost:15173/` in the laptop's
browser. Replace the username or hostname with the ones used for your own SSH
connection. If Vite reports a port other than 5173 because that port is in
use, use the reported port on the right side of the SSH forwarding command.
The Vite script binds to `0.0.0.0` for container development; an SSH tunnel is
the safer way to reach a remote development server without relying on a
publicly exposed port.

### Create the production build

Run:

```bash
npm --prefix frontend run build
```

`tsc -b` checks the referenced TypeScript projects. Vite then creates hashed
assets in `frontend/dist/`. Hashes let deployments cache files safely because a
content change creates a new URL.

Use a multi-stage Dockerfile:

```text
build stage: npm ci → type-check → Vite build
                         ↓ copies only dist/
runtime stage: server.mjs + compiled static assets
```

The final image does not contain the TypeScript source or build dependencies.
`server.mjs` preserves `/health/` and `/api-health/` from Lesson 3 and serves
the built single-page application for other paths.

### Understand `frontend/server.mjs`

The Vite development server is for editing source code locally. The final
Docker image instead needs a small **HTTP server** that sends the already-built
files in `dist/` to the browser. `frontend/server.mjs` is that server. It is
not a React component and does not render JSX on the server. The browser
downloads HTML, CSS, and JavaScript, then runs the React app itself.

The `.mjs` extension identifies a JavaScript file using ES module syntax such
as `import`. This file uses Node's built-in `http`, `fs/promises`, `path`, and
`url` modules; the runtime image does not need Express or Vite installed.
The Dockerfile starts it with `node server.mjs`.

At startup, the file reads two environment variables:

```javascript
const port = Number(process.env.PORT ?? 5173);
const apiUrl = process.env.API_URL ?? "http://api:8000/health/";
```

`process.env` contains the container's environment variables. `??` means
“use the value on the right when the value on the left is missing or null.”
The frontend listens on port 5173 by default. `API_URL` points to Django's
health endpoint inside the Compose network, where `api` is the service name.
`API_URL` is **not** a general proxy for every `/api/` request.

Read the request routing as three cases:

| Request | Response | What it checks |
| --- | --- | --- |
| `/health/` | JSON with frontend `status: "ok"` | This Node server is responding. |
| `/api-health/` | Django health response, or HTTP 502 if Django cannot be reached | Frontend container can contact the API. |
| `/` or another path | A built file from `dist/`, otherwise `dist/index.html` | The browser can load the React application. |

`http.createServer` receives each request and a response object. The route
handlers call `response.writeHead(...)` to set the HTTP status and
`Content-Type`, then `response.end(body)` to send the body. Each special route
returns after responding so it cannot accidentally continue into static-file
handling. For `/api-health/`, `fetch(apiUrl)` contacts Django. A network error
produces HTTP 502, which means the frontend server responded but could not
reach its upstream API.

For static files, `new URL(...).pathname` extracts the request path;
`path.resolve` constructs an absolute candidate under `dist/`; and the
`safeCandidate` check rejects a path that resolves outside that directory.
`readFile` loads the file and the `contentTypes` table sets an appropriate
MIME type—for example, `text/css` for a CSS asset. A missing path falls back
to `dist/index.html`, allowing a future client-side route such as `/projects/`
to load the React app and let React decide what page to show. Lesson 9 does
not implement those routes yet.

There is an important limitation: the current fallback also returns
`index.html` for a missing asset or unrecognized `/api/` path. Therefore,
`server.mjs` is a minimal tutorial static server, **not** a general API proxy
or a fully hardened production web server. Do not infer API success merely
because an unknown path returned HTTP 200. Later lessons must define explicit
API routing and appropriate 404 behavior as those features are added.

After `docker compose up --build --detach --wait`, inspect the behavior:

```bash
curl -i http://localhost:5173/health/
curl -i http://localhost:5173/api-health/
curl -i http://localhost:5173/
```

The first response proves the frontend process is alive. The second proves
the frontend-to-Django network path works. The third proves the built HTML
can be served. These checks complement—not replace—the React component tests
and browser inspection. If you changed `FRONTEND_PORT` in Compose, use that
host port instead of 5173.

## Part 14 — Extend the shared quality gate and CI

Add `scripts/check-frontend.sh` and call it from `scripts/check` after the
backend gate. The frontend check runs tests and a production build.

Add these Make targets:

```text
make frontend-bootstrap
make frontend-test
make frontend-check
```

CI must run `actions/setup-node` using `.nvmrc`, cache npm using
`frontend/package-lock.json`, and install with `make frontend-bootstrap` before
the shared `make check` command.

The lockfile cache accelerates installation; it does not replace `npm ci`.
Neither a successful build nor a successful test suite replaces the other:
tests verify behavior while the build verifies types and production bundling.

## Part 15 — Verify and open the PR

```bash
make frontend-test
make frontend-check
make check
make container-test
git diff --check
```

Open `Lesson 9: build the tested React application shell`. Include red/green
evidence, screenshots at desktop and narrow widths, keyboard verification, and
the complete command output. Require the frontend-aware CI check before merge.

## Acceptance criteria

- Node.js 22 and locked npm installation are documented and checked.
- The React TypeScript application mounts through `createRoot`.
- The dashboard uses semantic landmarks and responsive styles.
- The stylesheet explains and implements the three-part header, card spacing,
  visible focus states, and narrow-screen layout without changing focus order.
- The header contains brand, horizontal navigation, and clearly disabled
  account controls until authentication exists.
- Navigation comes from a tested pure role policy.
- Hidden navigation is explicitly described as UX rather than authorization.
- Keyboard focus starts at the brand link and remains visible on links.
- An error boundary presents a tested fallback.
- Test DOM state is cleaned between cases.
- TypeScript strict checking, six frontend tests, and the Vite build pass.
- `make check`, CI, and Docker include the frontend.
- The production container serves compiled assets and retains health checks.

## Gold-standard implementation

Read this only after implementation and first review. The checkpoint is
`lesson-09`:

```bash
git fetch --tags
git diff lesson-09 -- . ':!docs/lessons/09-REACT-FOUNDATIONS.md'
```

The reference keeps API integration out of the foundation, tests a pure policy
before rendering it, uses semantic queries, fails clearly when the mount point
is missing, and ships only built assets in the runtime image.

## What you should now be able to explain

- the roles of HTML, CSS, JavaScript, the DOM, and the browser;
- objects, arrays, functions, callbacks, modules, `map`, destructuring, and
  spread syntax;
- TypeScript inference, interfaces, unions, optional properties, and why types
  do not validate runtime API data;
- React versus ReactDOM versus the DOM;
- JSX, components, props, state, and effects;
- compile-time TypeScript versus runtime JavaScript;
- development server versus production build;
- `package.json` versus `package-lock.json`;
- `npm install` versus `npm ci`;
- Vitest, jsdom, Testing Library, and test isolation;
- semantic HTML, accessible names, and keyboard focus;
- error-boundary coverage and limitations; and
- why tests, type checking, build validation, and container smoke tests coexist.

## Beginner glossary

- **runtime:** the environment executing code, such as Node.js or a browser;
- **DOM:** the browser's object representation of the current document;
- **module:** a source file that imports or exports values;
- **callback:** a function passed to other code to run at the appropriate time;
- **component:** a reusable React unit that describes part of the interface;
- **prop:** an input passed from a parent to a component;
- **state:** component-owned data whose update can cause another render;
- **hook:** a React function such as `useState` or `useEffect` that gives a
  function component access to React features;
- **render:** React calling components to calculate the desired element tree;
- **JSX:** syntax for writing React element descriptions alongside JavaScript;
- **static type:** a source-code constraint checked before execution; and
- **bundle:** browser-ready files produced from the source module graph.
