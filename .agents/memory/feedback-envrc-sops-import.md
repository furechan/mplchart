---
name: feedback-envrc-sops-import
description: This project's .envrc deliberately calls sops_import (not load_env) — an intentional opt-in to the sops store
metadata:
  type: feedback
---

The `.envrc` uses `sops_import pypi` directly instead of `load_env pypi`, against the dotfiles doctrine that call sites go through `load_env`.

**Why:** Per the user, `load_env` is the abstraction for the across-the-board backend flip; `sops_import` means "choose sops now" for this project. The sops pipeline is self-sufficient, so opting in per-project is fine.

**How to apply:** Don't "fix" the `.envrc` back to `load_env`, and don't flag it as a doctrine violation. Related: [[feedback-envrc]].
