""" Utilities for the examples folder """

from pathlib import Path

folder = Path(__file__).parent
output = folder.joinpath("../output").resolve(strict=True)


def save_image(fname, data, *, encoding='utf-8', verbose=True):
    file = output / fname
    if verbose:
        print(f"Updating {fname} ...")
    file.write_text(data, encoding=encoding)
