# GitHub branch and environment protection

These settings live in GitHub rather than in the repository. An owner should
configure them after the **Repository validation** check first appears on the
Lesson 1 pull request and before that pull request is merged. The production CD
skeleton can be tested after Lesson 1 is merged because manually dispatched
workflows must exist on `main`.

## Protect `main` with a branch ruleset

Before adding protection, verify that the local branch is `main`:

```bash
git branch --show-current
```

If the output is `master`, first determine whether the repository has a commit:

```bash
git rev-parse --verify HEAD
```

For an empty repository where that command fails, rename the unborn branch:

```bash
git symbolic-ref HEAD refs/heads/main
git commit --allow-empty -m "Initialize repository"
git push -u origin main
```

For a repository where the command prints a commit SHA, rename and publish the
existing branch:

```bash
git branch -m main
git push -u origin main
```

Select `main` as the default branch in GitHub. Remove the old remote `master`
branch only after confirming that it contains no work that needs to be
preserved. This course uses `main` exclusively.

GitHub offers both **Rulesets** and **Classic branch protection rules**. Use a
**branch ruleset** for this course. Rulesets are GitHub's newer protection
model, are visible to repository readers, and allow multiple rulesets to apply
to the same branch. Classic protection allows only one applicable classic rule
at a time.

The message **Classic branch protections have not been configured** does not
mean an active ruleset is missing or invalid. It reports only that no rule was
created with the older classic interface.

### Create the recommended ruleset

1. Open **Settings → Rules → Rulesets**.
2. Select **New ruleset → New branch ruleset**. Do not choose a tag ruleset or
   push ruleset.
3. Name it `Protect main`.
4. Set **Enforcement status** to **Active**. `Evaluate` observes violations but
   does not block them, and `Disabled` enforces nothing.
5. Leave the bypass list empty for the normal course workflow. If an instructor
   needs emergency access, add it explicitly and document why.
6. Under **Target branches**, select **Include default branch**. Because the
   repository default was verified above, this targets `main`.
7. Enable **Restrict deletions**.
8. Enable **Block force pushes**.
9. Enable **Require a pull request before merging**, then configure:
   - required approvals: `1` when an instructor or peer reviewer has write
     access; use `0` only for solo study where no independent reviewer is
     available;
   - dismiss stale pull request approvals when new commits are pushed;
   - require conversation resolution before merging.
10. Look for **Repository validation** under **Require status checks to pass**.
    If it is available, add it and require the branch to be up to date before
    merging. If it is not available yet, leave **Require status checks to
    pass** disabled; GitHub will not save this rule with an empty check list.
11. Review the target and rules carefully, then select **Create**.

### Add the required status check after its first run

GitHub offers only checks that it has already observed in the repository. On a
new repository, **Repository validation** does not exist until the CI workflow
runs for the first time.

If the check was unavailable while creating the ruleset:

1. Save the active ruleset with the pull-request, approval, deletion, and
   force-push protections, but with **Require status checks to pass** disabled.
2. Push `.github/workflows/ci.yml` on
   `lesson/01-ci-cd-foundation` and open a draft pull request targeting `main`.
3. Open the pull request's **Checks** section and wait for
   **Repository validation** to finish. A failed run is sufficient for GitHub
   to learn the check's name.
4. Return to **Settings → Rules → Rulesets → Protect main** and edit the
   ruleset.
5. Enable **Require status checks to pass**.
6. Select **Add checks**, search for `Repository validation`, and select it.
   GitHub may display it as **CI / Repository validation** while showing the
   workflow and job together.
7. Enable the option requiring the branch to be up to date before merging.
8. Save the ruleset, then return to the pull request and confirm GitHub lists
   the check as required.

Do not enter an unrelated check merely to satisfy the form. The required check
must be the job defined by this repository's `ci.yml` workflow.

Do not enable **Restrict updates** for this lesson. That rule permits only
bypass actors to update `main` and can prevent an ordinary reviewed pull request
from being merged.

### Satisfy the required review

GitHub does not let a pull-request author approve their own work. When required
approvals is `1`, the approval must come from a different account that has
write access to the repository.

For an instructor-led course:

1. Open **Settings → Collaborators** (or **Collaborators and teams**).
2. Invite the instructor or assigned peer reviewer with **Write** access.
3. Wait for the invitation to be accepted.
4. Have that reviewer open the student's pull request, review the changes, and
   submit **Approve**.
5. If the student pushes another commit and stale approvals are dismissed, ask
   the reviewer to approve the new revision.

An approval from an account with read-only access does not satisfy this rule.
The pull-request author also cannot satisfy it using their own approval.

For a student working completely alone, edit the ruleset and set required
approvals to `0`, while keeping **Require a pull request before merging**,
required CI checks, conversation resolution, deletion protection, and
force-push protection enabled. Record `solo study—no independent reviewer` in
the pull request. Do not add yourself to a broad bypass list merely to get past
the review rule; bypassing would weaken the other protections as well.

The resulting active ruleset should enforce:

- require a pull request before merging;
- require one independent approval in instructor-led use, or zero approvals in
  documented solo-study use;
- dismiss stale approvals when new commits are pushed;
- require status checks before merging;
- require the **Repository validation** check;
- require branches to be up to date before merging;
- require conversation resolution before merging;
- do not allow force pushes;
- do not allow deletions;
- apply to repository administrators unless they were deliberately added to
  the bypass list.

Anyone with read access can inspect active repository rulesets, which helps a
student understand why GitHub accepted or rejected a change. GitHub also allows
multiple rulesets to apply simultaneously; satisfying one does not cancel the
others. See GitHub's documentation on
[rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
and [available rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).

### Classic fallback

Use **Settings → Branches → Add classic branch protection rule** only when a
branch ruleset is unavailable for the repository or account. Set the branch
pattern to `main` and enable the equivalent pull-request, approval, status-check,
up-to-date, conversation-resolution, force-push, and deletion protections listed
above. Do not configure both systems merely to remove GitHub's informational
message; overlapping rules are harder for a beginner to diagnose.

Feature availability depends on repository visibility and GitHub plan. GitHub
currently makes rulesets available for public repositories on GitHub Free, and
for public and private repositories on GitHub Pro, Team, and Enterprise Cloud.
If an account cannot enforce the recommended rules, record that limitation in
the Lesson 1 pull request and use the strongest available classic protection.

## Protect the production environment

In **Settings → Environments**, create `production` and configure:

- at least one required reviewer who is not the person requesting deployment;
- deployment branches restricted to the protected `main` branch or release
  tags;
- environment-scoped secrets only when a later lesson needs them.

Do not add deployment secrets during Lesson 1. The current CD workflow stops
after its approval placeholder and performs no external write.

## Verify the policy

1. Open a pull request that removes a required repository file and confirm the
   **Repository validation** check fails.
2. Restore the file and confirm the check passes.
3. Confirm GitHub still blocks merging until review and required checks finish.
4. Manually run **CD skeleton** with a commit SHA that passed CI.
5. Confirm the production job waits for environment approval and then only
   prints the placeholder message.

Repository settings can differ by GitHub plan and organization policy. Record
any unavailable control in the Lesson 1 pull request rather than silently
skipping it.
