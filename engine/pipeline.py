from __future__ import annotations

import json
from pathlib import Path

from .boot import write_boot
from .chronology import write_chronology
from .handoff import write_handoff
from .interface import write_interface
from .identity import write_identity
from .hero import write_hero
from .signals import write_signals
from .telemetry import write_telemetry
from .systems import write_systems
from .svg_primitives import build_primitive_library, render_origin_mark
from .theme import resolve_theme
from .tokens import DEFAULT_TOKEN_PATH, TokenBundle, load_tokens


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SOURCE = ASSETS / "source"
GENERATED = ASSETS / "generated"
TEMP = ASSETS / "temp"
BUILD = ASSETS / "build"


def ensure_asset_tree() -> None:
    for directory in (SOURCE, GENERATED, TEMP, BUILD):
        directory.mkdir(parents=True, exist_ok=True)


def write_foundation_assets(tokens: TokenBundle | None = None) -> dict[str, str]:
    bundle = tokens or load_tokens()
    ensure_asset_tree()
    outputs: dict[str, str] = {}

    primitive_dark = GENERATED / "primitives-dark.svg"
    primitive_light = GENERATED / "primitives-light.svg"
    primitive_dark.write_text(build_primitive_library("dark", bundle).svg, encoding="utf-8")
    primitive_light.write_text(build_primitive_library("light", bundle).svg, encoding="utf-8")
    outputs["primitives-dark"] = str(primitive_dark)
    outputs["primitives-light"] = str(primitive_light)

    origin_dark = GENERATED / "origin-dark.svg"
    origin_light = GENERATED / "origin-light.svg"
    origin_dark.write_text(render_origin_mark(resolve_theme("dark", bundle), bundle), encoding="utf-8")
    origin_light.write_text(render_origin_mark(resolve_theme("light", bundle), bundle), encoding="utf-8")
    outputs["origin-dark"] = str(origin_dark)
    outputs["origin-light"] = str(origin_light)

    boot_dark = GENERATED / "boot-dark.svg"
    boot_light = GENERATED / "boot-light.svg"
    write_boot(boot_dark, "dark", bundle)
    write_boot(boot_light, "light", bundle)
    outputs["boot-dark"] = str(boot_dark)
    outputs["boot-light"] = str(boot_light)

    identity_dark = GENERATED / "identity-dark.svg"
    identity_light = GENERATED / "identity-light.svg"
    write_identity(identity_dark, "dark", bundle)
    write_identity(identity_light, "light", bundle)
    outputs["identity-dark"] = str(identity_dark)
    outputs["identity-light"] = str(identity_light)

    systems_dark = GENERATED / "systems-dark.svg"
    systems_light = GENERATED / "systems-light.svg"
    write_systems(systems_dark, "dark", bundle)
    write_systems(systems_light, "light", bundle)
    outputs["systems-dark"] = str(systems_dark)
    outputs["systems-light"] = str(systems_light)

    telemetry_dark = GENERATED / "telemetry-dark.svg"
    telemetry_light = GENERATED / "telemetry-light.svg"
    write_telemetry(telemetry_dark, "dark", bundle)
    write_telemetry(telemetry_light, "light", bundle)
    outputs["telemetry-dark"] = str(telemetry_dark)
    outputs["telemetry-light"] = str(telemetry_light)

    chronology_dark = GENERATED / "chronology-dark.svg"
    chronology_light = GENERATED / "chronology-light.svg"
    write_chronology(chronology_dark, "dark", bundle)
    write_chronology(chronology_light, "light", bundle)
    outputs["chronology-dark"] = str(chronology_dark)
    outputs["chronology-light"] = str(chronology_light)

    signals_dark = GENERATED / "signals-dark.svg"
    signals_light = GENERATED / "signals-light.svg"
    write_signals(signals_dark, "dark", bundle)
    write_signals(signals_light, "light", bundle)
    outputs["signals-dark"] = str(signals_dark)
    outputs["signals-light"] = str(signals_light)

    interface_dark = GENERATED / "interface-dark.svg"
    interface_light = GENERATED / "interface-light.svg"
    write_interface(interface_dark, "dark", bundle)
    write_interface(interface_light, "light", bundle)
    outputs["interface-dark"] = str(interface_dark)
    outputs["interface-light"] = str(interface_light)

    handoff_dark = GENERATED / "handoff-dark.svg"
    handoff_light = GENERATED / "handoff-light.svg"
    write_handoff(handoff_dark, "dark", bundle)
    write_handoff(handoff_light, "light", bundle)
    outputs["handoff-dark"] = str(handoff_dark)
    outputs["handoff-light"] = str(handoff_light)

    hero_dark = BUILD / "hero-dark.svg"
    hero_light = BUILD / "hero-light.svg"
    write_hero(hero_dark, "dark", bundle)
    write_hero(hero_light, "light", bundle)
    outputs["hero-dark"] = str(hero_dark)
    outputs["hero-light"] = str(hero_light)

    manifest = {
        "tokens": str(DEFAULT_TOKEN_PATH),
        "generated": outputs,
    }
    (GENERATED / "foundation-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    outputs["manifest"] = str(GENERATED / "foundation-manifest.json")
    return outputs
