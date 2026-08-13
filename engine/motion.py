from __future__ import annotations

from dataclasses import dataclass

from .tokens import TokenBundle, load_tokens


@dataclass(frozen=True)
class MotionTokens:
    fast: int
    normal: int
    slow: int
    reveal: int
    assemble: int
    dissolve: int
    idle: int
    standard_easing: str
    emphasized_easing: str
    calm_easing: str


def resolve_motion(tokens: TokenBundle | None = None) -> MotionTokens:
    bundle = tokens or load_tokens()
    motion = bundle.motion
    easing = motion["easing"]
    return MotionTokens(
        fast=int(motion["fast"]),
        normal=int(motion["normal"]),
        slow=int(motion["slow"]),
        reveal=int(motion["reveal"]),
        assemble=int(motion["assemble"]),
        dissolve=int(motion["dissolve"]),
        idle=int(motion["idle"]),
        standard_easing=str(easing["standard"]),
        emphasized_easing=str(easing["emphasized"]),
        calm_easing=str(easing["calm"]),
    )

