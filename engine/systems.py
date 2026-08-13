from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .motion import MotionTokens, resolve_motion
from .svg_primitives import build_primitive_defs, render_background_grid
from .theme import Theme, resolve_theme
from .tokens import TokenBundle, load_tokens


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYSTEMS_PATH = ROOT / "assets" / "source" / "kalaos.systems.json"


@dataclass(frozen=True)
class SystemLabel:
    dx: int
    dy: int
    anchor: str


@dataclass(frozen=True)
class SystemPosition:
    x: int
    y: int


@dataclass(frozen=True)
class SystemNode:
    id: str
    name: str
    domain: str
    description: str
    technologies: tuple[str, ...]
    state: str
    importance: str
    position: SystemPosition
    label: SystemLabel


@dataclass(frozen=True)
class SystemRelation:
    source: str
    target: str
    kind: str
    label: str


@dataclass(frozen=True)
class SystemsLayout:
    canvas_width: int
    canvas_height: int
    frame_x: int
    frame_y: int
    frame_width: int
    frame_height: int
    frame_radius: int
    field_x: int
    field_y: int
    field_width: int
    field_height: int
    state_x: int
    state_y: int
    title_x: int
    title_y: int
    subtitle_x: int
    subtitle_y: int


@dataclass(frozen=True)
class SystemsDocument:
    layout: SystemsLayout
    nodes: tuple[SystemNode, ...]
    relations: tuple[SystemRelation, ...]


@dataclass(frozen=True)
class SystemsRender:
    svg: str
    theme_mode: str


def _seconds(ms: int) -> str:
    return f"{ms / 1000:.2f}s"


def _parse_label(raw: dict[str, object]) -> SystemLabel:
    return SystemLabel(
        dx=int(raw["dx"]),
        dy=int(raw["dy"]),
        anchor=str(raw["anchor"]),
    )


def _parse_position(raw: dict[str, object]) -> SystemPosition:
    return SystemPosition(x=int(raw["x"]), y=int(raw["y"]))


def _parse_node(raw: dict[str, object]) -> SystemNode:
    return SystemNode(
        id=str(raw["id"]),
        name=str(raw["name"]),
        domain=str(raw["domain"]),
        description=str(raw["description"]),
        technologies=tuple(str(value) for value in raw.get("technologies", ())),
        state=str(raw["state"]),
        importance=str(raw["importance"]),
        position=_parse_position(raw["position"]),
        label=_parse_label(raw["label"]),
    )


def _parse_relation(raw: dict[str, object]) -> SystemRelation:
    return SystemRelation(
        source=str(raw["source"]),
        target=str(raw["target"]),
        kind=str(raw["kind"]),
        label=str(raw["label"]),
    )


def _parse_layout(raw: dict[str, object]) -> SystemsLayout:
    canvas = raw["canvas"]
    frame = raw["frame"]
    field = raw["field"]
    header = raw["header"]
    return SystemsLayout(
        canvas_width=int(canvas["width"]),
        canvas_height=int(canvas["height"]),
        frame_x=int(frame["x"]),
        frame_y=int(frame["y"]),
        frame_width=int(frame["width"]),
        frame_height=int(frame["height"]),
        frame_radius=int(frame["radius"]),
        field_x=int(field["x"]),
        field_y=int(field["y"]),
        field_width=int(field["width"]),
        field_height=int(field["height"]),
        state_x=int(header["state_x"]),
        state_y=int(header["state_y"]),
        title_x=int(header["title_x"]),
        title_y=int(header["title_y"]),
        subtitle_x=int(header["subtitle_x"]),
        subtitle_y=int(header["subtitle_y"]),
    )


def load_systems_document(path: Path | str = DEFAULT_SYSTEMS_PATH) -> SystemsDocument:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    layout = _parse_layout(raw["layout"])
    nodes = tuple(_parse_node(node) for node in raw["systems"])
    relations = tuple(_parse_relation(relation) for relation in raw["relationships"])
    return SystemsDocument(layout=layout, nodes=nodes, relations=relations)


def _text(theme: Theme, x: float, y: float, size: int, fill: str, text: str, weight: int = 400, anchor: str = "start", tracking: float = 0.0) -> str:
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


def _importance_rank(node: SystemNode) -> int:
    mapping = {
        "primary": 4,
        "secondary": 3,
        "experiment": 2,
        "archived": 1,
    }
    return mapping.get(node.importance, 2)


def _domain_color(theme: Theme, domain: str) -> str:
    palette = {
        "EDUCATION": theme.accent_lavender,
        "COMMERCE": theme.accent_cyan,
        "MOBILE": theme.accent_violet,
    }
    return palette.get(domain, theme.text_secondary)


def _node_radius(node: SystemNode) -> float:
    return {4: 12.5, 3: 10.5, 2: 8.8, 1: 7.4}[_importance_rank(node)]


def _node_mark(theme: Theme, node: SystemNode) -> str:
    rank = _importance_rank(node)
    color = _domain_color(theme, node.domain)
    x = node.position.x
    y = node.position.y
    radius = _node_radius(node)
    field = radius * (2.2 if rank >= 4 else 2.0 if rank == 3 else 1.8)
    bracket = 5.5 + rank * 0.9
    half = field
    state_fill = theme.success_green if node.state == "ACTIVE" else theme.text_muted
    if node.state == "BUILDING":
        state_fill = theme.accent_cyan
    elif node.state == "LEGACY":
        state_fill = theme.text_muted
    return (
        f'<g opacity="1">'
        f'<rect x="{x - half}" y="{y - half}" width="{half * 2}" height="{half * 2}" fill="none" stroke="{color}" stroke-width="1" stroke-opacity="{0.16 + rank * 0.05:.2f}"/>'
        f'<path d="M {x - half} {y - half + bracket} V {y - half} H {x - half + bracket}" fill="none" stroke="{theme.border_hairline}" stroke-width="1.2" stroke-linecap="round" stroke-opacity="{0.34 + rank * 0.07:.2f}"/>'
        f'<path d="M {x + half - bracket} {y - half} H {x + half} V {y - half + bracket}" fill="none" stroke="{theme.border_hairline}" stroke-width="1.2" stroke-linecap="round" stroke-opacity="{0.34 + rank * 0.07:.2f}"/>'
        f'<path d="M {x - half} {y + half - bracket} V {y + half} H {x - half + bracket}" fill="none" stroke="{theme.border_hairline}" stroke-width="1.2" stroke-linecap="round" stroke-opacity="{0.28 + rank * 0.06:.2f}"/>'
        f'<path d="M {x + half - bracket} {y + half} H {x + half} V {y + half - bracket}" fill="none" stroke="{theme.border_hairline}" stroke-width="1.2" stroke-linecap="round" stroke-opacity="{0.28 + rank * 0.06:.2f}"/>'
        f'<circle cx="{x}" cy="{y}" r="{radius * (0.95 if rank >= 3 else 0.9)}" fill="{state_fill}" opacity="{0.88 if rank >= 3 else 0.78}"/>'
        f'<circle cx="{x}" cy="{y}" r="{max(1.4, radius * 0.22)}" fill="{theme.background}" opacity="0.88"/>'
        f'</g>'
    )


def _node_group(theme: Theme, node: SystemNode, typography: dict[str, dict[str, float]], motion: MotionTokens, delay_ms: int) -> str:
    display = typography["display"]
    section = typography["section"]
    small = typography["small"]
    caption = typography["caption"]
    rank = _importance_rank(node)
    x = node.position.x
    y = node.position.y
    lx = x + node.label.dx
    ly = y + node.label.dy
    label_anchor = node.label.anchor
    leader_x = lx - 10 if label_anchor == "start" else lx + 10
    leader_y = ly - 10
    lead_brightness = 0.10 + rank * 0.06
    name_size = 18 if rank >= 4 else 15 if rank == 3 else 13
    name_weight = int(display["weight"] if rank >= 4 else section["weight"])
    pieces = [
        f'<g opacity="1">',
        f'<animate attributeName="opacity" from="0" to="1" dur="{_seconds(motion.reveal)}" begin="{_seconds(delay_ms)}" fill="freeze" calcMode="spline" keySplines="0.42 0 0.58 1"/>',
        f'<animateTransform attributeName="transform" type="translate" from="0 5" to="0 0" dur="{_seconds(motion.reveal)}" begin="{_seconds(delay_ms)}" fill="freeze" calcMode="spline" keySplines="0.42 0 0.58 1"/>',
        f'<line x1="{x}" y1="{y}" x2="{leader_x}" y2="{leader_y}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="{lead_brightness:.2f}"/>',
        _node_mark(theme, node),
        _text(theme, lx, ly, name_size, theme.text_primary, node.name, name_weight, anchor=label_anchor, tracking=0.25),
        _text(theme, lx, ly + 16, int(small["size"]), theme.text_secondary, f'{node.domain} / {node.state}', int(small["weight"]), anchor=label_anchor, tracking=0.18),
    ]
    if rank >= 4:
        pieces.append(_text(theme, lx, ly + 30, int(small["size"]), theme.text_muted, " / ".join(node.technologies), int(small["weight"]), anchor=label_anchor, tracking=0.08))
        pieces.append(_text(theme, lx, ly + 44, int(caption["size"]), theme.text_muted, node.description, int(caption["weight"]), anchor=label_anchor, tracking=0.16))
    elif rank >= 3:
        pieces.append(_text(theme, lx, ly + 30, int(caption["size"]), theme.text_muted, " / ".join(node.technologies), int(caption["weight"]), anchor=label_anchor, tracking=0.08))
    elif node.description:
        pieces.append(_text(theme, lx, ly + 30, int(caption["size"]), theme.text_muted, node.description, int(caption["weight"]), anchor=label_anchor, tracking=0.12))
    pieces.append("</g>")
    return "".join(pieces)


def _relation_style(theme: Theme, kind: str) -> tuple[str, float, str]:
    styles = {
        "continuation": (theme.accent_violet, 1.25, "5 7"),
        "dependency": (theme.accent_cyan, 1.2, "none"),
        "shared_domain": (theme.warning_amber, 1.15, "3 7"),
    }
    return styles.get(kind, (theme.border_hairline, 1.2, "none"))


def _relation_path(source: SystemNode, target: SystemNode, relation: SystemRelation) -> tuple[str, float, float]:
    x1 = source.position.x
    y1 = source.position.y
    x2 = target.position.x
    y2 = target.position.y
    if relation.kind == "dependency":
        bend_y = y1 + (y2 - y1) * 0.35
        return (
            f'M {x1} {y1} V {bend_y:.1f} H {x2} V {y2}',
            (x1 + x2) / 2.0,
            bend_y - 12,
        )
    if relation.kind == "shared_domain":
        bend_x = x1 + (x2 - x1) * 0.34
        bend_y = y1 + (y2 - y1) * 0.58
        return (
            f'M {x1} {y1} H {bend_x:.1f} V {bend_y:.1f} H {x2}',
            bend_x + 2,
            bend_y - 12,
        )
    bend_x = x1 + (x2 - x1) * 0.46
    bend_y = y1 + (y2 - y1) * 0.28
    return (
        f'M {x1} {y1} H {bend_x:.1f} V {bend_y:.1f} H {x2}',
        bend_x,
        bend_y - 12,
    )


def _relation_group(theme: Theme, source: SystemNode, target: SystemNode, relation: SystemRelation, typography: dict[str, dict[str, float]], motion: MotionTokens, delay_ms: int) -> str:
    caption = typography["caption"]
    color, width, dash = _relation_style(theme, relation.kind)
    path_d, label_x, label_y = _relation_path(source, target, relation)
    label_anchor = "start" if relation.kind == "continuation" else "middle"
    dash_attr = f' stroke-dasharray="{dash}"' if dash != "none" else ""
    return (
        '<g opacity="1">'
        f'<animate attributeName="opacity" from="0" to="1" dur="{_seconds(motion.normal)}" begin="{_seconds(delay_ms)}" fill="freeze" calcMode="spline" keySplines="0.42 0 0.58 1"/>'
        f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-opacity="0.42"{dash_attr}/>'
        f'<text x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="{label_anchor}" font-size="{max(9, int(caption["size"]) - 2)}" font-weight="{caption["weight"]}" letter-spacing="0.55" fill="{theme.text_muted}" opacity="0.62">{relation.label.upper()}</text>'
        "</g>"
    )


def render_systems(mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_SYSTEMS_PATH) -> SystemsRender:
    bundle = tokens or load_tokens()
    theme = resolve_theme(mode, bundle)
    motion = resolve_motion(bundle)
    document = load_systems_document(config_path)
    layout = document.layout
    typography = bundle.typography_scale
    nodes_by_id = {node.id: node for node in document.nodes}

    ordered_nodes = sorted(document.nodes, key=lambda node: (-_importance_rank(node), node.position.x, node.position.y))
    primary_nodes = [node for node in ordered_nodes if _importance_rank(node) >= 4]
    secondary_nodes = [node for node in ordered_nodes if _importance_rank(node) == 3]
    minor_nodes = [node for node in ordered_nodes if _importance_rank(node) <= 2]

    header = (
        _text(theme, layout.state_x, layout.state_y, int(typography["caption"]["size"]), theme.text_secondary, "DISCOVERY", int(typography["caption"]["weight"]), tracking=1.8)
        + _text(theme, layout.title_x, layout.title_y, int(typography["display_xl"]["size"]), theme.text_primary, "CHARTED SYSTEMS", int(typography["display_xl"]["weight"]), tracking=1.3)
        + _text(theme, layout.subtitle_x, layout.subtitle_y, int(typography["small"]["size"]), theme.text_muted, "Worlds mapped and built.", int(typography["small"]["weight"]), tracking=0.2)
        + f'<line x1="{layout.title_x}" y1="{layout.subtitle_y + 12}" x2="{layout.title_x + 420}" y2="{layout.subtitle_y + 12}" stroke="{theme.border_hairline}" stroke-width="1"/>'
    )

    guide_lines = (
        f'<line x1="{layout.field_x + layout.field_width * 0.52:.0f}" y1="{layout.field_y}" x2="{layout.field_x + layout.field_width * 0.52:.0f}" y2="{layout.field_y + layout.field_height}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.14"/>'
        f'<line x1="{layout.field_x}" y1="{layout.field_y + layout.field_height * 0.52:.0f}" x2="{layout.field_x + layout.field_width}" y2="{layout.field_y + layout.field_height * 0.52:.0f}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.10"/>'
    )

    relation_delay = motion.reveal + motion.normal
    relation_groups: list[str] = []
    for index, relation in enumerate(document.relations):
        source = nodes_by_id.get(relation.source)
        target = nodes_by_id.get(relation.target)
        if not source or not target:
            continue
        relation_groups.append(_relation_group(theme, source, target, relation, typography, motion, relation_delay + index * 90))

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{layout.canvas_width}" height="{layout.canvas_height}" viewBox="0 0 {layout.canvas_width} {layout.canvas_height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">KalaOS charted systems</title>',
        f'<desc id="desc">Discovery layer for KalaOS mapping built systems as a structured coordinate field.</desc>',
        "<defs>",
        build_primitive_defs(mode, bundle),
        f'<clipPath id="kalaos-systems-field"><rect x="{layout.field_x}" y="{layout.field_y}" width="{layout.field_width}" height="{layout.field_height}"/></clipPath>',
        "</defs>",
        f'<rect width="{layout.canvas_width}" height="{layout.canvas_height}" fill="{theme.background}"/>',
        render_background_grid(theme, bundle, opacity=0.11),
        f'<rect x="{layout.frame_x}" y="{layout.frame_y}" width="{layout.frame_width}" height="{layout.frame_height}" rx="{layout.frame_radius}" fill="none" stroke="{theme.border_panel}" stroke-width="{bundle.stroke_widths["standard"]}"/>',
        _reveal_group(header, delay_ms=motion.fast, duration_ms=motion.reveal, dy=4),
        f'<g clip-path="url(#kalaos-systems-field)">{guide_lines}',
    ]

    for index, node in enumerate(primary_nodes):
        parts.append(_node_group(theme, node, typography, motion, delay_ms=motion.reveal + index * 120))
    for index, node in enumerate(secondary_nodes):
        parts.append(_node_group(theme, node, typography, motion, delay_ms=motion.reveal + motion.normal + index * 110))
    for index, node in enumerate(minor_nodes):
        parts.append(_node_group(theme, node, typography, motion, delay_ms=motion.reveal + motion.slow + index * 90))
    for group in relation_groups:
        parts.append(group)

    parts.append("</g>")
    parts.append("</svg>")
    return SystemsRender(svg="".join(parts), theme_mode=mode)


def write_systems(path: Path, mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_SYSTEMS_PATH) -> Path:
    systems = render_systems(mode=mode, tokens=tokens, config_path=config_path)
    path.write_text(systems.svg, encoding="utf-8")
    return path
