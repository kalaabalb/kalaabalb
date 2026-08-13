# KALAOS CHRONOLOGY

Stage 7 introduces chronology.

Chronology is the memory of KalaOS expressed as preserved strata.
It is not a timeline and it is not a resume history section.

## Purpose

Chronology shows how the system became what it is.

It should feel like accumulated structure, not a list of dated entries.

## Emotional Role

Chronology should feel observed, restrained, and continuous.

The visitor should feel that earlier states remain present beneath later ones.

## Data Source

Chronology is driven by observed repository evidence.

Primary inputs:

- `MANIFESTO.md`
- `LANGUAGE.md`
- `VISUAL_DNA.md`
- `ARCHITECTURE.md`
- `ORIGIN.md`
- `BOOT.md`
- `IDENTITY.md`
- `SYSTEMS.md`
- `TELEMETRY.md`
- `ENGINE.md`
- `assets/source/kalaos.tokens.json`
- `assets/source/kalaos.identity.json`
- `assets/source/kalaos.systems.json`
- `assets/source/kalaos.telemetry.json`

If the chronology cannot be resolved from local evidence, the renderer must fail intentionally with a designed no-signal state.

## Temporal Model

Chronology uses preserved strata rather than a line of events.

Older states remain quieter and more fragmented.
Newer states are more resolved.

The current state is the point where the preserved traces converge.

## Visual Model

The field should read as a layered cross-section of the system.

It should not resemble:

- a timeline
- a roadmap
- a contribution graph
- a milestone list

## State Hierarchy

The visible hierarchy is:

1. CHRONOLOGY
2. current state
3. historical strata labels
4. temporal metadata
5. tiny reference information

Dates are secondary.
Structure is the hero.

## Motion

Motion should communicate resolution.

The sequence is:

1. field establishes
2. oldest strata resolve faintly
3. later strata establish
4. transitions appear
5. current state resolves
6. metadata settles

Motion must remain understandable when removed.

## Reduced Motion

Reduced-motion output must preserve:

- the chronology field
- the strata labels
- the temporal metadata
- the current state
- the reference information

No essential chronology information may disappear.

## Failure State

If reliable chronology cannot be resolved, the renderer should show:

- `NO CHRONOLOGY SIGNAL`

or:

- `CHRONOLOGY UNAVAILABLE`

The failure state should still feel designed.

## Theme Behavior

Dark and light chronology outputs must share the same geometry and structure.

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

Future temporal layers should extend the source snapshot rather than introduce a separate architecture.

Chronology must remain configuration-driven and deterministic.

If new observed evidence becomes available, add it through the same structured source file and rebuild the existing pipeline.
