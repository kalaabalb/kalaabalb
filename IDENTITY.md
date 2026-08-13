# KALAOS IDENTITY

Stage 4 defines the identity layer for KalaOS.

This is not a profile page, not a résumé, and not a social card.
It is the canonical contract for reconstructing a human identity from a source portrait through the existing KalaOS system.

## Purpose

The identity layer exists to turn a single source image into a deterministic point-field reconstruction that feels native to KalaOS.

It must:

- reuse the established token system
- reuse the shared geometry and surface primitives
- reuse the canonical Origin Mark where needed
- remain theme-aware without changing structure
- remain readable when motion is reduced
- avoid generic portfolio patterns

## Input Model

The identity layer is driven by a source configuration and a source portrait image.

The source config defines:

- subject identity fields
- portrait sampling parameters
- palette mapping
- layout bounds
- reduced-motion-safe metadata ordering

The source portrait image is not displayed directly as an image asset.
It is interpreted as structured visual data and reconstructed into points.

## Reconstruction Rules

The portrait renderer must behave deterministically.

Given the same source image, config, tokens, and theme, it must produce the same output.

The reconstruction should:

- sample the source image on a stable grid
- derive point density from luminance and local contrast
- use the established palette tokens
- preserve the subject silhouette before internal detail
- avoid a flat pixel-art look
- avoid photographic filters
- avoid decorative noise that is not derived from the source

The output should read as a point-field identity, not as a pasted photograph.

## Composition Rules

The identity composition should follow the existing visual system:

- strong frame discipline
- clear negative space
- measured metadata placement
- restrained supporting labels
- no competing modules
- no navigation chrome
- no social icon strip
- no project listing

The portrait and the metadata must feel like one system.
Neither should dominate by decoration.

## Theme Rules

Dark and light identity output must share the same structure.

Only theme-dependent values may differ:

- background
- surface fill
- border tone
- text tone
- point palette mapping

No theme may introduce alternate geometry or alternate layout logic.

## Motion Rules

Motion is used to reveal state, not to entertain.

The identity layer may use:

- a restrained entry reveal
- ordered metadata appearance
- point-field assembly feel

It must not use:

- looping effects
- glow choreography
- elastic motion
- dramatic zooming
- fake terminal theatrics

When reduced motion is enabled, the identity must remain fully understandable without animation.

## Boundary Rules

The identity layer may not become any of the following:

- a profile template
- a contact page
- a portfolio section
- a gallery
- a social banner
- a résumé replacement

Its job is only to formalize identity inside KalaOS.

## Canonical Relationship

The identity layer depends on the existing KalaOS foundation:

- MANIFESTO.md
- LANGUAGE.md
- VISUAL_DNA.md
- ARCHITECTURE.md
- ORIGIN.md
- BOOT.md
- ENGINE.md

It must not redefine the visual language.
It must only express it through identity reconstruction.
