---
name: feedback-docs-title-style
description: Docs titles/nav use sentence case; brand names keep canonical casing (mplchart/mplfinance/pandas lowercase, Polars/TA-Lib/Python capitalized)
metadata:
  type: feedback
---

Docs page titles and nav entries use sentence case ("How indicators work", "Plotting TA-Lib indicators"), not Title Case. Adopted 2026-07-27 across all notebook H1s, md H1s, and mkdocs.yml labels.

**Why:** modern tech-docs convention (Google/Microsoft style guides, pandas docs); coexists cleanly with lowercase brand names — Title Case made "mplfinance vs mplchart" look like an outlier.

**How to apply:** new titles capitalize the first word only, plus brand canonical casing: mplchart, mplfinance, pandas always lowercase (pandas even in prose per its own branding); Polars, TA-Lib, Python, Matplotlib capitalized in prose (polars/matplotlib lowercase as package names in code context). Prose rule: pandas/polars lowercase mid-sentence, capitalized sentence-initial. For notebooks the H1 is the nav label ([[project-mkdocs-notebook-nav-titles]]) — keep mkdocs.yml labels aligned with H1s.
