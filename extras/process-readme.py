"""
Script to translate README.md relative urls
Creates output/README.md for usage with pypi
Requires toml, jmespath !
"""


import re
import toml
import argparse
import jmespath
import posixpath

import configparser

from pathlib import Path

root = Path(__file__).parent.parent


def get_project_url():
    """ extract project url from project configuration """

    pyproject = root.joinpath("pyproject.toml")
    setupcfg = root.joinpath("setup.cfg")
    setup = root.joinpath("setup.py")

    if pyproject.exists():
        config = toml.load(pyproject)
        return jmespath.search("project.urls.homepage", config)

    if setupcfg.exists():
        config = configparser.ConfigParser()
        config.read(setupcfg)
        return config.get('metadata', 'url')

    if setup.exists():
        contents = setup.read_text()
        match = re.search(r"(?xm) ^ \s* url \s* = \s* ([\"']) ([^\"']+) \1 \s* $", contents)
        if match:
            url = match.group(2)
            return url

    raise ValueError("Cound not extract url!")


def process_readme(file, project_url, branch="main", verbose=False):
    """ translate relative urls to full urls """

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

    readme = root.joinpath("README.md").resolve(strict=True)
    outfile = root.joinpath("output/README.md").resolve()

    project_url = get_project_url()

    print("project_url", project_url)

    textout = process_readme(readme, project_url, verbose=options.verbose)

    print(f"Updating {outfile} ...")
    outfile.write_text(textout)


if __name__ == "__main__":
    main()
