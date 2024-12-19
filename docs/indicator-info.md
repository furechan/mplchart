# Indicator info meta-data


## Model

Info attributes are stored as dictionary items in the `info` attribute of an indicator when available, or else as regular attributes of the indicator. 

Most metadata attributes are treated as read-only except for `default_pane` which can be modifed by some primitives/modifiers ...

>QUESTION
Should we split main attributes like `same_scale`, `default_pane` from the other optional read-only attibutes ?

>QUESTION
Should we use a `force_target` attribute to override `default_pane`. The main logic is in the `Chart.get_axes` method.


## Retrieve metadata with `get_info`

```python
from mplchart.utils import get_info

default_pane = get_info(indicator, 'default_pane')
```

## Known attributes

```python
same_scale: bool        # wether the output uses same scale as input
defaul_pane: str        # wich pane to use for a new scale
overbought: float       # overbought level
oversold: float         # oversold level
yticks: tuple           # force major ticks
```

