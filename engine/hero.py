from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .layout import HeroLayout, resolve_hero_layout
from .motion import MotionTokens, resolve_motion
from .svg_primitives import render_background_grid
from .theme import Theme, resolve_theme
from .tokens import TokenBundle, load_tokens


@dataclass(frozen=True)
class HeroRender:
    svg: str
    theme_mode: str


def _boot_line(theme: Theme, x: int, y: int, text: str) -> str:
    return f'<text x="{x}" y="{y}" font-size="12" fill="{theme.text_secondary}">{text}</text>'


def _cursor(theme: Theme, x: int, y: int, duration: str) -> str:
    return (
        f'<text x="{x}" y="{y}" font-size="24" fill="{theme.accent_violet}">▍'
        f'<animate attributeName="opacity" values="0;1;0" dur="{duration}" repeatCount="indefinite"/>'
        "</text>"
    )


def render_hero(mode: str = "dark", tokens: TokenBundle | None = None) -> HeroRender:
    bundle = tokens or load_tokens()
    theme = resolve_theme(mode, bundle)
    layout = resolve_hero_layout(bundle)
    motion = resolve_motion(bundle)
    frame = layout.frame
    title_x, title_y = layout.title
    subtitle_x, subtitle_y = layout.subtitle
    cursor_x, cursor_y = layout.cursor
    boot_log_x, boot_log_y = layout.boot_log
    boot_log_step = layout.boot_log_step
    footer_left_x, footer_left_y = layout.footer_left
    footer_right_x, footer_right_y = layout.footer_right

    boot_lines = [
        "Calibrating Spatial Grid",
        "Initializing Coordinate Space",
        "Synchronizing Archives",
        "Loading Identity",
        "Verifying Modules",
        "Environment Ready",
    ]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{layout.canvas_width}" height="{layout.canvas_height}" viewBox="0 0 {layout.canvas_width} {layout.canvas_height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">KalaOS {mode} core</title>',
        f'<desc id="desc">Modular KalaOS boot surface driven by the shared engine tokens.</desc>',
        f'<rect width="{layout.canvas_width}" height="{layout.canvas_height}" fill="{theme.background}"/>',
        render_background_grid(theme, bundle),
        f'<rect x="{frame.x}" y="{frame.y}" width="{frame.width}" height="{frame.height}" rx="{frame.radius}" fill="{theme.panel}" stroke="{theme.border_panel}" stroke-width="{bundle.stroke_widths["standard"]}"/>',
        f'<text x="{title_x}" y="{title_y}" text-anchor="middle" font-size="{bundle.typography_scale["display_xl"]["size"]}" font-weight="{bundle.typography_scale["display_xl"]["weight"]}" letter-spacing="7" fill="{theme.text_primary}">KALAOS</text>',
        f'<text x="{subtitle_x}" y="{subtitle_y}" text-anchor="middle" font-size="{bundle.typography_scale["section"]["size"]}" letter-spacing="1.6" fill="{theme.text_secondary}">Build 0.0.1-alpha</text>',
        _cursor(theme, cursor_x, cursor_y, f"{motion.idle / 1000:.1f}s"),
        f'<text x="{footer_left_x}" y="{footer_left_y}" font-size="{bundle.typography_scale["caption"]["size"]}" fill="{theme.text_muted}" letter-spacing="1.2">INITIALIZATION IN PROGRESS</text>',
        f'<text x="{footer_right_x}" y="{footer_right_y}" text-anchor="end" font-size="{bundle.typography_scale["caption"]["size"]}" fill="{theme.text_muted}" letter-spacing="1.2">CORE ENGINE READY</text>',
    ]

    for index, line in enumerate(boot_lines):
        parts.append(_boot_line(theme, boot_log_x, boot_log_y + index * boot_log_step, line))

    parts.append("</svg>")
    return HeroRender(svg="".join(parts), theme_mode=mode)


def write_hero(path: Path, mode: str = "dark", tokens: TokenBundle | None = None) -> Path:
    hero = render_hero(mode=mode, tokens=tokens)
    path.write_text(hero.svg, encoding="utf-8")
    return path
