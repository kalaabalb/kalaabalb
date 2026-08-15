from __future__ import annotations

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


def _focus_weight(box: PortraitBox, x: int, y: int, cols: int, rows: int) -> float:
    nx = (x + 0.5) / cols
    ny = (y + 0.5) / rows
    cx, cy = 0.50, 0.42
    rx, ry = 0.39, 0.55
    dx = (nx - cx) / rx
    dy = (ny - cy) / ry
    return _clamp(1.0 - (dx * dx + dy * dy))


def _feature_weight(nx: float, ny: float) -> float:
    def gaussian(cx: float, cy: float, sx: float, sy: float, amplitude: float) -> float:
        dx = (nx - cx) / sx
        dy = (ny - cy) / sy
        return amplitude * pow(2.718281828, -(dx * dx + dy * dy) * 0.5)

    weight = 0.0
    weight += gaussian(0.50, 0.22, 0.14, 0.07, 0.38)  # hairline / upper hair silhouette
    weight += gaussian(0.31, 0.39, 0.09, 0.05, 0.55)  # left eye / brow
    weight += gaussian(0.69, 0.39, 0.09, 0.05, 0.55)  # right eye / brow
    weight += gaussian(0.50, 0.50, 0.08, 0.11, 0.48)  # nose bridge / contour
    weight += gaussian(0.50, 0.61, 0.12, 0.06, 0.36)  # mouth / lips
    weight += gaussian(0.50, 0.78, 0.13, 0.08, 0.30)  # jaw / chin
    weight += gaussian(0.22, 0.45, 0.06, 0.09, 0.18)  # left ear
    weight += gaussian(0.78, 0.45, 0.06, 0.09, 0.18)  # right ear
    weight += gaussian(0.50, 0.83, 0.06, 0.04, 0.18)  # necklace / cross
    return _clamp(weight)


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
            row.append(_clamp(structural * (0.34 + 0.66 * focus) + feature * 0.42))
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
            signal = signal_grid[y][x]
            support = _grid_average(signal_grid, x, y, radius=1)
            field = _clamp(signal * 0.56 + support * 0.30 + feature * 0.44)
            if ny > 0.70:
                field *= 0.84
            if ny > 0.80:
                field *= 0.74
            if field <= settings.threshold + (1.0 - focus) * 0.16 - feature * 0.05:
                continue
            edge = _local_contrast(signal_grid, x, y)
            size = settings.minimum_point_size + (settings.maximum_point_size - settings.minimum_point_size) * (field ** settings.luminance_response)
            size *= 0.80 + min(0.38, (edge + support) * 0.34 + feature * 0.18)
            alpha = 0.10 + 0.90 * field * (0.40 + 0.60 * focus) + feature * 0.08
            gx = (luma_grid[y][x + 1] - luma_grid[y][x - 1]) if 0 < x < cols - 1 else 0.0
            gy = (luma_grid[y + 1][x] - luma_grid[y - 1][x]) if 0 < y < rows - 1 else 0.0
            shift_x = gx * step_x * (0.14 + feature * 0.12)
            shift_y = gy * step_y * (0.14 + feature * 0.12)
            base_x = box.x + (x + 0.5) * step_x + shift_x
            base_y = box.y + (y + 0.5) * step_y + shift_y
            color_index = min(len(colors) - 1, int(field * len(colors)))
            fill = colors[color_index]
            structural = field * (0.58 + 0.42 * focus) + feature * 0.10
            recognition = field * (0.86 + 0.74 * focus) + edge * 0.18 + feature * 0.22
            atmosphere = field * (0.14 + 0.18 * (1.0 - focus)) - feature * 0.04
            shirt_suppression = 1.0
            if ny > 0.68:
                shirt_suppression *= 0.84
            if ny > 0.76:
                shirt_suppression *= 0.76
            if ny > 0.82:
                shirt_suppression *= 0.68
            structural *= shirt_suppression
            recognition *= 0.92 + feature * 0.12
            atmosphere *= shirt_suppression

            if structural > 0.20 + (1.0 - focus) * 0.04 - feature * 0.03:
                points.append(f'<circle cx="{base_x:.2f}" cy="{base_y:.2f}" r="{size:.2f}" fill="{fill}" opacity="{alpha:.3f}"/>')

            if (focus > 0.28 or feature > 0.18) and recognition > 0.34:
                secondary_shift = 0.18 + edge * 0.09 + feature * 0.06
                secondary_x = base_x - shift_x * secondary_shift
                secondary_y = base_y - shift_y * secondary_shift
                secondary_size = size * (0.60 + edge * 0.08 + feature * 0.04)
                secondary_alpha = min(0.95, alpha * (0.70 + focus * 0.10 + feature * 0.08))
                secondary_fill = colors[max(0, color_index - 1)]
                points.append(
                    f'<circle cx="{secondary_x:.2f}" cy="{secondary_y:.2f}" r="{secondary_size:.2f}" fill="{secondary_fill}" opacity="{secondary_alpha:.3f}"/>'
                )

            if (focus > 0.40 or feature > 0.20) and recognition > 0.48 and edge > 0.05:
                perp_x = -shift_y * (0.24 + focus * 0.08 + feature * 0.08)
                perp_y = shift_x * (0.24 + focus * 0.08 + feature * 0.08)
                tertiary_x = base_x + perp_x
                tertiary_y = base_y + perp_y
                tertiary_size = size * (0.38 + feature * 0.05)
                tertiary_alpha = min(0.90, alpha * (0.44 + feature * 0.12))
                tertiary_fill = colors[min(len(colors) - 1, color_index + 1)]
                points.append(
                    f'<circle cx="{tertiary_x:.2f}" cy="{tertiary_y:.2f}" r="{tertiary_size:.2f}" fill="{tertiary_fill}" opacity="{tertiary_alpha:.3f}"/>'
                )

            if focus < 0.34 and feature < 0.08 and atmosphere > 0.16:
                sparse_size = max(settings.minimum_point_size * 0.68, size * 0.40)
                sparse_alpha = min(0.34, 0.06 + atmosphere * 0.26)
                sparse_fill = colors[0] if field < 0.40 else colors[1]
                points.append(
                    f'<circle cx="{base_x:.2f}" cy="{base_y:.2f}" r="{sparse_size:.2f}" fill="{sparse_fill}" opacity="{sparse_alpha:.3f}"/>'
                )
    points.append("</g>")
    return "".join(points)
