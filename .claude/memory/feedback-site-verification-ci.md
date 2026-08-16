---
name: feedback-site-verification-ci
description: search-engine verification lives once at the furechan.github.io origin; project repos carry no verification files at all
metadata:
  type: feedback
---

Project repos carry **no** search-engine verification files — not committed under `docs/`, not injected by the pages workflow. Verification is done once at the origin, in the `furechan/furechan.github.io` user-site repo, which serves `google3e5afa36401ddb09.html` and `BingSiteAuth.xml` at the site root.

**Why:** on 2026-08-16 the user added `furechan.github.io` as a single property in both Google Search Console and Bing Webmaster Tools, and deleted the per-project `mintalib` and `mplchart` properties. Both engines treat an owner of a parent URL-prefix property as an owner of every path under that origin, so `https://furechan.github.io/mplchart/` inherits ownership and a project-local token verifies nothing. The tokens are account-scoped, so the origin copies are the same files the projects used to serve.

This replaces the earlier CI-injection convention (2026-07-25 to 2026-08-16), where a `run` step in `pages.yml` wrote the google file into the build output. That step and `docs/BingSiteAuth.xml` were removed from mplchart on 2026-08-16.

**How to apply:** do not add verification files or CI injection steps to project repos, and remove them if found. The one thing that must not disappear is the pair of files at the origin root — both engines recheck periodically and un-verify the whole origin if they 404. Sitemaps are separate from verification: a project sitemap (`https://furechan.github.io/<project>/sitemap.xml`) is submitted under the origin property.

Related convention: the workflow is named `pages.yml` in both projects — it publishes the project *website* (docs + articles, eventually blog-like content), so it's named for the site, not "docs".
