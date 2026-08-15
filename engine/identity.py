from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .layout import Rect
from .motion import MotionTokens, resolve_motion
from .portrait import PortraitBox, PortraitSettings, render_portrait_points
from .svg_primitives import build_primitive_defs, render_background_grid
from .theme import Theme, resolve_theme
from .tokens import TokenBundle, load_tokens


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IDENTITY_PATH = ROOT / "assets" / "source" / "kalaos.identity.json"


@dataclass(frozen=True)
class IdentitySubject:
    name: str
    role: str
    origin: str
    domains: tuple[str, ...]


@dataclass(frozen=True)
class IdentityLayout:
    canvas_width: int
    canvas_height: int
    frame: Rect
    portrait: PortraitBox
    metadata_x: int
    metadata_y: int
    metadata_step: int


@dataclass(frozen=True)
class IdentityDocument:
    subject: IdentitySubject
    portrait: PortraitSettings
    layout: IdentityLayout
    state_label: str


@dataclass(frozen=True)
class IdentityRender:
    svg: str
    theme_mode: str


def _seconds(ms: int) -> str:
    return f"{ms / 1000:.2f}s"


def _parse_subject(raw: dict[str, object]) -> IdentitySubject:
    domains = tuple(str(value) for value in raw.get("domains", ()))
    return IdentitySubject(
        name=str(raw["name"]),
        role=str(raw["role"]),
        origin=str(raw["origin"]),
        domains=domains,
    )


def _parse_portrait(path: Path, raw: dict[str, object]) -> PortraitSettings:
    source = Path(str(raw["source"]))
    if not source.is_absolute():
        source = (path.parent / source).resolve()
    palette = tuple(str(value) for value in raw["palette"])
    return PortraitSettings(
        source=source,
        sampling_density=int(raw["sampling_density"]),
        minimum_point_size=float(raw["minimum_point_size"]),
        maximum_point_size=float(raw["maximum_point_size"]),
        luminance_response=float(raw["luminance_response"]),
        contrast=float(raw["contrast"]),
        threshold=float(raw["threshold"]),
        palette=palette,
        background=str(raw["background"]),
    )


def _parse_layout(raw: dict[str, object]) -> IdentityLayout:
    frame = raw["frame"]
    portrait = raw["portrait"]
    metadata = raw["metadata"]
    canvas = raw["canvas"]
    return IdentityLayout(
        canvas_width=int(canvas["width"]),
        canvas_height=int(canvas["height"]),
        frame=Rect(
            x=int(frame["x"]),
            y=int(frame["y"]),
            width=int(frame["width"]),
            height=int(frame["height"]),
            radius=int(frame["radius"]),
        ),
        portrait=PortraitBox(
            x=int(portrait["x"]),
            y=int(portrait["y"]),
            width=int(portrait["width"]),
            height=int(portrait["height"]),
        ),
        metadata_x=int(metadata["x"]),
        metadata_y=int(metadata["y"]),
        metadata_step=int(metadata["step"]),
    )


def load_identity_document(path: Path | str = DEFAULT_IDENTITY_PATH) -> IdentityDocument:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    subject = _parse_subject(raw["subject"])
    portrait = _parse_portrait(config_path, raw["portrait"])
    layout = _parse_layout(raw["layout"])
    return IdentityDocument(
        subject=subject,
        portrait=portrait,
        layout=layout,
        state_label="IDENTITY / FOUND",
    )


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


def _identity_metadata(theme: Theme, document: IdentityDocument, typography: dict[str, dict[str, float]], motion: MotionTokens) -> str:
    heading = typography["heading"]
    display = typography["display"]
    section = typography["section"]
    body = typography["body"]
    small = typography["small"]
    meta_x = document.layout.metadata_x
    meta_y = document.layout.metadata_y
    step = document.layout.metadata_step
    subject = document.subject
    domains = ", ".join(subject.domains) if subject.domains else "Undisclosed"
    rows = [
        _text(theme, meta_x, meta_y, int(heading["size"]), theme.text_secondary, document.state_label, int(heading["weight"]), tracking=1.6),
        _text(theme, meta_x, meta_y + step, int(display["size"]), theme.text_primary, subject.name, int(display["weight"]), tracking=0.4),
        _text(theme, meta_x, meta_y + step * 2, int(section["size"]), theme.text_secondary, "ROLE", int(section["weight"]), tracking=0.3),
        _text(theme, meta_x + 110, meta_y + step * 2, int(section["size"]), theme.text_primary, subject.role, int(section["weight"]), tracking=0.0),
        _text(theme, meta_x, meta_y + step * 3, int(section["size"]), theme.text_secondary, "ORIGIN", int(section["weight"]), tracking=0.3),
        _text(theme, meta_x + 110, meta_y + step * 3, int(body["size"]), theme.text_primary, subject.origin, int(body["weight"]), tracking=0.0),
        _text(theme, meta_x, meta_y + step * 4, int(small["size"]), theme.text_secondary, "DOMAINS", int(small["weight"]), tracking=0.2),
        _text(theme, meta_x + 110, meta_y + step * 4, int(small["size"]), theme.text_muted, domains, int(small["weight"]), tracking=0.1),
    ]
    return _reveal_group(
        "".join(rows),
        delay_ms=motion.assemble * 2 + motion.slow + motion.fast,
        duration_ms=motion.assemble,
        dy=4,
    )


def _identity_portrait(theme: Theme, document: IdentityDocument, motion: MotionTokens) -> str:
    layout = document.layout
    settings = document.portrait
    field = layout.portrait
    point_field = render_portrait_points(theme, settings, field)
    return (
        _reveal_group(point_field, delay_ms=motion.normal * 2, duration_ms=motion.assemble, dy=4)
    )


def render_identity(mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_IDENTITY_PATH) -> IdentityRender:
    bundle = tokens or load_tokens()
    theme = resolve_theme(mode, bundle)
    motion = resolve_motion(bundle)
    document = load_identity_document(config_path)
    layout = document.layout
    frame = layout.frame
    typography = bundle.typography_scale
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{layout.canvas_width}" height="{layout.canvas_height}" viewBox="0 0 {layout.canvas_width} {layout.canvas_height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">KalaOS identity</title>',
        f'<desc id="desc">Identity layer for KalaOS with deterministic point-field portrait reconstruction and sparse metadata.</desc>',
        "<defs>",
        build_primitive_defs(mode, bundle),
        "</defs>",
        f'<rect width="{layout.canvas_width}" height="{layout.canvas_height}" fill="{theme.background}"/>',
        render_background_grid(theme, bundle, opacity=0.12),
        f'<rect x="{frame.x}" y="{frame.y}" width="{frame.width}" height="{frame.height}" rx="{frame.radius}" fill="none" stroke="{theme.border_panel}" stroke-width="{bundle.stroke_widths["standard"]}"/>',
        _identity_portrait(theme, document, motion),
        _identity_metadata(theme, document, typography, motion),
        f'<line x1="{layout.metadata_x - 36}" y1="{layout.metadata_y - 8}" x2="{layout.metadata_x - 36}" y2="{layout.metadata_y + 4 * layout.metadata_step + 18}" stroke="{theme.border_hairline}" stroke-width="1"/>',
        "</svg>",
    ]
    return IdentityRender(svg="".join(parts), theme_mode=mode)


def write_identity(path: Path, mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_IDENTITY_PATH) -> Path:
    identity = render_identity(mode=mode, tokens=tokens, config_path=config_path)
    path.write_text(identity.svg, encoding="utf-8")
    return path
