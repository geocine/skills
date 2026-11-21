# Design document skeletons

Two documents, kept in unison. The **proposal** explains how the system works and why; the
**plan** says how it gets built and how anyone knows it is done. Same visual language, same
running example, same ids.

Every page and section follows `writing-style.md`: a short name, a claim first, "Read this
page to…", the drawing that answers the page's question, and "What to read next". The
"What it must contain" column says what facts a section holds, not how long its title is:
section titles stay two to four words.

## Pages every design has

These three are written as well as the sections in the two skeletons. They are where a new
developer starts, so write them last, when the rest is settled, and place them first.

| Page | Where | What it must contain |
|---|---|---|
| Developer guide | Second in the reading order, after "Why" | The divisions of the system (does / never does); how they talk (link, what crosses, contract); one user action end to end as a sequence drawing with the same steps listed; the words that carry the design; where your code goes; a reading order. |
| Adding a <thing> | With the feature or extension material | The claim (what is written once); what you write and what the build gives back; numbered steps with file paths and code on the running example; which running part uses which file; the run-time path; rules; how to choose where a choice exists; what to do when nothing fits. One page per kind of thing. |
| How the work gets done | First in the build material | What is built or ported in what order and why; one unit of work as a swimlane with a lane for the person; what stays with a person and why; links to the proof rules and the gates. |

## Architecture proposal

| # | Section | What it must contain |
|---|---|---|
| 1 | Why change | Before/after diagram of the current system vs the new one on the running example; the measurable pains (crashes, memory, release time) with numbers. |
| 2 | Design principles | 5–8 principles, each one sentence + the reference that proves it works. |
| 3 | Prior art | The Phase 2 matrix, condensed: what each reference teaches, what we take, what we refuse. |
| 4 | Processes | Every process, privilege, lifetime, supervision; typed boundaries. |
| 5 | Core model | The central abstraction (features, documents, devices…) and how capability, not identity, drives behaviour. |
| 6 | Domain layers | One section per major layer (e.g. device model, protocol layer, storage), each diagram-first. |
| 7 | Adding a <thing> | The extension walkthrough: every file touched to add one new item. The design is good when this list is short. |
| 8 | IPC and state | Wire format, schema registry, versioning, intent vs applied state, reconciliation. |
| 9 | UI | What the screens look like (wireframes) and who decides each part; the layers; what is data and what is code; how a definition reaches pixels; the surfaces (inline, pinned, tooltip, overlay, dialog); how two panels work together; the command table shared by keys, menus, CLI and agents. |
| 10 | Optional features | How heavy or optional features are isolated (separate hosts, lazy load, kill switches). |
| 11 | Deployment units | What ships separately, versioning of each, what updates without a release. |
| 12 | Repository | Monorepo/polyrepo, dependency rules enforced by a check, ownership. |
| 13 | Quality | Test pyramid, simulator, fleet matrix, what gates a merge vs a release. |
| 14 | Build, release, delivery | Pipeline, rings, rollback, "is it in production?" answered by a ledger. |
| 15 | Observability | Trace id from click to wire, flight recorder, crash reporting, support tooling. |
| 16 | Resources | Memory/CPU/latency budgets and the mechanisms that hold them. |
| 17 | Migration | How users move from the current system; coexistence or not, cohorts, rollback. |
| 18 | Risks | Risk, signal, mitigation, owner. |

Drop sections that do not apply; never pad.

## Build plan

| # | Section | What it must contain |
|---|---|---|
| 1 | System | The whole system on one diagram, every component typed. |
| 2 | Core components | Each component: responsibility, inputs/outputs, threads, state it owns, failure behaviour. Types vs instances explicit. |
| 3 | Walkthroughs | The running example traced step by step (scenario players). Each is known by its title, with no label such as W1. On the site each plays on the page that teaches its subject, not on a reference page. |
| 4 | End-to-end flows | Bootstrap, detection/discovery, the main interaction, the main failure. |
| 5 | Decisions | D1…Dn, grouped by subject (five to eight groups, a page each on the site). Each decision is a heading with its text, basis (report sections) and consequence. The one-line index is generated from them. |
| 6 | Prior art | Links into the reference pages per decision. |
| 7 | Feature slices | Features as vertical slices through the layers; dependencies between features. |
| 8 | Repository layout | The tree, ownership, dependency rules. |
| 9 | Contracts | C-1…C-n: endpoints, contract, encoding, versioning, who may call. |
| 10 | Lifecycle | States of the core entity and who may move it between them (leases, ownership). |
| 11 | Resilience | What crashes, what restarts it, what the user sees. |
| 12 | Performance and reliability | Budgets per path, how they are measured. |
| 13 | Platform areas | Install, update, privilege, accessibility, i18n, telemetry, sync — one card each. |
| 14 | Cutover | For a rewrite: cohorts, coverage gates, rollback. |
| 15 | Invariants and definition of done | I-1…I-n, each with the check that proves it; DoD per epic type. |
| 16 | Work breakdown | E1…En: lane, owner, depends on, weeks, DoD. Critical path drawn. |
| 17 | Milestones and gates | M0…Mn: week range, exit criteria that are observable. |
| 18 | Team and cadence | Lanes, who owns which folders, how agents are driven, review flow. |
| 19 | Risks, metrics | Risk register; metrics with budgets and alert thresholds. |
| A | Tooling | Build, test, release commands. |
| B | Glossary | Every acronym and term. |
| C | References | Reference pages and external sources. |

## Decision record format

```
D7 · One actor per device
Decision  Every device is owned by one actor with a mailbox; nothing else writes to it.
Basis     OpenRGB per-controller threads (openrgb-architecture.html#pipeline);
          the current system's shared-handle races (current-architecture.html#features).
Consequence  Cross-device effects go through the bus; I-3 checks single ownership.
```

## Writing rules (both documents)

The full rules, with examples and the checks to run, are in `writing-style.md`. In short:

- Short names; the explanation goes under the name. No ids or private labels in headings.
- One word per concept, and an id prefix that matches the word.
- Every page and section opens with a claim; every page says who it is for and what to read next.
- Assertive voice; decisions, not options. Hedges go to the risk register.
- The drawing that answers the section's question comes first (`visual-rules.md`, "Which
  drawing"); then tables with one line per cell, lists, and code contracts.
- Define every term and acronym at first use and in the glossary.
- Code samples agree with every other sample in the docs.
- One running example everywhere.
- Ids are permanent; append, never renumber after anyone has linked to them.
- When the two documents disagree, fix one of them in the same change.
