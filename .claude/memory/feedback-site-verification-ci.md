---
name: feedback-site-verification-ci
description: google site verification files are injected at CI time in the pages workflow, never committed to docs sources
metadata:
  type: feedback
---

Google Search Console verification files (`google<hex>.html`) are written into the built site by a `run` step in the pages workflow — not committed under `docs/`.

**Why:** the user set this convention in mintalib (2026-07-25) and mplchart follows it: the token is noise in the docs sources, and the file only needs to exist in the deployed site. The token is *account*-scoped, not site-scoped, so the same file (`google3e5afa36401ddb09.html`) verifies every site the account claims.

**How to apply:** after the site build step, before the pages artifact upload:

```yaml
- name: Add google site verification
  run: |
    echo "google-site-verification: google3e5afa36401ddb09.html" > site/google3e5afa36401ddb09.html
```

(build output dir varies per project: `site` in mplchart, `_site` in mintalib). Keep the step forever — Google rechecks the file periodically and un-verifies if it disappears.

Related convention: the workflow is named `pages.yml` in both projects — it publishes the project *website* (docs + articles, eventually blog-like content), so it's named for the site, not "docs".
