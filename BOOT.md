# KalaOS Boot Experience

Boot Experience v1 is the first constructed surface of KalaOS.

It does not simulate a computer.
It does not imitate a terminal.
It presents a system becoming present.

## State Machine

The boot sequence follows six visible states plus the implicit empty field that precedes them.

1. Void
2. Origin
3. Identification
4. Calibration
5. Deferred Identity
6. System Ready
7. Handoff

The sequence must read as construction first, information second, identity last.

## State Order

The visual order is fixed.

1. The field begins sparse.
2. The canonical Origin Mark assembles.
3. `KALAOS` appears.
4. The environment calibrates.
5. `IDENTITY DEFERRED` is revealed.
6. `SYSTEM READY` stabilizes the surface.
7. The handoff for `Identity.app` is established.

No future state may reorder these steps without revising the boot contract.

## Timing Philosophy

Motion is measured rather than expressive.

The sequence should feel like state transitions, not effects.

Use the existing motion tokens to stage the experience:

- `fast` for small adjustments
- `normal` for short reveals
- `reveal` for state disclosure
- `assemble` for the full boot progression
- `slow` only where the environment needs more breathing room

The intended result is a quiet build-up, not a dramatic animation.

## Motion Behavior

Motion is allowed only when it communicates structure.

Accepted behaviors:

- fade-in
- restrained position reveal
- sequential state disclosure
- final stabilization

Rejected behaviors:

- bounce
- elastic easing
- pulse
- glow cycles
- continuous rotation
- screen shake
- fake typing
- zoom theatrics

The Origin Mark remains the canonical construction symbol and must not be redesigned.

## Accessibility Behavior

Reduced motion must remain legible.

If motion is unavailable or disabled:

- the Origin Mark must still be visible
- `KALAOS` must still read clearly
- the state text must still communicate the boot progression
- the handoff must still be understandable

No information may depend exclusively on animation.

## Responsive Strategy

The boot experience must remain coherent at desktop, tablet, and mobile sizes.

The composition should rely on:

- the shared grid
- the shared frame geometry
- proportional spacing
- scalable SVG output

It must not depend on hover.
It must not depend on JavaScript.
It must remain compatible with GitHub-rendered Markdown.

## Future Handoff

The final boot state is not Identity.app.

It only establishes the architectural point where Identity.app will begin in a later phase.

The handoff should signal:

- the environment is stable
- the origin has been established
- identity is deferred, not absent

The boot experience ends by opening the next phase rather than completing the story.
