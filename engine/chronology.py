from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .layout import Rect
from .motion import MotionTokens, resolve_motion
from .svg_primitives import build_primitive_defs, render_background_grid
from .theme import Theme, resolve_theme
from .tokens import TokenBundle, load_tokens


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHRONOLOGY_PATH = ROOT / "assets" / "source" / "kalaos.chronology.json"


@dataclass(frozen=True)
class ChronologyLayout:
    canvas_width: int
    canvas_height: int
    frame: Rect
    header_state_x: int
    header_state_y: int
    header_title_x: int
    header_title_y: int
    header_subtitle_x: int
    header_subtitle_y: int
    strata: Rect
    summary_x: int
    summary_y: int
    summary_gap: int


@dataclass(frozen=True)
class ChronologyPoint:
    x: float
    dy: float


@dataclass(frozen=True)
class ChronologyEra:
    id: str
    label: str
    period: str
    state: str
    reference: str
    importance: str
    band: float
    trace: tuple[ChronologyPoint, ...]


@dataclass(frozen=True)
class ChronologyTransition:
    source: str
    target: str
    kind: str
    label: str


@dataclass(frozen=True)
class ChronologySummary:
    eras: int
    transitions: int
    last_observed: str


@dataclass(frozen=True)
class ChronologyDocument:
    title: str
    subtitle: str
    state: str
    layout: ChronologyLayout
    eras: tuple[ChronologyEra, ...]
    transitions: tuple[ChronologyTransition, ...]
    summary: ChronologySummary


@dataclass(frozen=True)
class ChronologyRender:
    svg: str
    theme_mode: str


def _seconds(ms: int) -> str:
    return f"{ms / 1000:.2f}s"


def _text(
    theme: Theme,
    x: float,
    y: float,
    size: int,
    fill: str,
    text: str,
    weight: int = 400,
    anchor: str = "start",
    tracking: float = 0.0,
) -> str:
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}"'
        f' letter-spacing="{tracking}" fill="{fill}">{text}</text>'
    )


def _reveal_group(content: str, delay_ms: int, duration_ms: int, dy: int = 6) -> str:
    return (
        '<g opacity="1">'
        f'<animate attributeName="opacity" from="0" to="1" dur="{_seconds(duration_ms)}" begin="{_seconds(delay_ms)}" fill="freeze" calcMode="spline" keySplines="0.42 0 0.58 1"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 {dy}" to="0 0" dur="{_seconds(duration_ms)}" begin="{_seconds(delay_ms)}" fill="freeze" calcMode="spline" keySplines="0.42 0 0.58 1"/>'
        f"{content}</g>"
    )


def _parse_layout(raw: dict[str, object]) -> ChronologyLayout:
    canvas = raw["canvas"]
    frame = raw["frame"]
    header = raw["header"]
    strata = raw["strata"]
    summary = raw["summary"]
    return ChronologyLayout(
        canvas_width=int(canvas["width"]),
        canvas_height=int(canvas["height"]),
        frame=Rect(
            x=int(frame["x"]),
            y=int(frame["y"]),
            width=int(frame["width"]),
            height=int(frame["height"]),
            radius=int(frame["radius"]),
        ),
        header_state_x=int(header["state_x"]),
        header_state_y=int(header["state_y"]),
        header_title_x=int(header["title_x"]),
        header_title_y=int(header["title_y"]),
        header_subtitle_x=int(header["subtitle_x"]),
        header_subtitle_y=int(header["subtitle_y"]),
        strata=Rect(
            x=int(strata["x"]),
            y=int(strata["y"]),
            width=int(strata["width"]),
            height=int(strata["height"]),
            radius=int(strata["radius"]),
        ),
        summary_x=int(summary["x"]),
        summary_y=int(summary["y"]),
        summary_gap=int(summary["gap"]),
    )


def _parse_point(raw: dict[str, object]) -> ChronologyPoint:
    return ChronologyPoint(
        x=float(raw["x"]),
        dy=float(raw["dy"]),
    )


def _parse_era(raw: dict[str, object]) -> ChronologyEra:
    return ChronologyEra(
        id=str(raw["id"]),
        label=str(raw["label"]),
        period=str(raw["period"]),
        state=str(raw["state"]),
        reference=str(raw["reference"]),
        importance=str(raw["importance"]),
        band=float(raw["band"]),
        trace=tuple(_parse_point(point) for point in raw["trace"]),
    )


def _parse_transition(raw: dict[str, object]) -> ChronologyTransition:
    return ChronologyTransition(
        source=str(raw["source"]),
        target=str(raw["target"]),
        kind=str(raw["kind"]),
        label=str(raw["label"]),
    )


def _parse_summary(raw: dict[str, object]) -> ChronologySummary:
    return ChronologySummary(
        eras=int(raw["eras"]),
        transitions=int(raw["transitions"]),
        last_observed=str(raw["last_observed"]),
    )


def load_chronology_document(path: Path | str = DEFAULT_CHRONOLOGY_PATH) -> ChronologyDocument:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    layout = _parse_layout(raw["layout"])
    chronology = raw["chronology"]
    eras = tuple(_parse_era(era) for era in chronology["eras"])
    transitions = tuple(_parse_transition(transition) for transition in chronology["transitions"])
    summary = _parse_summary(chronology["summary"])
    return ChronologyDocument(
        title=str(chronology["title"]),
        subtitle=str(chronology["subtitle"]),
        state=str(chronology["state"]),
        layout=layout,
        eras=eras,
        transitions=transitions,
        summary=summary,
    )


def _importance_rank(era: ChronologyEra) -> int:
    mapping = {
        "primary": 4,
        "current": 5,
        "secondary": 3,
        "archived": 1,
    }
    return mapping.get(era.importance, 2)


def _tone(theme: Theme, era: ChronologyEra) -> str:
    palette = {
        "foundation": theme.accent_lavender,
        "origin": theme.accent_violet,
        "boot": theme.accent_cyan,
        "identity": theme.success_green,
        "systems": theme.warning_amber,
        "telemetry": theme.text_secondary,
        "chronology": theme.accent_lavender,
    }
    return palette.get(era.id, theme.text_secondary)


def _row_y(layout: ChronologyLayout, era: ChronologyEra) -> float:
    return layout.strata.y + layout.strata.height * era.band


def _trace_points(layout: ChronologyLayout, era: ChronologyEra, y: float) -> list[tuple[float, float]]:
    trace_x = layout.strata.x + 210
    trace_width = layout.strata.width - 240
    amplitude = 20 + _importance_rank(era) * 3.0
    points: list[tuple[float, float]] = []
    for point in era.trace:
        x = trace_x + trace_width * point.x
        py = y + point.dy * amplitude
        points.append((x, py))
    return points


def _era_group(
    theme: Theme,
    era: ChronologyEra,
    layout: ChronologyLayout,
    typography: dict[str, dict[str, float]],
    motion: MotionTokens,
    delay_ms: int,
) -> str:
    section = typography["section"]
    small = typography["small"]
    caption = typography["caption"]
    y = _row_y(layout, era)
    points = _trace_points(layout, era, y)
    tone = _tone(theme, era)
    rank = _importance_rank(era)
    if not points:
        return ""
    trace_width = 1.2 + rank * 0.24
    opacity = 0.20 + rank * 0.08
    path_d = "M " + " L ".join(f"{x:.1f} {py:.1f}" for x, py in points)
    marker_x, marker_y = points[-1]
    lead_x = layout.strata.x
    label_x = layout.strata.x
    fragments = []
    for index, (frag_x, frag_y) in enumerate(points[1:-1], start=1):
        frag_opacity = max(0.18, 0.44 - index * 0.04 + rank * 0.03)
        frag_radius = max(0.85, 1.05 + rank * 0.12 - index * 0.03)
        fragments.append(
            f'<circle cx="{frag_x:.1f}" cy="{frag_y:.1f}" r="{frag_radius:.2f}" fill="{tone}" opacity="{frag_opacity:.2f}"/>'
        )
    return _reveal_group(
        (
            f'<g opacity="1">'
            f'<line x1="{lead_x}" y1="{y - 12}" x2="{lead_x + 160}" y2="{y - 12}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.20"/>'
            f'<text x="{label_x}" y="{y - 2}" font-size="{int(section["size"])}" font-weight="{int(section["weight"])}" letter-spacing="0.22" fill="{theme.text_primary}">{era.label}</text>'
            f'<text x="{label_x}" y="{y + 13}" font-size="{int(small["size"])}" font-weight="{int(small["weight"])}" letter-spacing="0.16" fill="{theme.text_secondary}">{era.state} / {era.period}</text>'
            f'<text x="{label_x}" y="{y + 27}" font-size="{int(caption["size"])}" font-weight="{int(caption["weight"])}" letter-spacing="0.10" fill="{theme.text_muted}">{era.reference}</text>'
            f'<path d="{path_d}" fill="none" stroke="{tone}" stroke-width="{trace_width:.2f}" stroke-linecap="round" stroke-linejoin="round" stroke-opacity="{opacity:.2f}"/>'
            f'{"".join(fragments)}'
            f'<circle cx="{marker_x:.1f}" cy="{marker_y:.1f}" r="{2.6 + rank * 0.7:.2f}" fill="{tone}" opacity="{0.58 + rank * 0.08:.2f}"/>'
            f'<circle cx="{marker_x:.1f}" cy="{marker_y:.1f}" r="{1.2 + rank * 0.22:.2f}" fill="{theme.background}" opacity="0.88"/>'
            "</g>"
        ),
        delay_ms=delay_ms,
        duration_ms=motion.reveal,
        dy=4,
    )


def _transition_group(
    theme: Theme,
    source: ChronologyEra,
    target: ChronologyEra,
    layout: ChronologyLayout,
    typography: dict[str, dict[str, float]],
    motion: MotionTokens,
    delay_ms: int,
    label: str,
    kind: str,
) -> str:
    source_y = _row_y(layout, source)
    target_y = _row_y(layout, target)
    source_points = _trace_points(layout, source, source_y)
    target_points = _trace_points(layout, target, target_y)
    if not source_points or not target_points:
        return ""
    start_x, start_y = source_points[-1]
    end_x, end_y = target_points[-1]
    bridge_x = layout.strata.x + layout.strata.width - 96
    color = {
        "preservation": theme.accent_lavender,
        "continuation": theme.accent_violet,
        "refinement": theme.accent_cyan,
        "resolution": theme.success_green,
        "mapping": theme.warning_amber,
    }.get(kind, theme.border_hairline)
    dash = {
        "preservation": "4 8",
        "continuation": "5 7",
        "refinement": "3 6",
        "resolution": "none",
        "mapping": "3 7",
    }.get(kind, "none")
    dash_attr = f' stroke-dasharray="{dash}"' if dash != "none" else ""
    mid_y = (start_y + end_y) / 2.0
    caption = typography["caption"]
    return _reveal_group(
        (
            f'<g opacity="1">'
            f'<path d="M {start_x:.1f} {start_y:.1f} H {bridge_x:.1f} V {end_y:.1f} H {end_x:.1f}" fill="none" stroke="{color}" stroke-width="1.15" stroke-linecap="round" stroke-opacity="0.30"{dash_attr}/>'
            f'<text x="{bridge_x - 4:.1f}" y="{mid_y - 3:.1f}" text-anchor="end" font-size="{int(caption["size"])}" font-weight="{int(caption["weight"])}" letter-spacing="0.5" fill="{theme.text_muted}" opacity="0.62">{label}</text>'
            f'<circle cx="{bridge_x:.1f}" cy="{end_y:.1f}" r="2.0" fill="{color}" opacity="0.42"/>'
            "</g>"
        ),
        delay_ms=delay_ms,
        duration_ms=motion.normal,
        dy=2,
    )


def _summary_row(theme: Theme, document: ChronologyDocument, typography: dict[str, dict[str, float]]) -> str:
    small = typography["small"]
    caption = typography["caption"]
    y = document.layout.summary_y
    x = document.layout.summary_x
    items = [
        (x, f"{document.summary.eras} ERAS", "OBSERVED"),
        (x + 268, f"{document.summary.transitions} TRANSITIONS", "RESOLVED"),
        (x + 540, document.summary.last_observed, "LAST OBSERVED"),
    ]
    parts = ['<g opacity="1">']
    for index, (item_x, value, label) in enumerate(items):
        if index:
            parts.append(f'<line x1="{item_x - 20}" y1="{y - 11}" x2="{item_x - 20}" y2="{y + 10}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.30"/>')
        parts.append(_text(theme, item_x, y, int(small["size"]), theme.text_primary, value, int(small["weight"]), tracking=0.18))
        parts.append(_text(theme, item_x, y + 14, int(caption["size"]), theme.text_muted, label, int(caption["weight"]), tracking=0.14))
    parts.append("</g>")
    return "".join(parts)


def render_chronology(mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_CHRONOLOGY_PATH) -> ChronologyRender:
    bundle = tokens or load_tokens()
    theme = resolve_theme(mode, bundle)
    motion = resolve_motion(bundle)
    document = load_chronology_document(config_path)
    layout = document.layout
    typography = bundle.typography_scale
    era_by_id = {era.id: era for era in document.eras}
    fallback = not document.eras or not document.transitions
    state_label = document.state if not fallback else "CHRONOLOGY UNAVAILABLE"
    title = document.title if not fallback else "CHRONOLOGY"
    subtitle = document.subtitle if not fallback else "NO CHRONOLOGY SIGNAL"
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{layout.canvas_width}" height="{layout.canvas_height}" viewBox="0 0 {layout.canvas_width} {layout.canvas_height}" role="img" aria-labelledby="title desc">',
        '<title id="title">KalaOS chronology</title>',
        '<desc id="desc">Chronology layer for KalaOS showing preserved temporal strata and observed transitions.</desc>',
        "<defs>",
        build_primitive_defs(mode, bundle),
        f'<clipPath id="kalaos-chronology-field"><rect x="{layout.strata.x}" y="{layout.strata.y}" width="{layout.strata.width}" height="{layout.strata.height}" rx="{layout.strata.radius}"/></clipPath>',
        "</defs>",
        f'<rect width="{layout.canvas_width}" height="{layout.canvas_height}" fill="{theme.background}"/>',
        render_background_grid(theme, bundle, opacity=0.11),
        f'<rect x="{layout.frame.x}" y="{layout.frame.y}" width="{layout.frame.width}" height="{layout.frame.height}" rx="{layout.frame.radius}" fill="none" stroke="{theme.border_panel}" stroke-width="{bundle.stroke_widths["standard"]}"/>',
        _text(theme, layout.header_state_x, layout.header_state_y, int(typography["caption"]["size"]), theme.text_secondary, state_label, int(typography["caption"]["weight"]), tracking=1.8),
        _text(theme, layout.header_title_x, layout.header_title_y, int(typography["display_xl"]["size"]), theme.text_primary, title, int(typography["display_xl"]["weight"]), tracking=1.2),
        _text(theme, layout.header_subtitle_x, layout.header_subtitle_y, int(typography["small"]["size"]), theme.text_muted, subtitle, int(typography["small"]["weight"]), tracking=0.2),
        f'<line x1="{layout.header_title_x}" y1="{layout.header_subtitle_y + 12}" x2="{layout.header_title_x + 540}" y2="{layout.header_subtitle_y + 12}" stroke="{theme.border_hairline}" stroke-width="1"/>',
        f'<rect x="{layout.strata.x}" y="{layout.strata.y}" width="{layout.strata.width}" height="{layout.strata.height}" rx="{layout.strata.radius}" fill="none" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.44"/>',
        f'<text x="{layout.strata.x}" y="{layout.strata.y - 16}" font-size="{int(typography["caption"]["size"])}" font-weight="{int(typography["caption"]["weight"])}" letter-spacing="1.3" fill="{theme.text_secondary}">TEMPORAL STRATA</text>',
        f'<text x="{layout.strata.x + 170}" y="{layout.strata.y - 16}" font-size="{int(typography["caption"]["size"])}" font-weight="{int(typography["caption"]["weight"])}" letter-spacing="1.3" fill="{theme.text_secondary}">TIME LEAVES STRUCTURE</text>',
        f'<text x="{layout.strata.x + layout.strata.width - 134}" y="{layout.strata.y - 16}" font-size="{int(typography["caption"]["size"])}" font-weight="{int(typography["caption"]["weight"])}" letter-spacing="1.3" fill="{theme.text_secondary}">CURRENT</text>',
    ]
    if fallback:
        parts.append(
            _reveal_group(
                (
                    f'<g clip-path="url(#kalaos-chronology-field)">'
                    f'<text x="{layout.strata.x}" y="{layout.strata.y + 40}" font-size="{int(typography["heading"]["size"])}" font-weight="{int(typography["heading"]["weight"])}" letter-spacing="0.5" fill="{theme.text_primary}">NO CHRONOLOGY SIGNAL</text>'
                    f'<text x="{layout.strata.x}" y="{layout.strata.y + 64}" font-size="{int(typography["small"]["size"])}" font-weight="{int(typography["small"]["weight"])}" letter-spacing="0.2" fill="{theme.text_muted}">CHRONOLOGY UNAVAILABLE</text>'
                    "</g>"
                ),
                delay_ms=motion.reveal,
                duration_ms=motion.reveal,
                dy=4,
            )
        )
    else:
        # Draw oldest layers first so newer traces can settle on top.
        sorted_eras = list(document.eras)
        for index, era in enumerate(sorted_eras):
            parts.append(
                _era_group(
                    theme,
                    era,
                    layout,
                    typography,
                    motion,
                    delay_ms=motion.fast + index * 95,
                )
            )
        transition_delay = motion.reveal + motion.normal
        for index, transition in enumerate(document.transitions):
            source = era_by_id.get(transition.source)
            target = era_by_id.get(transition.target)
            if not source or not target:
                continue
            parts.append(
                _transition_group(
                    theme,
                    source,
                    target,
                    layout,
                    typography,
                    motion,
                    delay_ms=transition_delay + index * 70,
                    label=transition.label.upper(),
                    kind=transition.kind,
                )
            )
        parts.append(_summary_row(theme, document, typography))
    parts.append("</svg>")
    return ChronologyRender(svg="".join(parts), theme_mode=mode)


def write_chronology(path: Path, mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_CHRONOLOGY_PATH) -> Path:
    chronology = render_chronology(mode=mode, tokens=tokens, config_path=config_path)
    path.write_text(chronology.svg, encoding="utf-8")
    return path
