# Rules for AI Assistants Working in This Repo

## Never run the test suite yourself — give the user the command

Always hand over the exact command and let the user run it themselves. Do not run the test suite proactively, and do not re-run it after every small edit to "verify" — that habit is exactly what this rule exists to stop.

Backend:

    cd backend && .venv/Scripts/python -m pytest -q

If a frontend test suite is added later, the same rule applies to it — give the command, don't run it.

**Why:** the user wants full control over when tests run and does not want to wait on an AI running them repeatedly. This is a standing project rule, not a one-off preference for a single session.

## Committing

- **Only commit when the user explicitly asks.** Don't commit proactively just because a change is finished — finishing the change and committing it are two separate steps, and only the user decides when the second one happens.
- **Only push when the user explicitly asks, separately from a commit request.** Being told to commit is not being told to push — confirm before anything leaves the local repo.
- **Never mention Claude or any AI in a commit** — no `Co-Authored-By: Claude` (or similar) trailer, no mention anywhere in the message. Commits are authored and attributed to the user alone; the git author identity should already reflect that via the user's own configured `user.name`/`user.email`.
- If asked to push a branch whose existing commits already contain an AI co-author trailer and that branch has never been pushed before, it's fine to clean up those messages first (verify with `git diff <old> <new> --stat` that only the messages changed, never the content) rather than pushing them as-is. Don't rewrite history on a branch that's already been pushed/shared without being asked.
