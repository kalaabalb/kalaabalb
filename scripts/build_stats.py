#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.parse import quote
from urllib.request import Request, urlopen

from PIL import ImageFont


ROOT = Path(__file__).resolve().parents[1]
FONT_REGULAR = ROOT / "fonts" / "LiberationSans-Regular.ttf"
FONT_BOLD = ROOT / "fonts" / "LiberationSans-Bold.ttf"


@dataclass(frozen=True)
class RepoInfo:
    name: str
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    language: str | None
    languages_url: str


@dataclass(frozen=True)
class UserInfo:
    login: str
    name: str | None
    public_repos: int
    followers: int
    following: int


def escape_text(value: str) -> str:
    return html.escape(value, quote=True)


@lru_cache(maxsize=None)
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(str(path), size)


def text_width(text: str, size: int, bold: bool = False) -> int:
    font = load_font(size, bold)
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def truncate_text(text: str, max_width: int, size: int, bold: bool = False) -> str:
    if text_width(text, size, bold) <= max_width:
        return text
    ellipsis = "…"
    if text_width(ellipsis, size, bold) > max_width:
        return ""
    left, right = 0, len(text)
    while left < right:
        mid = (left + right) // 2
        candidate = text[:mid].rstrip() + ellipsis
        if text_width(candidate, size, bold) <= max_width:
            left = mid + 1
        else:
            right = mid
    return text[: max(0, right - 1)].rstrip() + ellipsis


def fetch_json(url: str, token: str | None = None) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "kalaabalb-profile-stats/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_user(username: str, token: str | None) -> UserInfo:
    data = fetch_json(f"https://api.github.com/users/{quote(username)}", token)
    assert isinstance(data, dict)
    return UserInfo(
        login=data["login"],
        name=data.get("name"),
        public_repos=int(data["public_repos"]),
        followers=int(data["followers"]),
        following=int(data["following"]),
    )


def fetch_repos(username: str, token: str | None) -> List[RepoInfo]:
    repos: List[RepoInfo] = []
    page = 1
    while True:
        data = fetch_json(
            f"https://api.github.com/users/{quote(username)}/repos?per_page=100&page={page}&type=owner&sort=updated",
            token,
        )
        assert isinstance(data, list)
        if not data:
            break
        for item in data:
            repos.append(
                RepoInfo(
                    name=item["name"],
                    stargazers_count=int(item["stargazers_count"]),
                    forks_count=int(item["forks_count"]),
                    open_issues_count=int(item["open_issues_count"]),
                    language=item.get("language"),
                    languages_url=item["languages_url"],
                )
            )
        if len(data) < 100:
            break
        page += 1
    return repos


def fetch_language_bytes(repos: Iterable[RepoInfo], token: str | None) -> Dict[str, int]:
    totals: Dict[str, int] = {}
    for repo in repos:
        if repo.name.endswith(".github.io"):
            continue
        data = fetch_json(repo.languages_url, token)
        assert isinstance(data, dict)
        for language, value in data.items():
            totals[language] = totals.get(language, 0) + int(value)
    return totals


def bytes_to_percentages(data: Dict[str, int], limit: int = 8) -> List[Tuple[str, float]]:
    ordered = sorted(data.items(), key=lambda item: item[1], reverse=True)
    ordered = ordered[:limit]
    total = sum(value for _, value in ordered) or 1
    return [(language, value * 100.0 / total) for language, value in ordered]


def color_for_language(language: str, theme: dict, index: int) -> str:
    palette = theme["palette"]
    return palette[index % len(palette)]


def legend_label(name: str) -> str:
    mapping = {
        "javascript": "JS",
        "typescript": "TS",
        "python": "Py",
        "dart": "Dart",
        "java": "Java",
        "html": "HTML",
        "css": "CSS",
        "c++": "C++",
        "c": "C",
        "cmake": "CMake",
        "node.js": "Node",
        "shell": "Shell",
        "objective-c": "ObjC",
    }
    return mapping.get(name.lower(), name)


def render_star_field(theme: dict) -> str:
    stars = []
    points = [
        (16, 18), (44, 36), (96, 20), (138, 51), (179, 28), (234, 41), (282, 17),
        (342, 30), (408, 19), (462, 44), (26, 198), (72, 182), (154, 194),
        (212, 184), (269, 196), (338, 181), (422, 192), (472, 170),
    ]
    palette = [theme["star"], theme["star_soft"], theme["star_warm"]]
    for idx, (x, y) in enumerate(points):
        stars.append(f'<circle cx="{x}" cy="{y}" r="{0.7 + (idx % 2) * 0.15:.2f}" fill="{palette[idx % len(palette)]}" fill-opacity="0.16"/>')
    return "".join(stars)


def build_theme(mode: str) -> dict:
    if mode == "light":
        return {
            "bg": "#f5f0ff",
            "panel": "#fffdfc",
            "border": "#d8cfef",
            "title": "#7c3aed",
            "text": "#1d1730",
            "muted": "#5d5470",
            "accent": "#7c3aed",
            "chip_bg": "#f1ebff",
            "chip_text": "#7c3aed",
            "star": "#d9ccff",
            "star_soft": "#b8a3e4",
            "star_warm": "#c97c2d",
            "palette": ["#7c3aed", "#d39a52", "#9a5f1c", "#a78bfa", "#c4b5fd", "#8b5cf6"],
        }
    return {
        "bg": "#070812",
        "panel": "#0a0b18",
        "border": "#2d2257",
        "title": "#a78bfa",
        "text": "#f6f0ff",
        "muted": "#c6b9e8",
        "accent": "#a78bfa",
        "chip_bg": "#15132b",
        "chip_text": "#d6c8f5",
        "star": "#d9ccff",
        "star_soft": "#7c6aa9",
        "star_warm": "#d39a52",
        "palette": ["#a78bfa", "#d39a52", "#c4b5fd", "#8b5cf6", "#d8cbff", "#f59e0b"],
    }


def metric_box(x: int, y: int, w: int, h: int, title: str, value: str, theme: dict) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{theme["bg"]}" stroke="{theme["border"]}" stroke-opacity="0.35"/>'
        f'<text x="{x + 16}" y="{y + 18}" font-size="10" fill="{theme["muted"]}">{escape_text(title)}</text>'
        f'<text x="{x + 16}" y="{y + 42}" font-size="19" font-weight="700" fill="{theme["text"]}">{escape_text(value)}</text>'
    )


def stat_card(user: UserInfo, repos: List[RepoInfo], theme: dict, build_id: str) -> str:
    total_stars = sum(repo.stargazers_count for repo in repos)
    total_forks = sum(repo.forks_count for repo in repos)
    total_issues = sum(repo.open_issues_count for repo in repos)
    name = user.name or user.login
    display_name = truncate_text(f"{name}'s GitHub stats", 240, 22, bold=True)

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<!-- build:{escape_text(build_id)} -->',
        '<svg xmlns="http://www.w3.org/2000/svg" width="495" height="230" viewBox="0 0 495 230">',
        render_star_field(theme),
        f'<rect width="495" height="230" rx="18" fill="{theme["panel"]}" stroke="{theme["border"]}" stroke-opacity="0.35"/>',
        f'<text x="20" y="32" font-family="Liberation Sans, sans-serif" font-size="22" font-weight="700" fill="{theme["title"]}">{escape_text(display_name)}</text>',
        f'<text x="20" y="52" font-family="Liberation Sans, sans-serif" font-size="11" fill="{theme["muted"]}">consecutive transmission days / repo-owned SVG</text>',
    ]

    boxes = [
        ("Public Repos", str(user.public_repos)),
        ("Total Stars", str(total_stars)),
        ("Followers", str(user.followers)),
        ("Following", str(user.following)),
    ]
    for idx, (label, value) in enumerate(boxes):
        col = idx % 2
        row = idx // 2
        x = 18 + col * 226
        y = 70 + row * 62
        parts.append(metric_box(x, y, 210, 56, label, value, theme))

    parts.append(
        f'<text x="20" y="216" font-family="Liberation Sans, sans-serif" font-size="10" fill="{theme["muted"]}">Issues in public repos: {total_issues}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def lang_card(user: UserInfo, language_bytes: Dict[str, int], theme: dict, build_id: str) -> str:
    rows = bytes_to_percentages(language_bytes, limit=6)
    total = sum(language_bytes.values()) or 1

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<!-- build:{escape_text(build_id)} -->',
        '<svg xmlns="http://www.w3.org/2000/svg" width="495" height="230" viewBox="0 0 495 230">',
        render_star_field(theme),
        f'<rect width="495" height="230" rx="18" fill="{theme["panel"]}" stroke="{theme["border"]}" stroke-opacity="0.35"/>',
        f'<text x="20" y="32" font-family="Liberation Sans, sans-serif" font-size="22" font-weight="700" fill="{theme["title"]}">Telemetry</text>',
        f'<text x="20" y="52" font-family="Liberation Sans, sans-serif" font-size="11" fill="{theme["muted"]}">aggregated from your public repositories</text>',
    ]

    bar_x = 20
    bar_y = 72
    bar_w = 455
    bar_h = 12
    parts.append(
        f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="6" fill="{theme["bg"]}" opacity="0.8"/>'
    )
    cursor = bar_x
    for idx, (lang, pct) in enumerate(rows):
        width = bar_w * pct / 100.0
        color = color_for_language(lang, theme, idx)
        parts.append(
            f'<rect x="{cursor:.2f}" y="{bar_y}" width="{width:.2f}" height="{bar_h}" rx="6" fill="{color}"/>'
        )
        cursor += width

    legend_top = 104
    max_text_width = 170
    for idx, (lang, pct) in enumerate(rows):
        row_y = legend_top + idx * 23
        color = color_for_language(lang, theme, idx)
        label = f"{legend_label(lang)} {pct:.0f}%"
        label = truncate_text(label, max_text_width, 11)
        parts.append(f'<circle cx="26" cy="{row_y - 4}" r="4" fill="{color}"/>')
        parts.append(
            f'<text x="36" y="{row_y}" font-family="Liberation Sans, sans-serif" font-size="11" fill="{theme["text"]}">{escape_text(label)}</text>'
        )

    parts.append(
        f'<text x="344" y="216" font-family="Liberation Sans, sans-serif" font-size="10" fill="{theme["muted"]}">{len(language_bytes)} languages / {total} bytes</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def render_svg(svg: str, out_path: Path) -> None:
    out_path.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="kalaabalb")
    parser.add_argument("--out", default="dist-stats")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    user = fetch_user(args.username, token)
    repos = fetch_repos(args.username, token)
    language_bytes = fetch_language_bytes([repo for repo in repos if repo.language or repo.languages_url], token)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    build_id = os.environ.get("GITHUB_SHA", "local")

    render_svg(stat_card(user, repos, build_theme("dark"), build_id), out_dir / "stats-dark.svg")
    render_svg(stat_card(user, repos, build_theme("light"), build_id), out_dir / "stats-light.svg")
    render_svg(lang_card(user, language_bytes, build_theme("dark"), build_id), out_dir / "langs-dark.svg")
    render_svg(lang_card(user, language_bytes, build_theme("light"), build_id), out_dir / "langs-light.svg")


if __name__ == "__main__":
    main()
