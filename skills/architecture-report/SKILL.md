---
name: architecture-report
description: Document a codebase's architecture as one self-contained HTML page in the Synapse Next docs style (sidebar TOC, legend-coded SVG diagrams with typed boundaries, hover/pin glossary terms, cards, contracts, syntax-highlighted formats). Scopes the report to what the user asked (a subsystem, a flow, a question such as "how does auth work" or "how do plugins load"); with no specific ask, writes a general exhaustive report (processes, communication and wire formats, data pipeline, UI rendering, extension points, domain model, services, state and config). Use when asked to document, map or explain the architecture of one or more repos, or part of one, as an HTML report, an architecture page or doc, or "a report like the herdr one".
argument-hint: "[repo path(s)] [focus or question, optional] [output path, optional]"
---

# Architecture report

Writes **one self-contained HTML file** that answers the user's request about the architecture of the repo(s) they name.

Files in this skill's folder:

| File | Use |
|---|---|
| `template.html` (~21 KB) | **The style contract.** Head (CSS + one small script) and page shell, then one sample of every building block. |
| `verify.js` | The check script. Run it by path; never retype it. |
| `reference.html` (56 KB) | An older finished report (herdr), in an older style. Only an example of content depth. **Never read it whole and never copy its markup.** |

## 0. Read the request first

The request is the text after the skill name (`$ARGUMENTS`) plus whatever the user said in the conversation before running it. Extract, before touching any file:

| Field | Where it comes from | Default |
|---|---|---|
| **Repos** | paths or repo names in the request | the current working directory |
| **Focus** | a subsystem, flow, feature, question or concern ("how input reaches the PTY", "the plugin system", "what happens on reconnect", "security boundaries") | none → **General mode** |
| **Depth / audience** | words like "quick", "overview", "deep dive", "for new contributors" | quick overview in Focused mode, exhaustive in General mode |
| **Output path** | a path in the request | `docs/architecture.html` in the first repo; in Focused mode `docs/architecture-<focus-slug>.html` |

Then pick the mode:

- **Focused mode**: the request names anything more specific than "the architecture". The report exists to answer that. Only research and write what serves it.
- **General mode**: no focus given, or the user asks for "everything" / "full" / "exhaustive". Cover every section in §4 that applies to the codebase.

If the focus is ambiguous in a way that would change which code you read (e.g. "the server" in a repo with three servers), ask one short question; otherwise decide and state your reading in the subtitle.

## 1. Token budget (both modes)

Spend tokens on the codebase, not on the template or on rereading.

- **Copy the shell, don't read it.** `sed -n '1,/<!-- CONTENT -->/p' <skill-dir>/template.html > <output>` copies the head and page shell. Then read only the sample part once: `sed -n '/<!-- CONTENT -->/,$p' <skill-dir>/template.html` (~40 lines). Replace `TITLE` in `<title>` and `.brand` with one `sed -i`.
- **Never hand-write what the template generates.** The sidebar TOC and the section numbers are built from `<h2 id>`; arrowheads come from the shared `#ah` / `#ahw` markers; the theme toggle, hover cards and figure highlighting are wired automatically.
- **Locate before reading.** Use Glob/Grep and file sizes to find the files that matter; read with `offset`/`limit` around the hits instead of whole large files. Skip generated code, lockfiles, vendored deps, fixtures, assets.
- **Agents only when they pay off.** Spawn Explore agents only for a codebase too large to sweep yourself, one per component, at most ~4. In Focused mode prefer zero or one agent, scoped to the focus. Ask each for a compact bullet list (≤ ~60 lines) with `file:line` refs, not file dumps.
- **Write once.** Append the whole body in one pass, then fix issues with small Edits. Do not reread the file to check it; `verify.js` does that.
- **Size the page to the ask.** Focused: typically 2–5 sections and 1–3 diagrams. General: every applicable section, but one small diagram per idea, tables over prose, no repeated explanations.

## 2. Building blocks (all in `template.html`)

| Block | Markup |
|---|---|
| Page shell | `<h1>`, a one-line `.sub` (repos, source paths, and in Focused mode the question), an optional `.lede`. No hand-written nav. |
| Sections | `<h2 id>` (add `data-toc="Short"` when the heading is long), `<h3>` small uppercase sub-heads, short `<p>`, lists with a **bold lead-in** per item, `<table>` inside `.tablewrap` for inventories (`table.dense` for long ones) |
| Answer box | `.answer` > `<ul>`: the Focused-mode answer |
| Numbers at a glance | `.kpis` > `.kpi` (`<b>` number + `<span>` label) |
| Ideas side by side | `.cards` > `.card` (`<h4>` + short text). One idea per card. |
| Comparison | `.contrast` (`<h4>` heading + table): before/after, option A/B, old/new |
| Interface / API | `.contract` (`<h4><span class="sid">ID</span>name</h4>`, `.purpose`, `<pre><code>`, `<ul>` of guarantees) |
| Linear pipelines | `.flow` > `.step` (`<b>` title + `<span>` detail) |
| Binary or wire layouts | `.bytes` strip (`<i>` offset, `<b>` name, `<span>` type), then a `<pre><code>` block |
| Highlighting | hand-written spans: `.c` comment, `.k` keyword / enum, `.f` field / method / key, `.s` string, `.n` number, `.t` type, `.p` punctuation |
| Ids that must not wrap | `<code class="id">` |
| Diagrams | `<figure>` > inline `<svg viewBox="0 0 860 H" role="img" aria-label>` + `<figcaption>`. Details below. |
| Glossary terms | `<a class="term" href="#g-x">word</a>` linking to `<dl class="gloss"><dt id="g-x">…</dt><dd>…</dd></dl>` in a final **Glossary** section. Hover previews, click pins, Esc / × / outside click closes. |
| Footer | `<p class="note">` with the date and the reminder that line numbers drift |

**Diagrams.** Draw in this order: boundaries, boxes, arrows, labels (labels on top).
- Boundary: `<g class="bd b-process|b-code|b-trust|b-machine|b-network"><rect/><text/></g>`. Every boundary that matters is drawn and typed.
- Box: `<g class="nd ui|mw|store|native|warn|faint" data-n="id" data-d="one-line detail"><rect rx="8"/><text class="tt">name</text><text class="ts">role</text></g>` (no category class = service grey; `faint` = context outside the focus).
- Arrow: `<path class="ar" data-e="from to" d="…" marker-end="url(#ah)"/>` (`.arw` + `#ahw` for errors/risk, add `.d` for dashed = async or optional). Arrow ends **touch** the box edges.
- Arrow label: `<text class="lbl" data-e="from to">transport or message</text>`, on the arrow, short.
- `data-n` / `data-e` turn on the hover highlight and the compact card that lists a box's connections. Boxes with no arrows get no card.
- Edit the sidebar `.legend` so it lists only the categories and boundaries the page uses.
- Keep diagrams small and discussable: one idea each, rather than one monster diagram. Text 12–13px; widen a box rather than shrink text.

Never draw ASCII diagrams. No left-border accent stripes. Colors only through the CSS tokens. No other scripts or assets.

## 3. Writing rules

- Assertive and plain: state how it works, with real names in `<code>` and `file:line`. No hedging; mark only genuinely unsettled items as uncertain, and collect them in one place.
- Visual first: every non-trivial explanation gets a small diagram, `.flow`, `.bytes` or table.
- One fact, one home: explain a mechanism once, in its topic section, and link to it (`<a href="#id">`) elsewhere.
- Every acronym and component word (actor, bus, lease, seam…) is a `.term` with a glossary entry the first time it appears in each section.

## 4. Sections

### Focused mode

Shape the page around the question, not around the general list:

1. **Answer** (`id="answer"`, always first): an `.answer` box of 3–6 bullets that directly answer the request, each with real names and a `file:line`.
2. **Context**: one small figure placing the focus inside the whole system (only the components it touches; everything else as one `faint` box).
3. **The body**: whichever of the general sections below explain the focus, cut down to the parts that matter, plus anything the question needs (a step-by-step walk-through, error and edge cases, invariants, config knobs, where to change it).
4. **Open questions**: what the code didn't settle.
5. **Glossary**.

Leave out every section that doesn't serve the focus; do not pad with a general overview.

### General mode

Include what applies to the codebase and skip what doesn't:

1. **Overview:** a `.kpis` row, one line on each component's job, plus a figure of all processes and the links between them, with each link labeled by its transport and every process/trust/machine boundary drawn.
2. **Processes:** a table of every process or role, with what it does and its lifetime. How each is launched and supervised on each OS. Startup sequence as a `.flow`.
3. **Communication:** endpoints, handshake, framing as a `.bytes` strip, message and frame kinds, API methods grouped by namespace (`.contract` for the important ones), events, flow control, reconnect, remote access. Highlight every format.
4. **Core data pipeline:** a figure of how the main data flows end to end, in both directions if there is input and output.
5. **UI or rendering:** the view tree, how state becomes pixels (a `.flow`), redraw scheduling, fonts, themes. Skip if there is no UI.
6. **Extension points:** plugins or mods, how one is added (folder layout, manifest, a minimal highlighted example), lifecycle, permissions.
7. **Key domain model:** for example tabs, sessions, workspaces or jobs. A figure of its hierarchy and where each piece is persisted, plus its lifecycle (create, switch, close, reconcile).
8. **Services:** one table per component, one line per module.
9. **State and config:** directories, files, config fields, for each OS.
10. **Glossary.**

### Either mode

When the user asks how to reuse the design elsewhere, add a **Blueprint** section (`grep -n 'id="blueprint"' reference.html` and read only that section for the depth expected). Say plainly that it is a generalized design, not existing code. When the user asks for a comparison (old vs new, two repos), use `.contrast` panels per section.

## 5. Workflow

1. **Parse** the request (§0) and decide the mode, the focus, the output path and the section list.
2. **Orient.** List the repo layout, manifests and file sizes, and read `README`, `AGENTS.md`/`CLAUDE.md` and the `docs/` index. In Focused mode, grep for the focus terms right away to find the entry points, and stop orienting once you have them.
3. **Research.** Follow the call paths from the entry points. For a large codebase in General mode, spawn read-only Explore agents in parallel, one per component (see §1 limits). Ask each for:
   - concrete `file:line` references;
   - real type, function and message names;
   - the topics from the chosen section list only (in Focused mode, pass the user's question verbatim);
   - uncertain items marked as uncertain.

   Read the key files yourself for the domain-model section or the core of the focus.
4. **Write.** Copy the shell with `sed` (§1), set the title, edit the legend, append the body, close with `</main></div></body></html>`.
5. **Verify.** Open the file in a headless browser (chrome-devtools `new_page` with a `file:///` URL), then run `evaluate_script` with `sourcePath: <skill-dir>/verify.js`; then `emulate` a `390x844x2,mobile,touch` viewport and run it again. It returns only failures:
   - SVG text overlapping other text or spilling out of / touching its box;
   - arrow ends that touch no box, missing markers;
   - horizontal page scroll; Inter font not loaded;
   - broken `#` anchors, `.term` links without a glossary `<dt>`, TOC/section mismatch;
   - theme toggle not changing the background and box fill, or covering the title/TOC.

   Fix with small Edits, reload (`evaluate_script` → `location.reload()`), rerun. Take at most one screenshot, only if something looks off.
6. **Report.** Give the full absolute path, the mode and focus you used, a few lines on what each section covers, and every uncertain item.
