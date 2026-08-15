from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .layout import Rect
from .motion import resolve_motion
from .svg_primitives import build_primitive_defs, render_background_grid
from .theme import Theme, resolve_theme
from .tokens import TokenBundle, load_tokens


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HANDOFF_PATH = ROOT / "assets" / "source" / "kalaos.handoff.json"


@dataclass(frozen=True)
class HandoffVector:
    name: str
    consequence_class: str
    consequence: str
    preparation: str
    release: str


@dataclass(frozen=True)
class HandoffLayout:
    canvas_width: int
    canvas_height: int
    frame: Rect
    header_state_x: int
    header_state_y: int
    header_title_x: int
    header_title_y: int
    header_subtitle_x: int
    header_subtitle_y: int
    future_x: int
    future_y: int
    state_strip_x: int
    state_strip_y: int
    state_strip_width: int
    threshold: Rect
    selected: Rect
    summary_x: int
    summary_y: int


@dataclass(frozen=True)
class HandoffDocument:
    title: str
    subtitle: str
    transition: str
    selected_vector: str
    state_model: tuple[str, ...]
    state_labels: tuple[str, ...]
    layout: HandoffLayout
    vectors: tuple[HandoffVector, ...]


@dataclass(frozen=True)
class HandoffRender:
    svg: str
    theme_mode: str


def _seconds(ms: int) -> str:
    return f"{ms / 1000:.2f}s"


def _text(
    x: float,
    y: float,
    size: int,
    fill: str,
    text: str,
    *,
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


def _parse_vector(raw: dict[str, object]) -> HandoffVector:
    return HandoffVector(
        name=str(raw["name"]),
        consequence_class=str(raw["consequence_class"]),
        consequence=str(raw["consequence"]),
        preparation=str(raw["preparation"]),
        release=str(raw["release"]),
    )


def load_handoff_document(path: Path | str = DEFAULT_HANDOFF_PATH) -> HandoffDocument:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    layout_raw = raw["layout"]
    frame = layout_raw["frame"]
    header = layout_raw["header"]
    threshold = layout_raw["threshold"]
    selected = layout_raw["selected"]
    state_strip = layout_raw["state_strip"]
    summary = layout_raw["summary"]
    layout = HandoffLayout(
        canvas_width=int(layout_raw["canvas"]["width"]),
        canvas_height=int(layout_raw["canvas"]["height"]),
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
        future_x=int(header["future_x"]),
        future_y=int(header["future_y"]),
        state_strip_x=int(state_strip["x"]),
        state_strip_y=int(state_strip["y"]),
        state_strip_width=int(state_strip["width"]),
        threshold=Rect(
            x=int(threshold["x"]),
            y=int(threshold["y"]),
            width=int(threshold["width"]),
            height=int(threshold["height"]),
            radius=int(threshold["radius"]),
        ),
        selected=Rect(
            x=int(selected["x"]),
            y=int(selected["y"]),
            width=int(selected["width"]),
            height=int(selected["height"]),
            radius=int(selected["radius"]),
        ),
        summary_x=int(summary["x"]),
        summary_y=int(summary["y"]),
    )
    handoff = raw["handoff"]
    return HandoffDocument(
        title=str(handoff["title"]),
        subtitle=str(handoff["subtitle"]),
        transition=str(handoff["transition"]),
        selected_vector=str(handoff.get("selected_vector", handoff["vectors"][0]["name"])),
        state_model=tuple(str(value) for value in handoff["state_model"]),
        state_labels=tuple(str(value) for value in handoff["state_labels"]),
        layout=layout,
        vectors=tuple(_parse_vector(item) for item in handoff["vectors"]),
    )


def _selected_vector(document: HandoffDocument) -> HandoffVector:
    for vector in document.vectors:
        if vector.name == document.selected_vector:
            return vector
    return document.vectors[0]


def _state_strip(theme: Theme, layout: HandoffLayout, labels: tuple[str, ...]) -> str:
    return (
        f'<line x1="{layout.state_strip_x}" y1="{layout.state_strip_y}" x2="{layout.state_strip_x + layout.state_strip_width}" y2="{layout.state_strip_y}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.38"/>'
        f'{_text(layout.state_strip_x, layout.state_strip_y - 6, 10, theme.text_secondary, labels[0], tracking=1.1)}'
        f'{_text(layout.state_strip_x + 292, layout.state_strip_y - 6, 10, theme.accent_cyan, labels[1], tracking=1.1)}'
        f'{_text(layout.state_strip_x + 544, layout.state_strip_y - 6, 10, theme.text_secondary, labels[2], tracking=1.1)}'
        f'<rect x="{layout.state_strip_x + 282}" y="{layout.state_strip_y}" width="120" height="2" fill="{theme.accent_cyan}"/>'
    )


def _threshold_shell(theme: Theme, layout: HandoffLayout, selected: HandoffVector) -> str:
    t = layout.threshold
    cx = t.x + t.width / 2
    cy = t.y + t.height / 2
    fill = {
        "EXPLORE": theme.accent_violet,
        "TRACE": theme.accent_cyan,
        "CONVERSE": theme.warning_amber,
    }[selected.name]
    return (
        f'<g id="handoff-threshold">'
        f'<rect x="{t.x}" y="{t.y}" width="{t.width}" height="{t.height}" rx="{t.radius}" fill="none" stroke="{theme.border_panel}" stroke-width="1.2"/>'
        f'<line x1="{cx:.1f}" y1="{t.y + 12}" x2="{cx:.1f}" y2="{t.y + t.height - 12}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.42"/>'
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6.4" fill="{theme.accent_lavender}" opacity="0.92"/>'
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="16" fill="none" stroke="{fill}" stroke-width="1" stroke-opacity="0.18"/>'
        f'<path d="M {cx - 10:.1f} {cy - 58} V {cy - 18} M {cx + 10:.1f} {cy + 18} V {cy + 58}" fill="none" stroke="{fill}" stroke-width="1.4" stroke-linecap="round" stroke-opacity="0.68"/>'
        f'{_text(t.x + 10, t.y + 24, 10, theme.text_muted, "THRESHOLD", tracking=1.2)}'
        f'{_text(t.x + 10, t.y + t.height - 10, 10, theme.text_muted, "CROSSING", tracking=1.0)}'
        "</g>"
    )


def _selected_surface(theme: Theme, layout: HandoffLayout, selected: HandoffVector) -> str:
    r = layout.selected
    t = layout.threshold
    fill = {
        "EXPLORE": theme.accent_violet,
        "TRACE": theme.accent_cyan,
        "CONVERSE": theme.warning_amber,
    }[selected.name]
    if selected.name == "EXPLORE":
        path = f'M {r.x + 28} {r.y + 94} H {r.x + 168} V {r.y + 56} H {t.x - 18} V {t.y + 84} H {t.x + 24}'
        detail = "DEEPER CONTEXT"
        start_x = r.x + 28
        consequence_x = r.x + 24
    elif selected.name == "TRACE":
        path = f'M {r.x + 28} {r.y + 86} H {r.x + 164} V {r.y + 44} H {t.x - 18} V {t.y + 152} H {t.x + 24}'
        detail = "PROVENANCE PATH"
        start_x = r.x + 26
        consequence_x = r.x + 24
    else:
        path = f'M {r.x + 28} {r.y + 78} H {r.x + 156} V {r.y + 32} H {t.x - 18} V {t.y + 220} H {t.x + 24}'
        detail = "COMMUNICATION BOUNDARY"
        start_x = r.x + 26
        consequence_x = r.x + 24
    return (
        f'<g id="handoff-selected">'
        f'<rect x="{r.x}" y="{r.y}" width="{r.width}" height="{r.height}" rx="{r.radius}" fill="none" stroke="{fill}" stroke-width="1.2" stroke-opacity="0.56"/>'
        f'<line x1="{r.x + 18}" y1="{r.y + r.height - 18}" x2="{r.x + r.width - 18}" y2="{r.y + r.height - 18}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.28"/>'
        f'{_text(start_x, r.y + 24, 16, fill, selected.name, weight=700, tracking=0.9)}'
        f'{_text(start_x, r.y + 46, 11, theme.text_secondary, "SELECTED ACTION", tracking=0.9)}'
        f'{_text(start_x, r.y + 66, 12, theme.text_primary, selected.preparation)}'
        f'{_text(start_x, r.y + 82, 10, theme.text_muted, "prepared inside KalaOS", tracking=0.2)}'
        f'<path d="{path}" fill="none" stroke="{fill}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" stroke-opacity="0.88"/>'
        f'<circle cx="{r.x + 42}" cy="{r.y + 94}" r="5.0" fill="{theme.accent_lavender}" opacity="0.92"/>'
        f'<circle cx="{t.x - 10}" cy="{t.y + 152 if selected.name == "TRACE" else t.y + 84 if selected.name == "EXPLORE" else t.y + 220}" r="4.8" fill="{theme.success_green}" opacity="0.92"/>'
        f'{_text(consequence_x, r.y + 122, 12, fill, selected.consequence_class, weight=700, tracking=1.0)}'
        f'{_text(consequence_x, r.y + 140, 10, theme.text_secondary, selected.consequence)}'
        f'{_text(consequence_x, r.y + 156, 10, theme.text_muted, selected.release)}'
        f'{_text(t.x + 34, t.y + 72, 10, fill, detail, anchor="start", tracking=1.1)}'
        f'<path d="M {r.x + 24} {r.y + 94} H {r.x + 160} M {r.x + 164} {r.y + 94} H {t.x - 16} M {t.x + 20} {t.y + 94 if selected.name == "EXPLORE" else t.y + 164 if selected.name == "TRACE" else t.y + 232} H {t.x + 98}" fill="none" stroke="{theme.border_hairline}" stroke-width="1" stroke-dasharray="4 8" stroke-opacity="0.34"/>'
        "</g>"
    )


def render_handoff(mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_HANDOFF_PATH) -> HandoffRender:
    bundle = tokens or load_tokens()
    theme = resolve_theme(mode, bundle)
    document = load_handoff_document(config_path)
    motion = resolve_motion(bundle)
    selected = _selected_vector(document)
    typography = bundle.typography_scale
    frame = document.layout.frame
    threshold = document.layout.threshold
    selected_box = document.layout.selected
    state_fill = {
        "EXPLORE": theme.accent_violet,
        "TRACE": theme.accent_cyan,
        "CONVERSE": theme.warning_amber,
    }[selected.name]
    svg = "".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{document.layout.canvas_width}" height="{document.layout.canvas_height}" viewBox="0 0 {document.layout.canvas_width} {document.layout.canvas_height}" role="img" aria-labelledby="title desc">',
            '<title id="title">KalaOS handoff</title>',
            '<desc id="desc">Single selected action crossing the KalaOS boundary into external consequence.</desc>',
            "<defs>",
            build_primitive_defs(mode, bundle),
            "</defs>",
            f'<rect width="{document.layout.canvas_width}" height="{document.layout.canvas_height}" fill="{theme.background}"/>',
            render_background_grid(theme, bundle, opacity=0.10),
            f'<rect x="{frame.x}" y="{frame.y}" width="{frame.width}" height="{frame.height}" rx="{frame.radius}" fill="{theme.panel}" stroke="{theme.border_panel}" stroke-width="{bundle.stroke_widths["standard"]}"/>',
            f'<g id="handoff-header">',
            f'<use href="#kalaos-origin-mark" x="{frame.x + 16}" y="{frame.y + 12}" width="34" height="34" opacity="0.36"/>',
            _text(document.layout.header_state_x, document.layout.header_state_y, int(typography["caption"]["size"]), theme.text_secondary, "INTERFACE / TRANSFER", weight=int(typography["caption"]["weight"]), tracking=1.8),
            _text(document.layout.header_title_x, document.layout.header_title_y, int(typography["display"]["size"]), theme.text_primary, document.title, weight=int(typography["display"]["weight"]), tracking=0.9),
            _text(document.layout.header_subtitle_x, document.layout.header_subtitle_y, int(typography["body"]["size"]), theme.text_secondary, document.subtitle, weight=int(typography["body"]["weight"])),
            _text(document.layout.future_x, document.layout.future_y, int(typography["caption"]["size"]), state_fill, f"SELECTED / {selected.name}", weight=int(typography["caption"]["weight"]), anchor="end", tracking=1.6),
            _state_strip(theme, document.layout, document.state_labels),
            _text(document.layout.future_x, 96, int(typography["small"]["size"]), theme.text_muted, "EXTERNAL / CONSEQUENCE", weight=int(typography["small"]["weight"]), anchor="end", tracking=1.2),
            _text(document.layout.future_x, 118, int(typography["small"]["size"]), theme.text_muted, document.transition, weight=int(typography["small"]["weight"]), anchor="end", tracking=0.9),
            "</g>",
            f'<line x1="{document.layout.state_strip_x}" y1="164" x2="{document.layout.state_strip_x + document.layout.state_strip_width}" y2="164" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.34"/>',
            _reveal_group(_selected_surface(theme, document.layout, selected), motion.assemble * 2, motion.assemble, dy=8),
            _reveal_group(_threshold_shell(theme, document.layout, selected), motion.assemble * 4, motion.assemble, dy=4),
            f'<g id="handoff-footer">',
            f'<line x1="{document.layout.summary_x}" y1="{document.layout.summary_y - 18}" x2="{document.layout.summary_x + 992}" y2="{document.layout.summary_y - 18}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.28"/>',
            _text(document.layout.summary_x, document.layout.summary_y, int(typography["caption"]["size"]), theme.text_muted, "STATE MODEL", weight=int(typography["caption"]["weight"]), tracking=1.2),
            _text(document.layout.summary_x + 118, document.layout.summary_y, int(typography["caption"]["size"]), theme.text_secondary, " • ".join(document.state_model), weight=int(typography["caption"]["weight"]), tracking=0.3),
            _text(document.layout.summary_x + 408, document.layout.summary_y, int(typography["caption"]["size"]), state_fill, f"ACTIVE: {selected.name} / {selected.consequence_class}", weight=int(typography["caption"]["weight"]), tracking=0.9),
            _text(document.layout.summary_x + 866, document.layout.summary_y, int(typography["caption"]["size"]), theme.text_muted, "EXTERNAL CONSEQUENCE", weight=int(typography["caption"]["weight"]), anchor="end", tracking=1.1),
            "</g>",
            "</svg>",
        ]
    )
    return HandoffRender(svg=svg, theme_mode=mode)


def write_handoff(path: Path, mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_HANDOFF_PATH) -> Path:
    handoff = render_handoff(mode=mode, tokens=tokens, config_path=config_path)
    path.write_text(handoff.svg, encoding="utf-8")
    return path
