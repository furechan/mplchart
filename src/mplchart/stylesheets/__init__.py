""" mplchart stlyesheets (experimental) """

from importlib import resources


def get_inifile(name):
    fname = f"mplchart-{name}.ini"
    return resources.files(__name__).joinpath(fname)
