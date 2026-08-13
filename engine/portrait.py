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
    cx, cy = 0.50, 0.44
    rx, ry = 0.41, 0.52
    dx = (nx - cx) / rx
    dy = (ny - cy) / ry
    return _clamp(1.0 - (dx * dx + dy * dy))


def render_portrait_points(
    theme: Theme,
    settings: PortraitSettings,
    box: PortraitBox,
    clip_id: str = "kalaos-portrait-clip",
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
            row.append(_clamp(structural * (0.44 + 0.56 * focus)))
        signal_grid.append(row)

    step_x = box.width / cols
    step_y = box.height / rows
    colors = [getattr(theme, token) for token in settings.palette]

    points: list[str] = [f'<g clip-path="url(#{clip_id})" shape-rendering="geometricPrecision">']
    for y in range(rows):
        for x in range(cols):
            focus = _focus_weight(box, x, y, cols, rows)
            signal = signal_grid[y][x]
            support = _grid_average(signal_grid, x, y, radius=1)
            field = _clamp(signal * 0.62 + support * 0.38)
            if field <= settings.threshold + (1.0 - focus) * 0.18:
                continue
            edge = _local_contrast(signal_grid, x, y)
            size = settings.minimum_point_size + (settings.maximum_point_size - settings.minimum_point_size) * (field ** settings.luminance_response)
            size *= 0.82 + min(0.30, (edge + support) * 0.34)
            alpha = 0.10 + 0.90 * field * (0.48 + 0.52 * focus)
            gx = (luma_grid[y][x + 1] - luma_grid[y][x - 1]) if 0 < x < cols - 1 else 0.0
            gy = (luma_grid[y + 1][x] - luma_grid[y - 1][x]) if 0 < y < rows - 1 else 0.0
            shift_x = gx * step_x * 0.20
            shift_y = gy * step_y * 0.20
            base_x = box.x + (x + 0.5) * step_x + shift_x
            base_y = box.y + (y + 0.5) * step_y + shift_y
            color_index = min(len(colors) - 1, int(field * len(colors)))
            fill = colors[color_index]
            structural = field * (0.65 + 0.35 * focus)
            recognition = field * (0.82 + 0.68 * focus) + edge * 0.16
            atmosphere = field * (0.18 + 0.24 * (1.0 - focus))

            if structural > 0.22 + (1.0 - focus) * 0.05:
                points.append(f'<circle cx="{base_x:.2f}" cy="{base_y:.2f}" r="{size:.2f}" fill="{fill}" opacity="{alpha:.3f}"/>')

            if focus > 0.30 and recognition > 0.36:
                secondary_shift = 0.20 + edge * 0.10
                secondary_x = base_x - shift_x * secondary_shift
                secondary_y = base_y - shift_y * secondary_shift
                secondary_size = size * (0.64 + edge * 0.10)
                secondary_alpha = min(0.92, alpha * (0.72 + focus * 0.12))
                secondary_fill = colors[max(0, color_index - 1)]
                points.append(
                    f'<circle cx="{secondary_x:.2f}" cy="{secondary_y:.2f}" r="{secondary_size:.2f}" fill="{secondary_fill}" opacity="{secondary_alpha:.3f}"/>'
                )

            if focus > 0.42 and recognition > 0.52 and edge > 0.06:
                perp_x = -shift_y * (0.30 + focus * 0.10)
                perp_y = shift_x * (0.30 + focus * 0.10)
                tertiary_x = base_x + perp_x
                tertiary_y = base_y + perp_y
                tertiary_size = size * 0.42
                tertiary_alpha = min(0.88, alpha * 0.50)
                tertiary_fill = colors[min(len(colors) - 1, color_index + 1)]
                points.append(
                    f'<circle cx="{tertiary_x:.2f}" cy="{tertiary_y:.2f}" r="{tertiary_size:.2f}" fill="{tertiary_fill}" opacity="{tertiary_alpha:.3f}"/>'
                )

            if focus < 0.38 and atmosphere > 0.22:
                sparse_size = max(settings.minimum_point_size * 0.75, size * 0.46)
                sparse_alpha = min(0.40, 0.08 + atmosphere * 0.32)
                sparse_fill = colors[0] if field < 0.40 else colors[1]
                points.append(
                    f'<circle cx="{base_x:.2f}" cy="{base_y:.2f}" r="{sparse_size:.2f}" fill="{sparse_fill}" opacity="{sparse_alpha:.3f}"/>'
                )
    points.append("</g>")
    return "".join(points)
