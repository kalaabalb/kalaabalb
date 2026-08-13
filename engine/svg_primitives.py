from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .layout import HeroLayout, resolve_hero_layout
from .theme import Theme, resolve_theme
from .tokens import TokenBundle, load_tokens


@dataclass(frozen=True)
class PrimitiveLibrary:
    svg: str


@dataclass(frozen=True)
class OriginMarkGeometry:
    center: float
    radius: float
    gap: float
    stroke: float
    segment: float
    top_start: float
    top_end: float
    bottom_start: float
    bottom_end: float
    left_start: float
    left_end: float
    right_start: float
    right_end: float


def _pattern_grid(theme: Theme, tokens: TokenBundle) -> str:
    unit = int(tokens.grid["unit"])
    return (
        f'<pattern id="kalaos-grid" width="{unit}" height="{unit}" patternUnits="userSpaceOnUse">'
        f'<path d="M {unit} 0 H 0 V {unit}" fill="none" stroke="{theme.grid}" stroke-opacity="1" stroke-width="1"/>'
        "</pattern>"
    )


def _coordinate_marks(theme: Theme, tokens: TokenBundle) -> str:
    labels = [
        ("00,00", 34, 58),
        ("18,00", 368, 58),
        ("00,44", 34, 430),
        ("18,44", 368, 430),
    ]
    parts = ['<g id="kalaos-coordinate-marks" fill="none">']
    for label, x, y in labels:
        parts.append(
            f'<text x="{x}" y="{y}" font-size="9" fill="{theme.coordinate}" letter-spacing="1.8">{label}</text>'
        )
    parts.append("</g>")
    return "".join(parts)


def _corner_geometry(theme: Theme) -> str:
    return (
        '<symbol id="kalaos-corner-geometry" viewBox="0 0 64 64">'
        f'<path d="M8 22V8H22" fill="none" stroke="{theme.accent_violet}" stroke-width="2" stroke-linecap="round"/>'
        f'<path d="M42 8H56V22" fill="none" stroke="{theme.accent_violet}" stroke-width="2" stroke-linecap="round"/>'
        f'<path d="M8 42V56H22" fill="none" stroke="{theme.accent_violet}" stroke-width="2" stroke-linecap="round"/>'
        f'<path d="M42 56H56V42" fill="none" stroke="{theme.accent_violet}" stroke-width="2" stroke-linecap="round"/>'
        "</symbol>"
    )


def _ruler(theme: Theme) -> str:
    return (
        '<symbol id="kalaos-ruler" viewBox="0 0 240 20">'
        f'<line x1="0" y1="10" x2="240" y2="10" stroke="{theme.border_hairline}" stroke-width="1"/>'
        f'<line x1="24" y1="5" x2="24" y2="15" stroke="{theme.accent_cyan}" stroke-width="1"/>'
        f'<line x1="120" y1="3" x2="120" y2="17" stroke="{theme.accent_violet}" stroke-width="1.5"/>'
        f'<line x1="216" y1="5" x2="216" y2="15" stroke="{theme.warning_amber}" stroke-width="1"/>'
        "</symbol>"
    )


def _calibration_marks(theme: Theme) -> str:
    return (
        '<symbol id="kalaos-calibration-marks" viewBox="0 0 64 64">'
        f'<circle cx="32" cy="32" r="20" fill="none" stroke="{theme.border_hairline}" stroke-width="1"/>'
        f'<line x1="32" y1="8" x2="32" y2="20" stroke="{theme.accent_cyan}" stroke-width="1"/>'
        f'<line x1="32" y1="44" x2="32" y2="56" stroke="{theme.accent_cyan}" stroke-width="1"/>'
        f'<line x1="8" y1="32" x2="20" y2="32" stroke="{theme.accent_cyan}" stroke-width="1"/>'
        f'<line x1="44" y1="32" x2="56" y2="32" stroke="{theme.accent_cyan}" stroke-width="1"/>'
        "</symbol>"
    )


def _separator(theme: Theme) -> str:
    return (
        '<symbol id="kalaos-separator" viewBox="0 0 240 8">'
        f'<line x1="0" y1="4" x2="240" y2="4" stroke="{theme.border_hairline}" stroke-width="1"/>'
        f'<line x1="102" y1="4" x2="138" y2="4" stroke="{theme.accent_violet}" stroke-width="1"/>'
        "</symbol>"
    )


def _particle(theme: Theme) -> str:
    return (
        '<symbol id="kalaos-particle" viewBox="0 0 8 8">'
        f'<circle cx="4" cy="4" r="1.25" fill="{theme.particle}"/>'
        "</symbol>"
    )


def _origin_geometry(tokens: TokenBundle) -> OriginMarkGeometry:
    unit = int(tokens.spacing["2"])
    radius = unit / 2.0
    gap = unit * 0.75
    stroke = unit * 0.5
    segment = unit * 2.5
    center = 32.0
    return OriginMarkGeometry(
        center=center,
        radius=radius,
        gap=gap,
        stroke=stroke,
        segment=segment,
        top_start=center - radius - gap - segment,
        top_end=center - radius - gap,
        bottom_start=center + radius + gap,
        bottom_end=center + radius + gap + segment,
        left_start=center - radius - gap - segment,
        left_end=center - radius - gap,
        right_start=center + radius + gap,
        right_end=center + radius + gap + segment,
    )


def _origin_mark(theme: Theme, geometry: OriginMarkGeometry) -> str:
    return (
        '<symbol id="kalaos-origin-mark" viewBox="0 0 64 64">'
        f'<circle cx="{geometry.center}" cy="{geometry.center}" r="{geometry.radius}" fill="{theme.accent_violet}" opacity="1">'
        f'<animate attributeName="opacity" values="0;1" dur="0.18s" begin="0s" fill="freeze"/>'
        "</circle>"
        f'<line x1="{geometry.center}" y1="{geometry.top_start}" x2="{geometry.center}" y2="{geometry.top_end}" stroke="{theme.accent_violet}" stroke-width="{geometry.stroke}" stroke-linecap="round" opacity="1">'
        f'<animate attributeName="opacity" values="0;1" dur="0.18s" begin="0.14s" fill="freeze"/>'
        "</line>"
        f'<line x1="{geometry.center}" y1="{geometry.bottom_start}" x2="{geometry.center}" y2="{geometry.bottom_end}" stroke="{theme.accent_violet}" stroke-width="{geometry.stroke}" stroke-linecap="round" opacity="1">'
        f'<animate attributeName="opacity" values="0;1" dur="0.18s" begin="0.28s" fill="freeze"/>'
        "</line>"
        f'<line x1="{geometry.left_start}" y1="{geometry.center}" x2="{geometry.left_end}" y2="{geometry.center}" stroke="{theme.accent_violet}" stroke-width="{geometry.stroke}" stroke-linecap="round" opacity="1">'
        f'<animate attributeName="opacity" values="0;1" dur="0.18s" begin="0.42s" fill="freeze"/>'
        "</line>"
        f'<line x1="{geometry.right_start}" y1="{geometry.center}" x2="{geometry.right_end}" y2="{geometry.center}" stroke="{theme.accent_violet}" stroke-width="{geometry.stroke}" stroke-linecap="round" opacity="1">'
        f'<animate attributeName="opacity" values="0;1" dur="0.18s" begin="0.56s" fill="freeze"/>'
        "</line>"
        "</symbol>"
    )


def _clip_and_mask(theme: Theme, layout: HeroLayout) -> str:
    frame = layout.frame
    return (
        f'<clipPath id="kalaos-clip-frame"><rect x="{frame.x}" y="{frame.y}" width="{frame.width}" height="{frame.height}" rx="{frame.radius}"/></clipPath>'
        f'<mask id="kalaos-soft-mask"><rect x="0" y="0" width="{layout.canvas_width}" height="{layout.canvas_height}" fill="white"/>'
        f'<rect x="{frame.x}" y="{frame.y}" width="{frame.width}" height="{frame.height}" rx="{frame.radius}" fill="black" opacity="0.08"/>'
        "</mask>"
    )


def build_primitive_library(mode: str = "dark", tokens: TokenBundle | None = None) -> PrimitiveLibrary:
    bundle = tokens or load_tokens()
    theme = resolve_theme(mode, bundle)
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 480" role="img" aria-labelledby="title desc">',
        f'<title id="title">KalaOS primitive library ({mode})</title>',
        f'<desc id="desc">Reusable SVG primitives for grids, rulers, marks, corners, masks, and particles.</desc>',
        "<defs>",
        build_primitive_defs(mode, bundle),
        "</defs>",
        f'<rect width="480" height="480" fill="{theme.background}" opacity="0"/>',
        "</svg>",
    ]
    return PrimitiveLibrary(svg="".join(parts))


def build_primitive_defs(mode: str = "dark", tokens: TokenBundle | None = None) -> str:
    bundle = tokens or load_tokens()
    theme = resolve_theme(mode, bundle)
    layout = resolve_hero_layout(bundle)
    geometry = _origin_geometry(bundle)
    return "".join(
        (
            _pattern_grid(theme, bundle),
            _corner_geometry(theme),
            _ruler(theme),
            _calibration_marks(theme),
            _separator(theme),
            _particle(theme),
            _origin_mark(theme, geometry),
            _clip_and_mask(theme, layout),
        )
    )


def render_background_grid(theme: Theme, tokens: TokenBundle | None = None, opacity: float = 0.22) -> str:
    bundle = tokens or load_tokens()
    unit = int(bundle.grid["unit"])
    layout = resolve_hero_layout(bundle)
    width = layout.canvas_width
    height = layout.canvas_height
    parts = [f'<g id="kalaos-background-grid" opacity="{opacity}">']
    for x in range(40, width, unit * 7):
        parts.append(f'<line x1="{x}" y1="18" x2="{x}" y2="{height - 18}" stroke="{theme.coordinate}" stroke-opacity="0.10"/>')
    for y in range(48, height, unit * 7):
        parts.append(f'<line x1="18" y1="{y}" x2="{width - 18}" y2="{y}" stroke="{theme.coordinate}" stroke-opacity="0.08"/>')
    parts.append(_coordinate_marks(theme, bundle))
    parts.append("</g>")
    return "".join(parts)


def render_origin_mark(theme: Theme, tokens: TokenBundle | None = None) -> str:
    bundle = tokens or load_tokens()
    geometry = _origin_geometry(bundle)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-labelledby="title desc">'
        '<title id="title">KalaOS Origin Mark</title>'
        '<desc id="desc">Construction symbol with a central point and four separated segments.</desc>'
        f'<circle cx="{geometry.center}" cy="{geometry.center}" r="{geometry.radius}" fill="{theme.accent_violet}" opacity="0">'
        f'<animate attributeName="opacity" values="0;1" dur="0.18s" begin="0s" fill="freeze"/>'
        "</circle>"
        f'<line x1="{geometry.center}" y1="{geometry.top_start}" x2="{geometry.center}" y2="{geometry.top_end}" stroke="{theme.accent_violet}" stroke-width="{geometry.stroke}" stroke-linecap="round" opacity="0">'
        f'<animate attributeName="opacity" values="0;1" dur="0.18s" begin="0.14s" fill="freeze"/>'
        "</line>"
        f'<line x1="{geometry.center}" y1="{geometry.bottom_start}" x2="{geometry.center}" y2="{geometry.bottom_end}" stroke="{theme.accent_violet}" stroke-width="{geometry.stroke}" stroke-linecap="round" opacity="0">'
        f'<animate attributeName="opacity" values="0;1" dur="0.18s" begin="0.28s" fill="freeze"/>'
        "</line>"
        f'<line x1="{geometry.left_start}" y1="{geometry.center}" x2="{geometry.left_end}" y2="{geometry.center}" stroke="{theme.accent_violet}" stroke-width="{geometry.stroke}" stroke-linecap="round" opacity="0">'
        f'<animate attributeName="opacity" values="0;1" dur="0.18s" begin="0.42s" fill="freeze"/>'
        "</line>"
        f'<line x1="{geometry.right_start}" y1="{geometry.center}" x2="{geometry.right_end}" y2="{geometry.center}" stroke="{theme.accent_violet}" stroke-width="{geometry.stroke}" stroke-linecap="round" opacity="0">'
        f'<animate attributeName="opacity" values="0;1" dur="0.18s" begin="0.56s" fill="freeze"/>'
        "</line>"
        "</svg>"
    )
