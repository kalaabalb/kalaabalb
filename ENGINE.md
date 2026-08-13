# KalaOS Engine

This repository now has a core engineering foundation for KalaOS.

## Source of Truth

The shared token source lives at:

- [`assets/source/kalaos.tokens.json`](./assets/source/kalaos.tokens.json)

All spacing, radii, stroke widths, typography scale, motion timing, opacity, z-index, grid rhythm, theme values, and hero layout coordinates flow from that file.

## Engine Modules

- [`engine/tokens.py`](./engine/tokens.py) loads and exposes the token bundle.
- [`engine/theme.py`](./engine/theme.py) resolves light and dark themes from the shared tokens.
- [`engine/motion.py`](./engine/motion.py) exposes the motion system as named durations and easing curves.
- [`engine/layout.py`](./engine/layout.py) centralizes reusable shell geometry.
- [`engine/svg_primitives.py`](./engine/svg_primitives.py) renders reusable SVG primitives and the primitive library.
- [`engine/boot.py`](./engine/boot.py) renders the staged boot experience from the locked foundation.
- [`engine/portrait.py`](./engine/portrait.py) converts a source portrait into a deterministic point field.
- [`engine/identity.py`](./engine/identity.py) composes the first identity reconstruction layer.
- [`engine/systems.py`](./engine/systems.py) composes the Discovery layer as a charted systems field.
- [`engine/telemetry.py`](./engine/telemetry.py) composes the system activity layer from observed local repository data.
- [`engine/chronology.py`](./engine/chronology.py) composes the temporal strata layer from observed repository evidence.
- [`engine/signals.py`](./engine/signals.py) composes the capability signal layer from observed repository evidence.
- [`engine/interface.py`](./engine/interface.py) composes the Stage 9 invocation layer from the resolved Signals field.
- [`engine/handoff.py`](./engine/handoff.py) composes the Stage 10 transfer boundary from the selected Stage 9 action.
- [`engine/hero.py`](./engine/hero.py) renders the modular hero surface from configuration.
- [`engine/pipeline.py`](./engine/pipeline.py) orchestrates directory setup and generated assets.

## Asset Pipeline

The asset tree is split into explicit stages:

- `assets/source/` for canonical source data
- `assets/generated/` for derived SVG primitives and manifests
- `assets/temp/` for scratch outputs used during future builds
- `assets/build/` for final render targets

This separation keeps source data stable, generated assets reproducible, and temporary work isolated from final outputs.

## Theme Contract

The theme engine exposes two supported modes:

- `dark`
- `light`

Every future KalaOS surface should consume the same theme contract instead of inventing new color logic.

## Primitive Contract

The primitive library provides reusable SVG building blocks for:

- grids
- construction lines
- coordinate marks
- rulers
- calibration marks
- separators
- corner geometry
- masks
- clipping primitives
- particle primitives
- the Origin Mark construction symbol

Future applications should reference these primitives instead of redefining their own visual grammar.

## Origin Mark Contract

The Origin Mark is generated as a reusable construction symbol and also exported as standalone dark and light assets.

It is the first shared reference point for every future KalaOS surface.

## Generated Origin Outputs

- `assets/generated/origin-dark.svg`
- `assets/generated/origin-light.svg`

## Boot Contract

The boot engine composes the first KalaOS experience from the shared primitives, motion system, and token bundle.

It produces staged dark and light boot assets:

- `assets/generated/boot-dark.svg`
- `assets/generated/boot-light.svg`

The boot sequence is configuration-driven and designed so the final constructed state remains understandable even when motion is reduced.

## Identity Contract

The identity engine resolves a source portrait into a deterministic point-field reconstruction and composes sparse identity metadata around it.

It produces staged dark and light identity assets:

- `assets/generated/identity-dark.svg`
- `assets/generated/identity-light.svg`

The portrait source remains external to the generated output pipeline and the identity renderer must stay reusable for another subject without architectural changes.

## Systems Contract

The systems engine maps built work as a structured coordinate field rather than a portfolio grid.

It consumes a source systems configuration and produces generated dark and light outputs:

- `assets/generated/systems-dark.svg`
- `assets/generated/systems-light.svg`

Node prominence, relationship meaning, and spatial placement remain data-driven so future systems can be added without changing the renderer architecture.

## Telemetry Contract

The telemetry engine observes system activity and language composition without turning into a conventional stats dashboard.

It produces generated dark and light outputs:

- `assets/generated/telemetry-dark.svg`
- `assets/generated/telemetry-light.svg`

The renderer consumes a structured source snapshot and must continue to work when the underlying data are reduced to an intentional `NO SIGNAL` state.

Telemetry remains a KalaOS surface, not a GitHub analytics widget.

## Chronology Contract

The chronology engine represents preserved time as structural strata rather than a conventional timeline.

It produces generated dark and light outputs:

- `assets/generated/chronology-dark.svg`
- `assets/generated/chronology-light.svg`

The renderer consumes observed repository evidence and should degrade to an explicit no-signal state if chronology cannot be resolved from the local workspace.

Chronology remains part of the same KalaOS visual world and must not drift into résumé language or roadmap language.

## Signals Contract

The signals engine represents capabilities resolved from local evidence rather than claimed skills.

It produces generated dark and light outputs:

- `assets/generated/signals-dark.svg`
- `assets/generated/signals-light.svg`

The renderer consumes a structured source snapshot and must stay configuration-driven, deterministic, and evidence-backed.

Signals must remain within the same KalaOS system language and must not collapse into a conventional skills section.

## Motion Contract

Motion is tokenized and named:

- `fast`
- `normal`
- `slow`
- `reveal`
- `assemble`
- `dissolve`
- `idle`

These values express state. They are not decorative timings.

## Hero Contract

The hero renderer is now configuration-driven.

It reads from the shared tokens and layout definitions instead of hardcoding shell geometry. Future phases can swap the content layer while keeping the same engine.

## Future Application Contract

Future applications plug into the engine by:

1. reading the shared token bundle
2. resolving the current theme
3. using the shared primitive library
4. consuming the motion system
5. placing surfaces on the shared grid
6. writing outputs into the asset pipeline stages

No future application should define its own parallel color system, spacing scale, or surface language unless the KalaOS source docs are revised first.

## Build Entry Point

Run the foundation build through:

- [`scripts/build_foundation.py`](./scripts/build_foundation.py)

That script regenerates the full locked KalaOS foundation through Stage 10, including the shared token bundle, primitive library outputs, the canonical Origin Mark assets, boot outputs, identity outputs, systems outputs, telemetry outputs, chronology outputs, signals outputs, interface outputs, handoff outputs, and the reusable hero surface. The generated files remain split across the dedicated source, generated, temp, and build asset folders so each stage stays reproducible and isolated.

The Stage 9 interface contract is now implemented as a generated dark and light asset pair:

- `assets/generated/interface-dark.svg`
- `assets/generated/interface-light.svg`

The Stage 10 handoff contract is now implemented as a generated dark and light asset pair:

- `assets/generated/handoff-dark.svg`
- `assets/generated/handoff-light.svg`

In practical terms, the build output now covers the complete implemented stack through Stage 10:

- foundation tokens and shared layout primitives
- reusable SVG primitives
- the canonical Origin Mark
- boot
- identity
- systems
- telemetry
- chronology
- signals
- interface
- handoff
- the reusable hero surface

This summary is intentionally limited to the implemented stages only and should not be read as a Stage 11 or later contract.
