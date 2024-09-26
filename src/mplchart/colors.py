
from matplotlib import pyplot as plt
from matplotlib import colors as mcolors


def default_edgecolor():
    """default edgecolor to use instead of black"""
    facecolor = plt.rcParams["axes.facecolor"]

    edgecolor = plt.rcParams["patch.edgecolor"]
    if edgecolor != facecolor:
        return edgecolor

    return "black"


def closest_color(color, color_cycle=None):
    """closest color in the props cycle"""
    if color_cycle is None:
        prop_cycle = plt.rcParams["axes.prop_cycle"]
        color_cycle = prop_cycle.by_key()["color"]
        
    def distance(c1, c2):
        v1 = mcolors.to_rgb(c1)
        v2 = mcolors.to_rgb(c2)
        return sum((a - b) ** 2 for a, b in zip(v1, v2))

    dist = [distance(color, c) for c in color_cycle]
    argmin = min(range(len(dist)), key=dist.__getitem__)
    return f"C{argmin}"
