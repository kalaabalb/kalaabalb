# KALAOS TELEMETRY

Stage 6 introduces the telemetry layer.

Telemetry is the observed activity of the systems already mapped in Stage 5.2.
It is not a GitHub statistics section and it is not a dashboard.

## Purpose

Telemetry shows that the mapped systems are producing signals.

The layer should feel observational, neutral, and technical.
It should let the visitor read activity before they read numbers.

## Data Sources

The renderer consumes a structured source snapshot:

- `assets/source/kalaos.telemetry.json`

The snapshot is derived from local repository context and can be regenerated from existing source trees.

It reflects observed file-based activity from the repositories available on disk.

## Temporal Model

The activity field uses a custom temporal trace rather than a contribution calendar.

The timeline is organized as:

- RECENT
- PAST
- OLDER

Temporal density is expressed as sparse pulses, short traces, and quiet intervals.

Silence is part of the signal.

## System Activity Model

Telemetry groups activity by system rather than by achievement.

Each system is rendered as:

- a system identifier
- a neutral state
- a reference string
- a compact trace field

The renderer must keep the relationship between signal and system visible.

## Language Field

The language field represents the programming-language composition of the observed repositories.

It is rendered as a continuous field.
It is not a pie chart.
It is not a bar chart.

Relative language presence affects:

- line length
- signal density
- trace weight
- optical emphasis

## Number Rules

Numbers are secondary.

They should orient the visitor without becoming the main story.

Use short values and stable formatting.
Do not exaggerate precision.
Do not invent counts.

## Unavailable Data

If telemetry cannot be resolved reliably, the layer must fail intentionally.

In that case the output should say:

- `NO SIGNAL`

or:

- `TELEMETRY UNAVAILABLE`

The failure state should still feel designed.

## Motion

Motion is used to express signal resolution.

The intended sequence is:

1. telemetry field establishes
2. temporal traces resolve
3. system activity appears
4. language field resolves
5. numbers settle
6. the final state becomes quiet

Motion must not become decorative.
It must remain understandable when removed.

## Reduced Motion

Reduced-motion output must preserve:

- the telemetry title
- the activity field
- the language field
- the system identifiers
- the summary numbers

No essential information may disappear.

## Theme Behavior

Dark and light telemetry outputs must remain structurally identical.

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

Future telemetry revisions should extend the source snapshot rather than invent a separate render path.

The renderer must remain configuration-driven.
If new systems or language sources are added later, they should be introduced through the same structured snapshot.
