from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

from .theme import Theme


@dataclass(frozen=True)
class PortraitBox:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class PortraitSettings:
    source: Path
    sampling_density: int
    minimum_point_size: float
    maximum_point_size: float
    luminance_response: float
    contrast: float
    threshold: float
    palette: tuple[str, ...]
    background: str


def _resample() -> int:
    return getattr(Image, "Resampling", Image).LANCZOS


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def _mix_rgb(a: tuple[int, int, int], b: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    ratio = _clamp(ratio)
    return tuple(int(round(a[i] * (1.0 - ratio) + b[i] * ratio)) for i in range(3))


def _scale_rgb(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(round(channel * factor)))) for channel in rgb)


def _theme_color(theme: Theme, token_name: str) -> str:
    return getattr(theme, token_name)


def _sample_luminance(pixels: object, x: int, y: int, cols: int, rows: int) -> float:
    r, g, b = pixels[x, y]
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def _local_contrast(luma_grid: list[list[float]], x: int, y: int) -> float:
    center = luma_grid[y][x]
    neighbors: list[float] = []
    for ny in range(max(0, y - 1), min(len(luma_grid), y + 2)):
        for nx in range(max(0, x - 1), min(len(luma_grid[0]), x + 2)):
            if nx == x and ny == y:
                continue
            neighbors.append(abs(center - luma_grid[ny][nx]))
    if not neighbors:
        return 0.0
    return sum(neighbors) / len(neighbors)


def _grid_average(values: list[list[float]], x: int, y: int, radius: int = 1) -> float:
    total = 0.0
    count = 0
    for ny in range(max(0, y - radius), min(len(values), y + radius + 1)):
        for nx in range(max(0, x - radius), min(len(values[0]), x + radius + 1)):
            total += values[ny][nx]
            count += 1
    return total / count if count else 0.0


def _gaussian(nx: float, ny: float, cx: float, cy: float, sx: float, sy: float, amplitude: float) -> float:
    dx = (nx - cx) / sx
    dy = (ny - cy) / sy
    return amplitude * math.exp(-0.5 * (dx * dx + dy * dy))


def _focus_weight(box: PortraitBox, x: int, y: int, cols: int, rows: int) -> float:
    nx = (x + 0.5) / cols
    ny = (y + 0.5) / rows
    cx, cy = 0.50, 0.42
    rx, ry = 0.39, 0.55
    dx = (nx - cx) / rx
    dy = (ny - cy) / ry
    return _clamp(1.0 - (dx * dx + dy * dy))


def _feature_weight(nx: float, ny: float) -> float:
    weight = 0.0
    weight += _gaussian(nx, ny, 0.50, 0.18, 0.18, 0.07, 0.32)  # hair / hairline
    weight += _gaussian(nx, ny, 0.50, 0.24, 0.16, 0.06, 0.22)  # upper forehead texture
    weight += _gaussian(nx, ny, 0.50, 0.35, 0.17, 0.025, 0.46)  # glasses upper rim
    weight += _gaussian(nx, ny, 0.50, 0.48, 0.17, 0.025, 0.38)  # glasses lower rim
    weight += _gaussian(nx, ny, 0.31, 0.41, 0.025, 0.06, 0.35)  # left frame
    weight += _gaussian(nx, ny, 0.69, 0.41, 0.025, 0.06, 0.35)  # right frame
    weight += _gaussian(nx, ny, 0.50, 0.41, 0.03, 0.05, 0.40)  # bridge
    weight += _gaussian(nx, ny, 0.39, 0.39, 0.065, 0.045, 0.42)  # left eye / brow
    weight += _gaussian(nx, ny, 0.61, 0.39, 0.065, 0.045, 0.42)  # right eye / brow
    weight += _gaussian(nx, ny, 0.40, 0.40, 0.028, 0.022, 0.25)  # left eye center
    weight += _gaussian(nx, ny, 0.60, 0.40, 0.028, 0.022, 0.25)  # right eye center
    weight += _gaussian(nx, ny, 0.39, 0.36, 0.09, 0.03, 0.28)  # left eyebrow arc
    weight += _gaussian(nx, ny, 0.61, 0.36, 0.09, 0.03, 0.28)  # right eyebrow arc
    weight += _gaussian(nx, ny, 0.50, 0.50, 0.05, 0.10, 0.45)  # nose bridge / contour
    weight += _gaussian(nx, ny, 0.50, 0.56, 0.045, 0.055, 0.22)  # nose tip / lower contour
    weight += _gaussian(nx, ny, 0.50, 0.61, 0.11, 0.035, 0.40)  # mouth / lips
    weight += _gaussian(nx, ny, 0.50, 0.63, 0.085, 0.025, 0.24)  # mouth separation
    weight += _gaussian(nx, ny, 0.43, 0.72, 0.07, 0.07, 0.28)  # left jaw
    weight += _gaussian(nx, ny, 0.57, 0.72, 0.07, 0.07, 0.28)  # right jaw
    weight += _gaussian(nx, ny, 0.50, 0.77, 0.13, 0.055, 0.28)  # chin
    weight += _gaussian(nx, ny, 0.22, 0.45, 0.045, 0.075, 0.22)  # left ear
    weight += _gaussian(nx, ny, 0.78, 0.45, 0.045, 0.075, 0.22)  # right ear
    weight += _gaussian(nx, ny, 0.38, 0.84, 0.12, 0.055, 0.22)  # left shoulder
    weight += _gaussian(nx, ny, 0.62, 0.84, 0.12, 0.055, 0.22)  # right shoulder
    weight += _gaussian(nx, ny, 0.50, 0.81, 0.028, 0.030, 0.22)  # necklace chain
    weight += _gaussian(nx, ny, 0.50, 0.84, 0.038, 0.036, 0.56)  # necklace / pendant
    weight += _gaussian(nx, ny, 0.50, 0.88, 0.020, 0.032, 0.48)  # cross stem
    weight += _gaussian(nx, ny, 0.50, 0.92, 0.014, 0.020, 0.28)  # cross lower tip
    return _clamp(weight)


def _face_continuity_weight(nx: float, ny: float) -> float:
    weight = 0.0
    weight += _gaussian(nx, ny, 0.50, 0.30, 0.27, 0.17, 0.24)  # forehead / brow continuity
    weight += _gaussian(nx, ny, 0.50, 0.44, 0.23, 0.20, 0.32)  # upper face continuity
    weight += _gaussian(nx, ny, 0.50, 0.58, 0.21, 0.19, 0.30)  # nose / mouth continuity
    weight += _gaussian(nx, ny, 0.50, 0.70, 0.19, 0.15, 0.24)  # jaw / chin continuity
    weight += _gaussian(nx, ny, 0.39, 0.47, 0.12, 0.13, 0.20)  # left cheek continuity
    weight += _gaussian(nx, ny, 0.61, 0.47, 0.12, 0.13, 0.20)  # right cheek continuity
    weight += _gaussian(nx, ny, 0.38, 0.82, 0.14, 0.08, 0.16)  # left shoulder continuity
    weight += _gaussian(nx, ny, 0.62, 0.82, 0.14, 0.08, 0.16)  # right shoulder continuity
    weight += _gaussian(nx, ny, 0.50, 0.52, 0.28, 0.22, 0.24)  # broad facial mass
    weight += _gaussian(nx, ny, 0.50, 0.39, 0.14, 0.09, 0.14)  # eye bridge continuity
    return _clamp(weight)


def _lens_void_weight(nx: float, ny: float) -> float:
    return _clamp(
        _gaussian(nx, ny, 0.40, 0.41, 0.10, 0.07, 0.60)
        + _gaussian(nx, ny, 0.60, 0.41, 0.10, 0.07, 0.60)
    )


def render_portrait_points(
    theme: Theme,
    settings: PortraitSettings,
    box: PortraitBox,
) -> str:
    image = Image.open(settings.source).convert("RGB")
    cols = max(12, int(box.width / settings.sampling_density))
    rows = max(12, int(box.height / settings.sampling_density))
    resized = ImageOps.fit(image, (cols, rows), method=_resample(), centering=(0.5, 0.45))
    pixels = resized.load()

    luma_grid: list[list[float]] = []
    for y in range(rows):
        row: list[float] = []
        for x in range(cols):
            row.append(_sample_luminance(pixels, x, y, cols, rows))
        luma_grid.append(row)

    signal_grid: list[list[float]] = []
    for y in range(rows):
        row: list[float] = []
        for x in range(cols):
            lum = luma_grid[y][x]
            contrast = _local_contrast(luma_grid, x, y)
            gx = abs((luma_grid[y][x + 1] - luma_grid[y][x - 1]) if 0 < x < cols - 1 else 0.0)
            gy = abs((luma_grid[y + 1][x] - luma_grid[y - 1][x]) if 0 < y < rows - 1 else 0.0)
            edge = min(1.0, (gx + gy) * 1.6 + contrast * 0.8)
            structural = (1.0 - lum) * 0.52 + contrast * 0.82 + edge * 0.66
            focus = _focus_weight(box, x, y, cols, rows)
            nx = (x + 0.5) / cols
            ny = (y + 0.5) / rows
            feature = _feature_weight(nx, ny)
            continuity = _face_continuity_weight(nx, ny)
            lens_void = _lens_void_weight(nx, ny)
            highlight = max(0.0, lum - 0.64)
            row.append(_clamp(structural * (0.34 + 0.66 * focus) + feature * 0.36 + continuity * 0.26 - highlight * 0.18 - lens_void * 0.36))
        signal_grid.append(row)

    step_x = box.width / cols
    step_y = box.height / rows
    colors = [getattr(theme, token) for token in settings.palette]

    points: list[str] = ['<g shape-rendering="geometricPrecision">']
    for y in range(rows):
        for x in range(cols):
            focus = _focus_weight(box, x, y, cols, rows)
            nx = (x + 0.5) / cols
            ny = (y + 0.5) / rows
            feature = _feature_weight(nx, ny)
            continuity = _face_continuity_weight(nx, ny)
            lens_void = _lens_void_weight(nx, ny)
            signal = signal_grid[y][x]
            support = _grid_average(signal_grid, x, y, radius=1)
            field = _clamp(signal * 0.54 + support * 0.30 + feature * 0.30 + continuity * 0.30 - lens_void * 0.20)
            if ny > 0.66:
                field *= 0.92
            if ny > 0.76:
                field *= 0.86
            if field <= settings.threshold + (1.0 - focus) * 0.16 - feature * 0.05 - continuity * 0.14:
                continue
            edge = _local_contrast(signal_grid, x, y)
            size = settings.minimum_point_size + (settings.maximum_point_size - settings.minimum_point_size) * (field ** settings.luminance_response)
            size *= 0.72 + min(0.38, (edge + support) * 0.30 + feature * 0.16 + continuity * 0.12)
            alpha = 0.10 + 0.90 * field * (0.40 + 0.60 * focus) + feature * 0.08 + continuity * 0.06
            gx = (luma_grid[y][x + 1] - luma_grid[y][x - 1]) if 0 < x < cols - 1 else 0.0
            gy = (luma_grid[y + 1][x] - luma_grid[y - 1][x]) if 0 < y < rows - 1 else 0.0
            shift_x = gx * step_x * (0.14 + feature * 0.10 + continuity * 0.07)
            shift_y = gy * step_y * (0.14 + feature * 0.10 + continuity * 0.07)
            base_x = box.x + (x + 0.5) * step_x + shift_x
            base_y = box.y + (y + 0.5) * step_y + shift_y
            tone = _clamp(lum * 0.93 + feature * 0.07)
            source_rgb = pixels[x, y]
            neutral_rgb = (217, 207, 239)
            skin_rgb = (176, 134, 114)
            dark_rgb = (44, 36, 58)
            if tone < 0.22:
                fill_rgb = _mix_rgb(source_rgb, dark_rgb, 0.38)
            elif tone < 0.52:
                fill_rgb = _mix_rgb(source_rgb, skin_rgb, 0.18)
            else:
                fill_rgb = _mix_rgb(source_rgb, neutral_rgb, 0.20)
            fill = _rgb_to_hex(fill_rgb)
            structural = field * (0.58 + 0.42 * focus) + feature * 0.10
            recognition = field * (0.84 + 0.74 * focus) + edge * 0.18 + feature * 0.22 + continuity * 0.14
            atmosphere = field * (0.14 + 0.18 * (1.0 - focus)) - feature * 0.04 + continuity * 0.05
            shirt_suppression = 1.0
            if ny > 0.68:
                shirt_suppression *= 0.92
            if ny > 0.76:
                shirt_suppression *= 0.86
            if ny > 0.82:
                shirt_suppression *= 0.78
            structural *= shirt_suppression
            recognition *= 0.92 + feature * 0.12 + continuity * 0.08
            atmosphere *= shirt_suppression

            if structural > 0.20 + (1.0 - focus) * 0.04 - feature * 0.03:
                points.append(f'<circle cx="{base_x:.2f}" cy="{base_y:.2f}" r="{size:.2f}" fill="{fill}" opacity="{alpha:.3f}"/>')

            if (focus > 0.28 or feature > 0.18) and recognition > 0.34:
                secondary_shift = 0.18 + edge * 0.09 + feature * 0.06 + continuity * 0.06
                secondary_x = base_x - shift_x * secondary_shift
                secondary_y = base_y - shift_y * secondary_shift
                secondary_size = size * (0.60 + edge * 0.08 + feature * 0.04 + continuity * 0.06)
                secondary_alpha = min(0.95, alpha * (0.70 + focus * 0.10 + feature * 0.08 + continuity * 0.06))
                secondary_fill = _rgb_to_hex(_scale_rgb(fill_rgb, 0.82))
                points.append(
                    f'<circle cx="{secondary_x:.2f}" cy="{secondary_y:.2f}" r="{secondary_size:.2f}" fill="{secondary_fill}" opacity="{secondary_alpha:.3f}"/>'
                )

            if (focus > 0.40 or feature > 0.20) and recognition > 0.48 and edge > 0.05:
                perp_x = -shift_y * (0.24 + focus * 0.08 + feature * 0.08 + continuity * 0.06)
                perp_y = shift_x * (0.24 + focus * 0.08 + feature * 0.08 + continuity * 0.06)
                tertiary_x = base_x + perp_x
                tertiary_y = base_y + perp_y
                tertiary_size = size * (0.38 + feature * 0.05 + continuity * 0.05)
                tertiary_alpha = min(0.90, alpha * (0.44 + feature * 0.12 + continuity * 0.08))
                tertiary_fill = _rgb_to_hex(_scale_rgb(fill_rgb, 1.06))
                points.append(
                    f'<circle cx="{tertiary_x:.2f}" cy="{tertiary_y:.2f}" r="{tertiary_size:.2f}" fill="{tertiary_fill}" opacity="{tertiary_alpha:.3f}"/>'
                )

            if focus < 0.34 and feature < 0.08 and atmosphere > 0.16:
                sparse_size = max(settings.minimum_point_size * 0.68, size * 0.40)
                sparse_alpha = min(0.34, 0.06 + atmosphere * 0.26)
                sparse_fill = _rgb_to_hex(_scale_rgb(fill_rgb, 0.68))
                points.append(
                    f'<circle cx="{base_x:.2f}" cy="{base_y:.2f}" r="{sparse_size:.2f}" fill="{sparse_fill}" opacity="{sparse_alpha:.3f}"/>'
                )
    points.append("</g>")
    return "".join(points)
