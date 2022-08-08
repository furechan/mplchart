from functools import lru_cache

import configparser

from pathlib import Path

here = Path(__file__).parent
root = Path(__file__).parent.parent


@lru_cache()
def get_config():
    setupcfg = root.joinpath("setup.cfg").resolve(strict=True)
    config = configparser.ConfigParser()
    config.read(setupcfg)
    return config
