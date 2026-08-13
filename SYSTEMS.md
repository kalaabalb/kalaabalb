# KALAOS SYSTEMS

Stage 5 introduces the Discovery layer.

This layer does not present a portfolio grid. It maps built work as a structured coordinate field.

## Purpose

The systems layer reveals what the subject builds after identity has already been resolved.

Its job is to make the visitor feel that:

- a system has been charted
- the nodes are meaningful
- the relationships are real
- the field still belongs to the same KalaOS world

## Data Schema

The systems layer is driven by a source configuration file:

- `assets/source/kalaos.systems.json`

The schema is intentionally extensible. Each node may define:

- `id`
- `name`
- `domain`
- `description`
- `technologies`
- `state`
- `importance`
- `position`
- `label`

Each relationship may define:

- `source`
- `target`
- `kind`
- `label`

The renderer must not hardcode project records.

## Node Model

Each node represents a built system rather than a conventional project card.

Nodes are rendered with:

- a coordinate position
- a small architectural node mark
- a visible hierarchy through scale and opacity
- staged annotation text
- a state indication
- a domain color relationship

The visible hierarchy is:

1. system mark
2. system name
3. contextual resolution

Level 3 remains quieter than the system identity itself.

Importance is expressed through geometry, spacing, and emphasis, not through badges or dashboard styling.

## Relationship Model

Connections are only drawn when there is a meaningful relationship in the source data.

Supported relationship meanings include:

- continuation
- dependency
- shared domain

Relations are visualized as thin structural lines with concise labels.

Relationship labels are tertiary annotations. They should not compete with system identity.

If no meaningful relationship exists, no line is drawn.

## Visual Hierarchy

The composition should read in layers:

1. discovery state
2. charted systems title
3. coordinate field
4. primary systems
5. secondary systems
6. less prominent systems
7. relationships

The field must remain larger than the amount of information inside it.

Negative space is intentional.

The eye should notice the system mark first, then the name, then contextual resolution.

## Coordinate System

The systems layer uses the shared KalaOS canvas and grid discipline.

Positions are resolved into the same coordinate language used by the rest of the engine.

The renderer may use a clipped field region, guide lines, and subtle references, but it should not become a literal map.

## Motion

Motion is used to communicate discovery.

The sequence should suggest:

- the field establishing itself
- primary systems appearing
- secondary systems resolving
- relationships appearing
- labels settling

Motion should never be required to understand the final state.

## Reduced Motion

Reduced-motion output must still contain:

- the full field
- all nodes
- all supported relationships
- the title
- the supporting line

No essential information may disappear with motion disabled.

## Theme Behavior

Dark and light systems output must share the same structure.

Only theme-dependent values may differ:

- background
- surface values
- borders
- text tones
- node colors

## Extension Rules

Future systems can be added by extending the source JSON and re-running the existing build pipeline.

Do not create parallel renderers or separate systems-specific build flows.

The Discovery layer must continue to feel like KalaOS, not a generic portfolio.
