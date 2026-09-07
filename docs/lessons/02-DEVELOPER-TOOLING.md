# Lesson 2: local developer tooling and quality gates

## Outcome

Starting from the repository produced by Lesson 1, you will establish one
repeatable developer command, pin the runtime families used by the finished
application, add shell validation, install a pre-commit hook, and make CI use
the same quality gate.

**Branch:** `lesson/02-developer-tooling`

## What you will learn

- the difference between a runtime, dependency, tool, and quality gate;
- how version declarations prevent “works on my machine” drift;
- how a Makefile provides stable project commands;
- how local Git hooks provide fast feedback;
- why CI must repeat local checks;
- how to introduce a check with red-green-refactor.

## Starting state

Lesson 1 must already be merged. In the student repository:

```bash
git switch main
git pull --ff-only
git status --short
make --version
```

`git status --short` should print nothing. If Lesson 1 did not create `make`
targets, that is expected; `make check` is introduced in this lesson.

## Step 1 — Create the lesson branch

```bash
git switch -c lesson/02-developer-tooling
```

All remaining changes belong on this branch.

## Step 2 — Prepare Python 3.12 before running bootstrap

Check the active interpreter:

```bash
python3 --version
```

If it reports Python 3.12, continue. If it does not, install or activate Python
3.12 using [Local developer tooling](../TOOLING.md#2-obtain-python-312-when-it-is-missing),
then run the version command again.

Do not run `make PYTHON=python3.12 bootstrap` unless this succeeds first:

```bash
python3.12 --version
```

The Make variable selects a command; it does not install one.

## Step 3 — Define the Lesson 2 contract (red)

Add these paths to `required_files` in
`scripts/validate-repository.sh` before creating them:

```bash
".nvmrc"
".pre-commit-config.yaml"
".python-version"
"Makefile"
"docs/TOOLING.md"
"requirements-dev.txt"
```

An executable file is a script that the operating system is permitted to run as
a command. Lesson 1 contains a single executable check similar to:

```bash
if [[ ! -x "scripts/check" ]]; then
  echo "ERROR: scripts/check must be executable" >&2
  failure_count=$((failure_count + 1))
fi
```

Lesson 2 adds more scripts. Replace that repeated single-file check with one
loop that applies the same rule to all of them:

```bash
for executable_file in \
  scripts/check \
  scripts/check-python-runtime.sh \
  scripts/check-shell.sh \
  scripts/validate-repository.sh; do
  if [[ ! -x "$executable_file" ]]; then
    echo "ERROR: $executable_file must be executable" >&2
    failure_count=$((failure_count + 1))
  fi
done
```

The backslashes continue one shell command across several readable lines. On
each iteration, `executable_file` holds one path. The `-x` test is true when the
file exists and has executable permission; `!` reverses it, so the error block
runs when the script cannot be executed.

The two new scripts do not exist yet, so this loop intentionally contributes to
the red result. After creating them in later steps, set their permission:

```bash
chmod +x scripts/check-python-runtime.sh scripts/check-shell.sh
```

Git records this executable bit with the file, allowing CI and other Linux/WSL
clones to run it. If your Lesson 1 solution already uses a loop, add the two new
paths to its existing list rather than creating a second loop.

Run the existing Lesson 1 command:

```bash
./scripts/check
```

It must fail because the new contract is not implemented. Save this output as
the lesson's red evidence.

## Step 4 — Declare the runtime families

Create `.python-version`:

```text
3.12
```

Create `.nvmrc`:

```text
22
```

These files declare the runtime families used by the finished application's
Python and Node container images. They inform developers and compatible version
managers; they do not install software.

Add validation that each file contains exactly its expected value:

```bash
if [[ -f .python-version ]] && ! grep -qx '3.12' .python-version; then
  echo "ERROR: .python-version must declare Python 3.12" >&2
  failure_count=$((failure_count + 1))
fi

if [[ -f .nvmrc ]] && ! grep -qx '22' .nvmrc; then
  echo "ERROR: .nvmrc must declare Node.js 22" >&2
  failure_count=$((failure_count + 1))
fi
```

## Step 5 — Validate the interpreter used by bootstrap

Create `scripts/check-python-runtime.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

python_command="${1:-python3}"

if ! command -v "$python_command" >/dev/null 2>&1; then
  echo "ERROR: Python command not found: $python_command" >&2
  echo "Install or activate Python 3.12; see docs/TOOLING.md" >&2
  exit 1
fi

"$python_command" - <<'PYTHON'
import sys

required = (3, 12)
actual = sys.version_info[:2]

if actual != required:
    print(
        f"ERROR: Python 3.12 is required, but {sys.version.split()[0]} is active.",
        file=sys.stderr,
    )
    print(
        "Install or activate Python 3.12; see docs/TOOLING.md",
        file=sys.stderr,
    )
    raise SystemExit(1)

print(f"Python runtime check passed: {sys.version.split()[0]}")
PYTHON
```

Make it executable:

```bash
chmod +x scripts/check-python-runtime.sh
```

Test both paths when commands are available:

```bash
./scripts/check-python-runtime.sh python3
./scripts/check-python-runtime.sh command-that-does-not-exist
```

The correct Python must pass; the nonexistent command must fail clearly.

## Step 6 — Add the Makefile and bootstrap environment

Create `requirements-dev.txt`:

```text
pre-commit==4.6.2
```

Create `Makefile` with the complete task interface:

```makefile
.PHONY: help bootstrap hooks check validate shell-check verify-python

PYTHON ?= python3
VENV := .venv
PRE_COMMIT := $(VENV)/bin/pre-commit

help:
	@echo "Available targets:"
	@echo "  bootstrap   Create the tooling environment and install dependencies"
	@echo "  hooks       Install the Git pre-commit hook"
	@echo "  check       Run every quality check available in this lesson"
	@echo "  validate    Validate repository policy"
	@echo "  shell-check Check shell scripts for syntax errors"

bootstrap: $(PRE_COMMIT)

verify-python:
	@./scripts/check-python-runtime.sh "$(PYTHON)"

$(PRE_COMMIT): requirements-dev.txt | verify-python
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install --requirement requirements-dev.txt

hooks: bootstrap
	$(PRE_COMMIT) install

check:
	./scripts/check

validate:
	./scripts/validate-repository.sh

shell-check:
	./scripts/check-shell.sh
```

The order-only prerequisite after `|` makes runtime verification run before
environment creation without treating its timestamp as build output.

Update `.gitignore` from `.venv/` to:

```gitignore
.venv*/
```

Now create the environment using the Python command verified in Step 2:

```bash
# When python3 reports 3.12
make bootstrap

# Or, only when python3.12 --version succeeds
make PYTHON=python3.12 bootstrap
```

If an earlier attempt created `.venv` with the wrong Python, follow
[the recovery procedure](../TOOLING.md#recover-from-a-venv-created-with-the-wrong-python)
before retrying.

## Step 7 — Add shell syntax checking

Create `scripts/check-shell.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

while IFS= read -r -d '' shell_file; do
  bash -n "$shell_file"
done < <(find scripts -type f -print0)

echo "Shell syntax validation passed."
```

Make it executable and add it to `scripts/check` after repository validation:

```bash
chmod +x scripts/check-shell.sh
```

```bash
bash scripts/validate-repository.sh
bash scripts/check-shell.sh
```

Complete the Makefile with these public targets:

```text
make help
make bootstrap
make hooks
make check
make validate
make shell-check
```

Each target should delegate to the focused script or tool rather than duplicate
its implementation.

## Step 8 — Prove shell checking goes red and green

Temporarily introduce an incomplete `if` statement in a shell script and run:

```bash
make shell-check
```

It must fail with a Bash syntax error. Undo only the intentional error and run
the command again. It must print:

```text
Shell syntax validation passed.
```

Do not commit the intentionally broken script.

## Step 9 — Configure and install the Git hook

Create `.pre-commit-config.yaml`:

```yaml
minimum_pre_commit_version: "4.6.2"
repos:
  - repo: local
    hooks:
      - id: project-quality-gate
        name: Project quality gate
        entry: make check
        language: system
        pass_filenames: false
        always_run: true
```

Install it:

```bash
make hooks
```

The hook runs `make check` before Git creates a commit. It provides fast local
feedback but does not replace CI because hooks can be absent or skipped.

## Step 10 — Add the tooling reference

Add `docs/TOOLING.md` and link it from `README.md`. It must present setup in
this order:

1. check Python;
2. install or activate Python 3.12 if necessary;
3. run `make bootstrap`;
4. run `make hooks`;
5. run `make check`;
6. diagnose or recreate an incorrect `.venv`.

Do not include machine-specific usernames, home directories, or server paths.

## Step 11 — Make automation use the same interface

Change the CI and CD quality commands to:

```yaml
run: make check
```

Update the contribution guide and PR template to tell developers to run
`make check`.

Do not add `actions/setup-python` or `actions/setup-node` yet. Lesson 2 CI runs
Bash repository checks; it does not execute Python or Node application code.
Installing unused runtimes adds time and post-job cleanup behavior without
testing anything. `make check` validates the contents of `.python-version` and
`.nvmrc`. Lesson 4 will set up Python when CI first runs Django code, and Lesson
9 will set up Node when CI first runs frontend code.

Update both workflows to `actions/checkout@v6`. Checkout uses Node 24
internally. That internal action runtime is independent of the future
application's Node 22 version declared in `.nvmrc`.

If a run still prints a `punycode` deprecation warning during **Post job
cleanup**, open the run and identify the action that owns that cleanup step. In
this lesson, `setup-python` and `setup-node` should not be present. Remove those
unused steps, push the correction, and inspect the new run rather than changing
the application's `.nvmrc`.

Add a root `pip` entry to `.github/dependabot.yml` so Dependabot monitors
`requirements-dev.txt`. Do not add npm yet because no `package.json` exists.

## Step 12 — Run the complete gate and open the PR

```bash
make check
git diff --check
git status --short
```

Expected quality output:

```text
Repository validation passed.
Shell syntax validation passed.
```

Commit and push:

```bash
git add .
git commit -m "Add reproducible developer tooling"
git push -u origin lesson/02-developer-tooling
```

Open a pull request targeting `main`. The Lesson 1 PR template should populate
automatically. Record the missing-file and shell-syntax red evidence, the final
green output, and any environment problem you solved.

## Acceptance criteria

- The work starts from the merged Lesson 1 `main` branch.
- Python 3.12 is verified before `.venv` is created.
- `.python-version` contains `3.12`; `.nvmrc` contains `22`.
- `make check` runs every quality check introduced so far.
- A deliberate shell syntax error fails, and its correction passes.
- Pre-commit is pinned and the installed hook calls `make check`.
- CI calls the same `make check` command and does not install unused runtimes.
- Dependabot monitors `requirements-dev.txt`.
- `.venv*` directories are ignored and no environment is committed.
- Documentation contains no machine-specific installation path.

## Common mistakes

- Assuming `PYTHON=python3.12` installs Python.
- Creating `.venv` before verifying the interpreter.
- Downgrading pre-commit to accommodate an obsolete Python.
- Nesting setup instructions inside troubleshooting instead of presenting them
  before bootstrap.
- Using spaces instead of a tab for Make recipes.
- trusting a local hook as the only enforcement mechanism.
- Adding linters for Django or React before those source trees exist.

## Gold-standard implementation

After your first attempt and CI run, compare with the WebAnnTutorial
`lesson-02` checkpoint.

The reference separates responsibilities:

```text
.python-version                    Python runtime declaration
.nvmrc                             Node runtime declaration
requirements-dev.txt               pinned developer dependency
scripts/check-python-runtime.sh    bootstrap precondition
scripts/validate-repository.sh     repository policy
scripts/check-shell.sh             shell parsing
scripts/check                      quality-gate composition
Makefile                           public task interface
.pre-commit-config.yaml            local Git integration
docs/TOOLING.md                    setup and recovery reference
```

The important design is the flow:

```text
obtain Python 3.12
        ↓
make bootstrap → verify runtime → create .venv → install pinned tools
        ↓
make hooks → install local Git hook
        ↓
make check → repository validation + shell syntax
        ↓
CI runs the same make check command
```

Record what matched, what differed, and which changes you made after comparison
in the pull request. A different implementation is acceptable only when it
preserves this ordering, isolation, reproducibility, and observable behavior.
