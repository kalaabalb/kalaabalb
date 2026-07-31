#!/usr/bin/env python3
"""Render projects SVGs from projects.json and live GitHub metadata."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from PIL import ImageFont


ROOT = Path(__file__).resolve().parents[1]
FONT_BOLD = ROOT / "fonts" / "LiberationSans-Bold.ttf"
FONT_REGULAR = ROOT / "fonts" / "LiberationSans-Regular.ttf"


@dataclass
class RepoStats:
    full_name: str
    name: str
    description: str
    tags: List[str]
    stars: int
    updated_at: datetime
    languages: Dict[str, int]

    @property
    def repo_url(self) -> str:
        return f"https://github.com/{self.full_name}"


def escape_text(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


@lru_cache(maxsize=None)
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(path, size=size)


def text_width(text: str, size: int, bold: bool = False) -> float:
    font = load_font(size, bold=bold)
    left, top, right, bottom = font.getbbox(text)
    return float(right - left)


def truncate_text(text: str, max_width: float, size: int, bold: bool = False, suffix: str = "…") -> str:
    if not text:
        return text
    if text_width(text, size, bold=bold) <= max_width:
        return text
    chars = len(text)
    while chars > 1:
        candidate = text[:chars].rstrip() + suffix
        if text_width(candidate, size, bold=bold) <= max_width:
            return candidate
        chars -= 1
    return suffix


def wrap_text(text: str, max_width: float, size: int, bold: bool = False, max_lines: int = 2) -> List[str]:
    words = [word for word in text.split() if word]
    if not words:
        return []

    lines: List[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if text_width(candidate, size, bold=bold) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        else:
            lines.append(truncate_text(word, max_width, size, bold=bold))
        current = word
        if len(lines) >= max_lines:
            break

    if len(lines) < max_lines and current:
        if text_width(current, size, bold=bold) <= max_width:
            lines.append(current)
        else:
            lines.append(truncate_text(current, max_width, size, bold=bold))

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if len(lines) == max_lines and len(" ".join(lines)) < len(text):
        lines[-1] = truncate_text(lines[-1], max_width, size, bold=bold)
    return lines


def api_get(path: str, token: str | None) -> object:
    url = f"https://api.github.com{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "kalaabalb-profile-builder",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_projects(path: Path) -> List[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def relative_time(dt: datetime) -> str:
    now = datetime.now(timezone.utc)
    delta = now - dt.astimezone(timezone.utc)
    days = max(0, delta.days)
    if days < 1:
        hours = max(0, delta.seconds // 3600)
        return f"updated {hours}h ago" if hours else "updated just now"
    if days < 31:
        return f"updated {days}d ago"
    if days < 365:
        months = days // 30
        return f"updated {months}mo ago"
    years = days // 365
    return f"updated {years}y ago"


def acronym(name: str) -> str:
    parts = [part for part in name.replace(".", "-").split("-") if part]
    if not parts:
        return "R"
    if len(parts) == 1:
        word = parts[0]
        return (word[:2] if len(word) > 1 else word[:1]).upper()
    if len(parts) == 2:
        return (parts[0][0] + parts[1][0]).upper()
    return "".join(part[0] for part in parts[:3]).upper()


def collect_repo_stats(project: dict, token: str | None) -> RepoStats:
    full_name = project["repo"]
    try:
        repo = api_get(f"/repos/{full_name}", token)
        languages = api_get(f"/repos/{full_name}/languages", token)
        stars = int(repo.get("stargazers_count", 0))
        updated_at = parse_time(repo.get("pushed_at", repo.get("updated_at")))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        repo = {}
        languages = {}
        stars = 0
        updated_at = datetime.now(timezone.utc)
    return RepoStats(
        full_name=full_name,
        name=project["name"],
        description=project["description"],
        tags=list(project.get("tags", [])),
        stars=stars,
        updated_at=updated_at,
        languages=dict(sorted(languages.items(), key=lambda item: item[1], reverse=True)),
    )


def bytes_to_percentages(languages: Dict[str, int]) -> List[Tuple[str, float]]:
    total = sum(languages.values()) or 1
    items = list(languages.items())[:3]
    return [(lang, (amount / total) * 100.0) for lang, amount in items]


def color_for_language(name: str, theme: dict, index: int) -> str:
    palette = [theme["teal"], theme["amber"], theme["sage"]]
    if name.lower() in {"dart", "javascript", "typescript"}:
        return theme["teal"]
    if name.lower() in {"java", "python", "c++", "c"}:
        return theme["amber"]
    return palette[index % len(palette)]


def build_donut(cx: float, cy: float, stats: RepoStats, theme: dict) -> str:
    segments = bytes_to_percentages(stats.languages)
    circumference = 2 * 3.141592653589793 * 28.0
    offset = 0.0
    parts = [
        f'<circle cx="{cx}" cy="{cy}" r="28" fill="none" stroke="{theme["donut_track"]}" stroke-width="10"/>'
    ]
    for idx, (lang, pct) in enumerate(segments):
        length = circumference * pct / 100.0
        seg_color = color_for_language(lang, theme, idx)
        dash = f"{length:.2f} {circumference - length:.2f}"
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="28" fill="none" stroke="{seg_color}" stroke-width="10" stroke-linecap="round" '
            f'transform="rotate(-90 {cx} {cy})" stroke-dasharray="{dash}" stroke-dashoffset="{-offset:.2f}">'
            f'<animate attributeName="stroke-dasharray" values="{dash};{length * 1.05:.2f} {circumference - length * 1.05:.2f};{dash}" dur="6s" repeatCount="indefinite"/>'
            "</circle>"
        )
        offset += length
    return "".join(parts)


def legend_rows(stats: RepoStats, theme: dict, x: float, y: float) -> str:
    parts: List[str] = []
    for idx, (lang, pct) in enumerate(bytes_to_percentages(stats.languages)):
        row_y = y + idx * 18
        color = color_for_language(lang, theme, idx)
        parts.append(f'<circle cx="{x}" cy="{row_y - 4}" r="4" fill="{color}"/>')
        parts.append(
            f'<text x="{x + 12}" y="{row_y}" font-size="11" fill="{theme["muted"]}">{escape_text(lang)} {pct:.0f}%</text>'
        )
    return "".join(parts)


def render_card(stats: RepoStats, theme: dict, x: int, y: int, width: int, height: int) -> str:
    monogram = acronym(stats.name)
    title_width = 160
    desc_width = 168
    display_title = truncate_text(stats.name, title_width, 22, bold=True)
    title = escape_text(display_title)
    description_lines = wrap_text(stats.description, desc_width, 14, max_lines=2)
    tags = stats.tags[:3]
    stars = stats.stars
    updated = relative_time(stats.updated_at)
    html = []
    html.append(f'<a href="{escape_text(stats.repo_url)}">')
    html.append(f'<g transform="translate({x} {y})">')
    html.append(f'<rect width="{width}" height="{height}" rx="18" fill="{theme["card"]}" stroke="{theme["stroke"]}"/>')
    html.append(f'<rect x="18" y="16" width="42" height="5" rx="2.5" fill="{theme["teal"]}"/>')
    html.append(f'<circle cx="32" cy="54" r="18" fill="{theme["badge_bg"]}" stroke="{theme["badge_stroke"]}"/>')
    html.append(f'<text x="32" y="60" text-anchor="middle" fill="{theme["badge_text"]}" font-size="15" font-weight="800">{escape_text(monogram)}</text>')
    html.append(f'<text x="60" y="50" fill="{theme["text"]}" font-size="22" font-weight="800">{title}</text>')
    html.append(
        f'<text x="60" y="50" dx="{len(display_title) * 11 + 8}" fill="{theme["text"]}" font-size="22" font-weight="800" opacity="0.9">_'
        f'<animate attributeName="opacity" values="0;1;1;0" dur="1.1s" repeatCount="indefinite"/>'
        "</text>"
    )
    desc_y = 76
    if description_lines:
        desc_parts = [f'<text x="60" y="{desc_y}" fill="{theme["muted"]}" font-size="14">']
        for idx, line in enumerate(description_lines):
            dy = 0 if idx == 0 else 17
            desc_parts.append(f'<tspan x="60" dy="{dy}">{escape_text(line)}</tspan>')
        desc_parts.append("</text>")
        html.append("".join(desc_parts))

    tag_x = 18
    tag_y = 122 if len(description_lines) > 1 else 118
    for tag in tags:
        label = escape_text(tag)
        box_w = max(54, 10 + len(tag) * 7)
        html.append(f'<rect x="{tag_x}" y="{tag_y}" width="{box_w}" height="22" rx="11" fill="{theme["tag_fill"]}" stroke="{theme["tag_stroke"]}"/>')
        html.append(f'<text x="{tag_x + box_w / 2:.1f}" y="{tag_y + 15}" text-anchor="middle" font-size="11" fill="{theme["tag_text"]}">{label}</text>')
        tag_x += box_w + 8

    html.append(f'<text x="18" y="156" font-size="12" fill="{theme["muted"]}">★ {stars} · {escape_text(updated)}</text>')
    html.append(build_donut(width - 46, 84, stats, theme))
    html.append(legend_rows(stats, theme, width - 110, 42))
    html.append(
        f'<text x="{width - 62}" y="{height - 16}" text-anchor="middle" font-size="11" fill="{theme["muted"]}">'
        f'← click to open'
        "</text>"
    )
    html.append("</g>")
    html.append("</a>")
    return "".join(html)


def render_svg(projects: List[RepoStats], theme: dict, build_id: str) -> str:
    width = 1140
    card_w = 340
    card_h = 176
    gap_x = 22
    gap_y = 16
    start_x = 58
    start_y = 154
    bottom_padding = 40
    rows = max(1, (len(projects) + 1) // 2)
    content_bottom = start_y + rows * card_h + (rows - 1) * gap_y
    height = content_bottom + bottom_padding
    panel_height = height - 58

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">Featured projects</title>',
        f'<desc id="desc">Clickable project cards generated from live GitHub repository data.</desc>',
        f'<!-- build:{escape_text(build_id)} -->',
        f'<rect width="{width}" height="{height}" rx="24" fill="{theme["bg"]}"/>',
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="24" fill="none" stroke="{theme["outer_stroke"]}"/>',
        f'<rect x="58" y="58" width="1024" height="{panel_height}" rx="24" fill="{theme["panel"]}" stroke="{theme["stroke"]}"/>',
        f'<text x="116" y="114" fill="{theme["text"]}" font-size="24" font-weight="800">Featured Projects</text>',
        f'<text x="116" y="134" fill="{theme["muted"]}" font-size="13">Selected public work across web, mobile, backend, and product systems.</text>',
        f'<rect x="116" y="144" width="872" height="2" fill="url(#accent-line)" />',
        "<defs>",
        f'<linearGradient id="accent-line" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{theme["teal"]}"/><stop offset="50%" stop-color="{theme["amber"]}"/><stop offset="100%" stop-color="{theme["sage"]}"/></linearGradient>',
        "</defs>",
    ]

    for index, stats in enumerate(projects):
        col = index % 2
        row = index // 2
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        parts.append(render_card(stats, theme, x, y, card_w, card_h))

    parts.append("</svg>")
    return "\n".join(parts)


def build_theme(name: str) -> dict:
    if name == "dark":
        return {
            "bg": "#070f0e",
            "panel": "#0a1817",
            "stroke": "#173330",
            "outer_stroke": "#233c39",
            "card": "#0b1716",
            "teal": "#54b7b2",
            "amber": "#d39a52",
            "sage": "#8fc97f",
            "text": "#f4efe7",
            "muted": "#c7d0cc",
            "badge_bg": "#122826",
            "badge_stroke": "#54b7b2",
            "badge_text": "#54b7b2",
            "tag_fill": "#132523",
            "tag_stroke": "#5e8f89",
            "tag_text": "#c7d0cc",
            "donut_track": "#203532",
        }
    return {
        "bg": "#f7f4ee",
        "panel": "#ffffff",
        "stroke": "#dad4c9",
        "outer_stroke": "#d5cec2",
        "card": "#ffffff",
        "teal": "#0f6e56",
        "amber": "#95611f",
        "sage": "#3b6d11",
        "text": "#1a2020",
        "muted": "#514f49",
        "badge_bg": "#ecf5f0",
        "badge_stroke": "#0f6e56",
        "badge_text": "#0f6e56",
        "tag_fill": "#f4ede2",
        "tag_stroke": "#c6b9a5",
        "tag_text": "#1a2020",
        "donut_track": "#e6ddd1",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(ROOT / "projects.json"))
    parser.add_argument("--out", default=str(ROOT / "dist-projects"))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    args = parser.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_projects = load_projects(input_path)
    repo_stats: List[RepoStats] = []
    for item in raw_projects:
        repo_stats.append(collect_repo_stats(item, args.token))

    build_id = os.environ.get("GITHUB_SHA", "local")
    dark = render_svg(repo_stats, build_theme("dark"), build_id)
    light = render_svg(repo_stats, build_theme("light"), build_id)

    (out_dir / "projects.svg").write_text(dark, encoding="utf-8")
    (out_dir / "projects-light.svg").write_text(light, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
