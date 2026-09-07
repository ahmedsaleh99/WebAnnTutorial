# Student repository workflow

## Two repositories, two purposes

The course uses a clear separation:

| Repository | Owner | Purpose |
| --- | --- | --- |
| WebAnnTutorial | Instructor/course | Lessons, acceptance criteria, and the evolving gold-standard implementation |
| Student repository | Student | The application built from an empty repository through the student's own pull requests |

Each student creates a new empty repository. They should not fork the tutorial
repository because a fork would begin with the reference history and completed
files instead of documenting what the student built.

Suggested student repository names include `web-annotation-course` or
`engann-from-scratch`.

## One-time student setup

Create a completely empty repository on GitHub. Do not initialize it with a
README, license, or `.gitignore`; Lesson 1 teaches how and why to add them.

Clone the empty student repository and create its `main` branch:

```bash
git clone git@github.com:YOUR-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
git symbolic-ref HEAD refs/heads/main
```

Verify that the branch is named `main`:

```bash
git branch --show-current
```

The output must be `main`. In a completely empty repository, `HEAD` initially
points to an **unborn branch**: Git can print `master` even though
`refs/heads/master` does not exist yet. That is why the setup uses
`git symbolic-ref` instead of `git branch -m`.

If the repository already has at least one commit and its branch is `master`,
rename the real branch instead:

```bash
git branch -m main
```

You can distinguish the two cases with:

```bash
git rev-parse --verify HEAD
```

If it reports that `HEAD` is not a valid revision, the repository has no
commits; use `git symbolic-ref HEAD refs/heads/main`. If it prints a commit SHA,
use `git branch -m main`.

Configure Git to use `main` automatically for repositories you create in the
future:

```bash
git config --global init.defaultBranch main
```

After the first commit, publish `main` and set its upstream:

```bash
git push -u origin main
```

This empty bootstrap commit is the only direct commit to `main` in the course.
It contains no application or lesson implementation and exists only to create a
base branch for the first pull request. All subsequent work, including the rest
of Lesson 1, must arrive through a lesson branch and pull request.

On GitHub, open the repository's default-branch setting and confirm that `main`
is selected. This course uses only `main`; do not create or retain a `master`
branch.

Keep the tutorial open separately in a browser, or clone it into a different
directory for reading. Do not add the tutorial repository as a merge source for
the student's application.

## Workflow for every lesson

1. Confirm the previous lesson is merged and the `main` branch is current.
2. Read the lesson outcome, concepts, deliverables, and acceptance criteria.
3. Create the lesson branch in the student repository.
4. Implement the requirements using red-green-refactor.
5. Run the shared local quality command and review the diff.
6. Push the student branch and open a pull request in the student repository.
7. Wait for CI and perform a self-review before reading the gold standard.
8. Compare with the lesson's gold-standard implementation.
9. Record similarities, justified differences, and improvements in the PR.
10. Make any warranted changes, obtain review, and merge.

The student's pull request history is part of the course deliverable. It should
show how the application grew, not only the final files.

Lesson 1 is a special case: GitHub discovers pull-request templates only on
`main`, while Lesson 1 is the change that first adds the template. Copy
`.github/PULL_REQUEST_TEMPLATE.md` manually into the Lesson 1 PR description.
After Lesson 1 is merged, GitHub inserts it automatically in future PRs.

## What "the same repository content" means

At the end, the student implementation should match the reference in:

- user-visible capabilities;
- API contracts and authorization rules;
- important domain invariants;
- service architecture and supported technology stack;
- automated tests and CI/CD quality gates;
- essential source, configuration, documentation, and operational files.

Generated files, local data, secrets, media, dependency directories, commit
SHAs, formatting-only choices, and other nonessential details do not need to be
identical. A student may use a different implementation when it passes the same
acceptance criteria and documents the tradeoff.

## Gold-standard checkpoints

Each completed lesson in WebAnnTutorial represents the expected state after
that lesson. The lesson explains the reference files and decisions. Course
releases should also tag these states using names such as `lesson-01`,
`lesson-02`, and so on, allowing a student to inspect one checkpoint without
jumping directly to later solutions.

The comparison happens only after the student's first implementation attempt.
It is a review tool, not starter code.

## Instructor review

For each student pull request, check:

- lesson acceptance criteria and required CI checks;
- evidence that the intended failing test/check existed first;
- understanding shown in the PR explanation and review discussion;
- security, data handling, and authorization implications;
- whether differences from the gold standard are intentional and sound;
- whether `main` remains a working checkpoint for the next lesson.
