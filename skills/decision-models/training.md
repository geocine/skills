# Training your own decision model

## Choose a path first

```text
Do you have labeled decisions yet?
├─ No  → start zero-shot, log decisions + outcomes (see data-collection.md)
│        ├─ Need general world knowledge / runtime-defined criteria → Path A (LLM logit readout)
│        ├─ Need multi-field JSON schemas on cheap hardware → Path B (parallel constrained decoding)
│        └─ Need high-volume label classification on CPU/small GPU → Path C (GLiClass zero-shot)
└─ Yes → fine-tune
         ├─ Classification-shaped, throughput matters → Path C (GLiClass fine-tune, ~few k examples)
         └─ Jev-like typed questions with calibration → Path D (LoRA + pointer head, proper-scoring fine-tune)
```

All paths share the same evaluation protocol (bottom of this file). RLCD itself is
unpublished; Path D is the honest open approximation — and an open reconstruction
proved it works end-to-end at laptop scale, including where it falls short of Jev.

Tiebreaker when both fine-tune branches fit: choose **Path C** for single- or
multi-label classification where throughput and small hardware dominate; choose
**Path D** when you need the typed primitives (Choice/Noul/Score mix), calibrated
distributions over options, or drop-in compatibility with TypeSafe's API contract.

## Path A — direct logit readout of an open LLM

Reference setup: a frozen open instruct model (measured: Qwen3.5-4B, one RTX 3090).
The methodology, measured results, and the evaluation protocol are covered in
[sources/technical-deep-dive.md](sources/technical-deep-dive.md).

Mechanism: prompt the frozen instruct model with state + criterion + described
options labeled A/B/C…; run **one forward pass**; softmax only over the logits of
the fixed answer tokens. No token is decoded. When many rows share the same state,
prefill it once and evaluate the criteria as parallel suffixes.

Input row format (also the recommended logging format):

```json
{"id": "route-1",
 "state": "Customer cannot access an account after a password reset.",
 "question": "Which queue should handle this request?",
 "options": [{"id": "access", "description": "Account access support."},
             {"id": "billing", "description": "Billing support."}]}
```

Measured expectations: 0.813 balanced accuracy on authored decisions, 0.845
agreement with published Jev references on the alignable subset; 20 decisions/s
with shared-state parallel suffixes vs 2.3 fresh (5–6 argmax drifts per 777 from
BF16 reuse). Known weaknesses to test for: option-order flips, probability quality
(TV distance 0.177 vs Jev's 0.127), occasional confident answers on
missing-evidence cases. A generic reranker is the wrong foundation for general
decisions (0.625 balanced accuracy) though excellent for pure retrieval ranking.

## Path B — parallel constrained decoding over schemas (MLX / Apple Silicon)

Reference implementation: an open MLX project (measured: Qwen2.5-1.5B 4-bit,
~1.1 GB RAM). Prefill context+schema once, broadcast the KV cache across all
fields, slice logits to each field's candidate tokens, softmax, assemble JSON
programmatically → 100% schema validity, 5.6–7x faster than autoregressive, exact
per-field probabilities. For a step-by-step worked example of this exact mechanism,
see [sources/technical-deep-dive.md](sources/technical-deep-dive.md).

API shape (illustrative — adapt names to the implementation at hand):

```python
from core.schema import StructuredSchema
from core.engine import run_parallel_generation

schema = StructuredSchema({
    "fraud_risk": {"type": "enum", "choices": ["LOW", "ELEVATED", "SUSPICIOUS", "CRITICAL"],
                    "description": "Risk assessment tier for incoming transaction"},
    "block_account": {"type": "boolean",
                       "description": "Whether immediate account restriction is required"},
})
result = run_parallel_generation(context, schema)   # result["parsed_json"], field_telemetry with top_choices
```

Supports enums up to 255 choices and booleans; any `mlx-lm` decoder swaps in. Its
preset schemas (fraud, code security, 28-field support triage, 255-choice tariff)
are good schema-design templates.

Multi-token option labels need disambiguation: when candidate labels tokenize into
several tokens or share a leading token, softmax at the first token position where
the candidates diverge, and walk the shared prefix tree with extra scoring passes
where needed — never let the model free-run to finish a label.

## Path C — GLiClass encoders (zero-shot now, fine-tune later)

Reference implementation: GLiClass ([arXiv:2508.07662](https://www.alphaxiv.org/abs/2508.07662),
pip `gliclass`). A GLiNER-style encoder
scoring declared labels against text in one forward pass — ~10x faster than
cross-encoders, runs on modest hardware, fully open weights.

```python
from gliclass import GLiClassModel, ZeroShotClassificationPipeline
from transformers import AutoTokenizer
model = GLiClassModel.from_pretrained("knowledgator/gliclass-small-v1.0")
tokenizer = AutoTokenizer.from_pretrained("knowledgator/gliclass-small-v1.0")
pipeline = ZeroShotClassificationPipeline(model, tokenizer, classification_type="multi-label", device="cuda:0")
results = pipeline(text, ["billing", "technical", "sales"], threshold=0.5)[0]
```

Useful features: hierarchical labels (`{"sentiment": [...], "topic": [...]}`),
few-shot in-context examples, per-text task prompts, retrieval-augmented
classification (RAC), long-document chunking, streaming classification over a KV
cache, Ray Serve deployment (`python -m gliclass.serve`).

**Fine-tuning on your logged data.** Training format maps directly from the
decision log in [data-collection.md](data-collection.md):

```json
[{"text": "Sample text.", "all_labels": ["sports", "science", "business"], "true_labels": ["sports"]},
 {"text": "Sample text.", "all_labels": ["sports", "science"], "true_labels": {"sports": 0.9}}]
```

- `text` ← rendered state (+ question, if you train one model across question types)
- `all_labels` ← the option set shown at decision time (keep it! negatives matter)
- `true_labels` ← the outcome label, optionally with soft confidence
- Entry points: `train.py` (supervised, from scratch or from a checkpoint),
  `train_rl.py` (RL variant), `notebooks/finetuning.ipynb`.
- Architecture/config knobs: uni-/bi-encoder, pooling strategies, scorer types
  (`simple` dot product fastest, `mlp`, `hopfield`).
- **Calibrate after fine-tuning, same discipline as Path D**: fit temperature
  scaling (or per-label threshold + Platt/isotonic for multi-label sigmoid scores)
  on the calibration split only, apply unchanged everywhere, and report ECE +
  reliability bins on the development split before trusting scores as probabilities.
- Honest caveat: this skill carries **no measured accuracy/calibration numbers for
  Path C** on the decision workloads (the measured baselines are Paths A and D).
  Treat vendor throughput claims as vendor claims and run the evaluation protocol
  below on your own frozen eval before promoting it.

## Path D — train a Jev-style decision model

What TypeSafe discloses: RLCD post-trains a pretrained LLM for "epistemically honest
probabilities"; the recipe is unpublished. An open-weights reconstruction is the
working proof of the recipe below: a LoRA adapter + small pointer head on
Qwen2.5-0.5B that serves TypeSafe's actual `/v1/systemone` contract (their SDK
works with a `base_url` change) and trains in **~1h45m on an Apple M5 laptop**
(or $0.15–0.30 per 0.5B trial on an H100).

**Architecture** (implements the reconstruction in
[sources/technical-deep-dive.md](sources/technical-deep-dive.md)):

- Pack state + all questions into **one sequence** with reserved delimiter tokens:
  `<state> … <q> instr <opt> o1 </opt> <opt> o2 </opt> … <decide>` per question.
- **Block-causal mask**: a question token sees the state and its own branch only;
  each branch restarts position ids after the state, so question order is irrelevant
  and isolation is exact (packed vs separate requests agree to ~4e-6, packed ~2x faster).
- **Pointer readout**: score each option's `</opt>` hidden state against the
  `<decide>` hidden state, softmax. `<decide>` follows all options, so the model
  reads the full list — this is what makes "none of the above" work.
- Trainable: LoRA r16 on all attention+MLP projections + the head ≈ 9.3M params
  (1.9% of a 0.5B backbone). Reserved tokens are repurposed existing special tokens;
  user text is sanitized so option boundaries cannot be forged.

**Data recipe** — no labeled product data required to start:

1. Convert public datasets to typed requests (the 0.5B reference run used six: Banking77 as
   77-way Choice, AG News as Choice+Nouls, MNLI as 3-way Choice, BoolQ as Noul,
   SST-5 and Yelp as 5-level Scores → 9,000 records / 13,500 questions).
   Your logged decisions from [data-collection.md](data-collection.md) drop into
   the same shape.
2. **Render training data through the same code path as serving** — the model must
   never meet a format at inference it did not see in training.
3. Vary renderings (~30% null option descriptions, structured instructions,
   object/array-wrapped states) and augment per record: shuffle option order,
   ~10% replace the true option with `other: None of the above`, ~15% add an
   irrelevant distractor.

**Training**: cross-entropy over the option distribution (a proper scoring rule —
log loss is minimized by the true conditional distribution), AdamW lr 2e-4, 2
epochs. Optional extra losses: permutation-consistency KL between
two option orders, and a cumulative-probability ordinal loss for Score. Then fit
**temperature scaling** on a held-out calibration split (measured: T=1.47 took ECE
0.065 → 0.031) and apply it unchanged everywhere. Compute the `confidence` field in
code from the distribution (`(p_max − 1/K)/(1 − 1/K)` for Choice), never as a
second head.

**Measured results and hard-won lessons (controlled studies on H100s):**

- In-distribution it works: 0.799 accuracy over 1,350 held-out questions vs ~0.4–0.6
  zero-shot; on the same frozen suite the 0.5B reconstruction hit 79.7% vs real
  Jev's 81.1% (−1.8 pp, 95% CI [−5.5, +1.7]).
- **Parity does not transfer.** On eight unseen datasets: the reconstruction 63.3% vs Jev 82.3%
  (−19.1 pp, CI [−23.1, −15.0]). Jev scored ~0.85 both in- and out-of-domain.
- **Backbone capacity dominates transfer**: 0.6B → 4B is +14–19 pp out-of-domain
  (matched study: +17.5 pp CI [+13.0, +22.1]); 4B → 8B only +1–7 pp.
- **More public training data can hurt transfer**: tripling public data at 4B raised
  in-distribution accuracy and *lowered* transfer ~3 pp. The lever is data mix, not
  volume. Programmatic compositional policy data added +4–5 pp at 4B, nothing at 0.6B.
- **Fine-tuning erodes base capability** (−11 pp MMLU at 8B vs its own base
  zero-shot). Probe base-capability retention; consider low-drift LoRA (fewer
  targets, lower rank/lr) and keeping knowledge-MCQ sources in the mix.
- Order sensitivity persists (7.4% argmax flips) unless addressed; an
  `option_isolation` mask variant achieved exactly 0 flips by construction at no
  measured accuracy cost. Jev shows 0 observed flips but its probabilities still
  move under permutation.
- Related external result: an independent 9B LoRA trained on 2,676 synthetic
  contrastive records reported 90.1% agreement with synthetic references vs Jev's
  93.2% — hard outcome labels + a proper scoring rule suffice; teacher
  probabilities are not required.

## Evaluation protocol (full version in [sources/technical-deep-dive.md](sources/technical-deep-dive.md))

- **Freeze everything before looking at results**: prompts, IDs, labels, metrics.
- Do not collapse unlike tasks into one accuracy number. Per family: full-denominator
  accuracy, **balanced accuracy**, macro F1, NLL/Brier, bootstrap intervals.
  Retrieval tasks get ranking metrics (MRR, Recall@k) — never mix them with
  decision-threshold accuracy.
- **Perturbation suite** on a fixed case set: (a) reverse option order, align by
  semantic id; (b) meaning-preserving criterion rewording; (c) append irrelevant
  context; (d) a missing-evidence population where `insufficient` is correct.
  Report flip counts, not just accuracy.
- **Calibration**: reliability bins, ECE, and within-bin (not just aggregate)
  agreement; most predictions cluster near certainty, so bin counts matter.
- Timing: fixed hardware, warm model, include prompt construction and readout;
  report batch-shape drift (batching changed 51/777 close BF16 reranker decisions —
  serving config is part of the evaluated system).
- Interpretation rules: a forced typed output can still be semantically wrong;
  softmax over allowed tokens is conditional on the alternatives, not operational
  confidence; your local timings say nothing about a hosted API.
