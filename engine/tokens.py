from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOKEN_PATH = ROOT / "assets" / "source" / "kalaos.tokens.json"


@dataclass(frozen=True)
class TokenBundle:
    raw: Mapping[str, Any]

    @property
    def meta(self) -> Mapping[str, Any]:
        return self.raw["meta"]

    @property
    def spacing(self) -> Mapping[str, int]:
        return self.raw["spacing"]

    @property
    def radii(self) -> Mapping[str, int]:
        return self.raw["radii"]

    @property
    def stroke_widths(self) -> Mapping[str, float]:
        return self.raw["stroke_widths"]

    @property
    def typography_scale(self) -> Mapping[str, Mapping[str, float]]:
        return self.raw["typography_scale"]

    @property
    def motion(self) -> Mapping[str, Any]:
        return self.raw["motion"]

    @property
    def z_index(self) -> Mapping[str, int]:
        return self.raw["z_index"]

    @property
    def opacity(self) -> Mapping[str, float]:
        return self.raw["opacity"]

    @property
    def grid(self) -> Mapping[str, int]:
        return self.raw["grid"]

    @property
    def themes(self) -> Mapping[str, Mapping[str, str]]:
        return self.raw["themes"]

    @property
    def layout(self) -> Mapping[str, Any]:
        return self.raw["layout"]


def load_tokens(path: Path | str = DEFAULT_TOKEN_PATH) -> TokenBundle:
    token_path = Path(path)
    raw = json.loads(token_path.read_text(encoding="utf-8"))
    return TokenBundle(raw=raw)

