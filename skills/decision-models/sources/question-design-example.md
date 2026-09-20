# Question design, staged composition, and policy-in-code: a worked example

Source: a real shipped code-review
workflow built on TypeSafe Jev. This is the best available production-grade example
of decision-model question design. Three lessons it demonstrates:

1. **Questions carry focus/ignore hints, concrete examples, and counterexamples** —
   not bare labels.
2. **Stages are chained only when an answer determines the next evidence**
   (screen → profile → locate evidence → classify mechanism → score severity →
   conditionally route). Independent questions over the same state go in one call.
3. **All policy lives in code as named constants**, never in prompts.

## The policy constants (one config module)

```ts
export const SCREEN_THRESHOLD = 0.7;        // screening signals >= this are followed up
export const SEVERITY_MAX = 3;              // severity scored on a 0-3 rubric
export const ROUTE_SEVERITY = 1.5;          // findings >= this are routed to a reviewer
export const BLOCKING_SEVERITY = 2;         // findings >= this request changes, not a comment
export const MIN_LOCATION_CONFIDENCE = 0.55; // evidence selection below this is discarded

export const reviewPriorityRubric = [       // Score levels: concrete, self-standing situations
  "Routine review is sufficient",
  "A focused review of the changed behavior is useful",
  "Careful review is needed before merge",
  "Specialist or immediate review is needed",
] as const;

export const severityRubric = [
  "No meaningful impact or no supported issue",
  "Minor or narrowly limited impact",
  "Significant correctness, reliability, compatibility, or security impact",
  "Critical security, data-loss, or widespread outage impact",
] as const;

export const owners = {
  security: "Security, authentication, authorization, or data exposure",
  api: "Public APIs, compatibility, schemas, or protocols",
  runtime: "Execution, concurrency, resources, or failure recovery",
  testing: "Coverage strategy, fixtures, or regression testing",
  maintainer: "The owning domain or feature maintainer",
} as const;

// Every mechanism Choice includes a noIssue escape hatch, e.g. for security:
export const securityMechanisms = {
  authorization: "Authorization or trust boundaries are weakened",
  injection: "Untrusted input can reach an unsafe interpreter or sink",
  exposure: "Sensitive data can be disclosed",
  unsafeDefault: "A default configuration creates avoidable exposure",
  other: "Another concrete security mechanism",
  noIssue: "The selected evidence does not support a concrete security issue",
};
```

## Stage 1: parallel Noul screening (one call, five independent judgments)

Every question names the evidence path (`file.patch`), narrows focus, excludes
distractions, and defines both answers with examples:

```ts
const response = await client.systemOne({
  state: { file, changedTests },
  questions: {
    correctness: noul(
      {
        question: "Does file.patch directly support that this change likely introduces incorrect runtime behavior?",
        inspect: "file.patch",
        focus: "Concrete behavior, state, data-flow, or async errors introduced by added or modified lines",
        ignore: ["Style preferences", "Naming concerns", "Unsupported speculation"],
      },
      {
        true: {
          what: "The patch contains a realistic path to a wrong runtime result",
          examples: ["A condition now handles the opposite case", "A value is written to the wrong field"],
        },
        false: {
          what: "The patch is correct, non-behavioral, or lacks direct evidence of a bug",
          examples: ["Formatting only", "A refactor that preserves data flow"],
        },
      },
    ),
    security: noul(
      {
        question: "Does file.patch directly support that this change introduces or weakens a security boundary?",
        inspect: "file.patch",
        focus: "Authorization, injection, secret exposure, trust boundaries, and unsafe defaults",
      },
      {
        true: {
          what: "The patch creates a concrete path around a security control or into an unsafe sink",
          examples: ["An authorization check is removed", "Untrusted input reaches command execution"],
        },
        false: {
          what: "No security boundary is weakened by the patch",
          not_for: "Code that merely uses security-related names",   // counterexample guard
        },
      },
    ),
    // reliability, compatibility follow the same shape...
    testGap: noul(
      {
        question: "Does file.patch change important behavior without adequate targeted evidence in changedTests?",
        compare: ["file.patch", "changedTests"],   // relates two state fields
        focus: "New branches, boundaries, failure paths, and component interactions",
      },
      {
        true: {
          what: "Important changed behavior has no targeted changed test",
          examples: ["A new failure branch has no assertion", "A protocol change lacks a compatibility test"],
        },
        false: {
          what: "Changed tests exercise the important behavior, or the patch is non-behavioral",
          examples: ["A focused regression test covers the branch", "Documentation-only change"],
        },
      },
    ),
  },
});
// Raw probabilities are stored; SCREEN_THRESHOLD is applied later, in code.
```

## Stage 2: profile (Choice + Score, fed the earlier probabilities as state)

```ts
const response = await client.systemOne({
  state: { file, screeningProbabilities },   // earlier answers become new state
  questions: {
    category: choice(
      { question: "Which category best describes file.patch?", focus: "Primary purpose of the change" },
      {
        behavior: "Adds or changes runtime behavior",
        interface: "Changes an exported API, type, protocol, or data shape",
        infrastructure: "Changes execution, scheduling, build, or operational plumbing",
        observability: "Changes events, logging, monitoring, or diagnostics",
        refactor: "Restructures implementation without intending behavior changes",
        routine: "A small routine change that fits none of the other categories",
      },
    ),
    reviewPriority: score(
      "Rate how closely a human should review file.patch, considering the code and screeningProbabilities.",
      [...reviewPriorityRubric],
    ),
  },
});
```

## Stage 3: evidence selection over code-enumerated candidates, with noMatch + confidence gate

Candidates come from code (parsed diff hunks), never from generation. The model only
selects. This is the anti-hallucination pattern.

```ts
const hunks = parseHunks(signal.file.patch);           // code enumerates candidates
const location = await client.systemOne({
  state: { file: signal.file.path,
           suspectedConcern: { dimension, definition, screeningProbability },
           candidateHunks: hunks },
  questions: {
    evidence: choice(
      {
        question: "Which candidate hunk provides the strongest direct evidence for suspectedConcern?",
        fallback: "Select noMatch when no hunk provides sufficient evidence",
      },
      {
        ...Object.fromEntries(hunks.map((h) => [h.id, "Candidate beginning at changed-file line " + h.startLine])),
        noMatch: "No candidate hunk directly supports the suspected concern",
      },
    ),
  },
});

const selected = location.answers.evidence;
if (selected.choice === "noMatch" || selected.confidence < MIN_LOCATION_CONFIDENCE) return null;
```

## Stages 4-6: mechanism, severity, conditional routing

```ts
// Mechanism Choice (with noIssue escape hatch) over the selected evidence only:
const mechanism = await ask(choice(
  "Which mechanism best describes the suspected concern supported by selectedEvidence?",
  securityMechanisms));
if (mechanism.choice === "noIssue") return null;

// Severity Score with an explicit assumption stated in the question:
const severity = await ask(score(
  "Assuming selectedEvidence exhibits suspectedConcern, rate the likely production impact.",
  [...severityRubric]));

// Routing question is only asked when policy says it matters:
if (severity.score >= ROUTE_SEVERITY) {
  const owner = await ask(choice("Which reviewer is best suited to investigate this concern?", owners));
}

// Final action is a code decision, not a model decision:
action: severity.score >= BLOCKING_SEVERITY ? "request_changes" : "comment"
```

## Transferable checklist

- Name the evidence field in the question (`file.patch`, `selectedEvidence`).
- Give `focus` and `ignore`/`not_for` to draw the decision boundary.
- Define both/all answers, each with `what` plus concrete `examples`.
- Enumerate candidates in code; the model selects; always include `noMatch`.
- Gate every consumed answer on a confidence floor.
- Feed earlier answers forward as named state fields, not as prose.
- Ask conditional questions only when a code-side threshold says they matter.
- Keep every threshold and rubric as a named constant in one config file.
