#!/usr/bin/env python3
"""Build animated profile hero SVGs from the source portrait.

The output is a real SMIL-based point-cloud morph. No <style> or <script> tags.
"""

from __future__ import annotations

import heapq
import json
import math
import os
import random
from collections import deque
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "hero-portrait.png"
ASSET_DIR = ROOT / "assets"
PORTRAIT_DENSE = ASSET_DIR / "portrait_dense_final.json"
LOGO_CLOUDS = ASSET_DIR / "logo_clouds.json"
PORTRAIT_REFERENCE = ASSET_DIR / "portrait_reference_render.svg"
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
FONT_REGULAR = ROOT / "fonts" / "LiberationSans-Regular.ttf"
FONT_BOLD = ROOT / "fonts" / "LiberationSans-Bold.ttf"
WORKING_CANVAS = 440.0
PORTRAIT_OPACITY_TIMES = "0;0.22;0.30;0.92;1"
MORPH_OPACITY_TIMES = "0;0.20;0.30;0.94;1"
MORPH_KEY_TIMES = "0;0.10;0.25;0.35;0.50;0.60;0.75;0.85;1.0"
MORPH_KEY_SPLINES = ";".join(["0.3 0 0.7 1"] * 8)

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

    pad = 4
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


def crop_portrait_focus(image: Image.Image) -> Image.Image:
    w, h = image.size
    left = int(round(w * 0.10))
    top = int(round(h * 0.00))
    right = int(round(w * 0.88))
    bottom = int(round(h * 0.84))
    return image.crop((left, top, right, bottom))


def sample_portrait_grid(image: Image.Image, mask: Image.Image, count: int) -> List[Tuple[float, float]]:
    gray = image.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    w, h = image.size
    gray_px = list(gray.getdata())
    edge_px = list(edges.getdata())
    mask_px = list(mask.getdata())
    px = image.load()

    def background_color() -> Tuple[int, int, int]:
        sample = []
        edge = 8
        for y in range(edge):
            for x in range(w):
                sample.append(px[x, y])
                sample.append(px[x, h - 1 - y])
        for x in range(edge):
            for y in range(h):
                sample.append(px[x, y])
                sample.append(px[w - 1 - x, y])
        return average_rgb(sample)

    bg = background_color()

    cols = 32
    rows = 24
    step_x = w / float(cols)
    step_y = h / float(rows)

    def scan(require_mask: bool) -> List[Tuple[float, float, float]]:
        cells: List[Tuple[float, float, float]] = []
        for row in range(rows):
            for col in range(cols):
                cx = (col + 0.5) * step_x
                cy = (row + 0.5) * step_y
                ix = min(w - 1, max(0, int(round(cx))))
                iy = min(h - 1, max(0, int(round(cy))))
                if require_mask and not mask_px[iy * w + ix]:
                    continue
                r, g, b, a = px[ix, iy]
                if a < 16:
                    continue
                dist = rgb_distance((r, g, b), bg)
                edge_value = edge_px[iy * w + ix] / 255.0
                lum = gray_px[iy * w + ix] / 255.0
                fx = (cx - w * 0.5) / max(1.0, w * 0.24)
                fy = (cy - h * 0.42) / max(1.0, h * 0.30)
                face_focus = math.exp(-(fx * fx + fy * fy))
                score = dist * 0.38 + edge_value * 130.0 + (1.0 - lum) * 28.0 + face_focus * 110.0
                cells.append((score, cx, cy))
        return cells

    cells = scan(require_mask=True)
    if len(cells) < max(80, count // 2):
        cells = scan(require_mask=False)

    cells.sort(key=lambda item: item[0], reverse=True)
    selected = cells[:count]
    points: List[Tuple[float, float]] = []
    for _, cx, cy in selected:
        jx = clamp(cx + (RNG.random() - 0.5) * step_x * 0.22, 0.0, w - 1.0)
        jy = clamp(cy + (RNG.random() - 0.5) * step_y * 0.22, 0.0, h - 1.0)
        points.append((jx, jy))
    return sort_points(points)


def build_subject_mask(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    ycbcr = image.convert("YCbCr")
    gray = image.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    w, h = image.size
    gray_px = list(gray.getdata())
    edge_px = list(edges.getdata())
    ycbcr_px = list(ycbcr.getdata())

    mask = Image.new("L", (w, h), 0)
    mask_px = mask.load()
    cx = (w - 1) / 2.0
    cy = (h - 1) / 2.0
    rx = w * 0.44
    ry = h * 0.46

    for y in range(h):
        for x in range(w):
            dx = (x - cx) / max(1.0, rx)
            dy = (y - cy) / max(1.0, ry)
            if dx * dx + dy * dy > 1.0:
                continue
            yy, cb, cr = ycbcr_px[y * w + x]
            dark = gray_px[y * w + x] < 145
            edge = edge_px[y * w + x] > 18
            skin = 77 <= cb <= 135 and 133 <= cr <= 180 and yy > 35
            if skin or (dark and edge) or edge:
                mask_px[x, y] = 255

    visited = bytearray(w * h)
    start = (int(round(cx)), int(round(cy)))
    if not mask_px[start[0], start[1]]:
        best = None
        best_dist = float("inf")
        for y in range(h):
            base = y * w
            for x in range(w):
                if not mask.getpixel((x, y)):
                    continue
                dist = (x - cx) ** 2 + (y - cy) ** 2
                if dist < best_dist:
                    best = (x, y)
                    best_dist = dist
        if best is None:
            return mask
        start = best

    queue = deque([start])
    visited[start[1] * w + start[0]] = 1
    component: List[Tuple[int, int]] = []
    while queue:
        x, y = queue.popleft()
        component.append((x, y))
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if not (0 <= nx < w and 0 <= ny < h):
                continue
            idx = ny * w + nx
            if visited[idx] or not mask_px[nx, ny]:
                continue
            visited[idx] = 1
            queue.append((nx, ny))

    if not component:
        return mask

    component_mask = Image.new("L", (w, h), 0)
    comp_px = component_mask.load()
    for x, y in component:
        comp_px[x, y] = 255
    return component_mask


def weighted_sample_points(image: Image.Image, mask: Image.Image, count: int) -> List[Tuple[float, float]]:
    gray = image.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    gray_px = list(gray.getdata())
    edge_px = list(edges.getdata())
    mask_px = list(mask.getdata())
    w, h = image.size

    candidates: List[Tuple[float, int, int]] = []
    for y in range(h):
        row = y * w
        for x in range(w):
            if not mask_px[row + x]:
                continue
            dark = 1.0 - (gray_px[row + x] / 255.0)
            edge = edge_px[row + x] / 255.0
            weight = max(0.01, 0.88 * edge + 0.12 * dark)
            candidates.append((weight, x, y))

    if not candidates:
        return [(0.0, 0.0)] * count

    candidates.sort(key=lambda item: item[0], reverse=True)
    trim = max(count * 4, int(len(candidates) * 0.62))
    candidates = candidates[:trim]

    heap: List[Tuple[float, Tuple[int, int]]] = []
    for weight, x, y in candidates:
        key = RNG.random() ** (1.0 / weight)
        item = (key, (x, y))
        if len(heap) < count:
            heapq.heappush(heap, item)
        elif key > heap[0][0]:
            heapq.heapreplace(heap, item)

    points = [point for _, point in heap]
    points.sort(key=lambda p: (p[1], p[0]))
    if len(points) < count:
        fallback = [(x, y) for _, x, y in candidates]
        fallback.sort(key=lambda p: (p[1], p[0]))
        while len(points) < count and fallback:
            base = fallback[len(points) % len(fallback)]
            angle = RNG.random() * math.tau
            radius = 2.0 + RNG.random() * 4.0
            nx = clamp(base[0] + math.cos(angle) * radius, 0, w - 1)
            ny = clamp(base[1] + math.sin(angle) * radius, 0, h - 1)
            if mask_px[int(ny) * w + int(nx)]:
                points.append((int(nx), int(ny)))
            else:
                points.append(base)
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
        valid = list(candidates)
        attempts = 0
        max_attempts = max(200, count * 50)
        while len(candidates) < count and attempts < max_attempts:
            attempts += 1
            x = RNG.uniform(min_x, max_x)
            y = RNG.uniform(min_y, max_y)
            if point_in_polygon(x, y, points):
                candidates.append((x, y))
        if len(candidates) < count and valid:
            while len(candidates) < count:
                base = valid[len(candidates) % len(valid)]
                angle = RNG.random() * math.tau
                radius = step * (0.18 + 0.12 * RNG.random())
                x = clamp(base[0] + math.cos(angle) * radius, min_x, max_x)
                y = clamp(base[1] + math.sin(angle) * radius, min_y, max_y)
                if point_in_polygon(x, y, points):
                    candidates.append((x, y))
                else:
                    candidates.append(base)
    return sort_points(candidates)[:count]


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
    return sort_points(pts)[:count]


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
    return sort_points(pts)[:count]


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
    return sort_points(pts)[:count]


def make_state_points() -> Tuple[List[Tuple[float, float]], ...]:
    raw = Image.open(SOURCE)
    portrait_focus = crop_portrait_focus(raw)
    portrait_resized = portrait_focus.resize(
        (420, max(1, int(round(portrait_focus.size[1] * 420.0 / portrait_focus.size[0])))),
        Image.LANCZOS,
    )
    portrait_mask = build_subject_mask(portrait_resized)
    portrait_raw = sample_portrait_grid(portrait_resized, portrait_mask, POINT_COUNT)

    panel_cx = LEFT_X + LEFT_W / 2
    panel_cy = LEFT_Y + LEFT_H / 2
    portrait_w = 300
    portrait_h = 360
    portrait_box = (panel_cx - portrait_w / 2, panel_cy - portrait_h / 2, portrait_w, portrait_h)

    portrait = scale_points(portrait_raw, portrait_resized.size, portrait_box)
    flutter = sample_flutter_shape((panel_cx, panel_cy), 220, 250, POINT_COUNT)
    react = sample_react_shape((panel_cx, panel_cy), 240, 200, POINT_COUNT)
    node = sample_node_shape((panel_cx, panel_cy), 120, POINT_COUNT)
    firebase = sample_flame_shape((panel_cx, panel_cy), 180, 250, POINT_COUNT)
    return portrait, flutter, react, node, firebase


def escape_text(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


@lru_cache(maxsize=None)
def measure_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(path, size=size)


def text_width(text: str, size: int, bold: bool = False) -> float:
    font = measure_font(size, bold=bold)
    bbox = font.getbbox(text)
    return float(bbox[2] - bbox[0])


def animate_values(values: Sequence[Tuple[float, float]]) -> Tuple[str, str]:
    path = [values[0], values[0], values[1], values[1], values[2], values[2], values[3], values[3], values[4], values[4], values[0]]
    xs = ";".join(f"{x:.2f}" for x, _ in path)
    ys = ";".join(f"{y:.2f}" for _, y in path)
    return xs, ys


def circle_fill(index: int, theme: dict) -> str:
    palette = [theme["text"], theme["teal"], theme["amber"], theme["sage"]]
    return palette[index % len(palette)]


def load_asset_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def map_panel_point(x: float, y: float, panel_x: float, panel_y: float, panel_w: float, panel_h: float) -> Tuple[float, float]:
    return (
        panel_x + (x / WORKING_CANVAS) * panel_w,
        panel_y + (y / WORKING_CANVAS) * panel_h,
    )


def map_panel_radius(r: float, panel_w: float, panel_h: float) -> float:
    return r * ((panel_w + panel_h) / (2.0 * WORKING_CANVAS))


def join_values(values: Sequence[float]) -> str:
    return ";".join(f"{value:.2f}" for value in values)


def render_portrait_layer(points: List[dict], theme: dict, panel_x: float, panel_y: float, panel_w: float, panel_h: float) -> str:
    parts = [
        '<g id="portraitLayer" opacity="1">',
        f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="{PORTRAIT_OPACITY_TIMES}" dur="24s" repeatCount="indefinite"/>',
    ]
    for item in points:
        cx, cy = map_panel_point(float(item["x"]), float(item["y"]), panel_x, panel_y, panel_w, panel_h)
        r = map_panel_radius(float(item["r"]), panel_w, panel_h)
        parts.append(
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{escape_text(str(item["color"]))}"/>'
        )
    parts.append("</g>")
    return "\n".join(parts)


def render_morph_layer(logo_clouds: dict, theme: dict, panel_x: float, panel_y: float, panel_w: float, panel_h: float) -> str:
    states = ["flutter", "react", "node", "firebase"]
    palette = [theme["teal"], theme["amber"], theme["sage"]]
    parts = [
        '<g id="morphLayer" opacity="0">',
        f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{MORPH_OPACITY_TIMES}" dur="24s" repeatCount="indefinite"/>',
    ]
    for index in range(len(logo_clouds["flutter"])):
        points = [logo_clouds[state][index] for state in states]
        mapped = [map_panel_point(x, y, panel_x, panel_y, panel_w, panel_h) for x, y in points]
        x_values = [mapped[0][0], mapped[0][0], mapped[1][0], mapped[1][0], mapped[2][0], mapped[2][0], mapped[3][0], mapped[3][0], mapped[0][0]]
        y_values = [mapped[0][1], mapped[0][1], mapped[1][1], mapped[1][1], mapped[2][1], mapped[2][1], mapped[3][1], mapped[3][1], mapped[0][1]]
        color = palette[index % len(palette)]
        parts.append(
            f'<circle cx="{mapped[0][0]:.2f}" cy="{mapped[0][1]:.2f}" r="1.45" fill="{color}" fill-opacity="0.92">'
            f'<animate attributeName="cx" values="{join_values(x_values)}" '
            f'keyTimes="{MORPH_KEY_TIMES}" keySplines="{MORPH_KEY_SPLINES}" calcMode="spline" dur="24s" repeatCount="indefinite"/>'
            f'<animate attributeName="cy" values="{join_values(y_values)}" '
            f'keyTimes="{MORPH_KEY_TIMES}" keySplines="{MORPH_KEY_SPLINES}" calcMode="spline" dur="24s" repeatCount="indefinite"/>'
            "</circle>"
        )
    parts.append("</g>")
    return "\n".join(parts)


def build_svg(theme: dict, out_path: Path) -> None:
    portrait_points = load_asset_json(PORTRAIT_DENSE)
    logo_clouds = load_asset_json(LOGO_CLOUDS)

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
    lines.append('<clipPath id="visual-map-clip"><rect x="52" y="104" width="378" height="440" rx="10"/></clipPath>')
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

    lines.append('<g clip-path="url(#visual-map-clip)">')
    lines.append(render_portrait_layer(portrait_points, theme, LEFT_X, LEFT_Y, LEFT_W, LEFT_H))
    lines.append(render_morph_layer(logo_clouds, theme, LEFT_X, LEFT_Y, LEFT_W, LEFT_H))
    lines.append("</g>")

    lines.append(f'<text x="64" y="520" font-size="11" fill="{theme["muted"]}">terminal render: identity and stack</text>')

    lines.append(f'<rect x="{RIGHT_X}" y="{RIGHT_Y}" width="{RIGHT_W}" height="{RIGHT_H}" rx="10" fill="{theme["panel_right"]}" stroke="{theme["panel_stroke"]}"/>')
    lines.append(f'<text x="486" y="140" font-size="18" fill="{theme["teal"]}" font-weight="700" letter-spacing="1.1">SYSTEM.INFO</text>')
    lines.append(f'<text x="1049" y="140" font-size="16" fill="{theme["accent_live"]}" font-weight="700">● LIVE</text>')
    pill_width = max(180, int(math.ceil(text_width(theme["mail"], 14, bold=True) + 24)))
    lines.append(f'<rect x="486" y="154" width="{pill_width}" height="24" rx="6" fill="{theme["accent_bar"]}"/>')
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
    row_y = 200
    for label, value in info_rows:
        lines.append(f'<text x="486" y="{row_y}" font-size="13" fill="{theme["teal"]}">{escape_text(label)}</text>')
        lines.append(f'<text x="1102" y="{row_y}" text-anchor="end" font-size="13" font-weight="700" fill="{theme["text"]}">{escape_text(value)}</text>')
        row_y += 21 if label not in {"Core.Database", "Core.Infra"} else 19

    lines.append(f'<text x="486" y="{row_y + 6}" font-size="12" fill="{theme["muted_dim"]}">- Contact -</text>')
    lines.append(f'<line x1="560" y1="{row_y + 2}" x2="1100" y2="{row_y + 2}" stroke="{theme["muted_dim"]}" stroke-width="1" stroke-dasharray="4 6" opacity="0.45"/>')
    row_y += 26

    contact_rows = [
        ("Grid.Mail", "alebachewkalaab99@gmail.com"),
        ("Grid.LinkedIn", "kalaab-alb"),
        ("Grid.Instagram", "kalaabalb"),
        ("Grid.GitHub", "@kalaabalb"),
    ]
    for label, value in contact_rows:
        lines.append(f'<text x="486" y="{row_y}" font-size="13" fill="{theme["teal"]}">{escape_text(label)}</text>')
        lines.append(f'<text x="1102" y="{row_y}" text-anchor="end" font-size="13" font-weight="700" fill="{theme["text"]}">{escape_text(value)}</text>')
        row_y += 21

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

    lines.append(f'<text x="486" y="540" font-size="14" fill="{theme["muted"]}">More about me and projects below in README</text>')
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
        "mail": "alebachewkalaab99@gmail.com",
        "terminal": "alebachewkalaab99@gmail.com - % ./profile.sh --live",
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
        "mail": "alebachewkalaab99@gmail.com",
        "terminal": "alebachewkalaab99@gmail.com - % ./profile.sh --live",
        "dot_r": "1.55",
    }
    build_svg(dark, OUT_DARK)
    build_svg(light, OUT_LIGHT)


if __name__ == "__main__":
    main()
