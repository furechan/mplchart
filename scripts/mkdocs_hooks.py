"""mkdocs hooks — publish the markdown sources alongside the rendered HTML.

llms.txt points at the markdown rather than the HTML, and agents that expand an
llms.txt commonly fetch same-origin links only, so the markdown has to be served
from the site itself. With use_directory_urls a page renders to <stem>/index.html,
which leaves <stem>.md free for the source next to it.
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
