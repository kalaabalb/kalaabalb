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
DEFAULT_TELEMETRY_PATH = ROOT / "assets" / "source" / "kalaos.telemetry.json"


@dataclass(frozen=True)
class TelemetryLayout:
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
    activity: Rect
    language: Rect
    summary_x: int
    summary_y: int
    summary_gap: int


@dataclass(frozen=True)
class TelemetrySystem:
    id: str
    label: str
    reference: str
    state: str
    files: int
    bins: tuple[int, ...]
    tone: str


@dataclass(frozen=True)
class TelemetryLanguage:
    name: str
    count: int
    tone: str


@dataclass(frozen=True)
class TelemetrySummary:
    systems: int
    languages: int
    files: int
    last_observed: str


@dataclass(frozen=True)
class TelemetryDocument:
    title: str
    subtitle: str
    state: str
    timeline_labels: tuple[str, ...]
    layout: TelemetryLayout
    systems: tuple[TelemetrySystem, ...]
    languages: tuple[TelemetryLanguage, ...]
    summary: TelemetrySummary


@dataclass(frozen=True)
class TelemetryRender:
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


def _tone(theme: Theme, name: str) -> str:
    return getattr(theme, name)


def _parse_layout(raw: dict[str, object]) -> TelemetryLayout:
    canvas = raw["canvas"]
    frame = raw["frame"]
    field = raw["field"]
    header = raw["header"]
    activity = raw["activity"]
    language = raw["language"]
    summary = raw["summary"]
    return TelemetryLayout(
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
        activity=Rect(
            x=int(activity["x"]),
            y=int(activity["y"]),
            width=int(activity["width"]),
            height=int(activity["height"]),
            radius=int(activity["radius"]),
        ),
        language=Rect(
            x=int(language["x"]),
            y=int(language["y"]),
            width=int(language["width"]),
            height=int(language["height"]),
            radius=int(language["radius"]),
        ),
        summary_x=int(summary["x"]),
        summary_y=int(summary["y"]),
        summary_gap=int(summary["gap"]),
    )


def _parse_system(raw: dict[str, object]) -> TelemetrySystem:
    return TelemetrySystem(
        id=str(raw["id"]),
        label=str(raw["label"]),
        reference=str(raw["reference"]),
        state=str(raw["state"]),
        files=int(raw["files"]),
        bins=tuple(int(value) for value in raw["bins"]),
        tone=str(raw["tone"]),
    )


def _parse_language(raw: dict[str, object]) -> TelemetryLanguage:
    return TelemetryLanguage(
        name=str(raw["name"]),
        count=int(raw["count"]),
        tone=str(raw["tone"]),
    )


def _parse_summary(raw: dict[str, object]) -> TelemetrySummary:
    return TelemetrySummary(
        systems=int(raw["systems"]),
        languages=int(raw["languages"]),
        files=int(raw["files"]),
        last_observed=str(raw["last_observed"]),
    )


def load_telemetry_document(path: Path | str = DEFAULT_TELEMETRY_PATH) -> TelemetryDocument:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    layout = _parse_layout(raw["layout"])
    telemetry = raw["telemetry"]
    systems = tuple(_parse_system(system) for system in telemetry["systems"])
    languages = tuple(_parse_language(language) for language in telemetry["languages"])
    summary = _parse_summary(telemetry["summary"])
    return TelemetryDocument(
        title=str(telemetry["title"]),
        subtitle=str(telemetry["subtitle"]),
        state=str(telemetry["state"]),
        timeline_labels=tuple(str(value) for value in telemetry["timeline_labels"]),
        layout=layout,
        systems=systems,
        languages=languages,
        summary=summary,
    )


def _system_row(
    theme: Theme,
    system: TelemetrySystem,
    row_y: float,
    layout: TelemetryLayout,
    typography: dict[str, dict[str, float]],
    motion: MotionTokens,
    delay_ms: int,
    max_count: int,
    slot_count: int,
) -> str:
    section = typography["section"]
    small = typography["small"]
    caption = typography["caption"]
    tone = _tone(theme, system.tone)
    label_x = layout.activity.x
    trace_x = layout.activity.x + 214
    trace_width = layout.activity.width - 226
    slot_width = trace_width / slot_count
    row_gap = 16
    trace_y = row_y + row_gap + 8
    baseline = trace_y + 1
    points: list[str] = []
    path_points: list[str] = []
    for index, count in enumerate(system.bins):
        x = trace_x + slot_width * index + slot_width * 0.5
        scale = count / max_count if max_count else 0.0
        pulse = 4.0 + 20.0 * scale
        top = trace_y - pulse
        bottom = trace_y + 3.0 + 4.0 * scale
        path_points.append(f"{x:.1f},{top:.1f}")
        if count > 0:
            dot_count = 1 if count < max_count * 0.18 else 2 if count < max_count * 0.6 else 3
            for dot in range(dot_count):
                dot_x = x + (dot - (dot_count - 1) / 2.0) * 2.4
                dot_y = top + 2.6 + dot * 0.7
                points.append(
                    f'<circle cx="{dot_x:.1f}" cy="{dot_y:.1f}" r="{1.1 + scale * 1.1:.2f}" fill="{tone}" opacity="{0.48 + scale * 0.30:.2f}"/>'
                )
    trace_path = ""
    if path_points:
        trace_path = (
            f'<path d="M {path_points[0]}'
            + "".join(f' L {value}' for value in path_points[1:])
            + f'" fill="none" stroke="{tone}" stroke-width="{1.1 + (system.files / max_count if max_count else 0.0) * 1.8:.2f}" stroke-linecap="round" stroke-opacity="0.24"/>'
        )
    relation_label = f"{system.state} / {system.files} FILES"
    return _reveal_group(
        (
            f'<g opacity="1">'
            f'<line x1="{trace_x}" y1="{baseline}" x2="{trace_x + trace_width}" y2="{baseline}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.22"/>'
            f'<text x="{label_x}" y="{row_y}" font-size="{int(section["size"])}" font-weight="{int(section["weight"])}" letter-spacing="0.25" fill="{theme.text_primary}">{system.label}</text>'
            f'<text x="{label_x}" y="{row_y + 15}" font-size="{int(small["size"])}" font-weight="{int(small["weight"])}" letter-spacing="0.18" fill="{theme.text_secondary}">{relation_label}</text>'
            f'<text x="{label_x}" y="{row_y + 30}" font-size="{int(caption["size"])}" font-weight="{int(caption["weight"])}" letter-spacing="0.12" fill="{theme.text_muted}">{system.reference}</text>'
            f'{trace_path}'
            f'{"".join(points)}'
            "</g>"
        ),
        delay_ms=delay_ms,
        duration_ms=motion.reveal,
        dy=4,
    )


def _language_row(
    theme: Theme,
    language: TelemetryLanguage,
    row_y: float,
    layout: TelemetryLayout,
    typography: dict[str, dict[str, float]],
    motion: MotionTokens,
    delay_ms: int,
    max_count: int,
) -> str:
    small = typography["small"]
    caption = typography["caption"]
    tone = _tone(theme, language.tone)
    label_x = layout.language.x
    track_x = layout.language.x + 116
    track_width = layout.language.width - 156
    scale = language.count / max_count if max_count else 0.0
    length = 58.0 + 132.0 * scale
    height = 4.0 + 4.0 * scale
    dot_top = row_y - height * 0.5
    dots = []
    for index, fraction in enumerate((0.28, 0.58, 0.84)):
        if fraction <= scale or index == 0:
            dot_x = track_x + length * fraction
            dots.append(
                f'<circle cx="{dot_x:.1f}" cy="{dot_top + 2.2:.1f}" r="{1.0 + scale * 0.9:.2f}" fill="{tone}" opacity="{0.42 + scale * 0.33:.2f}"/>'
            )
    return _reveal_group(
        (
            f'<g opacity="1">'
            f'<text x="{label_x}" y="{row_y}" font-size="{int(small["size"])}" font-weight="{int(small["weight"])}" letter-spacing="0.18" fill="{theme.text_primary}">{language.name}</text>'
            f'<line x1="{track_x}" y1="{row_y - 1}" x2="{track_x + length}" y2="{row_y - 1}" stroke="{tone}" stroke-width="{height:.2f}" stroke-linecap="round" stroke-opacity="0.38"/>'
            f'<line x1="{track_x}" y1="{row_y - 1}" x2="{track_x + track_width}" y2="{row_y - 1}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.10"/>'
            f'<text x="{layout.language.x + layout.language.width - 2}" y="{row_y}" text-anchor="end" font-size="{int(caption["size"])}" font-weight="{int(caption["weight"])}" letter-spacing="0.14" fill="{theme.text_secondary}">{language.count}</text>'
            f'{"".join(dots)}'
            "</g>"
        ),
        delay_ms=delay_ms,
        duration_ms=motion.reveal,
        dy=3,
    )


def _summary_row(theme: Theme, document: TelemetryDocument, typography: dict[str, dict[str, float]]) -> str:
    small = typography["small"]
    caption = typography["caption"]
    y = document.layout.summary_y
    x = document.layout.summary_x
    items = [
        (x, f"{document.summary.systems} SYSTEMS", "OBSERVED"),
        (x + 268, f"{document.summary.languages} LANGUAGES", "RESOLVED"),
        (x + 520, f"{document.summary.files} FILES", "SAMPLED"),
        (x + 760, document.summary.last_observed, "LAST OBSERVED"),
    ]
    parts = ['<g opacity="1">']
    for index, (item_x, value, label) in enumerate(items):
        if index:
            parts.append(f'<line x1="{item_x - 20}" y1="{y - 11}" x2="{item_x - 20}" y2="{y + 10}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.30"/>')
        parts.append(_text(theme, item_x, y, int(small["size"]), theme.text_primary, value, int(small["weight"]), tracking=0.18))
        parts.append(_text(theme, item_x, y + 14, int(caption["size"]), theme.text_muted, label, int(caption["weight"]), tracking=0.14))
    parts.append("</g>")
    return "".join(parts)


def _render_observed_field(
    theme: Theme,
    document: TelemetryDocument,
    typography: dict[str, dict[str, float]],
    motion: MotionTokens,
) -> str:
    layout = document.layout
    max_system = max((max(system.bins) for system in document.systems), default=1)
    max_language = max((language.count for language in document.languages), default=1)
    slot_count = len(document.systems[0].bins) if document.systems else 12
    system_rows = []
    language_rows = []
    system_step = 56
    language_step = 18
    system_start = layout.activity.y + 44
    language_start = layout.language.y + 38
    for index, system in enumerate(document.systems):
        system_rows.append(
            _system_row(
                theme,
                system,
                system_start + index * system_step,
                layout,
                typography,
                motion,
                delay_ms=motion.reveal + index * 110,
                max_count=max_system,
                slot_count=slot_count,
            )
        )
    for index, language in enumerate(document.languages):
        language_rows.append(
            _language_row(
                theme,
                language,
                language_start + index * language_step,
                layout,
                typography,
                motion,
                delay_ms=motion.reveal + motion.normal + index * 55,
                max_count=max_language,
            )
        )
    time_labels = document.timeline_labels
    axis_x = layout.activity.x + 214
    axis_width = layout.activity.width - 226
    axis_step = axis_width / 12.0
    axis_marks = []
    for index in range(13):
        x = axis_x + axis_step * index
        axis_marks.append(f'<line x1="{x:.1f}" y1="{layout.activity.y + 26}" x2="{x:.1f}" y2="{layout.activity.y + 32}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.14"/>')
    label_positions = [axis_x + 2, axis_x + axis_width * 0.36, axis_x + axis_width * 0.72]
    label_group = []
    for label, pos in zip(time_labels, label_positions, strict=False):
        label_group.append(_text(theme, pos, layout.activity.y + 18, int(typography["caption"]["size"]), theme.text_secondary, label, int(typography["caption"]["weight"]), tracking=1.4))
    return (
        _reveal_group(
            (
                f'<g>'
                f'<line x1="{layout.activity.x}" y1="{layout.activity.y - 2}" x2="{layout.activity.x + layout.activity.width}" y2="{layout.activity.y - 2}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.24"/>'
                f'<line x1="{layout.language.x - 18}" y1="{layout.language.y - 2}" x2="{layout.language.x + layout.language.width}" y2="{layout.language.y - 2}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.18"/>'
                f'<line x1="{layout.language.x - 18}" y1="{layout.activity.y + 30}" x2="{layout.language.x - 18}" y2="{layout.language.y + layout.language.height - 8}" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.22"/>'
                f'<text x="{layout.activity.x}" y="{layout.activity.y - 16}" font-size="{int(typography["caption"]["size"])}" font-weight="{int(typography["caption"]["weight"])}" letter-spacing="1.3" fill="{theme.text_secondary}">SYSTEM ACTIVITY</text>'
                f'<text x="{layout.language.x}" y="{layout.language.y - 16}" font-size="{int(typography["caption"]["size"])}" font-weight="{int(typography["caption"]["weight"])}" letter-spacing="1.3" fill="{theme.text_secondary}">LANGUAGE FIELD</text>'
                f'{_text(theme, layout.activity.x + 152, layout.activity.y - 16, int(typography["caption"]["size"]), theme.text_muted, "TIME", int(typography["caption"]["weight"]), tracking=1.3)}'
                f'{"".join(label_group)}'
                f'{"".join(axis_marks)}'
                f'{"".join(system_rows)}'
                f'{"".join(language_rows)}'
                f'{_summary_row(theme, document, typography)}'
                "</g>"
            ),
            delay_ms=motion.fast,
            duration_ms=motion.reveal,
            dy=4,
        )
    )


def render_telemetry(mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_TELEMETRY_PATH) -> TelemetryRender:
    bundle = tokens or load_tokens()
    theme = resolve_theme(mode, bundle)
    motion = resolve_motion(bundle)
    document = load_telemetry_document(config_path)
    layout = document.layout
    typography = bundle.typography_scale
    fallback = document.state.upper() != "OBSERVED" or not document.systems or not document.languages
    header_state = document.state if not fallback else "SIGNAL UNRESOLVED"
    title = document.title if not fallback else "TELEMETRY"
    subtitle = document.subtitle if not fallback else "TELEMETRY UNAVAILABLE"
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{layout.canvas_width}" height="{layout.canvas_height}" viewBox="0 0 {layout.canvas_width} {layout.canvas_height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">KalaOS telemetry</title>',
        f'<desc id="desc">Telemetry layer for KalaOS showing observed system activity and the language field.</desc>',
        "<defs>",
        build_primitive_defs(mode, bundle),
        "</defs>",
        f'<rect width="{layout.canvas_width}" height="{layout.canvas_height}" fill="{theme.background}"/>',
        render_background_grid(theme, bundle, opacity=0.11),
        f'<rect x="{layout.frame.x}" y="{layout.frame.y}" width="{layout.frame.width}" height="{layout.frame.height}" rx="{layout.frame.radius}" fill="none" stroke="{theme.border_panel}" stroke-width="{bundle.stroke_widths["standard"]}"/>',
        _text(theme, layout.header_state_x, layout.header_state_y, int(typography["caption"]["size"]), theme.text_secondary, header_state, int(typography["caption"]["weight"]), tracking=1.8),
        _text(theme, layout.header_title_x, layout.header_title_y, int(typography["display_xl"]["size"]), theme.text_primary, title, int(typography["display_xl"]["weight"]), tracking=1.2),
        _text(theme, layout.header_subtitle_x, layout.header_subtitle_y, int(typography["small"]["size"]), theme.text_muted, subtitle, int(typography["small"]["weight"]), tracking=0.2),
        f'<line x1="{layout.header_title_x}" y1="{layout.header_subtitle_y + 12}" x2="{layout.header_title_x + 556}" y2="{layout.header_subtitle_y + 12}" stroke="{theme.border_hairline}" stroke-width="1"/>',
        f'<rect x="{layout.field.x}" y="{layout.field.y}" width="{layout.field.width}" height="{layout.field.height}" rx="{layout.field.radius}" fill="none" stroke="{theme.border_hairline}" stroke-width="1" stroke-opacity="0.44"/>',
    ]
    if fallback:
        parts.append(
            _reveal_group(
                (
                    f'<g>'
                    f'<text x="{layout.activity.x}" y="{layout.activity.y + 28}" font-size="{int(typography["heading"]["size"])}" font-weight="{int(typography["heading"]["weight"])}" letter-spacing="0.6" fill="{theme.text_primary}">NO SIGNAL</text>'
                    f'<text x="{layout.activity.x}" y="{layout.activity.y + 52}" font-size="{int(typography["small"]["size"])}" font-weight="{int(typography["small"]["weight"])}" letter-spacing="0.2" fill="{theme.text_muted}">TELEMETRY UNAVAILABLE</text>'
                    "</g>"
                ),
                delay_ms=motion.reveal,
                duration_ms=motion.reveal,
                dy=4,
            )
        )
    else:
        parts.append(_render_observed_field(theme, document, typography, motion))
    parts.append("</svg>")
    return TelemetryRender(svg="".join(parts), theme_mode=mode)


def write_telemetry(path: Path, mode: str = "dark", tokens: TokenBundle | None = None, config_path: Path | str = DEFAULT_TELEMETRY_PATH) -> Path:
    telemetry = render_telemetry(mode=mode, tokens=tokens, config_path=config_path)
    path.write_text(telemetry.svg, encoding="utf-8")
    return path
