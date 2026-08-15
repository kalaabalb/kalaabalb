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
DEFAULT_SIGNALS_PATH = ROOT / "assets" / "source" / "kalaos.signals.json"


@dataclass(frozen=True)
class SignalsLayout:
    canvas_width: int
    canvas_height: int
    frame: Rect
    header_state_x: int
    header_state_y: int
    header_title_x: int
    header_title_y: int
    header_subtitle_x: int
    header_subtitle_y: int
    field: Rect


@dataclass(frozen=True)
class SignalEvidence:
    path: str


@dataclass(frozen=True)
class SignalPosition:
    x: int
    y: int


@dataclass(frozen=True)
class SignalItem:
    id: str
    label: str
    category: str
    state: str
    importance: str
    evidence: tuple[SignalEvidence, ...]
    position: SignalPosition


@dataclass(frozen=True)
class SignalsDocument:
    layout: SignalsLayout
    signals: tuple[SignalItem, ...]


@dataclass(frozen=True)
class SignalsRender:
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


def _parse_layout(raw: dict[str, object]) -> SignalsLayout:
    canvas = raw["canvas"]
    frame = raw["frame"]
    header = raw["header"]
    field = raw["field"]
    return SignalsLayout(
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
        field=Rect(
            x=int(field["x"]),
            y=int(field["y"]),
            width=int(field["width"]),
            height=int(field["height"]),
            radius=int(field["radius"]),
        ),
    )


def _parse_evidence(raw: str) -> SignalEvidence:
    return SignalEvidence(path=str(raw))


def _parse_position(raw: dict[str, object]) -> SignalPosition:
    return SignalPosition(x=int(raw["x"]), y=int(raw["y"]))


def _parse_signal(raw: dict[str, object]) -> SignalItem:
    return SignalItem(
        id=str(raw["id"]),
        label=str(raw["label"]),
        category=str(raw["category"]),
        state=str(raw["state"]),
        importance=str(raw["importance"]),
        evidence=tuple(_parse_evidence(value) for value in raw["evidence"]),
        position=_parse_position(raw["position"]),
    )


def load_signals_document(path: Path | str = DEFAULT_SIGNALS_PATH) -> SignalsDocument:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    layout = _parse_layout(raw["layout"])
    signals = tuple(_parse_signal(item) for item in raw["signals"])
    return SignalsDocument(layout=layout, signals=signals)


def _importance_rank(signal: SignalItem) -> int:
    mapping = {
        "current": 4,
        "primary": 3,
        "secondary": 2,
        "archived": 1,
    }
    return mapping.get(signal.importance, 2)


def _state_rank(signal: SignalItem) -> int:
    mapping = {
        "UNRESOLVED": 1,
        "DETECTED": 2,
        "RESOLVING": 3,
        "RESOLVED": 4,
    }
    return mapping.get(signal.state, 2)


def _tone(theme: Theme, category: str) -> str:
    palette = {
        "BUILD": theme.accent_violet,
        "SYSTEM": theme.accent_cyan,
        "MOBILE": theme.success_green,
        "BACKEND": theme.warning_amber,
        "INTERFACE": theme.accent_lavender,
        "DATA": theme.text_secondary,
        "LEARNING": theme.text_muted,
    }
    return palette.get(category, theme.text_secondary)


def _leader_anchor(signal: SignalItem, field: Rect) -> str:
    return "end" if signal.position.x > field.x + field.width * 0.58 else "start"


def _signal_paths(signal: SignalItem, layout: SignalsLayout) -> list[list[tuple[float, float]]]:
    field = layout.field
    x = float(signal.position.x)
    y = float(signal.position.y)
    state_rank = _state_rank(signal)
    importance = _importance_rank(signal)
    left = field.x + 16
    right = field.x + field.width - 16
    top = field.y + 18
    bottom = field.y + field.height - 18
    spread = 20 + importance * 6
    pull = 34 + state_rank * 10
    mid_x = x - pull if x < field.x + field.width * 0.5 else x + pull
    mid_y = y - spread * 0.35
    paths: list[list[tuple[float, float]]] = []
    if signal.state == "UNRESOLVED":
        paths.append([(left if x < field.x + field.width * 0.5 else right, y - 26), (mid_x, mid_y), (x - 12 if x < field.x + field.width * 0.5 else x + 12, y - 4)])
        paths.append([(x - 64 if x < field.x + field.width * 0.5 else x + 64, top + 24), (mid_x, y - 16), (x, y)])
    elif signal.state == "DETECTED":
        paths.append([(left if x < field.x + field.width * 0.5 else right, y - 28), (mid_x, mid_y), (x, y)])
        paths.append([(x - 48 if x < field.x + field.width * 0.5 else x + 48, top + 26), (x - 18 if x < field.x + field.width * 0.5 else x + 18, y - 14), (x, y)])
    elif signal.state == "RESOLVING":
        paths.append([(left if x < field.x + field.width * 0.5 else right, y - 30), (mid_x, mid_y), (x - 16 if x < field.x + field.width * 0.5 else x + 16, y - 10), (x, y)])
        paths.append([(x - 56 if x < field.x + field.width * 0.5 else x + 56, bottom - 44), (x - 22 if x < field.x + field.width * 0.5 else x + 22, y + 18), (x, y)])
        paths.append([(x - 84 if x < field.x + field.width * 0.5 else x + 84, top + 42), (x - 34 if x < field.x + field.width * 0.5 else x + 34, y - 24), (x, y)])
    else:
        paths.append([(left if x < field.x + field.width * 0.5 else right, y - 34), (mid_x, mid_y), (x - 20 if x < field.x + field.width * 0.5 else x + 20, y - 14), (x, y)])
        paths.append([(x - 64 if x < field.x + field.width * 0.5 else x + 64, bottom - 28), (x - 26 if x < field.x + field.width * 0.5 else x + 26, y + 18), (x, y)])
        paths.append([(x - 110 if x < field.x + field.width * 0.5 else x + 110, top + 34), (x - 38 if x < field.x + field.width * 0.5 else x + 38, y - 24), (x, y)])
    return paths


def _signal_group(
    theme: Theme,
    signal: SignalItem,
    layout: SignalsLayout,
    typography: dict[str, dict[str, float]],
    motion: MotionTokens,
    delay_ms: int,
) -> str:
    small = typography["small"]
    caption = typography["caption"]
    heading = typography["heading"]
    section = typography["section"]
    rank = _importance_rank(signal)
    state_rank = _state_rank(signal)
    color = _tone(theme, signal.category)
    x = float(signal.position.x)
    y = float(signal.position.y)
    anchor = _leader_anchor(signal, layout.field)
    label_x = x - 18 if anchor == "end" else x + 18
    label_anchor = "end" if anchor == "end" else "start"
    state_text = signal.state.replace("_", " ")
    paths = _signal_paths(signal, layout)
    path_parts: list[str] = []
    for index, points in enumerate(paths):
        if len(points) < 2:
            continue
        opacity = {
            1: 0.18,
            2: 0.26,
            3: 0.34,
            4: 0.42,
        }.get(state_rank, 0.24)
        stroke = 1.0 + rank * 0.22 + state_rank * 0.16
        dash = {
            1: "3 9",
            2: "5 7",
            3: "none",
            4: "none",
        }.get(state_rank, "none")
        dash_attr = f' stroke-dasharray="{dash}"' if dash != "none" else ""
        path_d = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in points)
        path_parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="{stroke:.2f}" stroke-linecap="round" stroke-linejoin="round" stroke-opacity="{opacity:.2f}"{dash_attr}/>')
        for frag_index, (fx, fy) in enumerate(points[1:-1], start=1):
            frag_opacity = max(0.10, opacity * 0.92 - frag_index * 0.04)
            frag_radius = max(0.85, 1.16 + rank * 0.14 - frag_index * 0.05)
            path_parts.append(f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{frag_radius:.2f}" fill="{color}" opacity="{frag_opacity:.2f}"/>')
    marker_radius = 2.0 + rank * 0.62 + state_rank * 0.24
    core_radius = max(1.0, marker_radius * 0.42)
    marker_opacity = 0.58 + state_rank * 0.07
    if signal.state == "UNRESOLVED":
        marker_opacity = 0.30
    label_size = 18 if state_rank >= 4 else 15 if state_rank == 3 else 13
    label_weight = int(heading["weight"] if state_rank >= 4 else section["weight"])
    evidence = " · ".join(item.path for item in signal.evidence)
    evidence_y = y + 27
    label_y = y - 2
    state_y = y + 14
    pieces = [
        f'<g opacity="1">',
        f'<animate attributeName="opacity" from="0" to="1" dur="{_seconds(motion.assemble)}" begin="{_seconds(delay_ms)}" fill="freeze" calcMode="spline" keySplines="0.42 0 0.58 1"/>',
        f'<animateTransform attributeName="transform" type="translate" from="0 4" to="0 0" dur="{_seconds(motion.assemble)}" begin="{_seconds(delay_ms)}" fill="freeze" calcMode="spline" keySplines="0.42 0 0.58 1"/>',
        f'<line x1="{x}" y1="{y}" x2="{label_x}" y2="{y - 12 if state_rank >= 3 else y - 8}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="{0.10 + rank * 0.04:.2f}"/>',
        *path_parts,
        f'<circle cx="{x}" cy="{y}" r="{marker_radius:.2f}" fill="{color}" opacity="{marker_opacity:.2f}"/>',
        f'<circle cx="{x}" cy="{y}" r="{core_radius:.2f}" fill="{theme.background}" opacity="0.90"/>',
    ]
    if signal.state != "UNRESOLVED":
        pieces.append(_text(theme, label_x, label_y, label_size, theme.text_primary, signal.label, label_weight, anchor=label_anchor, tracking=0.3))
    pieces.append(_text(theme, label_x, state_y, int(small["size"]), theme.text_secondary, state_text, int(small["weight"]), anchor=label_anchor, tracking=0.18))
    if signal.state != "UNRESOLVED":
        pieces.append(_text(theme, label_x, evidence_y, int(caption["size"]), theme.text_muted, evidence, int(caption["weight"]), anchor=label_anchor, tracking=0.08))
    else:
        pieces.append(_text(theme, label_x, evidence_y, int(caption["size"]), theme.text_muted, evidence, int(caption["weight"]), anchor=label_anchor, tracking=0.08))
    if signal.state == "RESOLVED":
        pieces.append(f'<circle cx="{x}" cy="{y}" r="{marker_radius + 4.0:.2f}" fill="none" stroke="{color}" stroke-width="1" stroke-opacity="0.16"/>')
    pieces.append("</g>")
    return _reveal_group("".join(pieces), delay_ms=delay_ms, duration_ms=motion.assemble, dy=4)


def render_signals(mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_SIGNALS_PATH) -> SignalsRender:
    bundle = tokens or load_tokens()
    theme = resolve_theme(mode, bundle)
    motion = resolve_motion(bundle)
    document = load_signals_document(config_path)
    layout = document.layout
    typography = bundle.typography_scale
    signal_order = sorted(document.signals, key=lambda item: (_state_rank(item), -_importance_rank(item), item.position.x))
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{layout.canvas_width}" height="{layout.canvas_height}" viewBox="0 0 {layout.canvas_width} {layout.canvas_height}" role="img" aria-labelledby="title desc">',
        '<title id="title">KalaOS signals</title>',
        '<desc id="desc">Signal acquisition field for KalaOS showing unresolved traces, detected capability, resolving structure, and resolved evidence-backed signals.</desc>',
        "<defs>",
        build_primitive_defs(mode, bundle),
        f'<clipPath id="kalaos-signals-field"><rect x="{layout.field.x}" y="{layout.field.y}" width="{layout.field.width}" height="{layout.field.height}" rx="{layout.field.radius}"/></clipPath>',
        "</defs>",
        f'<rect width="{layout.canvas_width}" height="{layout.canvas_height}" fill="{theme.background}"/>',
        render_background_grid(theme, bundle, opacity=0.10),
        f'<rect x="{layout.frame.x}" y="{layout.frame.y}" width="{layout.frame.width}" height="{layout.frame.height}" rx="{layout.frame.radius}" fill="none" stroke="{theme.border_panel}" stroke-width="{bundle.stroke_widths["standard"]}"/>',
        _text(theme, layout.header_state_x, layout.header_state_y, int(typography["caption"]["size"]), theme.text_secondary, "EVIDENCE / RESOLVING", int(typography["caption"]["weight"]), tracking=1.8),
        _text(theme, layout.header_title_x, layout.header_title_y, int(typography["display_xl"]["size"]), theme.text_primary, "SIGNALS", int(typography["display_xl"]["weight"]), tracking=1.1),
        _text(theme, layout.header_subtitle_x, layout.header_subtitle_y, int(typography["small"]["size"]), theme.text_muted, "Capabilities detected from local evidence, not claimed.", int(typography["small"]["weight"]), tracking=0.2),
        f'<line x1="{layout.header_title_x}" y1="{layout.header_subtitle_y + 12}" x2="{layout.header_title_x + 540}" y2="{layout.header_subtitle_y + 12}" stroke="{theme.border_hairline}" stroke-width="1"/>',
        f'<rect x="{layout.field.x}" y="{layout.field.y}" width="{layout.field.width}" height="{layout.field.height}" rx="{layout.field.radius}" fill="none" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.44"/>',
    ]
    for index, signal in enumerate(signal_order):
        delay = motion.assemble + _state_rank(signal) * 120 + index * 220
        if signal.state == "UNRESOLVED":
            delay += motion.normal + motion.fast
        parts.append(
            _signal_group(
                theme,
                signal,
                layout,
                typography,
                motion,
                delay_ms=delay,
            )
        )
    parts.append(
        _reveal_group(
            (
                f'<text x="{layout.field.x}" y="{layout.field.y + layout.field.height + 30}" font-size="{int(typography["caption"]["size"])}" font-weight="{int(typography["caption"]["weight"])}" letter-spacing="0.14" fill="{theme.text_muted}">Evidence comes from locked stage documents, source snapshots, and the shared engine pipeline.</text>'
            ),
            delay_ms=motion.assemble * 4 + motion.slow,
            duration_ms=motion.assemble,
            dy=4,
        )
    )
    parts.append("</svg>")
    return SignalsRender(svg="".join(parts), theme_mode=mode)


def write_signals(path: Path, mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_SIGNALS_PATH) -> Path:
    signals = render_signals(mode=mode, tokens=tokens, config_path=config_path)
    path.write_text(signals.svg, encoding="utf-8")
    return path
