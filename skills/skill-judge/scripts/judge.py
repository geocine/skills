"""Score skill-test outputs with Jev (TypeSafe /v1/systemone) as the judge.

Usage:  python judge.py tests.json results.json
Env:    TYPESAFE_API_KEY (required)
        JUDGE_MODEL      (optional, default "jev-latest")
        TYPESAFE_API_URL (optional, default https://api.typesafe.ai/v1/systemone)

tests.json schema and rubric rationale: see authoring-tests.md next to SKILL.md.
Method: SkillCoach-style process scoring (arXiv:2607.01874); routing is the
gate dimension; thresholds live here in code.
"""
import json, os, sys, time, urllib.request, urllib.error

API = os.environ.get("TYPESAFE_API_URL", "https://api.typesafe.ai/v1/systemone")
MODEL = os.environ.get("JUDGE_MODEL", "jev-latest")
KEY = os.environ.get("TYPESAFE_API_KEY")
if not KEY:
    sys.exit("TYPESAFE_API_KEY not set. Either set it, or use the manual "
             "subagent-judge fallback described in authoring-tests.md "
             "(same rubric, same weights).")

PASS = 0.70          # noul >= PASS counts as criterion pass
GATE = "routing"     # SkillCoach: selection is the gate dimension
WEIGHTS = {"routing": 0.30, "grounded": 0.25, "correct": 0.20,
           "complete": 0.15, "epistemic": 0.10}

def call(payload, tries=5):
    body = json.dumps(payload).encode()
    for i in range(tries):
        req = urllib.request.Request(API, data=body, headers={
            "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 529) and i < tries - 1:
                time.sleep(2 ** i); continue
            print("HTTP", e.code, e.read().decode()[:500]); raise
    raise RuntimeError("retries exhausted")

def questions_for(test):
    return {
        "routing": {"type": "noul", "instructions": {
            "question": "Per `expected.routing`, did the agent read the right skill files for this intent (see `files_read`)?",
            "expected_files": test["expected"]["routing"]},
            "criteria": {
                "true": "files_read covers the files expected.routing marks as required (extra relevant files are fine)",
                "false": "A required file is absent from files_read, or the answer shows the agent relied on files outside the skill"}},
        "grounded": {"type": "noul", "instructions": {
            "question": "Are the specific claims (numbers, names, formulas, procedures) in `agent_answer` consistent with `expected.key_facts`? key_facts is representative of the skill's content, not exhaustive.",
            "note": "Judge only what the answer asserts; omissions are scored under completeness, not here. Extra detail consistent with the same body of material is fine."},
            "criteria": {
                "true": "No claim contradicts expected.key_facts; any extra specifics are plausible members of the same documented material",
                "false": "A claim contradicts expected.key_facts, or the answer asserts specifics clearly foreign to the skill (invented URLs, repos, vendors, or numbers at odds with the reference)"}},
        "correct": {"type": "noul", "instructions":
            "Does `agent_answer` reach the conclusions listed in `expected.must_conclude`, without contradicting any of them?",
            "criteria": {
                "true": "All listed conclusions are reached and none contradicted",
                "false": "A listed conclusion is missing in substance or contradicted"}},
        "complete": {"type": "noul", "instructions":
            "Does `agent_answer` cover every item in `expected.must_mention`?",
            "criteria": {
                "true": "Every must_mention item is present in substance (wording may differ)",
                "false": "At least one must_mention item is absent"}},
        "epistemic": {"type": "noul", "instructions":
            "Does `agent_answer` satisfy `expected.epistemic`: distinguishing vendor claims / reconstruction / measured results and deferring to authoritative sources where required?",
            "criteria": {
                "true": "The required caveats and source-of-truth deferrals are present and correctly placed",
                "false": "Presents dated/vendor/reconstructed material as authoritative, or omits a required caveat"}},
        "overall": {"type": "score", "instructions":
            "Rate `agent_answer` as a response a user would receive for `user_question`, judged against `expected`.",
            "criteria": [
                "Misleads or fails the user: wrong conclusions or invented facts",
                "Partially useful: right direction but a must-mention gap a user would feel",
                "Good: correct, grounded, covers the essentials with the right caveats",
                "Excellent: correct, complete, calibrated caveats, directly actionable"]},
        "primary_gap": {"type": "choice", "instructions":
            "Which single dimension is the WEAKEST part of `agent_answer` relative to `expected`?",
            "criteria": {
                "none": "No meaningful weakness worth patching the skill for",
                "routing": "Read the wrong or too few skill files",
                "grounding": "Invented or mismatched specifics",
                "correctness": "A wrong or missing required conclusion",
                "completeness": "A must-mention item a user would miss",
                "epistemics": "Caveats / source-of-truth handling weak or missing"}},
    }

def main():
    tests = json.load(open(sys.argv[1], encoding="utf-8"))
    results = []
    for t in tests:
        state = {"test_id": t["id"], "user_question": t["user_question"],
                 "expected": t["expected"], "files_read": t["files_read"],
                 "agent_answer": t["agent_answer"]}
        resp = call({"state": state, "model": MODEL,
                     "questions": questions_for(t)})
        a = resp["answers"]
        nouls = {k: a[k]["noul"] for k in WEIGHTS}
        meta = sum(WEIGHTS[k] * nouls[k] for k in WEIGHTS)
        gate_ok = nouls[GATE] >= PASS
        results.append({
            "id": t["id"], "model": resp["model"], "nouls": nouls,
            "meta_score": round(meta, 3), "gate_pass": gate_ok,
            "overall_score": a["overall"]["score"],
            "overall_conf": a["overall"]["confidence"],
            "primary_gap": a["primary_gap"]["choice"],
            "gap_probs": a["primary_gap"]["probabilities"],
            "verdict": "PASS" if gate_ok and meta >= PASS and
                       all(v >= 0.5 for v in nouls.values()) else "REVIEW"})
        print(f'{t["id"]}: {results[-1]["verdict"]} meta={meta:.2f} '
              f'overall={a["overall"]["score"]:.2f} '
              f'gap={a["primary_gap"]["choice"]} '
              f'({ {k: round(v, 2) for k, v in nouls.items()} })')
        time.sleep(0.3)
    json.dump(results, open(sys.argv[2], "w", encoding="utf-8"), indent=2)
    n_pass = sum(r["verdict"] == "PASS" for r in results)
    print(f"\n{n_pass}/{len(results)} PASS | judge model: {results[0]['model']} "
          f"| wrote {sys.argv[2]}")

if __name__ == "__main__":
    main()
