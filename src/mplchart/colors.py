"""Mplchart color utils"""

import colorsys

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def scale_lightness(color, amount):
    """Scale a color's HLS lightness by ``amount`` (clamped to [0, 1]), as hex.

    ``amount < 1`` darkens, ``> 1`` lightens — the same adjustment as
    mplfinance's ``_adjust_color_brightness``.
    """
    hue, lightness, saturation = colorsys.rgb_to_hls(*mcolors.to_rgb(color))
    rgb = colorsys.hls_to_rgb(hue, max(0.0, min(1.0, lightness * amount)), saturation)
    return mcolors.to_hex(rgb)


def normalize_color(color):
    """Normalize any matplotlib color spec (name, hex, RGB/RGBA tuple) to a hex string.

    The styler guarantees only concrete hex strings leave color resolution —
    hex is scalar-safe for ``np.where`` consumers (tuples are not) and
    ``to_rgba`` validates the spec, failing fast on garbage. Alpha is kept
    (``#rrggbbaa``) only when not fully opaque.
    """
    rgba = mcolors.to_rgba(color)
    return mcolors.to_hex(rgba, keep_alpha=rgba[3] != 1.0)


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
    argmin = min(range(len(dist)), key=lambda i: dist[i])
    # normalize to hex — cycle entries may be RGB tuples (matplotlib >= 3.11)
    # and callers use the result as a scalar (e.g. np.where)
    return mcolors.to_hex(color_cycle[argmin])
