""" mplchart styling (experimental) """

import io
import warnings
import configparser

import matplotlib.colors as mcolors

from .stylesheets import get_inifile


def get_stylesheet(name=None):
    """ Stylesheet factory method """

    stylesheet = Stylesheet()

    if name is not None:
        inifile = get_inifile(name)
        if inifile.exists():
            stylesheet.load(inifile)
        else:
            warnings.warn(f"File {inifile.name} not found!")

    return stylesheet


class Stylesheet:
    """ Stylesheet """

    def __init__(self):
        self.config = configparser.ConfigParser()

    def load(self, path):
        """ read from pathlike """
        if path.exists():
            data = path.read_text()
            self.config.read_string(data, source=path.name)

    def dumps(self):
        buffer = io.StringIO()
        self.config.write(buffer, space_around_delimiters=True)
        return buffer.getvalue()

    def get_setting(self, key: str, section: str, fallback=None):
        result = self.config.get(section, key.lower(), fallback=fallback)

        if section == "color" and not mcolors.is_color_like(result):
            return fallback

        if section in ["width", "linewidth", "alpha"]:
            result = float(result)

        return result

    def get_settings(self, key: str, **kwargs):
        result = dict()

        for section, fallback in kwargs.items():
            value = self.get_setting(key, section, fallback=fallback)
            if value is not None:
                result[section] = value

        return result

