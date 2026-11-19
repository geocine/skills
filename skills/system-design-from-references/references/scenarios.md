# Scenarios as executable specs

A scenario is a flow drawn as a grid of typed boxes plus ordered steps. The same JSON file is
animated by the docs site and later executed by a test runner (each step's `expect` becomes
an assertion, and the run writes a proof file). That keeps the drawings honest: a diagram
that cannot be run is a claim nobody checks.

Schema: `../assets/scenarios.schema.json`.

## Shape

```json
{
  "id": "w1-change-setting",
  "title": "Change a setting on one device",
  "summary": "The user changes DPI; the daemon applies it and confirms.",
  "group": "Walkthroughs",
  "cols": 4, "rows": 2,
  "sections": ["core", "intent"],
  "nodes": [
    { "id": "ui",    "label": "UI",            "col": 0, "row": 0, "kind": "ui",     "component": "client" },
    { "id": "rt",    "label": "Router",        "col": 1, "row": 0, "kind": "mw",     "component": "router" },
    { "id": "act",   "label": "Mouse actor",   "sub": "one per device", "col": 2, "row": 0, "kind": "mw", "component": "actor" },
    { "id": "io",    "label": "USB transport", "col": 3, "row": 0, "kind": "native", "component": "io" },
    { "id": "db",    "label": "Store",         "col": 2, "row": 1, "kind": "store",  "component": "store" }
  ],
  "groups": [{ "label": "daemon process", "nodes": ["rt", "act", "db"], "style": "process" }],
  "steps": [
    { "from": "ui", "to": "rt", "label": "set dpi 1600",
      "text": "The UI sends a typed request over S-1.",
      "expect": "router receives SetSetting{key:dpi,value:1600} within 5 ms",
      "proof": { "kind": "contract", "ref": "S-1" } },
    { "from": "act", "to": "io", "label": "write report",
      "text": "The actor encodes the report; the transport writes it (I-3: one writer).",
      "expect": "exactly one transport write for the device",
      "proof": { "kind": "invariant", "ref": "I-3" }, "ms": 2 }
  ]
}
```

Fields: `kind` is the visual colour class (ui, mw, svc, store, native, warnb); `component`
is the identity (which core component type the box is an instance of); `groups` are typed
boundaries; `proof.kind` is one of contract, sim, invariant, bench, chaos, hil, review;
narration ids (D7, S-1, I-3, E12, M2) and `[[section-id]]` become links.

## Build-time checks (fail the build)

- every step and boundary references a real node; no two nodes share a cell;
- a boundary rectangle contains only its members;
- no step's straight edge passes through a box that is not one of its endpoints;
- every id and `[[section]]` in narration resolves against the plan;
- every node has a `component`.

## Coverage

Bootstrap · discovery/detection · the running example end to end · one failure per critical
seam (timeout, crash, disconnect) · migration/cutover · any flow with ordering subtleties
(sync, experiments, updates).

## Docs site

Built only when the output is `react` (chosen in Phase 0; see SKILL.md, "React docs site").
With `single`, the same scenarios render as static walkthroughs in the build plan.

- Vite + React + TypeScript, HashRouter (works on any static host), `base: './'`.
- A build script extracts `<section id>` blocks from the two documents into the site, so
  content is never retyped; pages interleave sections from both documents by topic, each
  section on exactly one page.
- Scenario players are embedded where the reader already is (replacing or following a
  figure), not on a separate page.
- Figures get hover cards and flow highlighting from the arrows already in the SVG.
- Publish both standalone documents and the reference pages under `docs/` so "open in the
  document" and prior-art links work; vendor copies of reference pages that live outside the
  repo so a clean clone builds.
- `llms.txt` for agents (llmstxt.org): generated on every build from the same HTML as the site —
  an index with one link per page, a Markdown copy of each page under `md/`, both whole
  documents, the scenarios with expect and proof per step, and `llms-full.txt` with everything.
  Copy `scripts/llms.mjs` from synapse-next-docs; robots.txt allows `/llms.txt`, `/llms-full.txt`
  and `/md/` while disallowing the rest.
- For a private deploy: `X-Robots-Tag: noindex, nofollow` header, a robots meta tag and a
  disallow-all `robots.txt`; an unguessable site name.
