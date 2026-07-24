# Styles — Target API Sketch

Speculative reference (2026-07-22): target interfaces for an mplfinance-like style option. Discussion-stage — this note is the reference to steer by, not a commitment; signatures may shift. Presentation-plane feature: touches `canvas.py` and primitives, never the data plane. Companion to [canvas-view-sketch.md](canvas-view-sketch.md).

## Canonical usage

```python
chart = Chart(prices, style="nightclouds")                    # shipped style by name

chart = Chart(prices, style={                                 # ad-hoc dict, same schema
    "stylesheet": "dark_background",
    "rc": {"grid.color": "#333333"},
    "settings": {"candles.up.color": "#26a69a", "candles.dn.color": "#ef5350"},
})

from mplchart.styles import Style                             # explicit spec object
chart = Chart(prices, style=Style(rc={...}, colors={...}))
```

## Module layout

```
src/mplchart/styles/
    __init__.py      # facade: re-exports Style, Styler, resolve_style, available_styles
    style.py         # static spec: Style, resolve_style, available_styles
    styler.py        # runtime: Styler
    lib/
        __init__.py  # empty
        nightclouds.py, yahoo.py, ...   # one module per shipped style
```

Dependency arrows: `chart → canvas → styles → colors`. Nothing imports back; data plane imports none of it.

## Style (static spec)

```python
@dataclass(frozen=True)
class Style:
    name: str = ""
    rc: Mapping = field(default_factory=dict)        # rcParams overrides (validated eagerly)
    settings: Mapping = field(default_factory=dict)  # symbolic keys → value (colors and more)

def resolve_style(spec: str | Mapping | Style) -> Style: ...
    # str → import mplchart.styles.lib.<name>, take its STYLE dict
    # dict → normalize: {"stylesheet": ..., "rc": ..., "settings": ...} —
    #        stylesheet collapsed under rc via load_stylesheet, wrap in Style
    # Style → passthrough

def available_styles() -> list[str]: ...            # pkgutil.iter_modules over lib/

def get_styler(style=None, *, overrides=()) -> Styler: ...
    # single normalizer, mirrors get_view; one polymorphic style= slot on
    # Chart/Canvas, no parameter threading.
    # style: None | prebuilt Styler (passthrough — or a derived copy when
    #        mappings are given) | str | dict | Style (→ resolve_style)
    # overrides: canonical settings keys, layered over the style settings
    #            whatever their source — a prebuilt Styler included
    # (color_scheme / map_color_scheme retired 2026-07-23 — see open questions)
```

- `rc` is validated at construction by round-tripping through `mpl.RcParams` — matplotlib's 322 per-key validators are the schema; errors point at the style definition, not the first plot.
- The `stylesheet` dict key (spelling settled 2026-07-23, matching `Styler(stylesheet=)`; supersedes the draft `base_mpl_style`) is input sugar, not a field: a stock matplotlib style is itself an rc dict (`mpl.style.library[name]`); resolution collapses to `effective_rc = base ⊕ rc` (implemented in `resolve_style`).
- `settings` validation is ours: `.color` values must be color-like, a list (cycle), or a sentinel (`line`, `fill`, `~`-prefixed); other properties validate per key (registry later, consumer contract for now).

### Settings key grammar

`<role>[.<variant>].<property>` — flat dotted keys, property always explicit (the rcParams rule: `grid.color`, never bare `grid`). Variants (`up/dn/off/wick/edge`) only where a role has them; arity is positional-from-the-right. Colors are one property among others:

```
candles.up.color    candles.wick.color    candles.alpha    candles.hollow
volume.up.color     volume.ma.color       volume.alpha     volume.width
sma.color           macd.color
```

Non-color settings cover the mplfinance `marketcolors` extras (`alpha`, `hollow`, widths if ever) without a second schema — one namespace, typed at the call site. Accessors take name and facet as separate arguments (`get_setting("candles.up", "color")`); the joined dotted key is the serialization form (dicts, files), never assembled by callers.

## Style lib modules

```python
# styles/lib/nightclouds.py — pure data, zero imports
STYLE = {
    "stylesheet": "dark_background",
    "rc": {"grid.color": "#333333"},
    "settings": {
        "candles.up.color": "#26a69a",
        "candles.dn.color": "#ef5350",
        "volume.up.color": "#26a69a",
        "volume.dn.color": "#ef5350",
        "sma.color": ["#e24a33", "#348abd", "#988ed5"],   # list = per-role cycle
    },
}
```

- Uniform `STYLE` attribute; `resolve_style` imports lazily by name — the directory is the registry, adding a style is one new file.
- Modules are dict literals with no imports: no circularity with the machinery modules, and the shape maps 1:1 onto a future TOML/mplstyle serialization.
- Style names follow module-name rules (identifiers; normalize dashes in `resolve_style` if wanted).
- **Total styles** (settled 2026-07-24, supersedes the ambient-adaptivity and sheet-name-rejection decisions of 2026-07-23/24): every styler is fully specified over the factory template (`base_template()` = `rcParamsDefault` minus `STYLE_BLACKLIST` minus `ENVIRONMENT_KEYS` — `figure.dpi`/`savefig.dpi` stay ambient, dpi is session preference, not look). No ambient inheritance: charts render identically everywhere; this is mplfinance's totality without its global mutation. No implicit baseline: `DEFAULT_RC` is gone — the default look is the shipped `mplchart` style (template + `axes.grid: True` + `grid.alpha: 0.4`), resolved when `style=None`; a style that doesn't set the two grid keys renders a bare chart (documented, easy to trace). Matplotlib sheet names are accepted as styles (`style="ggplot"` = the sheet's complete look, zero mplchart opinions; lib names shadow) — the earlier confusion objection dissolved under totality, since every style now yields a complete coherent chart. Ambient `plt.style.use` no longer affects charts — pass the sheet name as the style instead.

## Styler (runtime)

Born per-Canvas from a resolved `Style` plus user overrides; owns all mutable styling state. This is today's `get_color`/`counter`/`next_*_color` cluster extracted from Canvas (the distilled remains of the old `stylemap.py`, re-homed now that the logic is growing again — `get_setting(name, facet, fallback=)` deliberately revives the deleted stylemap's `get_setting(prefix, name, default)` signature with settled semantics).

```python
class Styler:
    def __init__(self, style: Style = EMPTY, overrides: Mapping = ()):
        self.settings = {**style.settings, **dict(overrides)}   # user overrides win
        self.rcparams = dict(style.rc)
        self.cycles = WeakKeyDictionary()                        # ax → {role: color iterator}

    def get_setting(self, name, facet, *, override=None, fallback=None, extract=True): ...
        # generic lookup: override → setting → fallback (the resolve_color
        # chain, minus the color pipeline — primitives resolve non-color
        # facets in one call: get_setting("ohlc", "alpha", override=self.alpha,
        # fallback=1.0)). The role is SANITIZED to its canonical key via
        # extract_prefix ("SMA(50)" → "sma") — one lookup, a key is a key,
        # not a label (settled 2026-07-24; raw-label keys like "sma-50.color"
        # no longer consulted — styles style roles, never instances);
        # extract=False skips sanitization. The facet is never sanitized;
        # each link defers on None only (alpha=0.0 is meaningful)
    def resolve_color(self, role, ax=None, *, override=None, fallback=None): ...
        # chain: override (user color, e.g. primitive kwarg) → setting under
        # the canonical key → fallback; role is a lookup key, never a color
        # candidate. Pipeline on the winner: list → cycle per (ax, canonical
        # key) — SMA(20)/SMA(50) share the sma cursor; "~" → closest_color; "line"/"fill" → ax prop cycle.
        # Output is normalize_color-munged: only concrete HEX leaves the
        # styler (np.where-safe scalars, to_rgba-validated)
    def replace(self, *, overrides=()): ...
        # ctor also takes stylesheet= (stock style name or .mplstyle path,
        # loaded via load_stylesheet, collapsed eagerly UNDER rcparams —
        # only the flat merged dict is stored; the mplfinance shape
        # base ⊕ rc ⊕ settings as a one-liner)
        # immutable-style (dataclasses.replace): new Styler, overrides merged
        # over settings, rcparams carried, fresh cycles, self untouched
    def next_line_color(self, ax): ...      # text.color first, then ax prop cycle
    def next_fill_color(self, ax): ...
    def context(self):                      # rc_context(self.rcparams) or nullcontext()
```

Cycle semantics (stated, previously implicit): a list-valued role advances per `(pane, name-as-passed)` and persists for the chart's lifetime; fresh chart → fresh cycles. Caller contract: pass a stable role name (the indicator type, e.g. `"sma"`) if successive instances should share a cycle — a per-instance label (`"sma-50"`) gets its own cycle. Two cycling mechanisms coexist: per-role lists (superset of mplfinance's single `mavcolors` cycle) and the matplotlib prop cycle via sentinels. Non-string color values (RGB tuples) pass through resolution untouched; sentinels resolve to `None` without an ax.

## Application — invariants

- **No style state survives to draw time.** rc values bake into artists at creation inside scoped contexts; symbolic colors resolve eagerly to concrete hex inside `resolve_color` (`closest_color` already ends in `to_hex` for this reason). No global mutation observable from outside; no named-color-registry games (names resolve at *draw* time, per-draw — unusable for scoped styling).
- **rc applies only via `styler.context()` at the creation choke points** (implemented 2026-07-23): `Canvas.__init__` (figure + root axes), `Canvas.root_axes`/`get_axes` (lazy pane creation), `Chart.plot_indicator` (all primitive drawing — the single `apply_to_chart` dispatch site; `vline`/`hline` now route through it), `Canvas.add_legends`, `Canvas.show`, `Canvas.render` (draw/savefig re-read rc). `rc_context` nests harmlessly.
- **Primitives are covered by construction**: they only run when the pipeline calls them. Contract addition for [primitive-contract.md](primitive-contract.md): primitives draw synchronously inside `apply_to_chart` — no deferred drawing.
- **Precedence** (total-styles model): factory template (`base_template()`) < `stylesheet` < `rc` — all within one total style, no ambient layer — and for roles: style `settings` < user overrides (`get_styler(overrides=)`) < explicit primitive kwargs. Environment carve-out: `figure.dpi`/`savefig.dpi` stay ambient.
- **Root patch renders `axes.facecolor`** (settled 2026-07-24): the root axes keeps its patch visible — it is the chart's background panel, so panel-based sheets (ggplot's gray, Solarize) render correctly and their grids read against it; panes stay transparent overlays. (Under total styles, sheets render as designed: `style="ggplot"` gets ggplot's own grid at full alpha — the historical ambient-dimming caveat is gone.)
- **Boundary**: mplchart styles what mplchart draws. Direct user access to axes between calls gets ambient matplotlib style (optionally warn via a `_style_active` debug flag when a style is configured).

## Canvas / Chart integration

```python
class Canvas:
    def __init__(self, figsize=None, *, figure=None, title=None, style=None):
        self.styler = get_styler(style)
        with self.styler.context():
            ...create figure, root axes...

    def resolve_color(self, name, ax=None, *, fallback=None):
        return self.styler.resolve_color(name, ax, fallback=fallback)   # facade

    def get_setting(self, name, facet, *, fallback=None):
        return self.styler.get_setting(name, facet, fallback=fallback)  # facade (presence probes, non-color facets)
```

Three objects, two planes: Chart = canvas + view; the styler nests inside Canvas (its cycle state is keyed on this figure's axes — ownership, not siblinghood). Primitives keep calling `chart.canvas.resolve_color(...)`; `Styler` is exported but semi-internal.

## Role vocabulary (draft)

Expanded candidate list in [style-settings.md](style-settings.md) — full mplfinance coverage accounting plus per-primitive keys; that note also switches roles to singular (`candle.*`, superseding the plural `candles.*` spellings below and in the examples above).

| Role | Consumer | Today |
|---|---|---|
| `candles.up` / `candles.dn` / `candles.off` | Candlesticks | ctor kwargs + rcParams defaults |
| `ohlc.up` / `ohlc.dn` | OHLC | ctor kwargs + rcParams defaults |
| `volume.up` / `volume.dn` / `volume.ma` | Volume | ctor kwargs + hardcoded green/red/gray |
| indicator prefixes (`macd`, `rsi`, `sma`, ...) | AutoPlot | already works via `extract_prefix` |
| sentinels `line` / `fill`, `~` prefix | all | already works |

Retrofit: Candlesticks/OHLC/Volume resolve defaults through `canvas.resolve_color(role, fallback=<current default>)`; explicit kwargs still win. This closes the asymmetry noted in [primitive-contract.md](primitive-contract.md) (scheme was AutoPlot-only). Candlesticks done 2026-07-23 (`candle.up/down/off`, `edge.up/down`, `wicks` keys; kwarg schemes atomic — see [candlestick-styles.md](candlestick-styles.md)); OHLC done 2026-07-23 (`ohlc.up/down.color` + `ohlc.alpha`; no anatomy, no mode flags — the interbar criterion is the chart type's definition; roles independent, shipped styles declare both palettes; side colors are independent per-side params — kwarg → setting → textcolor, no atomic scheme since there is no coordinated look to protect); Volume done 2026-07-23 (`volume.up/down/ma.color` + `volume.alpha`, per-element params like OHLC; direction fixed to intrabar close ≥ open matching candlesticks — was interbar; explicit kwargs now exact, no longer prop-cycle-snapped — only the `~`-defaults snap). Retrofit complete: every price/volume renderer resolves through the styler.

## mplfinance findings (reference)

- Applies styles by mutating global rcParams with **no restore** (`plt.style.use('default')` first — resets the user's own style); the clean fix (`with_rc_context` decorator) exists in their source, commented out. The scoped-context design here is that fix, turned on.
- Marketcolors never go near rcParams — threaded explicitly to artist constructors (same split as this design; only their rc half is unhygienic).
- Style dict = rc-ish keys + `marketcolors` + exactly three non-color settings (`alpha`, `y_on_right`, `vcdopcod`). No widths/linestyles in styles — separate subsystem. Validates colors-only scope for v1.
- One dedicated cycle (`mavcolors`, moving averages only, reset per plot call) + ambient prop cycle.

## Performance (measured 2026-07-24)

No caching anywhere — measured and rejected (remeasured 2026-07-24 under total styles). `load_stylesheet`: 4µs (library name), 67µs (template filter), 22µs (`.mplstyle` file, warm); `Styler` ctor: 77µs (template build); `get_styler("nightclouds")`: ~100µs; `rc_context` enter/exit: 233µs (~700 totalized keys). Chart+Candlesticks: ~7.5-7.9ms (~10% over the pre-totalization 6.9ms); PNG render 46ms dwarfs it all. Caching resolution would save ~0.4% of chart creation; frozendicts are a shared-cache safety device with no cache to protect — eager `dict(...)` copies stay. The one future knob if profiling ever demands: collapsing the several per-chart `rc_context` entries into one (~0.5ms) — architectural, not justified today. Bench script pattern: timeit over load/resolve/context/chart/render layers. (Incidental confirmation: `.mplstyle` inline `#` truncation is real — the bench sheet had to write bare hex, as the interop caveat below warns.)

## Docs requirements (for the future styles page)

- Carry the trademark disclaimer: "Style names refer to the chart looks they imitate; mplchart is not affiliated with or endorsed by TradingView, StockCharts.com, or any named service." (Also present in `styles/lib/__init__.py` and the named modules.)
- Teach: `style=None` → the `mplchart` style; `style="default"` → matplotlib's factory look (they differ by exactly the two grid keys); sheets are styles (`style="ggplot"`); custom styles as dicts; the two grid keys.

## Deferred (mechanisms verified, not v1)

- **`.mplstyle` interop**: loading landed 2026-07-23 (`load_stylesheet` — stock names via `mpl.style.library`, paths via `rc_params_from_file(use_default_template=False)`, and the `"default"` special name → factory template minus `STYLE_BLACKLIST`, mirroring `plt.style.use`; the opt-in ambient-independent base — mplfinance's reset, scoped. Exposed as `Styler(stylesheet=)`). Still deferred: dotted-name resolution (`plt.style.use("mplchart.styles.<name>")` finds `<name>.mplstyle` next to the package `__init__` via `importlib.resources`) lets bare-matplotlib users consume the rc half; symbolic layer could ride in `# mplchart:` magic comments (full-line comments pass the parser silently; inline comments truncate at first `#` — write bare hex). Interchange format only; dicts stay the truth.
- **TOML authoring** for user styles (`tomllib`, comments, 1:1 onto the dict schema). Preferred over JSON (no comments) and pydantic (dependency for a 3-field schema).
- **rc TypedDict** (generated from `RcParams.validate`, functional syntax for dotted keys, `total=False`): pyright/Pylance catches bad keys/values in dict literals; ty does not enforce TypedDicts yet. Export for opt-in annotation only — never as the parameter type (plain dicts aren't assignable to TypedDicts; would break dynamically-built styles).
- **mplfinance style-dict compat** (translate `marketcolors`) — stretch goal; translator prototyped in `playground/candlesticks-styles.ipynb` (2026-07-23), all 16 shipped styles' candle looks reproduce.

## Open questions

- ~~Fate of `Chart(color_scheme=)`~~ — resolved 2026-07-23: deprecated and ignored (DeprecationWarning at Chart, pointing at `style=` settings); removed from `Canvas`/`get_styler`, `map_color_scheme` deleted along with the bare-key munging (internal form is always canonical).
- Role growth: `candles.wick` (mplfinance separates wick color; mplchart currently can't), body-edge vs fill split.
- ~~First shipped styles~~ — shipped 2026-07-23/24: `mplchart` (the default look as an ordinary lib style), `modern` (contemporary web-platform look, né tradingview), `nightclouds` (dark, sheet-based), `chartist` (colored hollow × interbar, né stockcharts). Renamed 2026-07-24 to descriptive names — no shipped style carries a platform trademark (the disclaimer in `styles/lib/__init__.py` covers future imitative additions). `Style`/`resolve_style`/`available_styles` implemented in `styles/style.py` (which also owns `load_stylesheet` — the static layer imports nothing from the runtime layer).
- `hline`/`vline`/`Stripes` roles, or leave them on rc grid defaults.
- AutoPlot passes per-instance labels (`"sma-50"`) as `resolve_color` names, so scheme cycles don't advance across instances — align at retrofit time by passing the indicator type as the role name.
- ~~Whether style should parameterize pane anatomy values (grid alpha 0.4 hardcoded in `config_pane_axes`)~~ — resolved 2026-07-23 via an rc baseline, superseded 2026-07-24 by **total styles**: the config functions read `axes.grid`/`axes.grid.axis` — root draws x iff axis ∈ {x, both}, panes y iff axis ∈ {y, both}; the default look's grid keys (`axes.grid: True`, `grid.alpha: 0.4`) live in the shipped `mplchart` style module. Structure (where grids draw) stays Canvas's; whether/how is rc. mplfinance grid fidelity note: their `explicit_grid` rule belongs in the style translator, not core.
- `Chart(style=...)` vs also allowing per-`plot()` style — rejected for rc (figure-wide semantics); per-pane differences belong to the colors layer.
