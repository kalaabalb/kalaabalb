from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .tokens import TokenBundle, load_tokens


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int
    radius: int


@dataclass(frozen=True)
class HeroLayout:
    canvas_width: int
    canvas_height: int
    frame: Rect
    title: tuple[int, int]
    subtitle: tuple[int, int]
    cursor: tuple[int, int]
    boot_log: tuple[int, int]
    boot_log_step: int
    footer_left: tuple[int, int]
    footer_right: tuple[int, int]


def resolve_hero_layout(tokens: TokenBundle | None = None) -> HeroLayout:
    bundle = tokens or load_tokens()
    layout = bundle.layout["hero"]
    frame = layout["frame"]
    canvas = layout["canvas"]
    return HeroLayout(
        canvas_width=int(canvas["width"]),
        canvas_height=int(canvas["height"]),
        frame=Rect(
            x=int(frame["x"]),
            y=int(frame["y"]),
            width=int(frame["width"]),
            height=int(frame["height"]),
            radius=int(frame["radius"]),
        ),
        title=(int(layout["title"]["x"]), int(layout["title"]["y"])),
        subtitle=(int(layout["subtitle"]["x"]), int(layout["subtitle"]["y"])),
        cursor=(int(layout["cursor"]["x"]), int(layout["cursor"]["y"])),
        boot_log=(int(layout["boot_log"]["x"]), int(layout["boot_log"]["y"])),
        boot_log_step=int(layout["boot_log"]["step"]),
        footer_left=(int(layout["footer_left"]["x"]), int(layout["footer_left"]["y"])),
        footer_right=(int(layout["footer_right"]["x"]), int(layout["footer_right"]["y"])),
    )
