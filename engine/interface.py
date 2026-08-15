from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .layout import Rect, resolve_hero_layout
from .motion import MotionTokens, resolve_motion
from .svg_primitives import build_primitive_defs, render_background_grid
from .theme import Theme, resolve_theme
from .tokens import TokenBundle, load_tokens


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INTERFACE_PATH = ROOT / "assets" / "source" / "kalaos.interface.json"


@dataclass(frozen=True)
class InterfaceVector:
    name: str
    initial_state: str
    action: str
    resolution_state: str
    visitor_sees: str
    system_prepares: str
    unresolved_until_handoff: str


@dataclass(frozen=True)
class InterfaceDocument:
    stage: int
    name: str
    purpose: str
    role: str
    question: str
    relationship_to_signals: str
    relationship_to_handoff: str
    interaction_philosophy: tuple[str, ...]
    core_vectors: tuple[InterfaceVector, ...]
    state_model: tuple[str, ...]
    constraints: tuple[str, ...]
    readiness_criteria: tuple[str, ...]


@dataclass(frozen=True)
class InterfaceRender:
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


def _parse_vector(raw: dict[str, object]) -> InterfaceVector:
    return InterfaceVector(
        name=str(raw["name"]),
        initial_state=str(raw["initial_state"]),
        action=str(raw["action"]),
        resolution_state=str(raw["resolution_state"]),
        visitor_sees=str(raw["visitor_sees"]),
        system_prepares=str(raw["system_prepares"]),
        unresolved_until_handoff=str(raw["unresolved_until_handoff"]),
    )


def load_interface_document(path: Path | str = DEFAULT_INTERFACE_PATH) -> InterfaceDocument:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return InterfaceDocument(
        stage=int(raw["stage"]),
        name=str(raw["name"]),
        purpose=str(raw["purpose"]),
        role=str(raw["role"]),
        question=str(raw["question"]),
        relationship_to_signals=str(raw["relationship_to_signals"]),
        relationship_to_handoff=str(raw["relationship_to_handoff"]),
        interaction_philosophy=tuple(str(value) for value in raw["interaction_philosophy"]),
        core_vectors=tuple(_parse_vector(value) for value in raw["core_vectors"]),
        state_model=tuple(str(value) for value in raw["state_model"]),
        constraints=tuple(str(value) for value in raw["constraints"]),
        readiness_criteria=tuple(str(value) for value in raw["readiness_criteria"]),
    )


def _multi_line_text(
    theme: Theme,
    x: float,
    y: float,
    lines: tuple[str, ...],
    size: int,
    fill: str,
    weight: int = 400,
    tracking: float = 0.0,
    line_step: int = 18,
) -> str:
    parts: list[str] = []
    for index, line in enumerate(lines):
        parts.append(_text(theme, x, y + index * line_step, size, fill, line, weight=weight, tracking=tracking))
    return "".join(parts)


def _state_strip(theme: Theme, width: int) -> str:
    labels = [
        ("RESOLVED", 72, theme.text_secondary),
        ("SELECT ACTION", 348, theme.accent_cyan),
        ("PREPARE STATE", 576, theme.text_secondary),
        ("BOUNDARY", 840, theme.text_secondary),
    ]
    parts = [
        f'<line x1="72" y1="134" x2="{width - 72}" y2="134" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.48"/>'
    ]
    for label, x, fill in labels:
        parts.append(_text(theme, x, 128, 12, fill, label, 400, tracking=1.1))
    parts.append(f'<rect x="322" y="134" width="112" height="2" fill="{theme.accent_cyan}"/>')
    return "".join(parts)


def _explore_diagram(theme: Theme, x: int, y: int) -> str:
    return (
        f'<g id="interface-explore-diagram">'
        f'<rect x="{x}" y="{y}" width="388" height="74" rx="14" fill="none" stroke="{theme.border_hairline}" stroke-width="1"/>'
        f'<rect x="{x + 16}" y="{y + 10}" width="356" height="54" rx="12" fill="none" stroke="{theme.accent_violet}" stroke-width="1.5" opacity="0.78"/>'
        f'<rect x="{x + 32}" y="{y + 18}" width="324" height="38" rx="10" fill="none" stroke="{theme.accent_cyan}" stroke-width="1.25" opacity="0.75"/>'
        f'<line x1="{x + 12}" y1="{y + 37}" x2="{x + 148}" y2="{y + 37}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.36"/>'
        f'<circle cx="{x + 212}" cy="{y + 37}" r="4.8" fill="{theme.accent_lavender}" opacity="0.92"/>'
        f'<circle cx="{x + 212}" cy="{y + 37}" r="13" fill="none" stroke="{theme.accent_violet}" stroke-width="1" stroke-opacity="0.20"/>'
        f'<text x="{x + 248}" y="{y + 42}" font-size="10" letter-spacing="1.4" fill="{theme.text_muted}">DEEPER SURFACES</text>'
        "</g>"
    )


def _trace_diagram(theme: Theme, x: int, y: int) -> str:
    points = [
        (x + 18, y + 49, "SYS"),
        (x + 110, y + 31, "TEL"),
        (x + 202, y + 43, "CHR"),
        (x + 302, y + 21, "SRC"),
    ]
    path = "M " + " L ".join(f"{px} {py}" for px, py, _ in points)
    parts = [
        f'<g id="interface-trace-diagram">',
        f'<rect x="{x}" y="{y}" width="388" height="74" rx="14" fill="none" stroke="{theme.border_hairline}" stroke-width="1"/>',
        f'<path d="{path}" fill="none" stroke="{theme.accent_cyan}" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round" stroke-opacity="0.56"/>',
        f'<path d="M {x + 18} {y + 49} L {x + 110} {y + 31} L {x + 202} {y + 43} L {x + 302} {y + 21}" fill="none" stroke="{theme.border_hairline}" stroke-width="1" stroke-dasharray="3 8" stroke-linecap="round" stroke-opacity="0.34"/>',
    ]
    for px, py, label in points:
        parts.append(f'<circle cx="{px}" cy="{py}" r="4.6" fill="{theme.accent_lavender}" opacity="0.92"/>')
        parts.append(f'<circle cx="{px}" cy="{py}" r="11.5" fill="none" stroke="{theme.accent_violet}" stroke-width="1" stroke-opacity="0.18"/>')
        parts.append(_text(theme, px, py + 18, 10, theme.text_muted, label, 400, anchor="middle", tracking=1.1))
    parts.append(f'<text x="{x + 250}" y="{y + 43}" font-size="10" letter-spacing="1.4" fill="{theme.text_muted}">PROVENANCE PATH</text>')
    parts.append("</g>")
    return "".join(parts)


def _converse_diagram(theme: Theme, x: int, y: int) -> str:
    return (
        f'<g id="interface-converse-diagram">'
        f'<rect x="{x}" y="{y}" width="388" height="74" rx="14" fill="none" stroke="{theme.border_hairline}" stroke-width="1"/>'
        f'<path d="M {x + 42} {y + 18} H {x + 146} V {y + 56} H {x + 42}" fill="none" stroke="{theme.warning_amber}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" stroke-opacity="0.74"/>'
        f'<path d="M {x + 346} {y + 18} H {x + 242} V {y + 56} H {x + 346}" fill="none" stroke="{theme.success_green}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" stroke-opacity="0.74"/>'
        f'<line x1="{x + 146}" y1="{y + 37}" x2="{x + 242}" y2="{y + 37}" stroke="{theme.accent_lavender}" stroke-width="1.2" stroke-opacity="0.52"/>'
        f'<circle cx="{x + 194}" cy="{y + 37}" r="4.6" fill="{theme.accent_cyan}" opacity="0.9"/>'
        f'<circle cx="{x + 194}" cy="{y + 37}" r="12.5" fill="none" stroke="{theme.accent_cyan}" stroke-width="1" stroke-opacity="0.20"/>'
        f'<text x="{x + 178}" y="{y + 70}" text-anchor="middle" font-size="10" letter-spacing="1.4" fill="{theme.text_muted}">BOUNDARY PREPARED</text>'
        "</g>"
    )


def _vector_copy(name: str) -> tuple[str, str]:
    mapping = {
        "EXPLORE": (
            "open deeper internal surfaces",
            "deeper inspection state prepared",
        ),
        "TRACE": (
            "follow evidence and provenance",
            "causal evidence path prepared",
        ),
        "CONVERSE": (
            "open a communication boundary",
            "orientation prepared; transfer withheld",
        ),
    }
    return mapping[name]


def _vector_lanes(theme: Theme, document: InterfaceDocument, layout: Rect, typography: dict[str, dict[str, float]], motion: MotionTokens) -> str:
    section = typography["section"]
    body = typography["body"]
    small = typography["small"]
    lanes = []
    row_tops = [176, 298, 420]
    diagram_x = 620
    for index, vector in enumerate(document.core_vectors):
        y = row_tops[index]
        lane_theme = [
            (theme.accent_violet, theme.accent_lavender),
            (theme.accent_cyan, theme.text_primary),
            (theme.warning_amber, theme.success_green),
        ][index]
        action_copy, prepare_copy = _vector_copy(vector.name)
        diagram = [
            _explore_diagram,
            _trace_diagram,
            _converse_diagram,
        ][index](theme, diagram_x, y + 6)
        content = "".join(
            [
                f'<line x1="72" y1="{y + 90}" x2="{layout.width - 72}" y2="{y + 90}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.34"/>',
                f'<rect x="72" y="{y + 2}" width="4" height="78" fill="{lane_theme[0]}"/>',
                _text(theme, 96, y + 18, int(section["size"]), lane_theme[0], vector.name, int(section["weight"]), tracking=0.8),
                _text(theme, 96, y + 38, int(small["size"]), theme.text_secondary, vector.initial_state, int(small["weight"]), tracking=0.8),
                _text(theme, 96, y + 58, int(body["size"]), theme.text_primary, action_copy, int(body["weight"]), tracking=0.0),
                _text(theme, 96, y + 78, int(small["size"]), theme.text_muted, prepare_copy, int(small["weight"]), tracking=0.4),
                _text(theme, 96, y + 108, int(small["size"]), theme.text_muted, f"LATENT UNTIL HANDOFF: {vector.unresolved_until_handoff}", int(small["weight"]), tracking=0.6),
                _text(theme, 1002, y + 18, int(small["size"]), lane_theme[0], vector.resolution_state, int(small["weight"]), anchor="end", tracking=0.9),
                diagram,
            ]
        )
        lanes.append(
            _reveal_group(
                content,
                delay_ms=motion.assemble * 2 + index * (motion.normal * 5),
                duration_ms=motion.assemble,
                dy=6,
            )
        )
    return "".join(lanes)


def render_interface(mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_INTERFACE_PATH) -> InterfaceRender:
    bundle = tokens or load_tokens()
    theme = resolve_theme(mode, bundle)
    motion = resolve_motion(bundle)
    document = load_interface_document(config_path)
    layout = resolve_hero_layout(bundle)
    frame = layout.frame
    typography = bundle.typography_scale
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{layout.canvas_width}" height="{layout.canvas_height}" viewBox="0 0 {layout.canvas_width} {layout.canvas_height}" role="img" aria-labelledby="title desc">',
        '<title id="title">KalaOS interface</title>',
        f'<desc id="desc">Invocation layer for KalaOS with three resolved action vectors: EXPLORE, TRACE, and CONVERSE.</desc>',
        "<defs>",
        build_primitive_defs(mode, bundle),
        "</defs>",
        f'<rect width="{layout.canvas_width}" height="{layout.canvas_height}" fill="{theme.background}"/>',
        render_background_grid(theme, bundle, opacity=0.10),
        f'<rect x="{frame.x}" y="{frame.y}" width="{frame.width}" height="{frame.height}" rx="{frame.radius}" fill="{theme.panel}" stroke="{theme.border_panel}" stroke-width="{bundle.stroke_widths["standard"]}"/>',
        f'<g id="interface-header">',
        f'<use href="#kalaos-origin-mark" x="{frame.x + 14}" y="{frame.y + 12}" width="40" height="40" opacity="0.92"/>',
        _text(theme, 80, 55, int(typography["caption"]["size"]), theme.text_secondary, "SIGNALS / RESOLVED", int(typography["caption"]["weight"]), tracking=1.8),
        _text(theme, 80, 88, int(typography["display"]["size"]), theme.text_primary, document.name, int(typography["display"]["weight"]), tracking=0.9),
        _text(theme, 80, 114, int(typography["body"]["size"]), theme.text_secondary, document.question, int(typography["body"]["weight"]), tracking=0.0),
        _text(theme, 928, 55, int(typography["caption"]["size"]), theme.text_secondary, "HANDOFF / FUTURE", int(typography["caption"]["weight"]), anchor="end", tracking=1.6),
        _state_strip(theme, layout.canvas_width),
        _text(theme, 930, 88, int(typography["small"]["size"]), theme.text_muted, "INVOCATION LAYER", int(typography["small"]["weight"]), anchor="end", tracking=1.2),
        _text(theme, 930, 110, int(typography["small"]["size"]), theme.text_muted, "SELECTION / ORIENTATION / PREPARATION", int(typography["small"]["weight"]), anchor="end", tracking=0.9),
        "</g>",
        f'<line x1="72" y1="158" x2="{layout.canvas_width - 72}" y2="158" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.42"/>',
        _vector_lanes(theme, document, frame, typography, motion),
        "</svg>",
    ]
    return InterfaceRender(svg="".join(parts), theme_mode=mode)


def write_interface(path: Path, mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_INTERFACE_PATH) -> Path:
    interface = render_interface(mode=mode, tokens=tokens, config_path=config_path)
    path.write_text(interface.svg, encoding="utf-8")
    return path
