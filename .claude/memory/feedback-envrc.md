---
name: Commit .envrc files; don't gitignore them
description: .envrc is a project-metadata pointer file and should be committed. Secrets live in separately-gitignored files that it sources.
type: feedback
---

`.envrc` files (direnv configs) should be **committed**, not gitignored.

**Why:** The user's convention is that `.envrc` just declares *how* to load the env — e.g. `source pypi.env` — and the actual secrets live in a separate file (`pypi.env`) that is itself gitignored. The `.envrc` itself contains no secrets, just the project-local shell glue (PATH tweaks, Python cache dir, sourcing commands). Committing it documents the project's env setup for other devs.

**How to apply:** Don't reflexively propose gitignoring `.envrc` because it looks "env-like." Open it and read the content — if it only contains `source foo.env` style references or `export` statements pointing at paths/non-secret values, it's safe (and expected) to commit. Apply the same judgment to any file: look at the content, not the name.
