---
name: project-mkdocs-notebook-nav-titles
description: mkdocs-jupyter overrides nav labels with the notebook H1 — to change nav text for .ipynb pages edit the H1, not mkdocs.yml
metadata:
  type: project
---

For `.ipynb` pages, mkdocs-jupyter sets the page/nav title from the notebook's first H1, silently overriding the label in `mkdocs.yml` nav. Plain `.md` pages respect the yml label as usual. Verified July 2026 against the built site (yml labels appeared zero times in the nav).

**Why:** plugin overrides page.title after nav construction.

**How to apply:** to change nav text for a notebook, edit its H1 markdown cell (then run the notebook checks per `.claude/rules/notebook-checks.md`). Keep yml labels aligned with H1s so `mkdocs.yml` stays truthful. `mkdocs-jupyter` has `ignore_h1_titles: true` if yml-label control is ever wanted. Related: [[project-examples-structure]].
