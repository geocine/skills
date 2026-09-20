# Concepts: decision models, System One, Jev, classifiers, encoders

## Definition and the two output paths

A decision model returns a bounded, machine-consumed judgment — a value from a
declared answer space plus a score/probability per option. The implementation
varies: a classifier head, a zero-shot encoder, constrained decoding into a schema,
direct readout of an LLM's option logits, or a purpose-trained hosted model (Jev).

```text
Autoregressive path
  state → token generation → free-form or schema-constrained tokens
  Structured-output APIs guarantee the schema, but the answer is still decoded one token at a time.

Direct decision path
  state + declared options → scores/logits → value + distribution
  No output-token loop. Answer space fixed by construction. Distribution not necessarily calibrated.
```

Worked example — a support message needs a category, nothing more:

```json
// input
{"message": "My card was charged twice.",
 "schema": {"category": ["billing", "technical", "sales", "other"]}}
// output (illustrative)
{"category": {"value": "billing", "probability": 0.96}}
```

Why it matters: most steps inside software and agents are narrow judgments —
routing, classification, scoring, verification, tool selection, branching, approval,
anomaly detection. A generated sentence ("Based on the context, I believe we should
escalate") must be read, interpreted, and turned back into a boolean. A decision
(`escalate: true, confidence 0.91`) can be executed.

## System One models and Jev (TypeSafe AI, launched 15 Sep 2026)

Named after Kahneman's fast/deliberative distinction; Jev after William Stanley
Jevons (efficiency → demand explosion). The table below is the **launch-time
snapshot** (15 Sep 2026); pricing, latency, limits, and model versions drift —
verify against the live docs ([System One](https://docs.typesafe.ai/concepts/system-one.md),
index at [llms.txt](https://docs.typesafe.ai/llms.txt)) before quoting them as
current. TypeSafe's claims, vendor-reported:

| Axis | Existing LLMs | Jev / System One |
| --- | --- | --- |
| Training | RLHF / RLVR | **RLCD** — Reinforcement Learning for Calibrated Decisions: "epistemically honest probabilities on System One tasks" |
| Inputs | Text, sequential messages | Unstructured data with emphasis on **structured program state** |
| Outputs | Strings (must be parsed/validated; can hallucinate) | Typed structured values defined in advance; "never makes type errors"; every answer carries calibrated probability + confidence |
| Sampling | Sequential, token by token | Parallel: all outputs in a single query |
| Cost | $0.20–$10/MTok in; output ~5x input | $0.042/MTok in; **output free** |
| Latency | 3–329 s end-to-end for frontier models | 70–500 ms (claims 40–200x faster at similar System One intelligence) |

Primitives: **Choice** (finite options, max cardinality 255; above that TypeSafe
uses a 2-stage score-then-choose), **Noul** (yes/no probability), **Score** (ordered
levels). Current primitive semantics and guidance: live pages for
[Choice](https://docs.typesafe.ai/primitives/choice.md),
[Noul](https://docs.typesafe.ai/primitives/noul.md),
[Score](https://docs.typesafe.ai/primitives/score.md), and
[Confidence](https://docs.typesafe.ai/confidence.md). The homepage "193.6x faster, 444.6x cheaper" figures come from their
workflow evals, which use GPT-6 Astra + Fable 5.1 averages as reference answers —
TypeSafe itself flags the biases (self-authored workflows, reference-model choice).

Their positioning of use cases: AI-powered workflows / "smart if-statements",
map-reduce over big data, real-time applications (~100 ms), and verify/guardrail/
jailbreak-detection over LLM traffic. Weights are not released.

## How Jev is (probably) built — from the 10,000-call reverse-engineering

Source: a public black-box study (Sep 2026, ~10,000 instrumented API calls against
jev-1.13.0). Full component-by-component reconstruction with experiments and evidence tags:
[sources/technical-deep-dive.md](sources/technical-deep-dive.md). Confidence levels
vary between published, observed, and inferred claims. Note the "(probably)":
TypeSafe has not published Jev's architecture, so this is reconstruction from
world knowledge and black-box probing — the live TypeSafe docs are the source of
truth for Jev's actual behavior.

1. **Readout head, not a decode loop.** `output_tokens` in the API is a billing
   figure computed after inference (it counts text the model never sees; a
   200-option answer returned as fast as a 2-option one). A final hidden vector maps
   through a linear layer + softmax over option slots.
2. **Shared state, isolated questions.** Token accounting is exactly additive
   (prefix + per-question suffixes). A secret placed in a sibling question is
   invisible (p≈0.00) but visible from shared state (p≈0.90). Server time is flat up
   to ~100 questions. Limits fit one packed 2^16-token sequence: state once + all
   question suffixes, each branch capped at 2^15. Natural implementation: prefix KV
   cache + separate causal suffixes (cf. Hydragen, DeFT).
3. **Causal transformer backbone**, frontier-pretrained (84.6% MMLU-Pro). Tokenizer
   matches none of 192 public tokenizers (closest: Qwen, 348/415 probes; vocabulary
   tracks o200k but digit-splitting rules it out).
4. **Options interact before the choice** (listwise, not independent logits).
   Adding an irrelevant 5th option shifted the log-odds between two existing options
   by −0.28 (all 10 randomized blocks) — impossible under fixed independent logits
   with a shared softmax. A reference card placed as the *last* option was used
   correctly 16/16; first or middle, ~12/16 — order sensitivity is real.
5. **Distribution trained against outcomes; "confidence" is arithmetic.** The
   official adapter computes Choice confidence as `c = (p_max − 1/K)/(1 − 1/K)` —
   distance above uniform, not a second learned estimate. Measured calibration:
   ECE 0.031 on a 1,200-item MMLU sample; on fresh 2-step word problems accuracy 32%
   with mean top probability 0.30 (encouragingly humble).
6. **Likely sparse MoE** (~30k tokens in ~160 ms fits ~10B active params;
   prefill-only workloads are compute-bound, exactly what sparsity saves). Least
   certain component; nothing else depends on it.
7. **Branches scheduled as a batch, not a conversation.** No dependency chain
   between answers. If a later question needs an earlier answer, the app adds a stage.

## Lineage — this did not start with Jev

| Year | Work | Contribution |
| --- | --- | --- |
| 2017 | Guo et al., *On Calibration of Modern Neural Networks* | Modern nets are systematically overconfident; a probability isn't calibrated until measured |
| 2018 | BERT | Sequence-classification heads: state in, bounded label out, no text |
| 2019 | Yin, Hay, Roth | Zero-shot classification via entailment: label sets declared at inference time |
| 2023 | OpenAI function calling → Structured Outputs (2024) | Schema-valid objects from an API (still decoded) |
| 2023 | Willard & Louf, guided generation | FSM-constrained decoding: answer space enforced during generation |
| 2023 | GLiNER | Bidirectional encoder scoring arbitrary user-declared labels in parallel, open weights |
| 2023 | Llama Guard / ShieldGemma (2024) | Bounded safety labels as the entire product; scoring over yes/no tokens |
| 2025 | GLiNER2 (Fastino) | Multi-task extraction+classification, schema interface, one forward pass, CPU |
| 2026 | GLiGuard | 0.3B schema-conditioned encoder, 14 harm categories + 11 jailbreak strategies, one pass, Apache-2.0 |
| 2026 | **Jev** | Hosted; the new claims are **calibration as an explicit training objective** plus the latency/price bundle. Vendor-reported, not yet independently reproduced |

arXiv IDs for every cited paper (alphaXiv-ready): see the research paper index in
[sources/technical-deep-dive.md](sources/technical-deep-dive.md).

## Model-family cheat sheet

| Family | Examples | Traits |
| --- | --- | --- |
| Classifier head on encoder | BERT + head | Fixed label set, needs per-task training, tiny and fast |
| Zero-shot encoder | GLiClass, GLiNER2 | Labels declared at inference, single forward pass, runs on CPU/small GPU, open weights, fine-tunable |
| Cross-encoder / reranker | Qwen3-Reranker | Strong at *ranking* candidates; weak as a general decision threshold (measured 0.625 vs 0.813 balanced accuracy) |
| Direct logit readout of LLM | e.g. Qwen3.5-4B, frozen | Runtime-defined criteria, general knowledge of the base LLM, no decoding; strongest open baseline measured |
| Constrained decoding | Outlines, Structured Outputs | Guarantees schema but still autoregressive; latency scales with output length |
| Parallel constrained decoding | open MLX implementations | KV-cache broadcast across schema fields; 5.6–7x faster, 100% schema validity |
| Purpose-trained open | 0.5B–9B LoRA trainees | LoRA + readout head on an open backbone, trained on typed decisions; can serve TypeSafe's API contract locally, trains on a laptop |
| Purpose-trained hosted | Jev | Adds outcome-trained distributions, parallel sampler, price/latency bundle; measured edge over open trainees is out-of-domain transfer, not the mechanism |

## Calibration, honestly

- **Proper scoring rules** (log loss, Brier) are minimized in expectation by the
  true conditional distribution — that is what RLCD-style training plausibly
  optimizes. Properness is not a deployment guarantee: finite data, optimization
  error, and distribution shift all leave residual miscalibration.
- Measure with **reliability bins / ECE** on held-out, representative data.
  Post-hoc temperature scaling is compatible with (and often needed after) training.
- **Choice-set effects are real** even in Jev (the irrelevant-option experiment).
  Any threshold policy should be tested under option reordering and set expansion.
- Measured three-path disagreement (DecisionBench, Qwen3 0.6B, 225 calls):
  generated JSON 97.7 ms/11 tokens, constrained 74.4 ms/7 tokens, direct readout
  24.6 ms/1 token — but pairwise agreement only 48–76%, and the direct path
  collapsed to answering "technical" 92% of the time. Fastest path, most degenerate.
  The moral: path choice is a behavior change requiring its own evaluation.

## Measured open-baseline reality check (open reproduction, RTX 3090)

- Quality: Qwen3.5-4B direct logits hit 0.845 modal agreement on the alignable
  102-row TypeSafe public subset vs. Jev's published 0.883, and 0.813 balanced
  accuracy on authored decisions. The native 4B reranker was far behind on general
  decisions (0.560/0.625) though perfect at retrieval ranking.
- Speed: 21 binary decisions over one shared ~8k-char state — direct parallel
  readout 1.02 s vs 5.33 s for the most compact valid generated JSON array (5.2x);
  777 decisions went from 333 s (fresh) to 38.8 s (shared-prefix parallel suffixes),
  at a cost of 6/777 argmax drifts from BF16 numerics.
- Not reproduced by anyone openly: RLCD itself, calibrated operational thresholds,
  frontier-level semantic ability, and TypeSafe's price/latency on equivalent serving.
