---
name: system-design-from-references
description: Clean-room system design. Takes architecture reports of several reference systems (produced beforehand by the architecture-report skill, the *-architecture.html pages) as the only input, compares them, and writes an assertive architecture proposal and a build plan with stable ids (decisions, seams, invariants, epics, milestones), plus scenarios that double as executable specs. The user chooses the output: single self-contained HTML files in the Synapse Next docs layout (sidebar document switcher, section TOC, legend, hover cards), or a React docs site built from the Synapse Next site (topic pages, animated scenario players, search). Use this whenever the user has architecture reports or reference pages and wants a design from them — "design the rewrite from these reports", "compare these architectures and propose ours", "master plan", "architecture proposal", "design doc from prior art", "clean room design" — even if they never say "reference". It never reads the reference systems' code or artifacts itself.
argument-hint: "[report paths or folder] [react (default) | single] [target system, optional]"
---

# Clean-room system design from architecture reports

Good designs are assembled from mechanisms that already work somewhere, with the reasons
written down. This skill does the **design side** of a clean-room process:

```
 REPORT SIDE: architecture-report skill    │  DESIGN SIDE: this skill
                                           │
 reference repos ─► architecture-report    │  reports ─► Phase 1 INTAKE    check reports, list gaps
 ─► <name>-architecture.html per system ───┼──────────►  Phase 2 COMPARE   concern × reference, pick + why
                                           │             Phase 3 PROPOSE   architecture proposal
       ◄────── questions for the report side (gaps) ──── Phase 4 PLAN      build plan with stable ids
                                           │             Phase 5 PROVE     scenarios as executable specs
                                           │             Phase 6 AUDIT     consistency, visuals, provenance
```

Each phase produces a durable file, so work can stop and resume at any phase.

The report side is the **architecture-report** skill (`.claude/skills/architecture-report/`,
beside this one). It reads the reference repos directly: the open-source projects (cloned
or opened locally) and the current product's own code. That is its job, and nothing on the
report side is restricted. Run it in its own session; run this skill in a separate session
that sees only the finished reports. Both sides now share the Synapse Next look and
layout (see "Output style"); older herdr-style reports are still valid input.

## Clean-room rules

The point of a clean room is that the new system is written from descriptions of behaviour
and interfaces, never from the reference systems' own code. Open source does not make the
code free to reuse: most of these projects are copyleft (GPL) or non-commercial, and code
copied from them would bind the new product to their licence. The report side reads the
code; the design side reads only the reports. Keeping that line is what makes the design
defensible and original, so treat these as the boundary of the skill:

- **Decide only from the reference architectures.** The reports are the only source of
  design decisions. Every mechanism the design adopts is one a report describes, or a blend
  of several. The user's frame (target and constraints, Phase 0) chooses between those
  mechanisms but never adds one. If no report covers a concern, the answer is a question
  for the report side or a new reference report, not an invented mechanism.
  Do not open, search, clone, decompile or run the reference systems' source, binaries,
  installers or packages, even when they are open source and already on disk.
- **Gaps go back as questions, not lookups.** When a report does not say how something
  works, add it to `design/questions-for-reports.md` (what is missing, which decision waits
  on it) and design around the gap or flag it as a risk. The report side answers by
  updating its report.
- **Restate, never copy.** Describe mechanisms in your own words and your own names. Do not
  carry over code, identifiers, comments, file layouts or proprietary strings. Interface
  facts needed for compatibility (a wire format, a file format a user's data is stored in)
  are restated as specifications in the plan's interface section, with the report section
  they came from.
- **Provenance on every decision.** Each decision's basis cites one or more report
  sections (`openrgb-architecture.html#pipeline`). A frame constraint may be named as the
  reason one reported mechanism beat another, never as the basis on its own. A decision
  with no report behind it is not a decision yet: it waits in the risk register, linked to
  its question for the report side.

## Phase 0 · Frame the job (short)

Write `design/00-frame.md` with:
- **Target**: what is being built, for whom, on which platforms; the current system it
  replaces, if any (its report is reference #1).
- **Hard constraints**: platforms, languages, team size, privilege model, budgets
  (memory, CPU, latency, binary size), compatibility that must not break.
- **Reports**: the list of architecture reports and the concern each is expected to teach.
- **Concerns** the design must answer: processes and privilege, IPC, state, extension
  model, UI rendering, update and delivery, observability, testing, migration.

- **Output**: `react` (default) or `single` (see below).

Ask the user only for what is not in the reports: the target and the constraints. Never ask
about the output; it defaults to `react`.

### Choose the output (single files or React)

Read it from the request (`$ARGUMENTS` and the conversation): "single", "html", "one file",
"static" → `single`; "react", "site", "docs site", "web app", "players", "deploy" → `react`.
**If the request does not say, use `react`** without asking, and state in the first progress
note that it is building the React docs site and that "single" gives two HTML files instead.

| Option | What the user gets | Pick it when |
|---|---|---|
| **Single files** (only when asked) | `source/<design>-architecture.html` and `source/<design>-master-plan.html`, each self-contained in the Synapse Next layout; scenarios as static walkthroughs; `scenarios.json` still written as the executable spec; a packaged `site/` with `llms.txt`, Markdown and Netlify config | the readers are the authors or a small team, the docs travel as files or attachments, or no Node build is wanted |
| **React docs site** (default) | the same two documents as the **source**, plus a Vite + React site generated from them: topic pages that interleave both documents, animated scenario players, search, glossary pages, `llms.txt`, private Netlify deploy | the audience is wider than the authors, scenarios should be played step by step, or the docs are meant to be the "bible" people browse |

Record the choice in `design/00-frame.md` as `Output: single` or `Output: react`. Both
modes share Phases 1–4 and the same two source documents (one fact, one home), so switching
from single to react later only adds the site; nothing is rewritten.

## Phase 1 · Intake the reports

Read every report fully. Check each against `references/report-contract.md`: it maps
architecture-report's standard sections (overview, processes, communication, pipeline, UI,
extension points, domain model, services, state, blueprint) to what the design takes from
each, and lists the extra sections a design needs that the report skill often skips
(feature-level interactions, common modules, delivery, observability, unknowns), with a
ready-to-send request for them. Produce `design/01-intake.md`:
- per report: which contract sections are present, thin, or missing;
- the feature-level interactions of the current system, with each quirk marked
  *preserve* or *drop, because…*;
- the report's Unknowns, carried forward;
- new entries in `design/questions-for-reports.md`.

Missing sections do not block the design; they lower confidence in the decisions that
depend on them, and those decisions say so.

## Phase 2 · Compare

One matrix: rows are the concerns from Phase 0, columns are references, each cell says in
one line how that reference solves it and links to the report section. Add **Pick** (the
mechanism the design takes, possibly a blend) and **Because** (the property that made it
win, or the failure in another reference that rules it out).

This matrix becomes the prior-art section of the proposal and the basis column of every
decision. A concern where no reference offers a mechanism has no pick: it becomes a
question for the report side (deepen an existing report, or add a reference that solves
it) and stays open until a report covers it.

## Phase 3 · Propose (the architecture document)

Explains the system to someone who will build or review it. Section skeleton in
`references/design-docs.md` ("Architecture proposal"). Rules:

- **Assertive**. State what is built and why: "The daemon owns every device handle", not
  "we could consider". No Keep/Change/Defer tags, no "to be confirmed". Open questions
  live in the Risks section with an owner and a date.
- **Every section opens with a diagram** that shows the mechanism (who talks to whom, what
  crosses which boundary, which state moves), then prose. Small, discussable diagrams beat
  one monster diagram. Follow `references/visual-rules.md`.
- **Component identity**: say which boxes are *types* (the actor, the transport) and which
  are *instances* (the keyboard actor, the USB transport).
- **One running example** (one product, one user action) reused across sections.
- **Before / after** for a rewrite, drawn from the current system's report.

## Phase 4 · Plan (the build document)

Turns the proposal into work. Skeleton in `references/design-docs.md` ("Build plan"). Its
backbone is **stable ids** every other artifact links to:

| Prefix | What | Example |
|---|---|---|
| D# | Decision, with basis (one or more report sections) | D7 One actor per device |
| S-# | Seam/interface between components: contract, encoding, versioning rule | S-2 daemon ↔ UI |
| I-# | Invariant, with the test or check that proves it | I-3 one writer per device |
| E# | Epic: owner, lane, dependencies, definition of done | E12 Keyboard family |
| M# | Milestone/gate: week range, observable exit criteria | M2 First device end to end |

Ids are never renumbered once published (append instead). The proposal and the plan must
agree; when they disagree, the plan's decision wins until a decision record changes it.
Include a critical path, a risk register (risk, signal, mitigation, owner — open questions
for the report side belong here too), metrics with budgets, and a glossary.

## Phase 5 · Prove (scenarios as executable specs)

Write the key flows as scenarios: a grid of typed component boxes and ordered steps, each
with narration, an observable `expect`, and a `proof` kind (contract, sim, invariant, bench,
chaos, hil, review). `src/scenarios/scenarios.json` is written in both output modes, because
a test runner later executes each `expect`. See `references/scenarios.md` and
`assets/scenarios.schema.json`.

Cover at minimum: bootstrap, the running example end to end, one failure path per critical
seam, every *preserve* quirk from intake, and the migration/cutover path.

How readers see the scenarios depends on the output:
- **single**: each scenario becomes a static walkthrough in the plan's Walkthroughs section:
  a `.contract` block (`W#`, steps as `ol.steps`, each step's `expect` and proof kind) plus
  one figure built from the scenario's grid (same boxes, numbered arrows in step order).
  Write it from `scenarios.json` so the two never disagree.
- **react**: the site animates each scenario in a FlowPlayer embedded in place (see
  `references/scenarios.md`, "Docs site"); the plan keeps a short `W#` summary that links to
  the player.

## Phase 6 · Audit (every time anything changes)

- Visuals: run the audit in `references/visual-rules.md` in a real browser on every page
  and every scenario step.
- Consistency: every D/S/I/E/M id cited resolves to a row in the plan; proposal and plan
  agree on each shared topic; every acronym is in the glossary; every link resolves.
- Provenance: every decision cites at least one report section, and every mechanism in the
  proposal traces to a decision; nothing in the docs reproduces reference code, identifiers or
  proprietary strings; every open question is either answered by an updated report or in
  the risk register.

- Publishing: the agent files and deployment configuration are regenerated from the current
  documents (`package_single.py` rerun, or `npm run build`), every `llms.txt` link resolves,
  and `netlify.toml` and `robots.txt` still carry the noindex and UTF-8 rules.

Report what was audited and fixed, plainly. Keep a backup of each document revision before
rewriting it (a `.backup/` folder or version control).

## Output style: the same as the Synapse Next docs

Every document this skill writes looks and reads like the Synapse Next documents, so readers
move between them without relearning anything. The skill lives in
`herdr-architecture/.claude/skills/` (outside any repository, so it is never committed).
Paths starting with `synapse-next-docs/` are relative to `herdr-architecture/`; `assets/`,
`references/` and `scripts/make_template.py` are inside this skill.

- **Start each document from `assets/doc-template.html`.** It carries the Synapse documents'
  own CSS (light/dark tokens, Inter and JetBrains Mono), the Dark/Light/System toggle, the
  arrow markers, the diagram classes, and the script that turns D/S/I/E/M ids into links with
  popover cards. The comment at its top lists the diagram and content vocabulary. Replace the
  `__PLACEHOLDERS__`, drop sections that do not apply, and add sections in the same patterns.
- **Layout: the Synapse Next docs site, in one HTML file.** The template wraps the page in
  the site's layout:
  - a sticky left sidebar with a **Documents** switcher (architecture ↔ build plan; set
    `aria-current="page"` on the current one and point the links at the real file names);
  - an **On this page** TOC built automatically from `<section id><h2><span class="num">`,
    highlighting the section being read (never hand-write a nav);
  - the **Legend** (keep only the entries the document uses, including the boundary types).

  It also gives every page the site's interactions:
  - typed boundaries `<g class="bd b-process|b-code|b-trust|b-machine|b-network">`;
  - figure hover: `data-n`/`data-d` on boxes and `data-e="from to"` on arrows and labels. The
    rest dims lightly and one card lists the box's connections;
  - glossary terms `<a class="term" href="#g-x">` that open a glossary row `<tr id="g-x">`,
    previewing on hover and pinning on click.

  On narrow screens the sidebar stacks on top.
- **Check every document with the shared script** `../architecture-report/verify.js`:
  chrome-devtools `new_page` (a `file:///` URL), then `evaluate_script` with that file as
  `sourcePath`, at desktop width and again after `emulate` `390x844x2,mobile,touch`. It
  returns only failures: overlapping or clipped diagram text, arrows that touch no box,
  broken anchors and terms, TOC mismatch, sideways scroll, theme toggle. The in-page audit in
  `references/visual-rules.md` stays for scenario-player steps on the docs site.
- **No new CSS.** If a pattern is missing, take it from
  `synapse-next-docs/source/synapse-next-master-plan.html` (same stylesheet). When the Synapse
  stylesheet changes, regenerate the template from `herdr-architecture/` with
  `python -I .claude/skills/system-design-from-references/scripts/make_template.py synapse-next-docs/source .claude/skills/system-design-from-references/assets/doc-template.html`.
- **Folder of a design**, mirroring `synapse-next-docs/`, created beside it in `herdr-architecture/`:
  ```
  <design>-docs/
    source/<design>-architecture.html   the proposal                 (both modes)
    source/<design>-master-plan.html    the build plan               (both modes)
    design/                             working notes: 00-frame, 01-intake, 02-compare,
                                        questions-for-reports.md     (both modes)
    references/                         copies of the architecture reports used (read-only input;
                                        committed so a deploy builds from the repo alone)
    src/scenarios/scenarios.json        scenarios (schema: assets/scenarios.schema.json)
    netlify.toml                        deployment configuration     (both modes)
    site/                               generated publish folder     (single only)
    package.json, vite.config.ts, tsconfig.json, index.html, .gitignore, scripts/, src/, public/
                                        the docs site                (react only)
  ```
  The documents link to a report as `../../<name>-architecture.html#section` (the original,
  beside the project). Both modes rewrite those links for publishing and copy the report.

Both modes always publish the same agent-readable set (llmstxt.org) beside the HTML; a run is
not finished until it exists:

| File | Contents |
|---|---|
| `llms.txt` | index: what the design is, how to read it (D/S/I/E/M ids), one link per Markdown file |
| `llms-full.txt` | the index plus every Markdown file in one file |
| `md/architecture.md`, `md/master-plan.md` | each document as Markdown, sections in document order, tables and code kept, figures as their claim (aria-label + caption) |
| `md/scenarios.md` | every scenario: components, boundaries, steps with expect and proof |
| `md/<page>.md` | react only: one per site page |
| `robots.txt` | `Disallow: /` for crawlers, but `/llms.txt`, `/llms-full.txt` and `/md/` allowed |
| `netlify.toml` | `X-Robots-Tag: noindex…` and `Referrer-Policy: no-referrer` on everything; `text/plain; charset=utf-8` for `/llms*.txt`; `text/markdown; charset=utf-8` for `/md/*` |

Links in them are relative, or absolute when the site URL is known (`URL` env on Netlify, or
`--base` for single mode).

### Single files (`Output: single`)

The two documents in `source/` are what people read. Package them with (from
`herdr-architecture/`):

```
python -I .claude/skills/system-design-from-references/scripts/package_single.py <design>-docs
```

It writes `site/` (both documents with report links rewritten to `references/`, the cited
reports, `md/`, `llms.txt`, `llms-full.txt`, `robots.txt`, and an `index.html` that opens the
architecture), plus `netlify.toml` (`publish = "site"`, no build step, the headers above) if
none exists. It needs only Python, never deletes anything, and lists cited reports it could not
find. Rerun it after every document change. Check `site/llms.txt` lists every file and spot-read
one section of `md/master-plan.md` against the HTML. Give the user both document paths and
the `site/` path.

### React docs site (`Output: react`)

Write the two documents exactly as in single mode first; they stay the only source, and the
site never retypes their content. Then build the site from the Synapse docs site instead of
writing a new one:
1. **Copy the site skeleton** from `synapse-next-docs/`: `package.json`, `vite.config.ts`,
   `tsconfig.json`, `index.html`, `.gitignore` (keeps generated `src/content/`,
   `public/docs|md|llms*|search.json` out of git), `netlify.toml`, `public/robots.txt` **only**
   (everything else in `public/` is generated Synapse output), `scripts/` (`extract.mjs`
   sections → site and documents/reports → `public/docs/`; `check.mjs` build checks; `llms.mjs`
   llms.txt + Markdown; `search.mjs` search index), and `src/` (`main.tsx`, `content.ts`,
   `pages.ts` topic pages that interleave both documents, `site.css`, `vite-env.d.ts`,
   `components/`, `scenarios/` code). Never copy `node_modules/`, `dist/`, `src/content/`,
   `source/`, `references/` or the rest of `public/`.
2. **Remove what is Synapse-only.** `src/handbook/`, `src/rulebook/`, `src/requirements/`
   and their pages (`Handbook.tsx`, `Rulebook.tsx`, `Requirements.tsx`, `FeatureGraph.tsx`,
   `RustCode.tsx` unless the design uses Rust contracts) are Synapse features, wired into
   the shell, views, search and scripts. Find every link with
   `grep -rn -E "handbook|rulebook|requirements|FeatureGraph|RustCode" src scripts` and
   remove the routes, nav entries, search sources and checks that use them (in `check.mjs`,
   also the requirement-coverage and Synapse-specific id-range checks). Keep the
   scenario, glossary, figure and reference checks. Replace `src/scenarios/scenarios.json`
   with the design's own and empty `proof.json`.
3. **Point it at this design**: the document names in `extract.mjs`, the page list in
   `pages.ts`, the site title in `index.html` and the shell, and in `search.mjs` the sources it
   indexes. In `llms.mjs`: the source file names, the `llms.txt` intro (one paragraph on what
   this design is, written from the proposal's hero), the two document titles and blurbs, and
   the scenarios blurb; delete the feature-handbook block and its `md/handbook.md` entry in
   `llms-full.txt`. Put the reports in `references/`. No Synapse wording may remain:
   `grep -rni synapse src scripts index.html netlify.toml public/robots.txt` must come back empty.
4. `npm install`, then `npm run build` (extract → llms → search → checks → type-check → Vite
   build); it must pass. Then confirm the build output, not just the exit code:
   `dist/llms.txt`, `dist/llms-full.txt`, `dist/md/` (one file per page in `pages.ts` plus
   `architecture.md`, `master-plan.md`, `scenarios.md`), `dist/search.json`, `dist/robots.txt`,
   and `dist/docs/` with every cited report. Every link in `llms.txt` must resolve to a file in
   `dist/`. Preview with `npm run dev` and run the audits in `references/visual-rules.md` on
   every page and every player step.
5. **Deployment configuration** is the copied `netlify.toml`: `npm run build`, publish `dist`,
   `NODE_VERSION = "22"`, and the headers above. Keep it. Deploy only when the user asks
   (private, noindex, an unguessable site name); on Netlify the `URL` env makes the llms links
   absolute.

Give the user the source paths, the dev URL, the build result and the list of generated
agent files.
- **Reference for tone, density and visuals**: `synapse-next-docs/source/synapse-next-architecture.html`
  and `synapse-next-docs/source/synapse-next-master-plan.html`. Do not copy their domain content into an unrelated
  design.
