# KALAOS SIGNALS

Stage 8 introduces the Signals layer.

Signals is the current capability field of KalaOS.
It is not a skills list, not a technology inventory, and not a résumé section.

## Purpose

Signals shows what can be resolved from the accumulated evidence of the system.

The layer should feel like capability being detected, not capability being claimed.

## Conceptual Role

Signals comes after Origin, Boot, Identity, Systems, Telemetry, and Chronology.

It should feel like the system has stabilized enough that real capabilities can be inferred from its work.

## Data Source

The renderer is driven by a structured source snapshot:

- `assets/source/kalaos.signals.json`

The snapshot must be derived from observable repository evidence.

## Evidence Model

Every resolved or resolving signal must point back to local evidence.

Acceptable evidence includes:

- source files
- build scripts
- stage documentation
- shared engine modules
- structured source snapshots
- repeated implementation patterns

Do not fabricate capabilities.

## Signal States

Signals use four states:

- `UNRESOLVED`
- `DETECTED`
- `RESOLVING`
- `RESOLVED`

Geometry, density, continuity, and completeness communicate state.

## Visual Model

Signals should read as a measurement field.

It should not look like:

- a conventional skills grid
- a card list
- a dashboard
- a radar chart
- a technology cloud

The field must contain partial traces, converging traces, quiet gaps, and compact resolved markers.

## Resolution Model

Unresolved signals are faint and incomplete.
Detected signals are clearer but still small.
Resolving signals show multiple traces converging.
Resolved signals are structurally coherent and readable.

The geometry is primary.
Text is secondary.

## Relationships

Signals may imply relationships to evidence through restrained structural traces.

These traces should explain why a signal exists.
They must not turn into a network diagram.

## Motion

Motion should represent acquisition:

1. the field appears
2. traces enter
3. coordinates form
4. some signals remain incomplete
5. stronger signals converge
6. resolved signals settle
7. the field quiets

Motion must remain understandable when removed.

## Reduced Motion

Reduced-motion output must preserve:

- the title
- the signal field
- all signal states
- evidence references
- the final resolved composition

No essential information may disappear.

## Failure State

If evidence is insufficient, the renderer should fail intentionally with a designed no-signal state.

Use:

- `NO SIGNAL`

or:

- `INSUFFICIENT EVIDENCE`

## Theme Behavior

Dark and light outputs must share the same geometry and structure.

Only theme-dependent values may differ:

- background
- surfaces
- borders
- text tones
- trace colors

## GitHub Compatibility

The generated SVG must remain self-contained.

It must not rely on:

- JavaScript
- external fonts
- browser APIs
- remote assets
- client-side fetching

## Extension Rules

Future signals should extend the source snapshot rather than introduce a parallel renderer.

Do not turn the layer into a conventional portfolio section.
Do not invent capabilities that are not supported by the repository evidence.
