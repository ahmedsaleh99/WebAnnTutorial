# Lesson 1: repository workflow and CI/CD foundation

## Outcome

You will turn an empty Git repository into a governed delivery pipeline. A
pull request will run an executable quality check, GitHub will prevent an
unverified change from merging, dependency updates will be proposed
automatically, and deployment will have an approval boundary without yet
touching a real server.

**Branch:** `lesson/01-ci-cd-foundation`

Complete every command and file change in your own empty student repository,
not in WebAnnTutorial. WebAnnTutorial contains the instructions and reference
checkpoint. If you have not created your repository yet, follow
[the student repository workflow](../STUDENT_WORKFLOW.md) first.

## Why CI/CD comes first

Continuous integration (CI) answers: "Can this proposed change safely join the
shared branch?" Continuous delivery/deployment (CD) answers: "Can this exact,
already-tested revision move to an environment?" Establishing those rules now
means Django, React, Docker, and every feature added later inherit the same
feedback and review process.

CI does not replace review. It automates repeatable facts; reviewers evaluate
intent, design, risks, and clarity. CD also does not mean every commit must be
sent automatically to production. This course uses a protected production
environment and explicit approval.

## Prerequisites

- Git installed and configured
- A GitHub account with access to the repository
- Bash (Git Bash, WSL, Linux, or macOS)
- Permission to configure repository branches and environments, or access to an
  instructor who can do so

Check the tools:

```bash
git --version
bash --version
```

## Part 1 — Create the lesson branch

In your empty student repository, point the unborn `HEAD` at `main`, create the
initial commit, and then create the lesson branch:

```bash
git symbolic-ref HEAD refs/heads/main
git branch --show-current
git commit --allow-empty -m "Initialize student repository"
git push -u origin main
git switch -c lesson/01-ci-cd-foundation
```

`git branch --show-current` must print `main` before the initial commit. This
course uses only `main`, not `master`. Configure Git to use `main` automatically
for future repositories:

```bash
git config --global init.defaultBranch main
```

Why not use `git branch -m main` here? Before the first commit, Git has no
`refs/heads/master` branch to rename even if `git branch --show-current` prints
`master`. After at least one commit exists, `git branch -m main` is the correct
way to rename an existing branch.

The push creates the pull request's base branch on GitHub. Confirm in GitHub's
repository settings that `main` is the default branch and that no `master`
branch remains.

The empty initialization commit is the course's only direct-to-`main`
exception. It is necessary because the first pull request needs an existing
base branch. Do all remaining Lesson 1 work on
`lesson/01-ci-cd-foundation`.

Never put a real password, token, private key, `.env` file, research video, or
participant data in a commit. Removing a secret in a later commit does not
remove it from Git history.

## Part 2 — Write the failing policy check (red)

In test-driven development, you first describe something that must be true and
prove that it is not true yet. Then you implement it. For this infrastructure
lesson, the requirement is: **every repository foundation file must exist**.

Create the `scripts` directory:

```bash
mkdir -p scripts
```

Create `scripts/validate-repository.sh` with this content:

```bash
#!/usr/bin/env bash
set -euo pipefail

required_files=(
  ".editorconfig"
  ".github/PULL_REQUEST_TEMPLATE.md"
  ".github/dependabot.yml"
  ".github/workflows/cd.yml"
  ".github/workflows/ci.yml"
  ".gitignore"
  "CONTRIBUTING.md"
  "LICENSE"
  "README.md"
  "docs/BRANCH_PROTECTION.md"
)

failure_count=0

for required_file in "${required_files[@]}"; do
  if [[ ! -f "$required_file" ]]; then
    echo "ERROR: required file is missing: $required_file" >&2
    failure_count=$((failure_count + 1))
  fi
done

if [[ "$failure_count" -ne 0 ]]; then
  echo "Repository validation failed with $failure_count error(s)." >&2
  exit 1
fi

echo "Repository validation passed."
```

This script loops over the filenames, reports each missing file, and exits with
status `1` if any are absent. A nonzero exit status tells a terminal or CI job
that the check failed.

Next, create `scripts/check` with this content:

```bash
#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repository_root"

bash scripts/validate-repository.sh
```

`scripts/check` is the public entry point. It finds the repository root and
calls the detailed validator. Make both files executable, then run the check:

```bash
chmod +x scripts/check scripts/validate-repository.sh
./scripts/check
```

Expected result: the command prints errors such as:

```text
ERROR: required file is missing: .editorconfig
ERROR: required file is missing: .github/workflows/ci.yml
ERROR: required file is missing: README.md
Repository validation failed with 10 error(s).
```

The exact number decreases if you already created some files. The important
result is that the command fails for the expected reason: the required files do
not exist yet. Do not "fix" the test by removing filenames from the list. Parts
3–6 make the check pass by creating the required files.

This is the infrastructure version of a failing test. The validator is the
test, the required-file list is the expected behavior, and the files added in
the next parts are the implementation.

Why use `scripts/check` instead of placing commands only in YAML? Developers
can reproduce CI locally, and future lessons can extend one interface with
backend tests, frontend tests, type checking, and Docker validation.

## Part 3 — Add repository conventions

Add these files:

- `.editorconfig` for consistent text encoding, indentation, line endings, and
  final newlines;
- `.gitignore` for secrets, virtual environments, dependencies, builds,
  databases, media, and local container data;
- `LICENSE` to state reuse rights explicitly;
- `README.md` as the repository entry point;
- `CONTRIBUTING.md` for branches, commits, tests, review, and the lesson flow;
- `.github/PULL_REQUEST_TEMPLATE.md` to collect deliverables, TDD evidence,
  verification, security considerations, and reflection;
- `docs/BRANCH_PROTECTION.md` to record the GitHub settings that cannot be
  stored completely in the repository.

### Configure consistent editor behavior

Create `.editorconfig` in the repository root:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2
trim_trailing_whitespace = true

[*.py]
indent_size = 4

[Makefile]
indent_style = tab

[*.md]
trim_trailing_whitespace = false
```

[EditorConfig](https://editorconfig.org/) lets supported editors apply basic
text-formatting rules from the repository instead of relying on every
contributor's personal settings.

- `root = true` tells an editor to stop looking for another `.editorconfig` in
  parent directories.
- `[*]` applies the first group to every file.
- `charset = utf-8` uses one portable text encoding.
- `end_of_line = lf` avoids Windows/Linux line-ending-only diffs.
- `insert_final_newline = true` keeps text files friendly to command-line tools
  and POSIX conventions.
- `indent_style = space` and `indent_size = 2` establish the general default
  used by YAML, JSON, TypeScript, CSS, and Markdown in this course.
- `trim_trailing_whitespace = true` removes invisible whitespace that creates
  noisy diffs.
- `[*.py]` overrides the general indentation width because standard Python uses
  four spaces.
- `[Makefile]` requires tabs because Make recipes distinguish tabs from spaces.
- `[*.md]` preserves trailing whitespace because Markdown can use two trailing
  spaces as an intentional hard line break.

EditorConfig influences editing but is not a complete formatter or linter.
Some editors support it automatically; others require an EditorConfig plugin.
Later lessons add language-specific tools that CI can enforce independently of
the editor.

### Exclude local and generated files from Git

Create `.gitignore` in the repository root:

```gitignore
# Operating systems and editors
.DS_Store
Thumbs.db
.idea/
.vscode/
*.swp

# Environment variables and secrets
.env
.env.*
!.env.example
*.pem
*.key

# Python and Django
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
.venv*/
venv/
db.sqlite3
media/
staticfiles/

# Node, Vite, and TypeScript
node_modules/
dist/
coverage/
*.tsbuildinfo

# Docker and local runtime data
docker-data/
*.log
```

The groups have different purposes:

- OS/editor rules exclude machine-specific metadata and temporary swap files.
- environment rules reduce the chance of committing local configuration,
  credentials, certificates, and private keys;
- Python rules exclude bytecode, caches, virtual environments, coverage
  output, the local SQLite database, uploaded media, and collected static files;
- Node rules exclude downloaded packages, builds, coverage, and TypeScript's
  incremental build metadata;
- Docker/runtime rules exclude persistent local service data and logs.

Gitignore patterns are interpreted from the directory containing the file. A
trailing `/` matches a directory, `*` is a wildcard, and `!` re-includes a
previously ignored path. Therefore `.env.*` ignores files such as `.env.local`,
while `!.env.example` allows a safe, documented example file to be committed in
a later lesson.

`.gitignore` is convenience, not secret protection. It affects only untracked
files. If Git already tracks a file, adding its name to `.gitignore` does not
remove it from history. Check a path with:

```bash
git check-ignore -v .env
git status --short
```

If a real secret is ever committed, immediately revoke or rotate it; merely
deleting the file in a later commit is insufficient.

GitHub loads a pull-request template only from the repository's default branch.
During Lesson 1, the new template exists only on the lesson branch, so it will
not automatically appear in the pull request that introduces it. For this first
pull request, copy the template contents manually into the PR description. Once
Lesson 1 is merged into `main`, GitHub will insert it automatically for Lesson 2
and later pull requests.

Run the check again. It should make progress but remain red until every
required automation file exists.

## Part 4 — Build continuous integration

### What a GitHub Actions workflow is

A workflow is an automated process described by a YAML file inside
`.github/workflows/`. GitHub reads that file and starts a **workflow run** when
one of its configured events occurs.

A workflow contains four important levels:

1. An **event** starts the workflow, such as opening a pull request or pushing a
   commit.
2. A **workflow run** is one execution of the entire YAML definition for a
   particular Git revision.
3. A **job** runs on a fresh machine called a runner. Multiple jobs can run in
   parallel unless dependencies are declared.
4. A **step** is one action or shell command inside a job. Steps in one job run
   in order and normally stop after a failure.

For this lesson, the flow is:

```text
push commit to lesson branch
        ↓
open or update pull request targeting main
        ↓
GitHub creates an Ubuntu runner
        ↓
runner checks out the proposed revision
        ↓
runner executes ./scripts/check
        ↓
exit 0 = pass; any nonzero exit = fail
        ↓
result appears on the pull request
```

GitHub-hosted runners are temporary. A new runner does not automatically have
the repository files, local uncommitted changes, or software installed on your
computer. Each job must obtain everything it needs.

### Create the workflow

Create `.github/workflows/ci.yml` with this complete content:

```yaml
name: CI

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  repository-validation:
    name: Repository validation
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Check out the repository
        uses: actions/checkout@v6

      - name: Run the same checks used locally
        run: ./scripts/check
```

YAML indentation is meaningful. Use spaces, not tabs, and keep child settings
indented beneath their parent keys.

### Understand each section

`name: CI` gives the workflow a readable name on GitHub's **Actions** page.

`on` defines the events that start it:

- `pull_request` runs CI when a pull request is opened, reopened, or updated.
  This tests proposed work before it enters `main`.
- `push` with `branches: [main]` runs CI again after changes reach `main`. This
  verifies the shared branch and catches differences between the reviewed
  revision and the final merged revision.
- A push to an ordinary lesson branch does not start this workflow by itself.
  It starts when that branch has a pull request targeting the repository.

`permissions: contents: read` limits the temporary `GITHUB_TOKEN` supplied to
the workflow. This job needs to read source code but does not need permission to
modify repository contents, issues, packages, deployments, or pull requests.
Start with no write authority and add a narrowly scoped permission only when a
later job has a documented reason.

`concurrency` groups runs by workflow and Git reference. When a student pushes
a replacement commit to the same pull request, `cancel-in-progress: true`
cancels its obsolete run. GitHub then spends time checking the newest revision
instead of finishing a result that can no longer be merged.

`jobs` contains the work. `repository-validation` is the job's machine-readable
identifier, while `name: Repository validation` is the status-check name shown
on the pull request. Branch protection will require that readable check.

`runs-on: ubuntu-latest` asks GitHub for a new hosted Ubuntu runner.
`timeout-minutes: 5` fails a stuck job instead of allowing it to run
indefinitely.

The first step uses `actions/checkout@v6`. An **action** is reusable workflow
code; checkout downloads the Git revision being tested into the otherwise empty
runner workspace. Without it, `./scripts/check` would not exist on the runner.

The second step uses `run`, which executes a shell command. GitHub marks the
step and job as successful when `./scripts/check` exits with status `0`. The
validator exits with status `1` when it finds a violation, so the step, job, and
workflow all become red.

Keep policy logic in the script rather than duplicating it in YAML. Both a
developer and GitHub can run the same command:

```bash
./scripts/check
```

### Observe the first CI run

To see CI fail before the remaining required files are implemented, commit the
work so far, push the lesson branch, and open a **draft** pull request targeting
`main`:

```bash
git add .
git commit -m "Add initial repository validation and CI"
git push -u origin lesson/01-ci-cd-foundation
```

On GitHub, open the pull request's **Checks** section or select the run under
the **Actions** tab. Expand **Repository validation**, then expand the failing
step. Its log should list the files that Parts 5 and 6 have not created yet.
That is the CI version of the red result already seen locally.

Continue working on the same lesson branch. After completing the remaining
parts, commit and push again. The pull request's `synchronize` event starts a new
workflow run, and concurrency cancels an older run if it is still executing.
The check should become green when all requirements are satisfied.

If you prefer not to open a draft pull request midway through the lesson, the
local failing run is still valid red evidence. Open the pull request in Part 8
and use the acceptance exercise to observe a failure and recovery on GitHub.

### Action version security

`actions/checkout@v6` uses a major-version tag, which is readable and easy to
maintain for this tutorial. A security-sensitive production repository can pin
an action to a reviewed full commit SHA so its code cannot change behind the
tag. Dependabot can then propose SHA updates through normal pull requests.

## Part 5 — Add dependency maintenance

### Why dependencies need maintenance

The workflow already depends on external code through
`actions/checkout@v6`. Later, the backend will depend on Python packages and the
frontend will depend on npm packages. Dependencies receive bug fixes and
security updates, but manually checking every package is easy to forget.

Dependabot reads `.github/dependabot.yml`, checks configured package ecosystems
on a schedule, and opens ordinary pull requests when supported updates are
available. It proposes changes; it does not approve or merge them. Every
Dependabot pull request must pass the same CI and review rules as a student's
pull request.

### Create the Dependabot configuration

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
    labels:
      - dependencies
      - ci
```

Understand each setting:

- `version: 2` selects version 2 of the Dependabot configuration format. It is
  not the version of a dependency.
- `updates` is a list because one repository can contain several package
  ecosystems.
- `package-ecosystem: github-actions` tells Dependabot to inspect `uses:`
  references in workflow files.
- `directory: /` means the repository root. GitHub Actions workflows always
  live below the root `.github/workflows/` directory.
- `interval: weekly` asks Dependabot to check once a week. It does not promise a
  pull request every week; a PR is opened only when an applicable update exists.
- `open-pull-requests-limit: 5` prevents update proposals from flooding the
  repository. New proposals wait when five Dependabot version-update PRs are
  already open for this ecosystem.
- `labels` makes these maintenance PRs easier to filter. Create the `ci` label
  manually if GitHub has not already created it; a missing custom label should
  not be treated as permission to skip review.

Dependabot reads its configuration from `main`. It will not begin scheduled
checks merely because the file exists on an unmerged lesson branch. After
Lesson 1 is merged, open **Insights → Dependency graph → Dependabot** or the
repository's security settings to confirm that version updates are enabled.
The exact menu name can vary with GitHub's current interface and organization
policy.

Do not configure Python or npm yet: neither package manifest exists in Lesson
1. When later lessons add `backend/requirements.txt` and
`frontend/package.json`, add separate `pip` and `npm` entries with the correct
directories. Configuration should reflect dependencies that really exist now.

### How an update flows through the repository

```text
Dependabot checks GitHub Action references on its weekly schedule
        ↓
an update is available
        ↓
Dependabot creates a branch and pull request
        ↓
the pull_request event starts CI
        ↓
Repository validation and review must pass
        ↓
only then may the update be merged into main
```

## Part 6 — Create a safe CD boundary

### CI, continuous delivery, and continuous deployment

CI validates proposed changes. A delivery pipeline then prepares a validated
revision so it can be released. A deployment pipeline changes a real
environment. The terms are sometimes combined as “CI/CD,” but the permissions
and risks are different: tests read code, while deployment may change servers,
databases, networking, and user-facing behavior.

Lesson 1 creates only the control boundary for CD. It proves that a person can
select an exact revision, revalidate it, and pass through a protected
`production` approval. It does **not** build an application artifact, connect to
a server, use deployment credentials, or change production. Those capabilities
arrive in Lesson 24 after the application and its operational procedures exist.

### Why select a commit SHA

A branch name such as `main` can point to a different commit tomorrow. A Git
commit SHA identifies one exact snapshot. Requiring the full 40-character SHA
makes the release candidate explicit and auditable:

```bash
git rev-parse HEAD
```

Copy the output only from a revision whose CI checks passed. Re-running
`./scripts/check` in CD provides defense in depth, but it does not itself prove
that someone reviewed the commit. Branch protection, CI history, and the
production reviewer provide the other controls.

### Create the CD skeleton

Create `.github/workflows/cd.yml`:

```yaml
name: CD skeleton

on:
  workflow_dispatch:
    inputs:
      commit_sha:
        description: Full commit SHA already validated by CI
        required: true
        type: string

permissions:
  contents: read

concurrency:
  group: production-deployment
  cancel-in-progress: false

jobs:
  validate-release-candidate:
    name: Validate release candidate
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Validate commit SHA format
        env:
          CANDIDATE_SHA: ${{ inputs.commit_sha }}
        run: |
          if [[ ! "$CANDIDATE_SHA" =~ ^[0-9a-fA-F]{40}$ ]]; then
            echo "commit_sha must be a full 40-character Git commit SHA" >&2
            exit 1
          fi

      - name: Check out the requested commit
        uses: actions/checkout@v6
        with:
          ref: ${{ inputs.commit_sha }}

      - name: Run the complete quality gate
        run: ./scripts/check

      - name: Record the immutable candidate
        run: git rev-parse HEAD

  production-approval:
    name: Production approval placeholder
    needs: validate-release-candidate
    runs-on: ubuntu-latest
    timeout-minutes: 5
    environment: production
    steps:
      - name: Explain the intentional stopping point
        run: echo "Approval passed; deployment is added in Lesson 24."
```

### Understand the trigger and input

`workflow_dispatch` adds a **Run workflow** button to the Actions page. The
workflow runs only when an authorized person starts it; pushes and pull requests
do not trigger it.

The required string input is available as `${{ inputs.commit_sha }}`. The first
step copies it into an environment variable and verifies that it contains
exactly 40 hexadecimal characters. Passing user input through `env` avoids
placing it directly inside shell syntax. Format validation prevents a student
from accidentally supplying `main`, a short SHA, or arbitrary text.

`actions/checkout` uses `ref: ${{ inputs.commit_sha }}` to retrieve that exact
commit. If the correctly formatted SHA does not exist in this repository,
checkout fails and later steps do not run.

### Understand permissions and concurrency

As in CI, `contents: read` is sufficient because the skeleton only reads a
revision. It cannot publish packages, modify the repository, or create a GitHub
deployment.

Every run uses the same `production-deployment` concurrency group. Only one
production candidate should cross the approval boundary at a time.
`cancel-in-progress: false` is intentional: starting a second candidate must not
silently cancel one that a reviewer may already be evaluating. A later release
process should require an explicit decision about the older run.

### Understand the two jobs

`validate-release-candidate` checks the input, checks out the commit, runs the
same quality gate as CI, and prints the checked-out SHA into the log. Printing
the SHA provides simple audit evidence of what was evaluated.

`production-approval` declares
`needs: validate-release-candidate`, so GitHub does not start it unless the first
job passes. It also declares `environment: production`. When that GitHub
environment has required reviewers, the job pauses and asks for approval before
allocating its runner and executing steps.

The final `echo` is intentionally harmless. Reaching it proves that validation,
job ordering, and environment approval worked. It is not a deployment.

### Configure and test the protected environment

The manual workflow becomes runnable only after `.github/workflows/cd.yml`
exists on `main`, so perform this verification after Lesson 1 is merged:

1. In GitHub, open **Settings → Environments** and create `production`.
2. Add at least one required reviewer when the repository plan and permissions
   support that protection.
3. Restrict deployments to `main` or protected branches.
4. Do not add secrets during this lesson.
5. Open **Actions → CD skeleton → Run workflow**.
6. Paste the full SHA of the merged, green Lesson 1 commit.
7. Confirm **Validate release candidate** passes.
8. Confirm **Production approval placeholder** waits for approval.
9. Approve it and confirm the log contains only the intentional placeholder.

Also try an invalid value such as `main`. The format step must fail before
checkout. If required reviewers are unavailable for the repository's GitHub
plan, document that limitation and the expected approval behavior in the pull
request.

Do not add SSH keys, cloud credentials, a server address, or a fake deployment
command. A safe placeholder demonstrates the workflow without creating an
unreviewed external side effect.

## Part 7 — Make the check green

Once Parts 3–6 create every listed file, the original required-file test should
turn green. Before the final run, harden `scripts/validate-repository.sh` to also
check that:

- `scripts/check` is executable;
- tracked non-Markdown files have no trailing whitespace;
- `.env` and `db.sqlite3` are not tracked;
- generated/runtime directories such as `node_modules`, `dist`, `coverage`,
  `media`, and `docker-data` are not tracked.

The gold-standard section explains the final validator structure. Make your own
attempt first using the same loop-and-failure-count pattern as the required-file
check.

Make both scripts executable and run:

```bash
chmod +x scripts/check scripts/validate-repository.sh
./scripts/check
git diff --check
```

Expected result:

```text
Repository validation passed.
```

The validator checks required files, executable metadata, trailing whitespace,
and common forbidden tracked paths. It is deliberately small and dependency
free because the repository does not yet contain a Python or Node toolchain.

## Part 8 — Commit and open the pull request

Review exactly what will be committed:

```bash
git status --short
git diff --check
git add .
git diff --cached --stat
git commit -m "Establish repository delivery workflow"
git push -u origin lesson/01-ci-cd-foundation
```

Open a pull request targeting `main`. The template will not populate
automatically for this first PR because `.github/PULL_REQUEST_TEMPLATE.md` is
not on `main` yet. Open that file on the lesson branch, copy its complete
contents, paste them into the pull-request description, and fill in every
section, including evidence from the failing and passing repository checks.

The CI workflow can run from the proposed change, so GitHub will run it for this
pull request even though the PR template itself is not yet available as the
default template.

After Lesson 1 is merged, begin creating the Lesson 2 pull request and confirm
that GitHub fills its description automatically. You do not need to submit the
Lesson 2 PR during this verification.

## Part 9 — Configure GitHub protections

Follow `docs/BRANCH_PROTECTION.md`. Repository settings are not fully expressed
by committed files, so this is a required manual deliverable. Use the
recommended **branch ruleset**, not classic branch protection, when rulesets are
available for the repository. Create the ruleset without the required-status
rule if GitHub has not observed any checks yet; GitHub does not allow that rule
to have an empty check list. After the first CI run makes
**Repository validation** available, edit the ruleset and require that check
before merging. Also create a protected `production` environment. Test the
manual CD skeleton after the merge, when the workflow exists on `main`.

## Acceptance exercise

On the lesson branch, temporarily rename one required file:

```bash
mv CONTRIBUTING.md CONTRIBUTING.md.disabled
./scripts/check
mv CONTRIBUTING.md.disabled CONTRIBUTING.md
./scripts/check
```

The first run must fail with a useful message and the second must pass. Do not
commit the temporary rename. After pushing, confirm CI is green and branch
protection requires the check and review before merge.

## Acceptance criteria

- A deliberately invalid repository change fails locally and in CI.
- Correcting the violation makes both checks pass.
- CI permissions are read-only and jobs have timeouts.
- Local and CI validation use the same command.
- The local and GitHub default branch is `main`, and no `master` branch exists.
- The Lesson 1 PR uses a manually copied template, and the template populates
  automatically for pull requests created after it is merged into `main`.
- Pull requests require the validation check before merge. Instructor-led
  repositories also require one independent approval; solo-study repositories
  document a self-review.
- The CD skeleton accepts an immutable commit, revalidates it, and crosses a
  protected environment approval without deploying anything.
- No credential or production deployment capability is committed.
- Dependency updates for GitHub Actions are configured.

## Common mistakes

- **CI-only commands:** when developers cannot reproduce a job locally, failures
  are slower to diagnose. Put behavior in `scripts/check`.
- **Broad workflow permissions:** omitted or write-all permissions increase the
  effect of a compromised action. Declare the smallest permissions explicitly.
- **Using a branch name as a release candidate:** a branch can move after
  approval. Use the tested full commit SHA or, later, an immutable image digest.
- **Secrets in repository files:** `.gitignore` prevents common accidents but
  cannot protect a file already tracked. Use GitHub environment secrets later.
- **A pretend deploy command:** placeholders must be visibly non-deploying so no
  student mistakes them for a production process.

## Review questions

1. Why should CI run on pull requests and again on `main`?
2. Which risks are reduced by `contents: read`, job timeouts, and concurrency?
3. Why does the CD skeleton request a commit SHA rather than deploy `main`
   without identifying a revision?
4. Which protections live in Git rather than GitHub settings?
5. What new checks should `./scripts/check` gain when Python and Node arrive?

## Gold-standard implementation

Read this section only after completing your own attempt and opening its pull
request in your student repository. The WebAnnTutorial `lesson-01` checkpoint
is the executable gold standard; do not merge or copy its Git history into your
repository.

### Reference steps

1. Define the observable repository contract in
   `scripts/validate-repository.sh` and observe it fail.
2. Add neutral repository conventions (`.editorconfig`, `.gitignore`, license,
   README, and contribution rules).
3. Add the PR template so review captures TDD and security evidence.
4. Add a minimal CI orchestrator that calls `./scripts/check` with read-only
   permissions, concurrency control, and a timeout.
5. Add Dependabot for the only current dependency ecosystem: GitHub Actions.
6. Add a manually dispatched CD skeleton that checks out an exact SHA,
   revalidates it, and waits at the protected production environment.
7. Make scripts executable and prove the contract fails then passes.
8. Configure branch/environment protection in GitHub and record manual evidence
   in the PR.

### Why this is the gold standard

- There is one reproducible quality entry point shared by humans and CI.
- The check begins with no external dependencies and can run immediately.
- Workflow authority is minimized and every job is bounded.
- CI validates proposed and merged states; CD revalidates an immutable input.
- Deployment authority is separated behind an environment approval.
- Manual GitHub settings are documented and testable instead of assumed.
- The structure is intentionally ready to extend rather than pretending the
  empty repository already needs Python, Node, or container tooling.

### Compare and reflect

Do not copy differences mechanically. For each difference, decide whether your
solution offers the same safety and observable behavior. Record the comparison
in the pull request template, make justified improvements, rerun
`./scripts/check`, and request final review.
