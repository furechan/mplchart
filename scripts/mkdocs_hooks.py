"""mkdocs hooks — publish the markdown sources alongside the rendered HTML.

The docs are navigable as markdown on their own: index.md links the reference
pages, which link each other, and agents that follow those links stay on one
origin. That only works if the sources are served next to the HTML — with
use_directory_urls a page renders to <stem>/index.html, which leaves <stem>.md
free for the source beside it, the URL the .md convention already predicts.
"""

import shutil
from pathlib import Path

_sources: list[str] = []


def on_files(files, config, **kwargs):
    # documentation_pages() is already filtered by exclude_docs / not_in_nav
    _sources[:] = [f.src_uri for f in files.documentation_pages() if f.src_uri.endswith(".md")]
    return files


def on_post_build(config, **kwargs):
    docs_dir, site_dir = Path(config["docs_dir"]), Path(config["site_dir"])
    for src_uri in _sources:
        dest = site_dir / src_uri
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(docs_dir / src_uri, dest)
    print(f"INFO    -  Published {len(_sources)} markdown sources alongside the HTML")
