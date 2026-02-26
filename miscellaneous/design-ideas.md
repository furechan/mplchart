# Some design ideas ...

```python

# Color Scheme

color_scheme = dict(
    overbought = "~gray",
    oversold = "~gray",
    macdsignal = "~blue",
    macdhist = "~blue",
    sma = ["~red", "~green", "~blue"],
)

# Settings dictionary ???

settings = {
    "rsi.overbought": 70,
    "rsi.oversold": 30,
    "rsi.yticks": (30, 50, 70)
    "pdi.color": "green",
    "ndi.color": "red",
    "sma.style": "dashed",
    "sma.width": 1.0 
}


# Setting dataclass ???

@dataclass
class Settings:
    ovrbought : float = None
    overbough : float = None
    yticks: tuple = None


settings = dict(
    rsi = Setting(overbought=70, oversold=30, yticks=(30, 50, 70))
    adx = Setting(yticks=(20, 40))
    dmi = Setting(yticks=(20, 40))
)



# Info mapping_proxy attribute

class RSI:
    info = mapping_proxy(
        name="rsi",
        oversold=30,
        overbought=70,
        yticks=(30, 50, 70),
    )

    def __init__(self, period=14, item:str =None)
    self.period = period
    self.item = item

    def __call__(self, prices):
        ...


def RSI(period: int):
    kwargs = dict(locals(), wrap=True)
    info = dict(
        name="rsi",
        oversold=30,
        overbought=70,
        yticks=(30, 50, 70),
    )
    return FuncIndicator(calc_rsi, info=info, kwargs=kwargs)



# Info mapping_proxy attribute

class RSI:
    info = mapping_proxy(
        name="rsi",
        oversold=30,
        overbought=70,
        yticks=(30, 50, 70),
    )

    def __init__(self, period=14, item:str =None)
    self.period = period
    self.item = item

    def __call__(self, prices):
        ...



# Position Overrides

from mplchart.modifiers import Position, NewAxes, SameAxes

SMA(20) | NewAxes()
RSI(20) | SameAxes()



# Color Overrrides

SMA(50) | Color("red")                              # indicator.style_override
MACD() | Color(macdsignal="~red")                   # inddictor.color_override


# Style overrides

SMA(50) | Style("solid", color=..., width=...)      # indicator.style_override
MACD() | Styles(macd=..., macdsignal)

# Attributes overrides

ADX() | Replace(yticks=(20, 40))                     # indicator.info

# Specific Plot Primitives

SMA(50) | LinePlot(color="...")
SMA(50) | AreaPlot(color="...")
SMA(50) | BarPlot(color="...")
SMA(50) | ScatterPlot(color="...")

# Generic Plot Primitive

SMA(50) | Plot("line", color="...")
SMA(50) | Plot("area", AreaPlot(color="...")
SMA(50) | Plot("scatter", color="...")
SMA(50) | Plot("bars", color="...")



# Style dataclass ???

@dataclass
class Style:
    name: str
    color: str = None
    width: float = None
    alpha: float = None


style = Style("solid", color=..., )


# Chart setting api

chart.get_setting("rsi.color", ax, indicator, default="line)


# Chart color api

chart.get_color("rsi", ax, indicator, fallback="line")
chart.get_color("macd", ax, indicator, fallback="line")


# Chart style api

chart.get_style("macd", ax, indicator, style="solid", color=..., width=..., alpha=...)
chart.get_style("rsi", ax, indicator, style="solid", color=..., width=..., alpha=...)


```