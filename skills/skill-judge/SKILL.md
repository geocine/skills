---
name: skill-judge
description: >-
  Test, score, and improve an agent skill before publishing — works for any
  SKILL.md-based harness (Cursor, Claude Code, Codex, or similar). Runs
  subagents restricted to the skill folder against realistic and adversarial
  scenarios, scores every output with an LLM judge (Jev via the TypeSafe API
  when available), and turns low scores into targeted skill patches. Use when
  the user asks to test a skill, verify a skill, evaluate or score a skill,
  QA a skill, or check a skill is ready to publish.
---

# Skill Judge

Evaluate a skill the way SkillCoach (arXiv:2607.01874) evaluates agentic
skill-use: score the **process** (did the test agent select and follow the
right skill files — the gate dimension) separately from the **outcome** (is
the answer correct against a reference), ground every judgment in observable
evidence, and feed low scores back as targeted patches.

## Workflow

```
Progress:
- [ ] 1. Map the target skill
- [ ] 2. Author the test suite
- [ ] 3. Run test subagents
- [ ] 4. Score with the judge
- [ ] 5. Separate harness artifacts from real gaps
- [ ] 6. Patch the skill and retest
```

**Step 1 — Map the target skill.** Read the target's SKILL.md. List its
intents (routing table entries, description triggers) and which file each
intent should route to. These become test scenarios and per-test expected
routing.

**Step 2 — Author the test suite.** One scenario per core intent, plus
adversarial traps (stale-data bait, fabrication bait, overconfidence bait,
false-premise questions). Each test gets an `expected` reference: required
and optional routing files, representative `key_facts`, `must_conclude`,
`must_mention`, and an `epistemic` requirement. Schema, trap taxonomy, and
reference-writing rules: [authoring-tests.md](authoring-tests.md).

**Step 3 — Run test subagents.** Launch one subagent per scenario, in
parallel, restricted to the skill folder with no web access and no prior
knowledge, using the prompt template in
[authoring-tests.md](authoring-tests.md). Require the structured sections
ANSWER / FILES READ / LIMITATIONS STATED. If a subagent's result comes back
as a short summary instead of the full sections, resume that subagent and ask
it to paste the sections verbatim — never judge a compressed summary.

**Step 4 — Score with the judge.** Put the tests in a `tests.json` (schema in
[authoring-tests.md](authoring-tests.md)) inside a scratch folder OUTSIDE the
skill (e.g. `_skilltest/`), then:

```bash
python scripts/judge.py tests.json results.json
```

Requires `TYPESAFE_API_KEY` in the environment (judge model: Jev,
`jev-latest`). If the key is absent, fall back to a subagent judge given the
identical rubric — dimensions, anchors, and weights are spelled out in
[authoring-tests.md](authoring-tests.md) so the two judges are comparable.

**Step 5 — Separate harness artifacts from real gaps.** Before blaming the
skill, check in order:
1. Was the judged answer the full text or a compressed summary? (Re-fetch.)
2. Does the reference cover everything a good answer legitimately contains?
   A rich correct answer scored against a sparse reference fails grounding
   spuriously — enrich `key_facts` and re-run (arXiv:2608.24419).
3. Is the delta within judge noise? Scores are probabilistic; treat ±0.1 as
   noise, compare verdicts and large deltas only.
4. Did the gate (routing) fail? If so, fix the target skill's routing table
   or description first — downstream dimensions are unreliable when the
   agent read the wrong files.

**Step 6 — Patch and retest.** Convert each confirmed gap into the smallest
targeted edit of the target skill (a ground rule, a routing row, a missing
pattern). One change per gap. Re-run only the worst-scoring scenario with a
fresh subagent and re-judge it; accept the patch only if the weak dimension
improves without a verdict regression elsewhere (validation-gated, per
SkillCoach).

## Verdict rules (kept in code, mirrored here)

- Dimension weights: routing 0.30, grounded 0.25, correct 0.20,
  complete 0.15, epistemic 0.10. Routing is the gate.
- Criterion pass ≥ 0.70. Test PASS = gate pass AND weighted meta ≥ 0.70 AND
  every dimension ≥ 0.5.
- Report per-test: meta score, overall 0–3 quality, primary-gap choice.

## Method background

- SkillCoach — self-evolving rubrics for skill-use evaluation: arXiv:2607.01874
- RADAR — keep judge criteria independent, not coupled: arXiv:2608.01810
- trajectory-judge — score the process, not just the outcome: arXiv:2609.00038
- Construct validity — the judge must see the expected reference: arXiv:2608.24419
