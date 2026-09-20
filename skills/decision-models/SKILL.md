---
name: decision-models
description: >-
  Explain and apply decision models: TypeSafe System One models (Jev),
  classifiers, encoders, constrained decoding, and direct logit readout.
  Use when the user asks what decision models / typesafe / Jev / RLCD /
  classifiers / zero-shot encoders are, how they work or compare; when
  brainstorming what decision-model use cases fit their codebase; when they
  want to train their own decision model, classifier, or Jev-like system on
  their data; or when they want to know what data to log so they can later
  migrate off TypeSafe (or any hosted decision API) seamlessly.
---

# Decision Models

A **decision model** is a system whose primary output is a bounded, machine-consumed
judgment: a value from a declared answer space, usually with a probability
distribution over the options. State in, decision out. No token-by-token generation;
the answer is read directly from scores/logits in (typically) one forward pass.

```text
Autoregressive path:  state → token generation → free-form or schema-constrained text → parse
Direct decision path: state + declared options → logits → value + distribution
```

**Jev** (TypeSafe AI) is the flagship hosted example — a "System One model" trained
with Reinforcement Learning for Calibrated Decisions (RLCD). The same interface can
be reproduced with classifier heads, zero-shot encoders (GLiClass/GLiNER family),
constrained decoding, or direct logit readout of an open LLM.

## Route by intent

| The user wants to... | Read |
| --- | --- |
| Understand concepts: decision models, System One, Jev, RLCD, classifiers, encoders, calibration, how Jev is built | [concepts.md](concepts.md) |
| Find use cases for **their** codebase / brainstorm what to build | [use-cases.md](use-cases.md) |
| Train their own decision model on their data | [training.md](training.md) |
| Know what data to gather now so they can switch away from TypeSafe later | [data-collection.md](data-collection.md) |
| Judge how solid the Jev-internals claims are (official vs reconstruction) | Ground rule 6 below, then [sources/technical-deep-dive.md](sources/technical-deep-dive.md) (epistemic-status note + per-claim evidence tags) |

Intents often chain: a use-case conversation should end by pointing at
data-collection (log decisions from day one); a training conversation needs the
data-collection schema as its input format.

## Deep documentation (in this skill's `sources/` folder)

Skill-authored deep docs; read the specific file when the conversation needs depth
beyond the reference files above:

| Bundled file | What it is |
| --- | --- |
| [sources/capability-map.md](sources/capability-map.md) | Documentation map of what decision models can do: nine capability areas with real shipped examples, the ecosystem shape, the 2017–2026 lineage with paper links, and Jev's launch-time economics. |
| [sources/technical-deep-dive.md](sources/technical-deep-dive.md) | How decision models compute (prefill + readout math, a step-by-step worked readout example), the component-by-component Jev reconstruction with evidence tags, an open-weights validation of it in code, calibration theory and measurements, output-path benchmarks, an evaluation protocol, and an arXiv paper index. |
| [sources/question-design-example.md](sources/question-design-example.md) | Production-grade question design and staged composition from a real Jev code-review workflow, with a transferable checklist. |

Evidence in these docs is dated (Sep 2026 measurements and claims). Anything
TypeSafe-specific that can drift — API contracts, SDK usage, models, pricing,
limits, prompting guidance — must be read from the live docs.

## Live TypeSafe docs (never rely on the snapshot for current details)

**The live TypeSafe docs are the source of truth. Read them as part of the task**
whenever writing or updating TypeSafe integration code, quoting current pricing or
limits, or recommending a primitive/SDK pattern.

- Start with the [documentation index](https://docs.typesafe.ai/llms.txt) to
  discover relevant pages and cookbooks. Use targeted reads, not the whole site.
- Mintlify serves Markdown by appending `.md` to a page path, e.g.
  `https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md`. Convert
  extensionless doc links to `.md`; resolve relative links against
  `https://docs.typesafe.ai`.
- Before writing an integration, read the current API or chosen SDK page and the
  question guidance relevant to the design. For a new workflow, inspect the closest
  cookbook: it often shows a better decomposition than a generic classifier.
- If the index is unavailable, use the direct links below. If Markdown fetching
  fails, try the normal page. If live access is unavailable, fall back to the
  skill's deep docs or installed SDK types, **state that limitation**, and avoid
  inventing version-dependent details.

| Task | Start here |
| --- | --- |
| Understand the programming model | [System One](https://docs.typesafe.ai/concepts/system-one.md), [building guide](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md) |
| Explore what to build | [Use-case map](https://docs.typesafe.ai/concepts/use-case-map.md), then relevant cookbooks from the index |
| Prepare inputs and questions | [State](https://docs.typesafe.ai/concepts/state.md), [primitives](https://docs.typesafe.ai/primitives.md), then [Choice](https://docs.typesafe.ai/primitives/choice.md) / [Noul](https://docs.typesafe.ai/primitives/noul.md) / [Score](https://docs.typesafe.ai/primitives/score.md) |
| Handle uncertainty | [Confidence](https://docs.typesafe.ai/confidence.md) |
| Write API code | [HTTP API](https://docs.typesafe.ai/api.md), [Python SDK](https://docs.typesafe.ai/sdk/python.md), or [JavaScript SDK](https://docs.typesafe.ai/sdk/javascript.md) |
| Update an older integration | [Migration guide](https://docs.typesafe.ai/migrating-to-v1.md) and the installed SDK's current reference |

## Ground rules (state these when relevant, they prevent expensive mistakes)

1. **A normalized score is not a calibrated probability.** Softmax over options is
   conditional on the supplied alternatives. Calibration must be measured on the
   user's own workload (ECE, reliability bins) before probabilities drive policy.
2. **Switching from generation to direct scoring changes behavior, not just speed.**
   Measured on one open model, the three output paths (generated JSON, constrained,
   direct readout) disagreed on 24–52% of inputs. Re-evaluate; don't assume parity.
3. **Small models can be fast and wrong.** A 0.6B model answered "technical" for 92%
   of support tickets by the direct path. Speed on a degenerate answerer is worthless.
4. **Perturbation-test any deployment**: option-order reversal, criterion rewording,
   irrelevant appended context, and missing-evidence cases. Even Jev shows
   option-order probability shifts large enough to cross a 0.9 threshold.
5. **Probabilities are only over declared options.** Include a no-match /
   `insufficient` option when nothing may fit; the model cannot choose an omitted answer.
6. **The "how Jev works" material is reconstruction, not vendor documentation.**
   TypeSafe has not published Jev's architecture; the deep dive's mechanism accounts
   are assumptions and observations built on world knowledge and black-box probing.
   For anything Jev-specific — behavior, guarantees, API contracts, pricing — the
   live TypeSafe docs (docs.typesafe.ai) are the source of truth.
7. **Keep policy in code.** Thresholds, weights, and branching live in the
   application; the model supplies reusable raw judgments. Changing a threshold
   should not require re-running inference.
8. **Scope this skill's numbers when quoting them.** Every measured figure here
   (accuracies, ECE, latencies, token effects) is a Sep 2026 snapshot from the
   skill's bundled studies on specific setups. Relay them as "the skill's bundled
   measurements" with their conditions and confidence intervals where given —
   not as current facts about Jev or any model in general.

## Question design quick reference (applies to all intents)

- Three primitive shapes: **Choice** (one of a defined set; distribution compares
  options), **Noul** (probability a condition holds; one per label if several may
  apply), **Score** (probability-weighted position on ordered, concretely described levels).
- One narrow, coherent judgment per question. Split independently useful dimensions.
- Give each question enough **state**: source text, identities, policies, current
  facts. Prefer named JSON fields; reference nested paths like `file.patch`.
- Independent questions over the same state run in parallel and cannot see each
  other's answers. A second stage is needed only when an earlier answer determines
  the next evidence or options.
- Nothing-applies handling per primitive: Choice gets an explicit `noMatch` /
  `insufficient` option; a Noul's `false` criteria must describe the no-evidence
  case; a Score's lowest level should be an explicit "no supported issue /
  insufficient evidence" description so ambiguous cases have somewhere honest to land.
- Sharpen criteria with focus/ignore hints, examples, and counterexamples — see
  [sources/question-design-example.md](sources/question-design-example.md) for
  production-grade examples.
