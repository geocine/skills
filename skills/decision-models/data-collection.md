# Data collection: log decisions now, migrate seamlessly later

Goal: every TypeSafe (or any hosted decision API) call the app makes should leave
behind a record that later serves three purposes with zero rework — a frozen
evaluation fixture, a fine-tuning dataset, and a replay harness for candidate
replacements. If the user is building with TypeSafe today, this is the insurance
policy; recommend it in the same conversation as any new integration.

## The decision log record

One JSONL row per question per call. Superset of the Path A input format in
[training.md](training.md), so rows replay directly through Path A readout tooling
and map 1:1 onto GLiClass training rows (Path C).
When wiring the logger around the TypeSafe SDK, read the current
[API](https://docs.typesafe.ai/api.md) / SDK page
([Python](https://docs.typesafe.ai/sdk/python.md),
[JavaScript](https://docs.typesafe.ai/sdk/javascript.md)) first — capture whatever
the current response actually contains (field names and confidence semantics can
change across versions; that is why `model_version` is logged).

```json
{
  "id": "triage-2026-09-19-000123.queue",
  "ts": "2026-09-19T09:45:12Z",
  "workflow": "support-triage",
  "question_key": "queue",
  "primitive": "choice",

  "state": {"ticket": {"subject": "...", "messages": ["..."]}, "customer": {"plan": "pro"}},
  "question": "Which queue should handle this ticket?",
  "options": [
    {"id": "billing", "description": "Billing and payment support."},
    {"id": "technical", "description": "Product and technical support."},
    {"id": "insufficient", "description": "The evidence is insufficient to decide."}
  ],

  "response": {
    "distribution": {"billing": 0.68, "technical": 0.24, "insufficient": 0.08},
    "chosen": "billing",
    "confidence": 0.52,
    "model_version": "jev-1.13.0",
    "latency_ms": 142
  },

  "policy": {"threshold": 0.5, "action_taken": "routed_to_billing"},

  "outcome": null
}
```

Notes on the example:

- `confidence` is **derived from the distribution**, not independent of it: for a
  Choice, `(p_max − 1/K)/(1 − 1/K)` — here `(0.68 − 1/3)/(1 − 1/3) ≈ 0.52`. Log
  whatever the API returns, but expect it to be arithmetic over the distribution.
- **Other primitives, same record shape.** Noul: `options` are the two described
  answers and `distribution` is `{"true": p, "false": 1-p}`. Score: `options` are
  the ordered level descriptions and `distribution` is over level ids, with the
  returned scalar logged as `chosen` (probability-weighted level).
- `state` may be a string or a structured object. Replay tooling that takes text
  (e.g. Path A) renders objects deterministically — keep that renderer versioned
  and identical between serving and replay.
- **Log failed calls too** (timeouts, errors, retries) under the same `id` scheme
  with `response: {"error": "...", "latency_ms": ...}` — a replacement must meet
  the reliability budget as well, and logging only successes biases the dataset.

Non-negotiable fields and why:

- **Exact state as sent** (not a reference to mutable data) — replays must see what
  the model saw. If state is huge, store a content hash + immutable blob.
- **Full option set as displayed, in order** — probabilities are conditional on the
  set; order sensitivity is a measured failure mode; `all_labels` negatives are
  needed for encoder fine-tuning.
- **Full returned distribution**, not just the argmax — distribution agreement and
  calibration can't be recovered from the top choice.
- **Model version and latency** — quality drifts across versions; latency is the
  budget any replacement must meet.
- **Policy applied** (threshold, action) — separates "model was wrong" from
  "threshold was wrong" during migration.
- **Outcome, backfilled** — see below. Without outcomes you can only measure
  agreement with the incumbent, never who is actually right.

## Capturing outcomes (the valuable part)

Attach ground truth to `outcome` when it materializes, asynchronously, keyed by `id`:

| Signal | Example |
| --- | --- |
| Human override | Agent re-routes the ticket from billing to technical → label `technical`, `source: "override"` |
| Downstream resolution | Ticket resolved in the routed queue without transfer → confirms the label |
| Escalation result | Escalated case judged non-urgent by a human → Noul label `false` |
| Business event | Flagged transaction later confirmed fraud / chargeback → label the true class (`fraud`) |
| Review verdict | A model-raised finding accepted or dismissed by the reviewer |
| Silence (weak) | No complaint/correction within N days (pick and document N) → weak positive |

Outcome object shape:
`{"label": "technical", "source": "override", "labeled_at": "...", "confidence": "strong" | "weak"}`
with `source` from a small documented enum (e.g. `override`, `resolution`,
`escalation`, `business_event`, `review`, `silence`). If outcomes conflict over
time (an override is itself overridden), append outcome events and treat the
latest strong signal as the label — never overwrite history.
Log **disagreements and low-confidence cases with priority** — they are the highest-
value training and eval rows. Sample a small random slice of high-confidence cases
for human audit anyway (to catch confidently-wrong regions).

## Volume and hygiene

- Log **100% of calls** (it's cheap text); label outcomes opportunistically.
  Useful thresholds per question type: ~200–500 labeled rows for a trustworthy eval;
  a few thousand for a GLiClass fine-tune; more for Path D distribution training.
- Watch class balance; report balanced accuracy, and oversample rare options in labeling.
- **Freeze an eval set early**, and use four partitions, not two (a discipline
  worth copying wholesale): **train**, **calibration** (only for fitting
  temperature scaling — fit here, apply unchanged everywhere), **development** (all
  model selection happens here), and a **locked test** read only for promoted
  candidates, ideally behind an explicit flag. Commit manifests of the exact row
  IDs plus checksums; never train on frozen rows.
- Split by *case/entity*, not by row, so near-duplicate states don't leak across splits.
- For policy/rule decisions, build **minimal pairs**: a relevant intervention
  (change one decisive fact — the answer must change) and an irrelevant intervention
  (change something inert — the answer must not). Keep each pair in one split and
  score pairs together; pair correctness catches shortcut learning that per-row
  accuracy hides.
- Deliberately collect a **missing-evidence population** (cases where `insufficient`
  is correct) — both Jev-like baselines and open models fail these silently.
- PII: prefer **vaulting** (store a reference/token, resolvable under access
  control) so the logged state stays exactly what the model saw. If you must
  redact irreversibly, redact **before the API call** so model, log, and future
  replays all see the same state — never mutate stored states afterward
  (mutation invalidates replays).

## Migration playbook (TypeSafe → self-hosted)

1. **Replay** the frozen eval set through the candidate (Path A/B/C/D from
   [training.md](training.md)); the log format is already the replay format.
2. Compare per question type: agreement with incumbent, accuracy against outcomes,
   balanced accuracy, distribution distance (TV), ECE, latency at your percentiles.
3. Run the **perturbation suite** (option reversal, rewording, irrelevant context,
   missing evidence) on the candidate — parity on clean rows isn't parity.
4. **Re-tune thresholds per candidate.** Probabilities are not transferable across
   models; a 0.5 Jev threshold means nothing to a Qwen readout. Re-fit on labeled
   outcomes, using the logged `policy` records to compare action-level agreement.
5. **Shadow mode**: run the candidate alongside TypeSafe in production, log both,
   compare on live traffic for a few weeks. Then cut over per question type
   (routing first, high-stakes scoring last), keeping the log schema identical so
   the same machinery monitors the replacement.
   The cutover itself can be trivial: a self-hosted Path D server can implement
   TypeSafe's `/v1/systemone` contract, so the official SDK points at the
   replacement with a `base_url` change and zero call-site edits — one more reason
   to code against the SDK rather than a bespoke wrapper.
6. Expect gaps: an open 4B baseline measured ~4 points below published Jev on modal
   agreement but with worse probability quality — some workflows tolerate that after
   threshold re-tuning, some don't. Decide per question type, not globally.
