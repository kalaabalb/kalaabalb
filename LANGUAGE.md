# KalaOS Language System

This document defines the official vocabulary of KalaOS.

It is not implementation guidance.
It is the communication contract every future KalaOS surface must follow.

## 1. The Voice

KalaOS speaks like a real operating environment, not like a person trying to sound like software.

Its voice is:

- calm
- architectural
- scientific
- minimal
- precise
- emotionally neutral

KalaOS should use short phrases unless the state being described requires more detail.
It should prefer nouns and verbs over adjectives.
It should explain only what is necessary to orient the visitor.
It should never sound conversational for its own sake.

The ideal KalaOS message is direct enough to be understood immediately, but restrained enough to feel deliberate.

## 2. The Golden Rules

1. Never shout.
2. Never use exclamation marks.
3. Never apologize.
4. Never over-explain.
5. Never market.
6. Never flatter the visitor.
7. Never speak casually.
8. Never pretend to be alive.
9. Never use filler words.
10. Never use decorative language to hide weak structure.
11. Never ask unnecessary questions.
12. Never describe what is already obvious from the interface.
13. Never repeat a message in a weaker form.
14. Never mix systems language with résumé language.
15. Never break the vocabulary contract of KalaOS.

## 3. System Vocabulary

KalaOS replaces generic interface language with operational language.

| Common term | KalaOS term | Reason |
| --- | --- | --- |
| Loading | Synchronizing | Loading is passive; synchronizing implies systems aligning into state. |
| Open | Initialize | Opening is generic; initialize signals an operational event. |
| Close | Archive | Close suggests dismissal; archive suggests preservation. |
| Settings | Configuration | Configuration is more precise and technical. |
| Section | Module | Module implies a functional unit inside a system. |
| Card | Surface | Surface feels like a designed plane, not a widget. |
| Window | Workspace | Workspace feels like an operational container. |
| Panel | Node | Node implies a connected component in a larger network. |
| User | Operator | Operator describes interaction within a system. |
| Visitor | Observer | Observer is more neutral and more fitting for a system interface. |
| Application | Environment | Application is too ordinary; environment suggests a contained world. |
| Repository | Artifact | Artifact implies a preserved technical object. |
| Profile | Identity | Identity is a more exact word for a persona inside the system. |
| Contact | Signal | Contact is social; signal is operational. |
| Projects | Constructs | Constructs suggests structured work inside the system. |
| Timeline | Chronology | Chronology feels more formal and system-driven. |
| Skills | Capabilities | Capabilities describes functional potential rather than self-promotion. |
| Languages | Systems | Systems is broader and more aligned with KalaOS language. |
| Statistics | Telemetry | Telemetry implies measurable system output. |
| About | Origin | Origin is more architectural and less personal. |
| Memory | Archive | Archive suggests preserved state. |
| Update | Recalibrate | Update is generic; recalibrate implies system adjustment. |
| Connect | Link | Link is short, technical, and stable. |
| Disconnect | Detach | Detach feels mechanical and controlled. |
| Status | State | State is more precise and less abstract. |
| Detail | Metadata | Metadata is the language of systems. |
| Note | Record | Record suggests durable storage. |
| Message | Transmission | Transmission sounds like routed system communication. |
| File | Asset | Asset fits the idea of reusable system material. |
| Folder | Archive | Archive suggests structured storage. |
| Dashboard | Console | Console is more grounded and less business-oriented. |
| Menu | Index | Index is more disciplined and searchable. |
| Search | Scan | Scan feels like a system action. |
| Alert | Notice | Notice is calmer and less alarming. |
| Error | Fault | Fault is more technical and less casual. |
| Success | Stable | Stable communicates resolved state. |
| Progress | Sequence | Sequence implies ordered system steps. |
| Help | Reference | Reference is more formal and less conversational. |

Every replacement must preserve clarity. KalaOS does not obscure meaning for style.

## 4. Forbidden Words

KalaOS will not use the following words in its interface vocabulary unless a future application has an exceptional technical reason:

- Awesome
- Cool
- Welcome
- Hi
- Hello
- Click here
- Contact me
- About me
- My Projects
- My Skills
- Developer
- Portfolio
- Profile
- GitHub Stats
- Resume
- Bio
- Summary
- Fun
- Hack
- Hacker
- Hacky
- Magic
- Wow
- Beautiful
- Nice
- Simple
- Friendly
- Personal
- Social

Why they are forbidden:

- They sound like marketing.
- They sound casual when the system should feel composed.
- They flatten the distinction between a product language and a personal introduction.
- They reduce the sense of operating-system identity.

## 5. Boot Terminology

Boot language should feel like a real initialization sequence.

Preferred boot messages:

- Calibrating Spatial Grid
- Initializing Coordinate Space
- Synchronizing Archives
- Loading Identity
- Verifying Modules
- Measuring Baseline
- Resolving Particles
- Building Workspace
- Reading System Memory
- Mounting Shell
- Establishing Frame
- Aligning Surfaces
- Indexing Metadata
- Rendering Field
- Staging Interface
- Preparing Modules
- Constructing Layout
- Mapping Coordinates
- Locking Reference Frame
- Confirming State
- Signal Stabilized
- Environment Ready
- KalaOS Ready

Boot messages should be sparse, sequential, and believable.
They should describe state transitions rather than narrate feelings.

## 6. State Terminology

KalaOS states describe system conditions.

Preferred states:

- Idle
- Synchronizing
- Rendering
- Initializing
- Offline
- Linked
- Archived
- Observed
- Indexed
- Scanning
- Dormant
- Stable
- Recovered
- Mapped
- Verified
- Calibrated
- Locked
- Pending
- Active
- Settled

State words should be used consistently across boot flows, panel labels, indicators, and notifications.

States should be descriptive, not decorative.

## 7. Interface Labels

Common interface elements should be renamed to fit KalaOS:

- Button → Action
- Panel → Node
- Sidebar → Rail
- Tooltip → Annotation
- Navigation → Route
- Modal → Overlay
- Dialog → Exchange
- Notification → Notice
- Error → Fault
- Warning → Caution
- Success → Stable
- Progress → Sequence
- Loader → Sequence Marker
- Input → Field
- Form → Intake
- Tab → Register
- Badge → Marker
- Tag → Label
- Card → Surface
- Menu → Index

These terms should be used only when they improve the system language.
If a generic term is clearer for a specific technical context, clarity still wins.

## 8. Microcopy

Microcopy should be short, factual, and state-driven.

Preferred examples:

- Identity Pending
- Coordinate Locked
- Rendering Complete
- Artifact Indexed
- Synchronization Complete
- Observer Connected
- Workspace Archived
- Module Detached
- Frame Stabilized
- Signal Captured
- Baseline Confirmed
- Surface Calibrated
- Archive Mounted
- Route Established
- Environment Ready
- State Verified

Microcopy should avoid personality.
It should tell the visitor what the system is doing or what state it has reached.

## 9. Numbers

KalaOS numbers must feel technical and consistent.

Guidelines:

- Use zero padding when it improves alignment.
- Use dotted or hyphenated version strings for builds and releases.
- Use coordinates in paired or grid-aligned formats.
- Use ISO-like dates when precision matters.
- Use short, stable identifiers for modules and artifacts.
- Use hash fragments only when the system truly needs them.

Examples:

- `Build 0.0.1-alpha`
- `v1.0.0`
- `Frame 04`
- `Module 12`
- `Coord 18.44 / 00.00`
- `2026-08-06`
- `ID-KA-014`
- `hash: 8c21f4`

Numbers should support orientation and versioning.
They should never feel like decoration.

## 10. Silence

Silence is part of the vocabulary.

KalaOS should intentionally say nothing when:

- the interface is already self-explanatory
- a state is obvious from motion or layout
- repeating text would reduce clarity
- the visitor should be left to observe before reading
- a transition is better understood through spacing than through words

Whitespace is communication because it creates order.
Absence is communication because it creates emphasis.
KalaOS should not fear empty space or missing labels when restraint improves the system.

## 11. Final Test

If every logo, icon, and color were removed, KalaOS should still sound like KalaOS.

The vocabulary must carry the identity.

It should feel operational, measured, and architectural.
It should not sound like a personal page.
It should not sound like a generic software dashboard.
It should sound like one coherent system with its own rules.

If a word does not belong to that world, it should not be used.

