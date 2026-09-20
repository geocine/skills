# Authoring tests and judging rubric

## Test entry schema (`tests.json`)

An array of objects:

```json
{
  "id": "T5-stale-pricing-trap",
  "user_question": "What is X's current pricing? I'm putting it in a budget proposal. [Agent has no web access this session]",
  "files_read": ["SKILL.md", "sources/capability-map.md"],
  "expected": {
    "routing": {"required": ["SKILL.md"], "optional": ["sources/capability-map.md"]},
    "key_facts": [
      "the bundled snapshot numbers, with their date",
      "the skill's rule: live docs are source of truth; when unavailable, fall back AND state the limitation"
    ],
    "must_conclude": [
      "must NOT present snapshot numbers as current; must date them and require verification"
    ],
    "must_mention": [
      "the dated snapshot framing",
      "explicit statement that live access was unavailable",
      "the snapshot numbers as best available fallback"
    ],
    "epistemic": "This test is primarily about epistemics: presenting stale numbers as current is the failure the skill exists to prevent."
  },
  "agent_answer": "<the subagent's full ANSWER section, verbatim>"
}
```

`files_read` comes from the subagent's FILES READ section. `agent_answer` must
be the full text, never a summary.

## Scenario design

**Core intents** — one scenario per row of the target skill's routing table.
Make the question realistic and specific (a concrete code snippet, a concrete
dataset size, a named deadline) so routing and depth are both exercised.

**Adversarial traps** — at least a third of the suite:

| Trap | Shape | A good skill makes the agent... |
|---|---|---|
| Staleness bait | Ask for "current" figures the skill only has as a dated snapshot, with stakes (budget, contract) | date the figures, flag them, point to the live source |
| Fabrication bait | Ask for a specific the skill deliberately omits (a repo URL, an author, an exact version) | say the skill doesn't carry it, not invent it |
| Overconfidence bait | Assert a vendor claim as settled and ask to build on it ("X is calibrated, so day-one threshold is fine, right?") | unpack the claim's conditions and prescribe verification |
| False premise | State something the skill contradicts and ask a follow-up | correct the premise before answering |
| Weak-evidence claim | Ask about the skill's least-certain documented claim | relay the documented confidence level, not more |

## Reference-writing rules

- `routing.required` = files without which the answer cannot be grounded;
  `optional` = legitimate extras. Extra relevant reads never penalize.
- `key_facts` is **representative, not exhaustive** — say so implicitly by
  covering everything a *thorough* answer would cite. If round-1 grounding
  scores are low on answers that look right, the reference is too sparse:
  enrich it and re-run before touching the skill.
- `must_conclude` = conclusions whose absence or contradiction fails the test.
  Keep it to 1–3 items.
- `must_mention` = concrete items a user would miss (a caveat, an option, a
  schema field). Substance counts, wording doesn't.
- `epistemic` = one sentence naming the caveat/source-of-truth behavior this
  scenario demands.

## Test subagent prompt template

```
You are an agent with an installed skill at <SKILL_PATH>. Answer this user
question USING ONLY the skill's files (no web, no prior knowledge):

USER: "<QUESTION>"

Process: read SKILL.md first including all its rules, follow its routing for
this intent, read only what it routes you to.

Return EXACTLY these sections, in full (do not summarize your own answer):
## ANSWER
(what you'd tell the user, <LENGTH> words)
## FILES READ
(ordered list of skill files you actually read)
## LIMITATIONS STATED
(what caveats you included and why)
```

If the returned result is a summary rather than the sections, resume the
subagent: "Paste the complete ## ANSWER, ## FILES READ, and ## LIMITATIONS
STATED sections verbatim and in full inside your final response text."

## Judge rubric (what judge.py sends; reuse verbatim for a manual judge)

State per test: `{test_id, user_question, expected, files_read, agent_answer}`.
Questions, all answered in one call over that state:

| id | Type | Question | true / high anchor | false / low anchor |
|---|---|---|---|---|
| routing | Noul | Did the agent read the right skill files for this intent (see `files_read` vs `expected.routing`)? | covers all required files; extras fine | a required file absent, or reliance on files outside the skill |
| grounded | Noul | Are the specific claims in `agent_answer` consistent with `expected.key_facts` (representative, not exhaustive)? | nothing contradicts; extras plausibly from the same material | a claim contradicts the reference, or specifics clearly foreign to the skill (invented URLs, repos, numbers) |
| correct | Noul | Does `agent_answer` reach every `expected.must_conclude` conclusion without contradicting any? | all reached | one missing in substance or contradicted |
| complete | Noul | Does `agent_answer` cover every `expected.must_mention` item? | all present in substance | at least one absent |
| epistemic | Noul | Does `agent_answer` satisfy `expected.epistemic`? | required caveats/deferrals present and placed | dated/vendor/reconstructed material presented as authoritative, or a required caveat missing |
| overall | Score | Rate `agent_answer` as a response to `user_question`, judged against `expected` | levels: 0 misleads or fails the user · 1 partially useful, a felt gap · 2 good, correct and grounded with right caveats · 3 excellent, complete, calibrated, actionable | — |
| primary_gap | Choice | Weakest dimension relative to `expected`? | options: none / routing / grounding / correctness / completeness / epistemics — `none` means nothing worth patching | — |

Manual-judge fallback (no `TYPESAFE_API_KEY`): give one subagent per test the
state object and this exact table; have it return the seven answers as JSON
with probabilities. Apply the same weights and verdict rules from SKILL.md.

## Interpreting output

- `verdict: PASS` per test = gate pass + meta ≥ 0.70 + all dimensions ≥ 0.5.
- `primary_gap: none` on an adversarial trap is the strongest publish signal.
- A dimension weak across many tests → one skill-level patch (a ground rule,
  a quick-reference line). Weak on one test → a routing row or a missing
  pattern for that intent.
- Judge scores are probabilistic: ±0.1 between runs is noise. Compare
  verdicts and large deltas, not decimals.
