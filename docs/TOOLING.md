# Local developer tooling

This is the reference for setting up the tools introduced in Lesson 2. Follow
the lesson in order when building the repository for the first time.

## Supported development shell

The project commands use Bash and GNU Make. Use one of:

- Linux;
- macOS with Bash and GNU Make;
- Windows Subsystem for Linux (WSL).

On Windows, run the course inside WSL. Native PowerShell uses different virtual
environment paths and is not the supported shell for these lessons.

## Required tools

```text
Git
Bash
GNU Make
Python 3.12
Node.js 22
```

Lesson 2 uses Python to install pre-commit. Node.js is declared now but is not
used until the React lessons.

## Setup sequence

### 1. Check Python

Run:

```bash
python3 --version
```

If it reports Python 3.12, continue to step 3. If it reports another version or
the command is missing, complete step 2 first.

### 2. Obtain Python 3.12 when it is missing

Use a Python 3.12 package supplied by your operating system when one is
available. If installing or replacing the system Python is undesirable, use
Conda to provide the interpreter without changing the operating system Python.

Check for Conda:

```bash
conda --version
```

If Conda is missing, install
[Miniforge](https://github.com/conda-forge/miniforge) from its
[official releases](https://github.com/conda-forge/miniforge/releases):

1. Select the installer for your operating system and CPU architecture.
2. Verify its published checksum when available.
3. Run the installer and allow it to initialize your shell.
4. Close and reopen the terminal.
5. Run `conda --version` again.

WSL users must use the Linux installer inside WSL. Do not use the Windows
installer for a WSL development environment.

Create and activate a small environment that supplies Python 3.12:

```bash
conda create --name webann-bootstrap python=3.12
conda activate webann-bootstrap
python3 --version
```

The final command must report Python 3.12. If `conda activate` is unavailable,
run `conda init bash`, close the terminal, reopen it, and activate the
environment again.

The Conda environment supplies the interpreter. It is not the project's package
environment.

### 3. Create the project tooling environment

From the student repository, choose the command matching your situation:

```bash
# python3 already reports Python 3.12
make bootstrap

# OR a separate python3.12 command exists
make PYTHON=python3.12 bootstrap

# OR webann-bootstrap is currently activated
make bootstrap
```

`PYTHON=...` selects an existing executable. It never installs Python. Check a
candidate command before passing it to Make:

```bash
python3.12 --version
```

Bootstrap verifies Python 3.12, creates `.venv`, and installs the pinned
development dependencies into that repository-local environment. Make uses
`.venv/bin/...` directly, so you do not need to activate `.venv`.

If Conda supplied the interpreter, keep `webann-bootstrap` installed because
the virtual environment may refer to it. You only need to activate Conda again
when recreating `.venv`.

### 4. Install the Git hook

```bash
make hooks
```

This configures the current clone so `git commit` runs the project quality gate.
The hook is local Git metadata; teammates install it in their own clones.

### 5. Run the quality gate

```bash
make check
```

Run this before pushing. CI runs the same command on every pull request.

## Daily commands

```bash
make help         # list supported tasks
make check        # run all current checks
make validate     # run repository-policy checks only
make shell-check  # parse shell scripts without executing them
```

## Recover from a `.venv` created with the wrong Python

Check which Python created it:

```bash
.venv/bin/python --version
```

If it is not Python 3.12, first make Python 3.12 available using the setup above.
Then move the incorrect environment aside and recreate it:

```bash
mv .venv .venv-python-old
make bootstrap
make hooks
make check
```

If you activated Conda to obtain Python 3.12, keep it active while running
`make bootstrap`. Both `.venv` and `.venv-python-old` match the `.venv*/`
gitignore rule. Delete the backup only after the new environment works.

## Diagnose common errors

### `Python 3.12 is required, but 3.8... is active`

The system `python3` is too old. Install Python 3.12 or activate
`webann-bootstrap`, verify `python3 --version`, and rerun `make bootstrap`.

### `Python command not found: python3.12`

`PYTHON=python3.12` was used without an installed `python3.12` executable. That
Make variable cannot install Python. Use the Conda path above or install the
command before selecting it.

### Pip lists pre-commit only up to an older release

The virtual environment was created by an unsupported Python version. Do not
downgrade the pinned dependency. Recreate `.venv` with Python 3.12.

### `conda: command not found` after installation

Open a new terminal. If it remains unavailable, use the installed Conda
executable to run `conda init bash`, then restart the terminal. Consult the
Miniforge installation instructions for the installation-specific path.

### A commit hook fails

Run `make check`, correct the reported problem, stage the correction, and commit
again. A hook provides early feedback; CI remains the shared enforcement gate.

