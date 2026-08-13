from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .tokens import TokenBundle, load_tokens


@dataclass(frozen=True)
class Theme:
    mode: str
    background: str
    panel: str
    surface: str
    glass: str
    text_primary: str
    text_secondary: str
    text_muted: str
    accent_violet: str
    accent_lavender: str
    accent_cyan: str
    warning_amber: str
    success_green: str
    error_red: str
    border_hairline: str
    border_panel: str
    glow: str
    particle: str
    coordinate: str
    grid: str

    def as_dict(self) -> dict[str, str]:
        return {
            "mode": self.mode,
            "background": self.background,
            "panel": self.panel,
            "surface": self.surface,
            "glass": self.glass,
            "text_primary": self.text_primary,
            "text_secondary": self.text_secondary,
            "text_muted": self.text_muted,
            "accent_violet": self.accent_violet,
            "accent_lavender": self.accent_lavender,
            "accent_cyan": self.accent_cyan,
            "warning_amber": self.warning_amber,
            "success_green": self.success_green,
            "error_red": self.error_red,
            "border_hairline": self.border_hairline,
            "border_panel": self.border_panel,
            "glow": self.glow,
            "particle": self.particle,
            "coordinate": self.coordinate,
            "grid": self.grid,
        }


def build_theme(tokens: TokenBundle, mode: str) -> Theme:
    theme = tokens.themes[mode]
    return Theme(
        mode=mode,
        background=theme["background"],
        panel=theme["panel"],
        surface=theme["surface"],
        glass=theme["glass"],
        text_primary=theme["text_primary"],
        text_secondary=theme["text_secondary"],
        text_muted=theme["text_muted"],
        accent_violet=theme["accent_violet"],
        accent_lavender=theme["accent_lavender"],
        accent_cyan=theme["accent_cyan"],
        warning_amber=theme["warning_amber"],
        success_green=theme["success_green"],
        error_red=theme["error_red"],
        border_hairline=theme["border_hairline"],
        border_panel=theme["border_panel"],
        glow=theme["glow"],
        particle=theme["particle"],
        coordinate=theme["coordinate"],
        grid=theme["grid"],
    )


def resolve_theme(mode: str, tokens: TokenBundle | None = None) -> Theme:
    bundle = tokens or load_tokens()
    if mode not in bundle.themes:
        raise KeyError(f"Unknown KalaOS theme mode: {mode}")
    return build_theme(bundle, mode)

