from pathlib import Path

root = Path(__file__).parent.parent


def save_output(fname, data, *, encoding='utf-8', verbose=True):
    output = root.joinpath("output").resolve(strict=True)
    file = output / fname
    if verbose:
        print(f"Updating {fname} ...")
    file.write_text(data, encoding=encoding)
