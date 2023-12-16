""" mplchart stylesheets (experimental) """

import re
import warnings
import configparser

import matplotlib.colors as mcolors

from pathlib import Path

DEFAULT_STYLE = 'defaults'
STYLES_FOLDER = Path(__file__).joinpath("../styles")


def get_stylesheet(name):
    return StyleSheet(name)


class Cycler:
    """ Trivial Property Cycler """

    def __init__(self, items):
        if isinstance(items, str):
            items = re.split(r",\s+", items)

        if not len(items):
            raise ValueError("Not a valid list")

        self.items = items
        self.size = len(items)
        self.count = 0

    def __next__(self):
        pos = self.count % self.size
        self.count += 1
        return self.items[pos]


class StyleSheet:
    """ Stylesheet """

    @staticmethod
    def get_inifile(name, strict=True):
        file = STYLES_FOLDER.joinpath(f"mplchart-{name}.ini").resolve(strict=strict)
        if file.exists:
            return file

    @classmethod
    def load_config(cls, style=None):
        config = configparser.ConfigParser()

        files = list()

        inifile = cls.get_inifile(DEFAULT_STYLE)
        files.append(inifile)

        if style is not None:
            inifile = cls.get_inifile(style)
            files.append(inifile)

        res = config.read(files)
        if len(res) < len(files):
            warnings.warn("Error loading configuration files ...")

        return config

    def __init__(self, style=None):
        config = self.load_config(style)

        self.config = config
        self.cached = dict()

    def reset(self):
        self.cached.clear()

    def get_settings(self, key: str, **kwargs):
        result = dict()
        for section, fallback in kwargs.items():
            value = self.get_setting(key, section, fallback=fallback)
            result[section] = value
        return result

    def get_setting(self, key: str, section: str, fallback=None):
        key = key.lower()

        if self.config.has_section(section):
            data = self.config[section]
        else:
            return fallback

        cycle_values = (section in ['color'])
        result = fallback
        found = set()

        while key in data:
            # check for recursion
            if key in found:
                return fallback
            else:
                found.add(key)

            result = data.get(key)

            if cycle_values and "," in result:
                ckey = section + ":" + key
                if ckey in self.cached:
                    cycler = self.cached.get(ckey)
                else:
                    cycler = self.cached[ckey] = Cycler(result)
                result = next(cycler)

            key = result

        if found:
            if section == 'color' and not mcolors.is_color_like(result):
                return fallback

            if section in ['width', 'linewidth', 'alpha']:
                result = float(result)

        return result
