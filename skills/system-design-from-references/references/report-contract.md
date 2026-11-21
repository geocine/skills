# Report contract

The reports come from the **architecture-report** skill (`.claude/skills/architecture-report/`,
beside this one). Each is one self-contained HTML page, named `<name>-architecture.html`,
with `<h2 id>` sections. Newer reports use the Synapse Next layout (sidebar TOC, legend,
glossary); older ones use the herdr style. Both carry the same sections. Use this file in Phase 1 to grade each
report and to word questions back to the report side. The design side never fills a gap by
looking at the reference system itself.

## Standard sections (what architecture-report writes)

Ids vary a little between reports (`wire` or `sdk`, `render` or `ui`, `extend` / `mods` /
`plugins`, `model` / `tabs` / `profiles` / `devices`); match by heading, not by id.

| Report section (typical id) | What the design takes from it |
|---|---|
| Overview (`overview`) | Every process and link with its transport; the shape to compare in Phase 2. |
| Processes (`processes`) | Roles, lifetime, launch and supervision per OS, startup order: input to the processes and resilience decisions. |
| Communication (`wire`, `sdk`) | Endpoints, handshake, framing, message kinds, flow control, reconnect: input to the contracts (C-#). Wire formats needed for compatibility are restated as specifications. |
| Core data pipeline (`pipeline`) | How the main payload flows, both directions: input to the core components and scenarios. |
| UI or rendering (`render`, `ui`) | View tree, state → pixels, redraw scheduling, themes. |
| Extension points (`extend`, `mods`, `plugins`) | How one thing is added, lifecycle, permissions: input to the "Adding a <thing>" section. |
| Domain model (`model`, `tabs`, `devices`, `profiles`) | Hierarchy, persistence, lifecycle: input to the core model and lifecycle sections. |
| Services (`services`, `core-services`, …) | One line per module: the inventory the design's components must cover. |
| State and config (`state`) | Files, directories, config fields per OS: input to storage, migration and import. |
| Blueprint (`blueprint`, optional) | Transferable mechanisms with trade-offs: the most direct input to Phase 2 picks. |

Items the report marks as uncertain count as **thin**.

## Extra sections the design needs (ask the report side for them)

architecture-report includes what applies to a codebase and skips the rest, so these are
often missing. For the **current system in a rewrite** they matter most:

| Extra section | Why the design needs it |
|---|---|
| Feature-level interactions | Per user-visible feature: trigger, hop-by-hop path, ordering and failure behaviour, and **quirks** users rely on. Without it, behaviour silently changes in the rewrite. |
| Common modules | Shared libraries, how consumers link them, the drift it causes: input to the repository decisions. |
| Delivery | Build, packaging, update channel, rollout, version pinning: input to deployment units and release. |
| Observability | Logs, traces, crash reporting, support tooling. |
| Unknowns | What the report could not establish: goes straight into the risk register. |
| Licence | The project's licence and version (e.g. GPL-2.0): tells the design side how strictly to keep names and structure apart. |

A ready-to-send request for the report side:

```
Use architecture-report on <repos> (General mode, exhaustive). Write <name>-architecture.html in herdr-architecture/.
Besides the standard sections, add: Feature-level interactions (per feature: trigger, hops
with real message names, ordering, failure behaviour, quirks), Common modules (how they are
linked and versioned), Delivery, Observability, a Blueprint, an Unknowns section listing
every uncertain item, and the licence in the subtitle.
```

## Grading

- **Present**: enough to base a decision on (mechanism, not just a name).
- **Thin**: names the thing but not how it works, or is marked uncertain; decisions that
  depend on it are marked low-confidence.
- **Missing**: becomes a question in `design/questions-for-reports.md`.

## Writing a question for the report side

```
Q12 · openrgb · Communication
Missing   How a client learns that a controller was removed mid-session.
Blocks    D9 (device removal semantics), C-3 versioning rule.
Meanwhile Design assumes an explicit removal event; risk R7 tracks it.
```

Questions describe the behaviour wanted, never a file or function to go read.

## Names and line references in reports

Reports cite `file:line` and real type, function and message names, because that is how the
report side proves its claims. The design side uses them to understand the mechanism and
cites the report section, not the file. It does not carry those names into the new design,
except wire-level names needed for compatibility, which become specifications in the plan.
