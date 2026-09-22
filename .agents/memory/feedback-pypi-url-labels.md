---
name: feedback-pypi-url-labels
description: Prefer explicit project URL labels (documentation/repository/changelog) over an ambiguous homepage link
metadata:
  type: feedback
---

In `pyproject.toml` project URLs, use only self-explanatory labels — `documentation`, `repository`, `changelog` — and omit `homepage`.

**Why:** With both a repo and a docs site, "Homepage" is ambiguous — the user assumes it's the repo when it's the only link, and can't tell what it points to when there are several. Duplicate links on the same PyPI page also add no SEO value.

**How to apply:** Don't add `urls.homepage` back when touching project metadata; each link label should say exactly what it points to.
