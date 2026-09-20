# Technical deep dive: how decision models compute, what Jev probably is, and what the measurements say

Skill-authored synthesis. Underlying evidence: a public black-box study
(Sep 2026; ~10,000 instrumented API calls against jev-1.13.0),
an open reproduction (one RTX 3090), and DecisionBench
(DecisionModels.ai, 225 timed local calls). Claims are tagged **published**
(vendor-stated), **observed** (measured behavior), or **inferred** (best explanation).

> **Epistemic status.** TypeSafe has never published Jev's architecture. Everything
> here about *how Jev works internally* is reconstruction: assumptions and
> observations grounded in world knowledge about transformers plus black-box
> probing of the API. Treat it as a working model that explains the measurements,
> not as vendor documentation. The live TypeSafe docs (docs.typesafe.ai) remain the
> source of truth for Jev's actual behavior, guarantees, and interfaces.

## 1. The computation model

A causal transformer processing a prompt (prefill) already builds a rich
representation before any token is decoded. Causal attention constrains which
positions can *use* which information, not the order tokens must be executed in:
during prefill every input token is known, so positions are processed together
within a layer. Autoregressive decoding adds the extra dependency — the next token
does not exist until the previous one is chosen. A decision model ends inference
after prefill plus a readout, skipping that loop entirely.

The readout maps a final hidden vector \(h\) to option scores:

\[ z = Wh + b, \qquad p_i = \frac{e^{z_i}}{\sum_{j=1}^{K} e^{z_j}} \]

where \(K\) is the number of declared answers. For yes/no, a scalar and a sigmoid
suffice. The classes need not be fixed concepts: they can be **option slots**
(first option, second option, …) whose meaning is supplied by the question text,
with code mapping slot probabilities back to the caller's option keys. An ordered
Score predicts probabilities over levels and returns the probability-weighted
average. The main alternative is a **pointer-style scorer** that compares the
decision position's representation against each option's own final hidden state.
A language model's vocabulary head (matrix + softmax) can implement the same
computation by reserving K label rows — the API cannot distinguish these.

JSON formatting happens in ordinary application code; the network only supplies
numbers. This is why "no type errors" is by construction, not a model skill.

### The readout, step by step (worked example)

This walkthrough shows the *general mechanism* as implemented by the open projects
in [training.md](../training.md) (Path B's parallel constrained decoding, Path D's
trained reconstruction); whether Jev's internals match it exactly is
unverified — see the epistemic-status note above. Target schema
`{"risk_level": HIGH|MEDIUM|LOW|NONE, "requires_review": true|false, "action_tier":
TIER_1|TIER_2|TIER_3}` over an OCR'd document as context.

Standard autoregressive decoding emits `{`, `"risk`, `_level"`, `:`, `"HIGH"`, … —
150–500 sequential forward passes, latency growing with every token, and the schema
can come out malformed. The decision path instead:

1. **Prefill once**: context + schema descriptions run through the decoder one time;
   every layer writes its keys/values to the KV cache.
2. For **each field**, pass the cached state plus a short field suffix (e.g.
   `"risk_level":`) through the model — all fields can go in parallel.
3. Take the **final hidden state** (one embedding vector for the last position).
4. Multiply by the **LM head** to get logits over the full vocabulary (~150k rows).
5. **Keep only the candidate rows** — the token scores for `HIGH`, `MEDIUM`, `LOW`,
   `NONE`; mask everything else.
6. **Softmax over that slice** → a distribution that sums to 1 (e.g. HIGH 0.9924,
   MEDIUM 0.0068, LOW 0.0006, NONE 0.0002).
7. **Argmax is the answer**; code assembles `{"risk_level": "HIGH", …}` from
   verified values, so the JSON is valid by construction.

One forward pass per request instead of hundreds, no brackets or quotes generated,
and every field carries its own probability. This "reserved vocabulary rows"
readout is the simplest variant; a trained pointer/slot head (the open
reconstruction and the suspected Jev design) replaces steps 4–5 with a dedicated
head but keeps the same shape. Multi-token option labels need the prefix-tree
disambiguation described in [training.md](../training.md) Path B.

### Shared state, branched questions

For a state of \(S\) tokens and \(Q\) questions, separate requests process the
state ~\(Q\) times; sharing a state prefix in the KV cache reduces the repeated
state processing from \(QS\) to \(S\). Question suffixes still attend to the state
(that work remains), but the state's representations are built once. Prior art for
serving this shape: Hydragen (shared-prefix attention), DeFT (tree attention).

Isolation between question branches gives the interface meaning: asking whether
the customer is angry must not change which queue the ticket is routed to. Branches
have no computational dependency even when their answers are statistically related.
The corollary: if a later question genuinely needs an earlier answer, the
application adds a second stage — shared context does not remove workflow logic.

## 2. The Jev reconstruction, component by component

1. **Readout instead of a decode loop** — published + observed. TypeSafe states
   Jev "outputs all probabilities in parallel instead of autoregressively
   generating by token." The API's `output_tokens` field is a billing artifact
   computed after inference: it counts question-identifier text the docs say is
   never sent to the model, an answer of `0.0` costs the same as `0.01`, a
   200-option question returned as fast as a two-option one, and a 255-option
   response "cost" 2,714 output tokens with no latency signature of decoding.
2. **Shared state, isolated questions** — observed. Token accounting is exactly
   additive (one minimal question 268 input tokens, two questions 276; a mixed
   three-question request matched the sum). The decisive intervention: a secret
   declared inside a *sibling question* was invisible to a probe question
   (p≈0.00); moving the same declaration into shared *state* raised it to
   0.90–0.92 (five repeats per condition). Server time is nearly flat to ~100
   questions, then grows; question text costs ~2x state text per token. Limits fit
   one packed 2^16-token sequence (state counted once + all suffixes), each branch
   capped at 2^15.
3. **Causal frontier backbone** — inferred. 84.6% MMLU-Pro requires frontier-scale
   pretraining; every model at that scale is a causal decoder; TypeSafe describes
   RLCD as post-training a pretrained LM. The tokenizer matches none of 192 public
   tokenizers across 415 probes (closest Qwen at 348/415; vocabulary tracks o200k
   but per-digit splitting rules it out) — consistent with a replaced vocabulary,
   continued pretraining, or API-side counting differences.
4. **Listwise option interaction** — observed. Two experiments:
   - *Reference card*: an option containing only a reference value ("status =
     amber — never select this option") controls which *other* option is correct.
     With the card as the last option: 16/16 correct, mean correct-answer
     probability ~0.88. Card first or middle: 12/16 and 11/16, probabilities
     scattered around 0.5. Card moved into shared state: 48/48. The decision can
     read the whole option list; it is also order-sensitive.
   - *Irrelevant option (IIA violation)*: with fixed independent logits and a
     shared softmax, adding a fifth option cannot change the odds between two
     existing options (the denominator cancels). Observed: log-odds between
     `customer` and `unknown` fell by a mean −0.28 (95% paired interval −0.36 to
     −0.19, decrease in all 10 randomized blocks) when "bad weather caused it" was
     appended. Options interact before the choice.
   - *Fake-option injection* (105 requests, 7 delimiter formats): injected text
     could never forge an option boundary — boundaries are marked in a way text
     cannot imitate.
5. **Distribution trained on outcomes; "confidence" is arithmetic** — published +
   verified in the official adapter. Choice confidence is
   \( c = \frac{p_{\max} - 1/K}{1 - 1/K} \) — distance above uniform, computed in
   the SDK, not a second learned estimate. Score uses a distance-from-modal-level
   formula. Keep the two objects separate: a concentrated distribution can be
   confidently wrong.
6. **Likely sparse MoE** — inferred, weakest claim. Prefill-only inference is
   compute-bound, exactly what sparse routing saves; MoE's usual serving penalties
   (decode-time memory bandwidth, KV cache competing with expert weights) mostly
   vanish without a decode loop. ~30k tokens in ~160 ms fits ~10B active
   parameters on standard hardware where a dense 70B would need ~1 s. Nothing else
   in the reconstruction depends on this.
7. **Batch scheduling of branches** — observed. Repeated identical requests (and
   duplicate questions within one request) return slightly different
   probabilities; response key order varies in recurring patterns. Numerical
   kernels, dynamic batching, and multiple workers explain this without any text
   sampling. Do not assume API-level determinism.

### The reconstruction validated in code

An open-weights project ([training.md](../training.md) Path D) implemented this
exact architecture — packed sequence,
block-causal branch mask, per-branch position-id restart, pointer readout over
`</opt>` states against a `<decide>` token — as a LoRA + head (9.3M trainable
params) on Qwen2.5-0.5B, serving TypeSafe's real `/v1/systemone` contract. Its
mechanism tests confirm the reconstruction's predicted behaviors on a model whose
internals we *can* see:

| Mechanism test | Reconstruction result | Jev (observed) |
| --- | --- | --- |
| Isolation: secret in sibling question / absent / in state | p = 0.03 / 0.03 / **0.99** | 0.00 / 0.00 / 0.90–0.92 |
| Packed vs separate requests | max prob diff 3.7e-6, packed 2.0x faster | additive token accounting |
| Option-order argmax flips | 7.4% (0.0 with an option-isolation mask variant) | 0 flips observed, but probabilities move |
| IIA: log-odds shift from one irrelevant option | 0.13 mean, 0.34 p90 | −0.28 mean |
| Boundary forgery: fake delimiters in option text | option count unchanged, forged option p ≤ 0.09 | never displaced real options |

Two architecture notes from the reconstruction the probes could not settle for Jev: a pointer
head over option end-tokens works and handles arbitrary K naturally (supporting the
pointer hypothesis's plausibility), and placing `<decide>` after all options is
what makes "none of the above" behave. The isolation-by-mask design also proved to
be a real injection defense: one question's text cannot manipulate a sibling's
answer, and reserved delimiters cannot be forged from user text.

The reconstruction's head-to-head with real Jev (frozen suites, record-clustered bootstrap):
in-distribution 79.7% vs 81.1% (−1.8 pp, CI [−5.5, +1.7]) — but on eight unseen
datasets 63.3% vs 82.3% (−19.1 pp, CI [−23.1, −15.0]), while Jev held ~0.85 both
in- and out-of-domain. Controlled follow-ups: backbone capacity dominates transfer
(0.6B→4B +17.5 pp CI [+13.0, +22.1]; 4B→8B +1–7 pp); tripling public training data
at 4B *lowered* transfer ~3 pp while raising in-distribution accuracy; fine-tuning
eroded base knowledge (−11 pp MMLU at 8B vs its own base). The implication for
Jev: its moat is less the mechanism (reproducible on a laptop) than frontier-scale
backbone knowledge plus training data whose in-domain/out-of-domain gap is
approximately zero. Full recipe and lessons: [training.md](../training.md), Path D.

## 3. Calibration: theory and measurements

**Theory.** Calibration is a property of predictions *across cases*: of the cases
assigned 0.8, about 80% should be right. Proper scoring rules — log loss
\(-\log p(y)\), Brier — are minimized in expectation by the true conditional
distribution, which is what "training for calibration" plausibly means (and the
honest open approximation of RLCD). Properness is not a deployment guarantee:
finite data, optimization error, and distribution shift all leave residual error.
Post-hoc temperature scaling is compatible with, and usually still needed after,
such training. Measure with reliability bins and expected calibration error (ECE);
within-bin agreement is stronger evidence than aggregate agreement, since over- and
under-confidence can cancel across groups.

**Measured on Jev (jev-1.13.0):**

- 1,200-item MMLU sample: ten-bin ECE **0.0313**; 990 of 1,200 predictions fell in
  the 0.9–1.0 bin.
- Fresh generated math: three-digit multiplication 86.7% accurate at mean top
  probability 0.83; two-step word problems 32% accurate at mean top probability
  0.30 — confidence tracked difficulty downward, which is the encouraging part.
  Exception: modular exponentiation, right 56% at mean probability 35%.
- MMLU-Pro 84.6% vs much weaker fresh word problems: benchmark scores are an
  imperfect measure of usable capability; the gap does not establish contamination.

**Measured on open baselines (the open reproduction):** direct 4B logits had total-variation
distance 0.177 from public reference distributions vs Jev's 0.127 (reranker 0.444),
and both open systems made at least one confident (>0.8) wrong call on a 36-row
missing-evidence set. Open scores are argmax-useful but not operationally calibrated
without further work.

## 4. Output paths: speed and disagreement

**DecisionBench** (Qwen3 0.6B Q4, Ollama, M3 Pro, 25 inputs x 3 repeats x 3 paths,
temperature 0):

| Path | Median latency | Output tokens |
| --- | ---: | ---: |
| Generated JSON | 97.7 ms | 11 |
| Schema-constrained | 74.4 ms | 7 |
| Direct logit readout | 24.6 ms | 1 |

Pairwise agreement: constrained vs direct 76%, generated vs constrained 68%,
generated vs direct 48%. Same model, same input, same four options — *how you ask*
changed the answer for a quarter to half of inputs. Worse: the direct path
collapsed on this small model, answering "technical" for 92% of inputs and never
"billing" (on inputs including "my card was charged twice"). Schema validity was
100% on all three paths. Lessons: path switching is a behavior change requiring
its own evaluation, and speed on a degenerate answerer is worthless.

**Open-reproduction systems benchmark** (frozen Qwen3.5-4B BF16, RTX 3090, ~8,000-char
state, 21 binary criteria): direct parallel readout returned 21 probability pairs
in a median **1.023 s**, zero output tokens; the most compact valid generated
baseline (ordered JSON array of yes/no) took **5.332 s** (first token 0.489 s,
111 tokens) and agreed with direct argmax on 18/21. A stricter minified-array
request degenerated (repeated values, hit the token cap in 3/3 runs) — recorded as
a failure, not used to inflate the ratio.

Full 777-decision workload (37 states x 21 criteria):

| Mode | Wall time | Decisions/s | Argmax drift vs fresh |
| --- | ---: | ---: | ---: |
| Direct, fresh batch 1 | 333.1 s | 2.33 | reference |
| Direct, serial state-prefix | 72.3 s | 10.75 | 5/777 |
| Direct, parallel suffixes | **38.8 s** | **20.03** | 6/777 |
| Reranker, pair batch 1 | 417.3 s | 1.86 | reference |
| Reranker, pair batch 8 | 435.2 s | 1.79 | 54/777 |

Prefix reuse is where the economics come from — and it costs a few BF16 argmax
drifts, so serving configuration is part of the evaluated system. The reranker
(two full state evaluations per binary decision) never recovered its repeated-state
work through batching.

## 5. Open-reproduction quality (frozen 706-row matrix)

| Frozen workload | Metric | Direct Qwen3.5-4B | Qwen3-Reranker-4B | Published Jev |
| --- | --- | ---: | ---: | ---: |
| Authored decisions, 144 rows | Mean family balanced accuracy | **0.813** | 0.625 | — |
| WANLI NLI, 256 rows | Balanced accuracy | **0.637** | 0.522 | — |
| TypeSafe public subset, 102 rows / 20 cases | Equal-case reference agreement | **0.845** | 0.560 | 0.883 |
| Judgment grid, 36 rows | Accuracy | **0.806** | 0.694 | — |

The 3.8-point gap to published Jev does not establish near-Jev capability: small
selected sample, Jev not run locally, and probability quality differed (section 3).
On retrieval tasks both systems had MRR 1.0 — the reranker's poor decision numbers
are a threshold problem, its ranking was intact. Keep ranking and decision metrics
separate.

Perturbations (36 base cases, output-blind variants):

| Variant | Direct accuracy | Direct flips | Reranker accuracy | Reranker flips |
| --- | ---: | ---: | ---: | ---: |
| Option reversal | 0.813 | 10 | 0.498 | 2 |
| Criterion rewording | 0.706 | 9 | 0.647 | 9 |
| Irrelevant context | 0.821 | 4 | 0.563 | 13 |

Reproduced by open components: the interface pattern (runtime criteria, typed
options, no decoding, shared-state reuse) and a strong 4B semantic baseline.
Not reproduced by anyone openly: RLCD (data and algorithm unpublished), operational
calibration, frontier-level semantics, and TypeSafe's price/latency on an
equivalent serving stack.

## 6. Evaluation protocol (use this for any implementation)

1. **Freeze before measuring**: prompts, case IDs, labels, metrics — committed
   before any candidate output is scored. Commit the exact evaluated ID manifests.
2. **Never collapse unlike tasks into one number.** Per task family:
   full-denominator accuracy, balanced accuracy, macro F1, NLL/Brier, bootstrap
   intervals grouped by source. Retrieval gets MRR/Recall@k only.
3. **Perturbation suite** on a fixed case set: option-order reversal (align by
   semantic ID), meaning-preserving criterion rewording, appended irrelevant
   context, and a missing-evidence population where `insufficient` is correct.
   Report flip counts as well as accuracy.
4. **Calibration**: reliability bins, ECE, within-bin agreement, and bin counts
   (most predictions cluster near certainty).
5. **Timing discipline**: fixed hardware, warm model, include prompt construction
   and readout in the timed region; measure batch-shape drift; never compare local
   timings to a hosted API's service latency.
6. **Interpretation rules**: a forced typed output can still be semantically wrong;
   softmax over declared options is not operational confidence; treat demo
   thresholds as examples to re-evaluate, not constants.

## 7. Research paper index (arXiv IDs)

Every paper cited in this skill, with its arXiv ID for lookup via alphaXiv or any
arXiv tool. IDs verified against alphaXiv where marked.

| Paper | arXiv ID | Role in this skill |
| --- | --- | --- |
| Attention Is All You Need (Vaswani et al., 2017) | [arXiv:1706.03762](https://www.alphaxiv.org/abs/1706.03762) | Transformer backbone: decoder masking, attention, output softmax |
| Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer (Shazeer et al., 2017) | [arXiv:1701.06538](https://www.alphaxiv.org/abs/1701.06538) ✓ | Conditional computation — the inferred Jev backbone style |
| On Calibration of Modern Neural Networks (Guo et al., 2017) | [arXiv:1706.04599](https://www.alphaxiv.org/abs/1706.04599) | Overconfidence, ECE, temperature scaling |
| BERT (Devlin et al., 2018) | [arXiv:1810.04805](https://www.alphaxiv.org/abs/1810.04805) | Classification heads: state in, bounded label out |
| Zero-shot classification via entailment (Yin, Hay, Roth, 2019) | [arXiv:1909.00161](https://www.alphaxiv.org/abs/1909.00161) | Labels declared at inference time |
| WANLI (Liu et al., 2022) | [arXiv:2201.05955](https://www.alphaxiv.org/abs/2201.05955) ✓ | External NLI check in the open-reproduction frozen matrix |
| Efficient guided generation (Willard & Louf, 2023) | [arXiv:2307.09702](https://www.alphaxiv.org/abs/2307.09702) | FSM-constrained decoding |
| GLiNER (Zaratiana et al., 2023) | [arXiv:2311.08526](https://www.alphaxiv.org/abs/2311.08526) | Parallel scoring of declared labels, open weights |
| Llama Guard (Inan et al., 2023) | [arXiv:2312.06674](https://www.alphaxiv.org/abs/2312.06674) | Bounded safety labels as a product |
| Hydragen (Juravsky et al., 2024) | [arXiv:2402.05099](https://www.alphaxiv.org/abs/2402.05099) ✓ | Shared-prefix attention — prior art for Jev-style serving |
| DeFT (Yao et al., 2024) | [arXiv:2404.00242](https://www.alphaxiv.org/abs/2404.00242) ✓ | Tree-structured attention for branched inference |
| FIRST (Reddy et al., 2024) | [arXiv:2406.15657](https://www.alphaxiv.org/abs/2406.15657) | Listwise reranking from first-token logits |
| GLiNER2 (Zaratiana et al., 2025) | [arXiv:2507.18546](https://www.alphaxiv.org/abs/2507.18546) | Multi-task schema classification, one pass, CPU |
| GLiClass (Stepanov et al., 2025) | [arXiv:2508.07662](https://www.alphaxiv.org/abs/2508.07662) | Generalist lightweight sequence classification (training Path C) |

✓ = ID resolved via alphaXiv search during authoring. Unmarked IDs were
transcribed from the cited material and are well-known papers, but re-resolve any
ID before quoting it in something that matters. Not on arXiv: Gneiting & Raftery (2007),
*Strictly Proper Scoring Rules, Prediction, and Estimation*, JASA 102(477):359–378
(the formal foundation for the proper-scoring-rule training objective).

### Related papers (discovered via alphaXiv, not cited by the source material)

Recent work that extends or independently corroborates this skill's themes. Worth
pulling when a conversation goes deep on the matching topic.

**Calibration and confidence:**

| Paper | arXiv ID | Why it matters here |
| --- | --- | --- |
| Same Answer, Different Confidence: Protocol Sensitivity in LLM Confidence Calibration (2026) | [arXiv:2605.27752](https://www.alphaxiv.org/abs/2605.27752) | Independently corroborates the "how you ask changes the answer" finding: measured calibration depends on which answer is scored and under which prompt |
| The Computational Basis of Confidence in Large Language Models (DeepMind/Princeton, 2026) | [arXiv:2607.12447](https://www.alphaxiv.org/abs/2607.12447) | What internal representations encode confidence — the substrate a readout head reads |
| Beyond Post-Hoc Temperature Scaling: Bilevel Optimization for LLM Calibration (2026) | [arXiv:2608.07419](https://www.alphaxiv.org/abs/2608.07419) | Temperature fitted on one domain transfers poorly — the exact failure the open reconstruction observed on transfer suites |
| Evaluating and Calibrating LLM Confidence on Questions with Multiple Correct Answers (2026) | [arXiv:2602.07842](https://www.alphaxiv.org/abs/2602.07842) | Calibration when several options are acceptable — the "spread probability need not mean low quality" case |
| Every Wrong Answer Counts: Option-Level Psychometrics for LLM Multiple-Choice Benchmarks (2026) | [arXiv:2608.02966](https://www.alphaxiv.org/abs/2608.02966) | Scoring the full option distribution, not just the argmax — same spirit as distribution-distance evaluation |
| When Linguistic and Internal Confidence Diverge in Large Language Models (2026) | [arXiv:2608.28382](https://www.alphaxiv.org/abs/2608.28382) | Evidence for the core thesis: a generated "90% confident" is not the model's internal probability |

**Single-pass decisions and reranking:**

| Paper | arXiv ID | Why it matters here |
| --- | --- | --- |
| SPD: Single Pass Decoding for Generative Reranking (Meta, 2026) | [arXiv:2609.01807](https://www.alphaxiv.org/abs/2609.01807) | One forward pass replacing autoregressive rank decoding — the decision-model thesis applied to ranking at production scale |
| One Pass, Any Order: Position-Invariant Listwise Reranking (2026) | [arXiv:2604.27599](https://www.alphaxiv.org/abs/2604.27599) | Order-invariance by construction — same goal as the reconstruction's option-isolation mask (0 flips) |
| You Only Pass Once: Answering and Abstaining Together in a Single Forward Pass (2026) | [arXiv:2608.14465](https://www.alphaxiv.org/abs/2608.14465) | Abstention as a first-class single-pass output — the `insufficient` option, done in the model |
| HeadRank: Decoding-Free Passage Reranking via Preference-Aligned Attention Heads (Tencent, 2026) | [arXiv:2604.17237](https://www.alphaxiv.org/abs/2604.17237) | Reads relevance from attention weights instead of decoding — another readout location |
| CompRank: Efficient LLM Reranking via Token-Level Compression and Decoding-Free Scoring (2026) | [arXiv:2606.11700](https://www.alphaxiv.org/abs/2606.11700) | Decoding-free scoring for production reranking cost budgets |
| Trie Automata for Constrained Decoding over Large Finite Sets (2026) | [arXiv:2608.12574](https://www.alphaxiv.org/abs/2608.12574) | Selecting from large finite string sets — the constrained-decoding answer to high-cardinality Choice |
