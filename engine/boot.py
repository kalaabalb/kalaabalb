from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .layout import HeroLayout, resolve_hero_layout
from .motion import MotionTokens, resolve_motion
from .svg_primitives import build_primitive_defs, render_background_grid
from .theme import Theme, resolve_theme
from .tokens import TokenBundle, load_tokens


@dataclass(frozen=True)
class BootRow:
    label: str
    value: str
    x: int
    y: int
    delay_ms: int
    duration_ms: int
    label_fill: str
    value_fill: str


def _seconds(ms: int) -> str:
    return f"{ms / 1000:.2f}s"


def _reveal_group(content: str, delay_ms: int, duration_ms: int, dy: int = 8) -> str:
    return (
        f'<g opacity="1">'
        f'<animate attributeName="opacity" from="0" to="1" dur="{_seconds(duration_ms)}" begin="{_seconds(delay_ms)}" fill="freeze" calcMode="spline" keySplines="0.42 0 0.58 1"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 {dy}" to="0 0" dur="{_seconds(duration_ms)}" begin="{_seconds(delay_ms)}" fill="freeze" calcMode="spline" keySplines="0.42 0 0.58 1"/>'
        f"{content}</g>"
    )


def _reduced_motion_style() -> str:
    return (
        '<style><![CDATA['
        '@media (prefers-reduced-motion: reduce) {'
        '.kalaos-ambient { display: none; }'
        '}'
        ']]></style>'
    )


def _boot_origin(
    theme: Theme,
    layout: HeroLayout,
    motion: MotionTokens,
    caption_size: int,
    caption_weight: int,
) -> str:
    frame = layout.frame
    size = 112
    x = frame.x + 52
    y = frame.y + 58
    label_x = x + size / 2
    label_y = y + size + 20
    begin = _seconds(motion.fast)
    duration = _seconds(motion.reveal)
    return (
        f'<g opacity="1">'
        f'<use href="#kalaos-origin-mark" x="{x}" y="{y}" width="{size}" height="{size}" opacity="1"/>'
        f'<animate attributeName="opacity" from="0" to="1" dur="{duration}" begin="{begin}" fill="freeze" calcMode="spline" keySplines="0.42 0 0.58 1"/>'
        f'<text x="{label_x}" y="{label_y}" text-anchor="middle" font-size="{caption_size}" font-weight="{caption_weight}" letter-spacing="1.2" fill="{theme.text_muted}">ORIGIN LOCKED</text>'
        "</g>"
    )


def _boot_title(
    theme: Theme,
    layout: HeroLayout,
    motion: MotionTokens,
    display_xl_size: int,
    display_xl_weight: int,
) -> str:
    frame = layout.frame
    x = frame.x + frame.width / 2
    y = frame.y + 184
    return _reveal_group(
        (
            f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{display_xl_size}" font-weight="{display_xl_weight}" letter-spacing="7" fill="{theme.text_primary}">KALAOS</text>'
        ),
        delay_ms=motion.assemble + motion.normal,
        duration_ms=motion.reveal,
        dy=10,
    )


def _boot_row(
    theme: Theme,
    row: BootRow,
    small_size: int,
    small_weight: int,
    body_size: int,
    body_weight: int,
    ambient: bool = False,
    ambient_delay_ms: int | None = None,
) -> str:
    particle = f'<use href="#kalaos-particle" x="{row.x - 18}" y="{row.y - 11}" width="8" height="8" opacity="0.9"/>'
    if ambient and ambient_delay_ms is not None:
        particle += (
            f'<use class="kalaos-ambient" href="#kalaos-particle" x="{row.x - 18}" y="{row.y - 11}" width="8" height="8" opacity="0.22">'
            f'<animate attributeName="opacity" values="0.22;0.32;0.22" dur="5.60s" begin="{_seconds(ambient_delay_ms)}" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.42 0 0.58 1;0.42 0 0.58 1"/>'
            "</use>"
        )
    return _reveal_group(
        (
            particle
            + 
            f'<text x="{row.x}" y="{row.y}" font-size="{small_size}" font-weight="{small_weight}" letter-spacing="1.2" fill="{row.label_fill}">{row.label}</text>'
            f'<text x="{row.x + 220}" y="{row.y}" font-size="{body_size}" font-weight="{body_weight}" fill="{row.value_fill}">{row.value}</text>'
        ),
        delay_ms=row.delay_ms,
        duration_ms=row.duration_ms,
        dy=6,
    )


def _boot_handoff(
    theme: Theme,
    layout: HeroLayout,
    delay_ms: int,
    motion: MotionTokens,
    caption_size: int,
    caption_weight: int,
) -> str:
    frame = layout.frame
    x = frame.x + 720
    y = frame.y + frame.height - 54
    return _reveal_group(
        (
            f'<text x="{x}" y="{y}" font-size="{caption_size}" font-weight="{caption_weight}" letter-spacing="1.2" fill="{theme.text_muted}">HANDOFF</text>'
            f'<text x="{x + 82}" y="{y}" font-size="{caption_size}" font-weight="{caption_weight}" letter-spacing="1.2" fill="{theme.text_secondary}">IDENTITY.APP</text>'
            f'<line class="kalaos-ambient" x1="{x}" y1="{y + 10}" x2="{x + 126}" y2="{y + 10}" stroke="{theme.accent_cyan}" stroke-width="1" stroke-opacity="0.18">'
            f'<animate attributeName="stroke-opacity" values="0.18;0.30;0.18" dur="5.60s" begin="{_seconds(delay_ms + motion.reveal)}" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.42 0 0.58 1;0.42 0 0.58 1"/>'
            "</line>"
        ),
        delay_ms=delay_ms,
        duration_ms=motion.reveal,
        dy=6,
    )


def render_boot(mode: str = "dark", tokens: TokenBundle | None = None) -> str:
    bundle = tokens or load_tokens()
    theme = resolve_theme(mode, bundle)
    layout = resolve_hero_layout(bundle)
    motion = resolve_motion(bundle)
    typography = bundle.typography_scale
    display_xl_size = typography["display_xl"]["size"]
    display_xl_weight = typography["display_xl"]["weight"]
    small_size = typography["small"]["size"]
    small_weight = typography["small"]["weight"]
    body_size = typography["body"]["size"]
    body_weight = typography["body"]["weight"]
    caption_size = typography["caption"]["size"]
    caption_weight = typography["caption"]["weight"]
    frame = layout.frame
    calibration_start = motion.assemble + motion.reveal + motion.normal
    row_step_ms = motion.normal + motion.fast // 4
    rows = [
        BootRow(
            label="ORIGIN",
            value="LOCKED",
            x=frame.x + 472,
            y=frame.y + 248,
            delay_ms=calibration_start,
            duration_ms=motion.reveal,
            label_fill=theme.text_secondary,
            value_fill=theme.accent_violet,
        ),
        BootRow(
            label="GRID",
            value="CALIBRATED",
            x=frame.x + 472,
            y=frame.y + 282,
            delay_ms=calibration_start + row_step_ms,
            duration_ms=motion.reveal,
            label_fill=theme.text_secondary,
            value_fill=theme.accent_cyan,
        ),
        BootRow(
            label="ENVIRONMENT",
            value="STABLE",
            x=frame.x + 472,
            y=frame.y + 316,
            delay_ms=calibration_start + row_step_ms * 2,
            duration_ms=motion.reveal,
            label_fill=theme.text_secondary,
            value_fill=theme.text_primary,
        ),
        BootRow(
            label="IDENTITY",
            value="DEFERRED",
            x=frame.x + 472,
            y=frame.y + 358,
            delay_ms=calibration_start + row_step_ms * 3,
            duration_ms=motion.reveal,
            label_fill=theme.text_secondary,
            value_fill=theme.accent_lavender,
        ),
        BootRow(
            label="SYSTEM",
            value="READY",
            x=frame.x + 472,
            y=frame.y + 400,
            delay_ms=calibration_start + row_step_ms * 4,
            duration_ms=motion.reveal,
            label_fill=theme.text_secondary,
            value_fill=theme.success_green,
        ),
    ]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{layout.canvas_width}" height="{layout.canvas_height}" viewBox="0 0 {layout.canvas_width} {layout.canvas_height}" role="img" aria-labelledby="title desc">',
        '<title id="title">KalaOS boot</title>',
        f'<desc id="desc">Boot environment for KalaOS with staged origin, calibration, deferred identity, system ready, and future handoff states.</desc>',
        "<defs>",
        _reduced_motion_style(),
        build_primitive_defs(mode, bundle),
        "</defs>",
        f'<rect width="{layout.canvas_width}" height="{layout.canvas_height}" fill="{theme.background}"/>',
        render_background_grid(theme, bundle, opacity=0.14),
        f'<rect x="{frame.x}" y="{frame.y}" width="{frame.width}" height="{frame.height}" rx="{frame.radius}" fill="{theme.panel}" stroke="{theme.border_panel}" stroke-width="{bundle.stroke_widths["standard"]}"/>',
        _boot_origin(theme, layout, motion, caption_size, caption_weight),
        _boot_title(theme, layout, motion, display_xl_size, display_xl_weight),
    ]
    for index, row in enumerate(rows):
        ambient = index == len(rows) - 1
        ambient_delay_ms = row.delay_ms + row.duration_ms if ambient else None
        parts.append(
            _boot_row(
                theme,
                row,
                small_size,
                small_weight,
                body_size,
                body_weight,
                ambient=ambient,
                ambient_delay_ms=ambient_delay_ms,
            )
        )
    parts.append(
        _boot_handoff(
            theme,
            layout,
            calibration_start + row_step_ms * 4,
            motion,
            caption_size,
            caption_weight,
        )
    )
    parts.append("</svg>")
    return "".join(parts)


def write_boot(path: Path, mode: str = "dark", tokens: TokenBundle | None = None) -> Path:
    path.write_text(render_boot(mode=mode, tokens=tokens), encoding="utf-8")
    return path
