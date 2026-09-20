# Capability map: what decision models can do

Skill-authored synthesis. Underlying evidence: TypeSafe's Jev launch post
(15 Sep 2026), the DecisionModels.ai ecosystem survey (snapshot 18 Sep 2026), and
project READMEs verified by that survey. Vendor-reported figures are marked as such;
verify anything drift-prone against the live docs
([index](https://docs.typesafe.ai/llms.txt)).

## The interface in one line

State in, decision out: a value from a declared answer space plus a distribution
over the options, produced without generating text. Everything below is a different
way of spending that one primitive.

## Capability areas

### 1. Routing and dispatch

Pick which handler, queue, tool, model, or branch takes the next step — with a
probability attached so code can define fallbacks.

- Support triage: message + context → queue Choice + urgency Noul + severity Score
  in one parallel call.
- Tool/function selection: choose from a fixed set instead of parsing free text;
  fill branch-specific arguments with speculative parallel questions.
- Model routing: an open LLM-router integration uses a decision backend to pick
  which model serves a request, falling back to rules.
- Agent step routing: `browser 0.76 / calculator 0.16 / search 0.08` — the
  distribution itself drives retry and escalation policy.

### 2. Risk, scoring, and approval in the hot path

Return approve/review/reject (or a graded score) fast enough to sit inside a
transaction or request path, with thresholds encoding cost asymmetry in code
(escalate when `p(urgent) > cost_ratio`).

- Fraud screening, moderation, anomaly flags, review prioritization.
- Real deployment shape: score every item cheaply, store raw judgments, apply and
  re-tune thresholds without re-running inference.

### 3. Staged judgment workflows

Compose many narrow decisions into a pipeline where code owns control flow.
The proven pattern (from a real shipped Jev code-review workflow;
worked example in [question-design-example.md](question-design-example.md)):
screen in parallel → profile → select evidence from code-enumerated candidates
(with `noMatch` + confidence floor) → classify mechanism → score severity →
conditionally route. Findings become review prompts, not generated critiques.

### 4. Extraction by selection

Code enumerates candidate values or spans; the model selects; code copies the
selected source text. Transcription hallucination becomes impossible. Low-confidence
selections cascade to a reasoning model or a human.

### 5. Verification and guardrails over LLM traffic

Cheap enough to run on *every* request: judge prompts, reasoning traces, and outputs;
citation checks ("does the cited span support this claim?"); jailbreak detection;
policy conditions as one Noul per condition. Prior art shipping as products:
Llama Guard, ShieldGemma, GLiGuard (14 harm categories + 11 jailbreak strategies in
one 0.3B forward pass).

### 6. Real-time control loops

Sub-second decisions make AI usable where a generation loop cannot keep up:

- A browser-agent integration: 7.09 s median browser task, down from 9.45 s; 101
  browser calls, down from 1,092 (maintainer-measured, three repeats of one task).
- A trading bot: one trade decision per Monad block — a hard latency budget.
- Emulator-game and drone demos: next-action classification from structured
  emulator state / camera input in a control loop.
- TypeSafe's Doom demo: ~10 decisions/s at roughly $7/hour (vendor-reported).
- A computer-use demo: OCR the screen, classify the next action, ~$0.0002/step
  (maintainer's own figure).

### 7. Map-reduce judgment over data

Turn large corpora into features and insights: score dimensions per item once,
in parallel over shared state; re-weight, re-threshold, and re-rank in code.
Labeled outcomes upgrade the judgments into classical ML features.
Shipped: a git-diff miner (classify diffs into bug fixes / security fixes with
CWEs), a per-sentence video scorer with a live overlay, and a browser extension
making element-by-element page-clutter decisions.

### 8. High-cardinality selection

Choice supports up to 255 options (Jev's request-validation cap). Wikiracing-style
link selection among hundreds of candidates works via a two-stage system: score
independently, then make an explicit Choice among the top-k. Not hallucinating a
non-existent option compounds over multi-step tasks.

### 9. Ranking and retrieval support

Compare candidates' relevance to a query and select useful context. Use per-item
comparable Scores for graded ranking; a dedicated reranker only when the task is
pure retrieval (rerankers measured strong at ranking, weak as general
decision-makers).

## Ecosystem shape (as of the 18 Sep 2026 DecisionModels.ai survey)

| Kind | Local | Open weights | What exists |
| --- | --- | --- | --- |
| Hosted model (Jev, TypeSafe) | no | no | Claims vendor-reported; no weights released |
| Local reproductions | yes | partly | Browser/WebGPU demos, a single-GPU (RTX 3090) direct-readout reproduction, MLX parallel constrained decisions, a Gemma 3 270M + scoring-head adapter |
| Tooling | — | — | LLM routers with an optional decision backend |
| Open encoders | yes | yes | GLiClass / GLiNER2 / GLiGuard — the open-weights classification lineage |
| Trained open decision models | yes | yes | A 0.5B LoRA + pointer-head Jev-architecture reconstruction (trains on a laptop, serves TypeSafe's `/v1/systemone` contract so the official SDK works locally); a 9B LoRA trained on synthetic contrastive records (90.1% agreement vs Jev's 93.2% on its own reference set) |

More than 700 public repositories mentioning Jev appeared within three days of
launch; the ones summarized above and in the capability areas were each verified
against their own repos by the survey.

## Lineage: this did not start with Jev

| Year | Work | Contribution |
| --- | --- | --- |
| 2017 | [On Calibration of Modern Neural Networks](https://arxiv.org/abs/1706.04599) — Guo et al. | Modern nets are systematically overconfident; probability isn't calibrated until measured |
| 2018 | [BERT](https://arxiv.org/abs/1810.04805) | Sequence-classification heads: state in, bounded label out, no text |
| 2019 | [Zero-shot classification via entailment](https://arxiv.org/abs/1909.00161) — Yin, Hay, Roth | Label sets declared at inference time — the "declare your options" interface, seven years before Jev |
| 2023 | [Function calling → Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) — OpenAI | Schema-valid objects from an API (still decoded token by token) |
| 2023 | [Guided generation](https://arxiv.org/abs/2307.09702) — Willard & Louf | FSM-constrained decoding: answer space enforced during generation |
| 2023 | [GLiNER](https://arxiv.org/abs/2311.08526) | Bidirectional encoder scoring arbitrary declared labels in parallel; open weights |
| 2023 | [Llama Guard](https://arxiv.org/abs/2312.06674) — Meta | Bounded safety labels as the entire product |
| 2025 | [GLiNER2](https://arxiv.org/abs/2507.18546) — Fastino | Multi-task extraction + classification, schema interface, one pass, CPU |
| 2025 | [GLiClass](https://arxiv.org/abs/2508.07662) — Stepanov et al. | Generalist lightweight sequence classification, ~10x faster than cross-encoders |
| 2026 | GLiGuard — Fastino | 0.3B schema-conditioned safety encoder, Apache-2.0 |
| 2026 | **Jev** — TypeSafe | New claims: **calibration as an explicit training objective** + the latency/price bundle. Vendor-reported, not independently reproduced |

A consolidated arXiv-ID index of all cited papers (including serving/methods papers
not in this table) is in [technical-deep-dive.md](technical-deep-dive.md).

## Jev economics and claims (launch snapshot, 15 Sep 2026 — verify live before quoting)

- Input $0.042/MTok; output free ("too cheap to meter"). LLM comparison:
  $0.20–$10/MTok in, output ~5x input.
- 70–500 ms end-to-end vs 3–329 s for frontier LLM responses; claims 40–200x
  faster at similar System One intelligence, and "193.6x faster, 444.6x cheaper"
  from their workflow evals (self-authored workflows; reference answers averaged
  from GPT-6 Astra and Fable 5.1 — TypeSafe flags both biases itself).
- Trained with RLCD (Reinforcement Learning for Calibrated Decisions) for
  "epistemically honest probabilities"; recipe unpublished.
- Type errors "mathematically impossible" — schema validity is by construction
  (true of every direct-readout system, including open ones).
- Choice cardinality cap 255; larger sets need the two-stage pattern.

## Where to verify and go deeper

- Live TypeSafe docs: [index](https://docs.typesafe.ai/llms.txt),
  [use-case map](https://docs.typesafe.ai/concepts/use-case-map.md), cookbooks.
- Open baselines to try today: GLiClass (`pip install gliclass`), open MLX
  parallel-constrained-decoding demos on Apple Silicon, and the trainable
  Jev-style reconstruction recipe in [the skill's training guide](../training.md) (Path D).
- Internals and measured evidence: [technical-deep-dive.md](technical-deep-dive.md).
