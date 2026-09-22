---
name: project-material-mkdocs2-banner
description: Red "Warning from the Material for MkDocs team" banner in mkdocs builds is expected noise, not an error
metadata:
  type: project
---

Every `mkdocs build`/`serve` with Material ≥9.6.x prints an unconditional red banner on stderr: "⚠ Warning from the Material for MkDocs team" about MkDocs 2.0 breaking changes (their PSA in the Material-vs-MkDocs-2.0 split; the Material team is building Zensical as their successor). It is not caused by anything in this repo, does not affect the exit code or output, and should be ignored when reading build logs. Opt-out if ever needed: set `NO_MKDOCS_2_WARNING=true` (checked in `material/templates/__init__.py`). Decided (July 2026) not to suppress it in `.envrc` or CI — not worth the config line.
