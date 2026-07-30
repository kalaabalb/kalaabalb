#!/usr/bin/env python3
"""Build animated profile hero SVGs from the source portrait.

The output is a real SMIL-based point-cloud morph. No <style> or <script> tags.
"""

from __future__ import annotations

import heapq
import math
import os
import random
from collections import deque
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from PIL import Image, ImageFilter, ImageStat


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "profile-portrait.png"
OUT_DARK = ROOT / "dark.svg"
OUT_LIGHT = ROOT / "light.svg"

W = 1180
H = 610
LEFT_X = 52
LEFT_Y = 104
LEFT_W = 378
LEFT_H = 440
RIGHT_X = 457
RIGHT_Y = 104
RIGHT_W = 661
RIGHT_H = 440
POINT_COUNT = 624
RNG = random.Random(97)

HOLD = 3.0
MOVE = 2.0
CYCLE = 25.0
KEY_TIMES = "0;0.12;0.20;0.32;0.40;0.52;0.60;0.72;0.80;0.92;1"
KEY_SPLINES = ";".join(["0.42 0 0.58 1"] * 10)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def rgb_distance(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def average_rgb(pixels: Sequence[Tuple[int, int, int, int]]) -> Tuple[int, int, int]:
    if not pixels:
        return (0, 0, 0)
    r = sum(px[0] for px in pixels) / len(pixels)
    g = sum(px[1] for px in pixels) / len(pixels)
    b = sum(px[2] for px in pixels) / len(pixels)
    return (int(r), int(g), int(b))


def detect_foreground(image: Image.Image) -> Tuple[Image.Image, Image.Image]:
    rgba = image.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    sample = []
    edge = 10
    for y in range(edge):
        for x in range(w):
            sample.append(px[x, y])
            sample.append(px[x, h - 1 - y])
    for x in range(edge):
        for y in range(h):
            sample.append(px[x, y])
            sample.append(px[w - 1 - x, y])
    bg = average_rgb(sample)

    mask = bytearray(w * h)
    threshold = 28.0
    for y in range(h):
        base = y * w
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 16:
                continue
            if rgb_distance((r, g, b), bg) > threshold:
                mask[base + x] = 1

    visited = bytearray(w * h)
    best: List[Tuple[int, int]] = []
    for y in range(h):
        for x in range(w):
            idx = y * w + x
            if not mask[idx] or visited[idx]:
                continue
            queue = deque([idx])
            visited[idx] = 1
            component: List[Tuple[int, int]] = []
            while queue:
                cur = queue.popleft()
                cy, cx = divmod(cur, w)
                component.append((cx, cy))
                if cx > 0:
                    nxt = cur - 1
                    if mask[nxt] and not visited[nxt]:
                        visited[nxt] = 1
                        queue.append(nxt)
                if cx + 1 < w:
                    nxt = cur + 1
                    if mask[nxt] and not visited[nxt]:
                        visited[nxt] = 1
                        queue.append(nxt)
                if cy > 0:
                    nxt = cur - w
                    if mask[nxt] and not visited[nxt]:
                        visited[nxt] = 1
                        queue.append(nxt)
                if cy + 1 < h:
                    nxt = cur + w
                    if mask[nxt] and not visited[nxt]:
                        visited[nxt] = 1
                        queue.append(nxt)
            if len(component) > len(best):
                best = component

    if not best:
        return rgba, Image.new("L", rgba.size, 0)

    min_x = min(x for x, _ in best)
    max_x = max(x for x, _ in best)
    min_y = min(y for _, y in best)
    max_y = max(y for _, y in best)

    pad = 10
    left = max(0, min_x - pad)
    top = max(0, min_y - pad)
    right = min(w, max_x + pad + 1)
    bottom = min(h, max_y + pad + 1)

    cropped = rgba.crop((left, top, right, bottom))
    crop_mask = Image.new("L", (right - left, bottom - top), 0)
    crop_px = crop_mask.load()
    for x, y in best:
        if left <= x < right and top <= y < bottom:
            crop_px[x - left, y - top] = 255

    return cropped, crop_mask


def resize_to_working_canvas(image: Image.Image, mask: Image.Image, target_w: int = 250) -> Tuple[Image.Image, Image.Image]:
    w, h = image.size
    scale = target_w / float(w)
    target_h = max(1, int(round(h * scale)))
    return image.resize((target_w, target_h), Image.LANCZOS), mask.resize((target_w, target_h), Image.NEAREST)


def weighted_sample_points(image: Image.Image, mask: Image.Image, count: int) -> List[Tuple[float, float]]:
    gray = image.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    gray_px = list(gray.getdata())
    edge_px = list(edges.getdata())
    mask_px = list(mask.getdata())
    w, h = image.size

    heap: List[Tuple[float, Tuple[int, int]]] = []
    for y in range(h):
        row = y * w
        for x in range(w):
            if not mask_px[row + x]:
                continue
            dark = 1.0 - (gray_px[row + x] / 255.0)
            edge = edge_px[row + x] / 255.0
            weight = max(0.01, 0.68 * edge + 0.32 * dark)
            key = RNG.random() ** (1.0 / weight)
            item = (key, (x, y))
            if len(heap) < count:
                heapq.heappush(heap, item)
            elif key > heap[0][0]:
                heapq.heapreplace(heap, item)

    points = [point for _, point in heap]
    points.sort(key=lambda p: (p[1], p[0]))
    if len(points) < count:
        fallback = [(x, y) for y in range(h) for x in range(w) if mask_px[y * w + x]]
        fallback.sort(key=lambda p: (p[1], p[0]))
        while len(points) < count and fallback:
            points.append(fallback[len(points) % len(fallback)])
    return [(float(x), float(y)) for x, y in points[:count]]


def scale_points(
    points: Sequence[Tuple[float, float]],
    source_size: Tuple[int, int],
    target_box: Tuple[float, float, float, float],
) -> List[Tuple[float, float]]:
    src_w, src_h = source_size
    left, top, width, height = target_box
    scaled = []
    for x, y in points:
        sx = left + (x / max(1.0, src_w - 1.0)) * width
        sy = top + (y / max(1.0, src_h - 1.0)) * height
        scaled.append((sx, sy))
    return scaled


def sort_points(points: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
    cx = sum(x for x, _ in points) / len(points)
    cy = sum(y for _, y in points) / len(points)
    return sorted(points, key=lambda p: (math.atan2(p[1] - cy, p[0] - cx), p[1], p[0]))


def point_in_polygon(x: float, y: float, polygon: Sequence[Tuple[float, float]]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        intersect = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi
        )
        if intersect:
            inside = not inside
        j = i
    return inside


def sample_polygon(points: Sequence[Tuple[float, float]], count: int, jitter: float = 0.65) -> List[Tuple[float, float]]:
    min_x = min(x for x, _ in points)
    max_x = max(x for x, _ in points)
    min_y = min(y for _, y in points)
    max_y = max(y for _, y in points)
    candidates: List[Tuple[float, float]] = []
    step = max(4.0, math.sqrt((max_x - min_x) * (max_y - min_y) / max(1, count)) * 0.85)
    y = min_y
    while y <= max_y + 1:
        x = min_x
        while x <= max_x + 1:
            jx = x + (RNG.random() - 0.5) * jitter * step
            jy = y + (RNG.random() - 0.5) * jitter * step
            if point_in_polygon(jx, jy, points):
                candidates.append((jx, jy))
            x += step
        y += step
    if len(candidates) < count:
        while len(candidates) < count:
            candidates.append((RNG.uniform(min_x, max_x), RNG.uniform(min_y, max_y)))
    candidates.sort(key=lambda p: (p[1], p[0]))
    return candidates[:count]


def sample_ellipse_ring(
    center: Tuple[float, float],
    rx: float,
    ry: float,
    count: int,
    rotation: float = 0.0,
    phase: float = 0.0,
) -> List[Tuple[float, float]]:
    cx, cy = center
    pts: List[Tuple[float, float]] = []
    for i in range(count):
        t = phase + (i / count) * math.tau
        x = rx * math.cos(t)
        y = ry * math.sin(t)
        xr = x * math.cos(rotation) - y * math.sin(rotation)
        yr = x * math.sin(rotation) + y * math.cos(rotation)
        pts.append((cx + xr, cy + yr))
    return pts


def sample_hexagon_ring(center: Tuple[float, float], radius: float, count: int) -> List[Tuple[float, float]]:
    cx, cy = center
    outer = []
    inner = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        outer.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        inner.append((cx + radius * 0.62 * math.cos(angle), cy + radius * 0.62 * math.sin(angle)))
    pts: List[Tuple[float, float]] = []
    per_edge = max(1, count // 12)
    for ring in (outer, inner):
        for i in range(6):
            x1, y1 = ring[i]
            x2, y2 = ring[(i + 1) % 6]
            for j in range(per_edge):
                t = j / max(1, per_edge)
                pts.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
    while len(pts) < count:
        angle = RNG.random() * math.tau
        radius_j = radius * (0.60 + 0.10 * RNG.random())
        pts.append((cx + radius_j * math.cos(angle), cy + radius_j * math.sin(angle)))
    pts.sort(key=lambda p: (p[1], p[0]))
    return pts[:count]


def sample_flame_shape(center: Tuple[float, float], width: float, height: float, count: int) -> List[Tuple[float, float]]:
    cx, cy = center
    outline = [
        (cx, cy - height * 0.48),
        (cx + width * 0.16, cy - height * 0.28),
        (cx + width * 0.30, cy - height * 0.06),
        (cx + width * 0.22, cy + height * 0.24),
        (cx, cy + height * 0.48),
        (cx - width * 0.22, cy + height * 0.18),
        (cx - width * 0.30, cy - height * 0.08),
        (cx - width * 0.15, cy - height * 0.28),
    ]
    return sample_polygon(outline, count, jitter=0.78)


def sample_flutter_shape(center: Tuple[float, float], width: float, height: float, count: int) -> List[Tuple[float, float]]:
    cx, cy = center
    ribbon = [
        (cx - width * 0.34, cy + height * 0.08),
        (cx - width * 0.02, cy - height * 0.34),
        (cx + width * 0.28, cy - height * 0.34),
        (cx - width * 0.02, cy),
        (cx + width * 0.33, cy + height * 0.34),
        (cx + width * 0.02, cy + height * 0.34),
        (cx - width * 0.30, cy + height * 0.02),
    ]
    return sample_polygon(ribbon, count, jitter=0.72)


def sample_react_shape(center: Tuple[float, float], width: float, height: float, count: int) -> List[Tuple[float, float]]:
    cx, cy = center
    orbital = int(count * 0.84)
    core = count - orbital
    orbit_counts = [orbital // 3, orbital // 3, orbital - 2 * (orbital // 3)]
    pts: List[Tuple[float, float]] = []
    for idx, rotation in enumerate((0.0, math.pi / 3.0, 2 * math.pi / 3.0)):
        pts.extend(
            sample_ellipse_ring(
                (cx, cy),
                width * 0.42,
                height * 0.14,
                orbit_counts[idx],
                rotation=rotation,
            )
        )
    for _ in range(core):
        angle = RNG.random() * math.tau
        radius = min(width, height) * 0.08 * math.sqrt(RNG.random())
        pts.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    pts.sort(key=lambda p: (p[1], p[0]))
    return pts[:count]


def sample_node_shape(center: Tuple[float, float], radius: float, count: int) -> List[Tuple[float, float]]:
    cx, cy = center
    outer = []
    inner = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        outer.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        inner.append((cx + radius * 0.54 * math.cos(angle), cy + radius * 0.54 * math.sin(angle)))
    pts = sample_polygon(outer + [outer[0]], count // 2, jitter=0.52)
    pts += sample_polygon(inner + [inner[0]], count - len(pts), jitter=0.42)
    pts.sort(key=lambda p: (p[1], p[0]))
    return pts[:count]


def make_state_points() -> Tuple[List[Tuple[float, float]], ...]:
    raw = Image.open(SOURCE)
    cropped, mask = detect_foreground(raw)
    resized, resized_mask = resize_to_working_canvas(cropped, mask, target_w=250)
    portrait_raw = weighted_sample_points(resized, resized_mask, POINT_COUNT)
    portrait_raw = sort_points(portrait_raw)

    portrait = scale_points(portrait_raw, resized.size, (84, 138, 214, 312))
    flutter = sample_flutter_shape((191, 262), 220, 250, POINT_COUNT)
    react = sample_react_shape((191, 262), 240, 200, POINT_COUNT)
    node = sample_node_shape((191, 262), 120, POINT_COUNT)
    firebase = sample_flame_shape((191, 262), 180, 250, POINT_COUNT)
    return portrait, flutter, react, node, firebase


def escape_text(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def animate_values(values: Sequence[Tuple[float, float]]) -> Tuple[str, str]:
    path = [values[0], values[0], values[1], values[1], values[2], values[2], values[3], values[3], values[4], values[4], values[0]]
    xs = ";".join(f"{x:.2f}" for x, _ in path)
    ys = ";".join(f"{y:.2f}" for _, y in path)
    return xs, ys


def circle_fill(index: int, theme: dict) -> str:
    palette = [theme["text"], theme["teal"], theme["amber"], theme["sage"]]
    return palette[index % len(palette)]


def build_svg(theme: dict, out_path: Path) -> None:
    states = make_state_points()
    xs = []
    ys = []
    for i in range(POINT_COUNT):
        pt_states = [state[i] for state in states]
        x_values, y_values = animate_values(pt_states)
        xs.append(x_values)
        ys.append(y_values)

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Liberation Mono\',monospace" '
        f'role="img" aria-labelledby="title desc">'
    )
    lines.append(f'<title id="title">{escape_text(theme["title"])}</title>')
    lines.append(f'<desc id="desc">{escape_text(theme["desc"])}</desc>')
    lines.append("<defs>")
    lines.append(
        f'<linearGradient id="frame" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{theme["teal"]}"/>'
        f'<stop offset="0.5" stop-color="{theme["amber"]}"/>'
        f'<stop offset="1" stop-color="{theme["sage"]}"/>'
        f"</linearGradient>"
    )
    lines.append("</defs>")
    lines.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="18" fill="{theme["bg"]}"/>')
    lines.append("<g>")
    lines.append(f'<rect x="20" y="20" width="1140" height="570" rx="18" fill="{theme["panel"]}" stroke="{theme["panel_stroke"]}"/>')
    lines.append(f'<rect x="20" y="20" width="1140" height="46" rx="18" fill="{theme["topbar"]}"/>')
    lines.append('<circle cx="48" cy="43" r="5.5" fill="#ff5f56"/>')
    lines.append('<circle cx="68" cy="43" r="5.5" fill="#ffbd2e"/>')
    lines.append('<circle cx="88" cy="43" r="5.5" fill="#27c93f"/>')
    lines.append(
        f'<text x="590" y="48" text-anchor="middle" font-size="12" fill="{theme["muted"]}">'
        f'{escape_text(theme["terminal"])}'
        "</text>"
    )
    lines.append(f'<text x="52" y="94" font-size="10" letter-spacing="3" fill="{theme["muted_dim"]}">VISUAL.MAP</text>')
    lines.append(f'<rect x="52" y="104" width="378" height="440" rx="10" fill="{theme["canvas"]}" stroke="{theme["teal"]}" stroke-width="2"/>')
    lines.append(f'<rect x="52" y="104" width="378" height="440" rx="10" fill="none" stroke="url(#frame)" stroke-width="2"/>')
    lines.append(f'<circle cx="371" cy="150" r="2.8" fill="{theme["amber"]}"/>')
    lines.append(f'<circle cx="382" cy="162" r="1.8" fill="{theme["sage"]}" opacity="0.7"/>')

    for i in range(POINT_COUNT):
        x_anim = xs[i]
        y_anim = ys[i]
        fill = circle_fill(i, theme)
        lines.append(
            f'<circle cx="{states[0][i][0]:.2f}" cy="{states[0][i][1]:.2f}" r="{theme["dot_r"]}" fill="{fill}" fill-opacity="0.95">'
            f'<animate attributeName="cx" values="{x_anim}" keyTimes="{KEY_TIMES}" keySplines="{KEY_SPLINES}" calcMode="spline" dur="{CYCLE}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cy" values="{y_anim}" keyTimes="{KEY_TIMES}" keySplines="{KEY_SPLINES}" calcMode="spline" dur="{CYCLE}s" repeatCount="indefinite"/>'
            "</circle>"
        )

    lines.append(
        f'<text x="64" y="520" font-size="11" fill="{theme["muted"]}">terminal render: portrait → point cloud</text>'
    )

    lines.append(f'<rect x="{RIGHT_X}" y="{RIGHT_Y}" width="{RIGHT_W}" height="{RIGHT_H}" rx="10" fill="{theme["panel_right"]}" stroke="{theme["panel_stroke"]}"/>')
    lines.append(f'<text x="486" y="140" font-size="18" fill="{theme["teal"]}" font-weight="700" letter-spacing="1.1">SYSTEM.INFO</text>')
    lines.append(f'<text x="1049" y="140" font-size="16" fill="{theme["accent_live"]}" font-weight="700">● LIVE</text>')
    lines.append(f'<rect x="486" y="154" width="180" height="24" rx="6" fill="{theme["accent_bar"]}"/>')
    lines.append(f'<text x="496" y="171" font-size="14" fill="{theme["accent_text"]}" font-weight="700">{escape_text(theme["mail"])}</text>')

    info_rows = [
        ("Subject", "kalaab Alex"),
        ("Role", "Frontend & Backend Developer"),
        ("Origin", "Ethiopia"),
        ("Status", "Building. Shipping. Learning."),
        ("Core.Lang", "Dart, JavaScript"),
        ("Core.Frontend", "React, Flutter"),
        ("Core.Backend", "Node.js, Express"),
        ("Core.Database", "MongoDB, MySQL, PostgreSQL"),
        ("Core.Infra", "Firebase, Docker, Git, Linux"),
    ]
    row_y = 204
    for label, value in info_rows:
        lines.append(f'<text x="486" y="{row_y}" fill="{theme["teal"]}">{escape_text(label)}</text>')
        lines.append(f'<text x="1102" y="{row_y}" text-anchor="end" font-weight="700" fill="{theme["text"]}">{escape_text(value)}</text>')
        row_y += 26 if label not in {"Core.Database", "Core.Infra"} else 24

    chip_specs = [
        ("Flutter", 80, theme["chip_fill_teal"], theme["chip_stroke_teal"]),
        ("Dart", 60, theme["chip_fill_amber"], theme["chip_stroke_amber"]),
        ("React", 70, theme["chip_fill_teal"], theme["chip_stroke_teal"]),
        ("Node.js", 88, theme["chip_fill_amber"], theme["chip_stroke_amber"]),
        ("Firebase", 90, theme["chip_fill_teal"], theme["chip_stroke_teal"]),
    ]
    x = 486
    for text, width, fill, stroke in chip_specs:
        lines.append(f'<rect x="{x}" y="488" width="{width}" height="22" rx="11" fill="{fill}" stroke="{stroke}"/>')
        lines.append(
            f'<text x="{x + width / 2:.1f}" y="503" text-anchor="middle" font-size="12" fill="{stroke}">{escape_text(text)}</text>'
        )
        x += width + 8

    lines.append(f'<text x="486" y="540" font-size="14" fill="{theme["muted"]}">▸ More about me &amp; projects below in README ↓</text>')
    lines.append(f'<rect x="1104" y="532" width="8" height="16" fill="{theme["teal"]}"/>')
    lines.append("</g>")
    lines.append("</svg>")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    dark = {
        "title": "kalaab Alex profile.sh",
        "desc": "Dark mode hero banner for the GitHub profile README.",
        "bg": "#070f0e",
        "panel": "#0a1817",
        "panel_right": "#0a1817",
        "panel_stroke": "#18302d",
        "topbar": "#0f1d1b",
        "canvas": "#071313",
        "teal": "#54b7b2",
        "amber": "#d39a52",
        "sage": "#8fc97f",
        "text": "#f4efe7",
        "muted": "#c7d0cc",
        "muted_dim": "#7f8d89",
        "accent_live": "#d39a52",
        "accent_bar": "#31242a",
        "accent_text": "#f4efe7",
        "chip_fill_teal": "#112725",
        "chip_stroke_teal": "#54b7b2",
        "chip_fill_amber": "#241a12",
        "chip_stroke_amber": "#d39a52",
        "mail": "kalaabalb.connect@gmail.com",
        "terminal": "kalaabalb.connect@gmail.com - % ./profile.sh --live",
        "dot_r": "1.55",
    }
    light = {
        "title": "kalaab Alex profile.sh",
        "desc": "Light mode hero banner for the GitHub profile README.",
        "bg": "#f7f4ee",
        "panel": "#ffffff",
        "panel_right": "#ffffff",
        "panel_stroke": "#d8d2c8",
        "topbar": "#f1ece3",
        "canvas": "#ffffff",
        "teal": "#0f6e56",
        "amber": "#95611f",
        "sage": "#3b6d11",
        "text": "#1a2020",
        "muted": "#514f49",
        "muted_dim": "#8d857a",
        "accent_live": "#95611f",
        "accent_bar": "#ece3d7",
        "accent_text": "#1a2020",
        "chip_fill_teal": "#edf6f3",
        "chip_stroke_teal": "#0f6e56",
        "chip_fill_amber": "#f4ecdf",
        "chip_stroke_amber": "#95611f",
        "mail": "kalaabalb.connect@gmail.com",
        "terminal": "kalaabalb.connect@gmail.com - % ./profile.sh --live",
        "dot_r": "1.55",
    }
    build_svg(dark, OUT_DARK)
    build_svg(light, OUT_LIGHT)


if __name__ == "__main__":
    main()
