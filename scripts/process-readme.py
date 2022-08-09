"""
script to translate README.md local urls
creates output/README.md for usage with pypi
"""

import re
import argparse
import posixpath

import configparser

from pathlib import Path

from functools import lru_cache

root = Path(__file__).parent.parent


@lru_cache()
def get_config():
    setupcfg = root.joinpath("setup.cfg").resolve(strict=True)
    config = configparser.ConfigParser()
    config.read(setupcfg)
    return config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    parser.set_defaults(verbose=True)

    options = parser.parse_args()
    verbose = options.verbose

    readme = root.joinpath("README.md").resolve(strict=True)
    output = root.joinpath("output").resolve(strict=True)

    config = get_config()
    project_url = config.get('metadata', 'url')

    branch = "main"

    def replace(m):
        exclam, alt, url = m.groups()
        ftype = "raw" if exclam else "blob"
        if url.startswith("/"):
            url = posixpath.join(project_url, ftype, branch, url[1:])
            result = f"{exclam}[{alt}]({url})"
            if verbose:
                print("mapping", m.group(0), "->", result)
        else:
            result = m.group(0)
        return result

    text = readme.read_text()

    textout = re.sub(r"(?x)(\!?)\[([^]]*)\]\(([^)]+)\)", replace, text)

    outfile = output.joinpath("README.md")

    print(f"Updating {outfile} ...")
    outfile.write_text(textout)


if __name__ == "__main__":
    main()
