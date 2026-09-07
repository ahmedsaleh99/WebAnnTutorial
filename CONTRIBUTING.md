# Contributing to the tutorial

This repository is learned and developed through small, reviewable pull
requests. Do not commit lesson work directly to `main`.

## Lesson workflow

1. Update your local `main` branch.
2. Create the lesson branch shown in that lesson's guide.
3. Read the acceptance criteria and write a failing test or check before
   implementation when the lesson adds behavior.
4. Run `make check` and confirm the relevant test or check fails for the
   expected reason.
5. Implement only the lesson scope, then rerun `make check`.
6. Refactor, review the diff, commit it, and push the branch.
7. Open a pull request and complete every section of the template.
8. Merge only after required checks pass and review is complete.

For the first Lesson 1 pull request, copy
`.github/PULL_REQUEST_TEMPLATE.md` into the description manually because GitHub
cannot discover it until it has been merged into `main`. Later pull requests
receive the template automatically.

`make check` is the public quality command. It currently runs repository policy
and shell syntax checks; later lessons extend it with backend, frontend, and
container checks.

## Branch and commit naming

- Lesson branches: `lesson/NN-short-description`
- Fix branches: `fix/short-description`
- Documentation branches: `docs/short-description`
- Commits: short, imperative summaries such as `Add repository validation`

Keep commits coherent. A reviewer should be able to understand why each commit
exists without reconstructing unrelated work.

## Pull request expectations

- Keep the change within one lesson or one clearly described fix.
- Link the relevant lesson and copy its acceptance criteria into the PR.
- Show the red and green commands/output for behavioral work.
- Add or update documentation alongside the behavior it describes.
- Never add real secrets, credentials, private research data, or large media.
- Request review only after the local check passes.

## Gold-standard solutions

Attempt the lesson before reading its gold-standard section. After your pull
request passes, compare the two implementations and write a short reflection:

- What choices were the same?
- What was different, and why?
- What will you change before requesting final review?

The gold standard is a reference implementation, not the only valid solution.
A different implementation is acceptable when it meets the same observable
criteria and its tradeoffs are explained.
