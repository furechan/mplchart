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


def save_output(fname, data, *, encoding='utf-8', verbose=True):
    output = root.joinpath("output").resolve(strict=True)
    file = output / fname
    if verbose:
        print(f"Updating {fname} ...")
    file.write_text(data, encoding=encoding)
