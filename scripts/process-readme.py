"""
Script to translate README.md relative urls
Creates output/README.md for usage with pypi
Requires tomli !
"""

import re
import tomli
import argparse
import posixpath

from pathlib import Path

ROOTDIR = Path(__file__).parent.parent


def jquery(data: dict, item: str, default=None):
    result = data

    for i in item.split("."):
        result = result.get(i, None)
        if result is None:
            return default

    return result


def get_project_url():
    """extract project url from project configuration"""

    pyproject = ROOTDIR.joinpath("pyproject.toml")

    if not pyproject.exists():
        raise FileNotFoundError("pyproject.toml")

    config = tomli.loads(pyproject.read_text())
    return jquery(config, "project.urls.homepage")


def process_readme(file, project_url, branch="main", verbose=False):
    """translate relative urls to full urls"""

    def replace(m):
        exclam, alt, url = m.groups()
        ftype = "raw" if exclam else "blob"
        if url.startswith("/"):
            url = posixpath.join(project_url, ftype, branch, url[1:])
            text = f"{exclam}[{alt}]({url})"
            if verbose:
                print("mapping", m.group(0), "->", text)
        else:
            text = m.group(0)
        return text

    source = file.read_text()

    result = re.sub(r"(?x)(\!?)\[([^]]*)\]\(([^)]+)\)", replace, source)

    return result


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    parser.set_defaults(verbose=False)

    options = parser.parse_args()

    readme = ROOTDIR.joinpath("README.md").resolve(strict=True)
    outfile = ROOTDIR.joinpath("output/README.md").resolve()

    project_url = get_project_url()

    print("project_url", project_url)

    textout = process_readme(readme, project_url, verbose=options.verbose)

    print(f"Updating {outfile} ...")
    outfile.write_text(textout)


if __name__ == "__main__":
    main()
