# Use cases: what to build, and how to find opportunities in a codebase

## Workflow for "what could we build with this in our app?"

1. **Scan the codebase for decision smells** (section below). Collect concrete
   sites: file, function, current mechanism.
2. **Map each site to a decision shape**: what is the state, what is the question,
   what is the closed answer space, what does code do with the answer.
3. **Rank by fit**: bounded answer space, latency-sensitive, currently brittle
   (regex/keyword/if-chains) or currently expensive (LLM prompt-and-parse), and
   an available outcome signal for later evaluation.
4. Present the top candidates (3–5 when the scanned surface yields that many; a
   single snippet may yield one) with the state/question/options sketch and what
   would change in the calling code. Recommend one starting point.
5. Point the user to [data-collection.md](data-collection.md): whatever they ship,
   log decisions and outcomes from day one.

## Decision smells to grep for

| Smell in the user's code | Decision-model replacement |
| --- | --- |
| LLM call whose output is immediately `JSON.parse`d / regex-extracted into an enum, boolean, or number | Direct Choice/Noul/Score — same judgment, no generation, no repair loop |
| Retry/repair loops around malformed LLM JSON | Typed readout: schema validity by construction |
| Keyword/regex classification (`if msg.includes("refund")`) | Choice over queue/category options with real semantics |
| Long if/else or switch chains interpreting free text or user intent | Choice routing with probabilities; thresholds stay in code |
| Manual triage queues, human review of every item | Score for review priority; route only above threshold |
| Tool/agent selection by prompt ("which tool should I use?") | Choice over the fixed tool set |
| Hand-tuned heuristic scores (spam-ness, risk points) | Score with described levels; calibrate on outcomes |
| Moderation / policy checks via generated explanations | Noul per policy condition; escalate uncertain cases |
| Ranking search results / candidates with a heuristic | Per-item comparable Scores, or a reranker if it is pure retrieval — live: [reranking](https://docs.typesafe.ai/cookbooks/rerank_typesafe.md), [hierarchical classification](https://docs.typesafe.ai/cookbooks/hierarchical_classification.md) |
| Validation of extracted fields against source documents | Noul: "does the evidence support field X?" with `insufficient` option |

Search hints: `JSON.parse(` near LLM client calls, `zodResponseFormat` /
`response_format`, `temperature: 0` chat calls returning one word, `switch` on
lowercased user text, TODO comments like "improve this heuristic".

## Use-case catalog (with real shipped examples)

Each entry: shape = state → question → options.

If building on TypeSafe, check the live [use-case map](https://docs.typesafe.ai/concepts/use-case-map.md)
and the cookbook index in [llms.txt](https://docs.typesafe.ai/llms.txt) first — new
cookbooks appear there, and one often shows a better decomposition than the generic
shape below (see the live-docs section in [SKILL.md](SKILL.md)).

- **Agent/tool routing.** Request text + available handlers → "which handles this?"
  → handler ids. Fill branch-specific arguments with speculative parallel questions.
  Shipped as open LLM-router integrations. Live:
  [function calling](https://docs.typesafe.ai/cookbooks/function_calling.md),
  [speculative fan-out](https://docs.typesafe.ai/patterns/fan-out.md).
- **Support triage.** Message + customer context → queue Choice + urgency Noul +
  severity Score in one parallel call. The canonical demo.
- **Fraud / risk scoring in the transaction path.** Transaction + history →
  approve/review/reject with probability; thresholds encode the cost asymmetry
  (escalate when `p(urgent) > cost_ratio`). A fintech-fraud preset schema ships with
  the open MLX implementation ([training.md](training.md), Path B).
- **Code review as staged judgments.** From a real shipped Jev code-review workflow;
  full worked example bundled in [sources/question-design-example.md](sources/question-design-example.md).
  Pattern worth copying:
  1. Noul risk matrix per file (correctness, security, reliability, compatibility, testGap)
  2. Choice + Score file profiles (category, review priority)
  3. Choice evidence selection over candidate hunks (**with `noMatch` option and a
     confidence floor** — this is how you avoid hallucinated findings)
  4. Choice mechanism classification, Score severity
  5. Conditional Choice reviewer routing only above a severity threshold.
  All thresholds live in one config module, not in prompts.
- **Extraction by selection, not generation.** Enumerate candidate values/spans in
  code; ask the model to select; copy the selected source text. Eliminates
  transcription hallucination. Cascade: cheap decision first, escalate low-confidence
  to a reasoning model or human. Live:
  [value extraction](https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook.md),
  [structure recovery](https://docs.typesafe.ai/cookbooks/autoformat.md),
  [extraction cascades](https://docs.typesafe.ai/cookbooks/sde_cascade.md).
- **Verification / guardrails over LLM traffic.** Score, judge, verify, and
  jailbreak-detect prompts and outputs — cheap enough to run on every request.
  Citation checks: "does the cited span support the claim?" per claim. Live:
  [citation checks](https://docs.typesafe.ai/cookbooks/citation_check.md).
- **Real-time control loops.** Classify next action from structured state at
  10+ Hz. Shipped: emulator game control (structured state → action), drone control
  (camera → next action), TypeSafe's Doom demo (~$7/hour at 10 queries/s), and a
  trading bot making one decision per block — a hard latency budget is the point.
- **Browser/computer use.** OCR or DOM snapshot → "which element should the agent
  act on?" Shipped: a browser-agent integration (7.09 s median task, down from
  9.45 s; 101 browser calls, down from 1,092), a screen-OCR computer-use demo
  (~$0.0002/step, maintainer-reported), and a browser extension making
  element-by-element page-clutter decisions.
- **Map-reduce feature extraction over big data.** Score dimensions once per item
  (cheap, parallel), store the raw judgments, let code re-weight/re-threshold
  without re-inference; labeled outcomes turn these into classical ML features.
  Shipped: a git-diff miner (classify commits into fix/security/CWE), a per-sentence
  video scorer rendering a live meter. Live:
  [composite scoring](https://docs.typesafe.ai/patterns/composite-scoring.md),
  [feature discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery.md).
- **High-cardinality selection (up to ~255 options).** Wikiracing link choice,
  tariff-code classification (a 255-choice tariff preset ships with the same open
  MLX implementation, [training.md](training.md) Path B). Above the cap:
  score independently in stage 1, explicit Choice among top-k in stage 2.

## Composition rules when sketching a build

- Ask independent questions over the same state **together** (parallel, cheaper via
  shared state). Add a second stage only when an answer determines the next
  evidence/options.
- Include speculative branch questions up front and consume only the winner's answers.
- Always include `noMatch`/`insufficient` where nothing may fit; gate on a
  confidence floor before acting (the code-review example gates evidence selection
  on a minimum location confidence).
- Keep raw probabilities in the data model; apply thresholds at the edge. A weight
  change should be a code change, not a re-inference.
- For latency budgets: shared-state parallel questions amortize the expensive
  prefill; question text costs roughly 2x state text per token (measured on Jev).
