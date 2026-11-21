# Before and after

Rewrites for each mode, then a skeleton for each. Every "before" breaks rules on purpose;
every "after" passes the checklist.

## Explainers

### Opening a tutorial

**Before (throat-clearing, corporate):**

> In this article, we will explore the concept of memoization in React. Memoization is an important optimization technique that can significantly improve the performance of your application. We will cover what memoization is, when to use it, and best practices for implementing it effectively.

**After (hook and a scoped promise):**

> Here's a component with a severe rendering performance problem:
>
> ```jsx
> function App() {
>   let [color, setColor] = useState('red');
>   return (
>     <div>
>       <input value={color} onChange={(e) => setColor(e.target.value)} />
>       <ExpensiveTree />
>     </div>
>   );
> }
> ```
>
> Every keystroke re-renders `<ExpensiveTree />`. I could put `memo()` on it and call it a day. But there are two better things to try first.

Why it works: code appears before theory, the reader feels the problem, and the promise is
scoped ("two things") instead of encyclopedic.

### Explaining a concept

**Before (abstract, dense, passive):**

> Variable assignment semantics in JavaScript are determined by the type of the value being assigned. Primitive values are copied by value, whereas objects are copied by reference, which means that mutations performed through one reference will be observable through all other references to the same object. This is a frequent source of bugs for developers unfamiliar with these semantics.

**After (challenge, short beats, reveal):**

> Read this code:
>
> ```js
> let a = { title: 'Budget' };
> let b = a;
> b.title = 'Copy of Budget';
> ```
>
> What is `a.title` now? Work it out before reading further.
>
> If you said `'Budget'`, the "variables are boxes" mental model betrayed you. `let b = a` didn't copy a box. It pointed a second wire at the *same* object.
>
> So `a.title` is `'Copy of Budget'`. There was only ever one object.

Why it works: the reader commits to an answer first, the wrong mental model is named and
corrected, and one concrete example carries the whole idea.

### Giving a recommendation

**Before (hedged, exhaustive):**

> There are several approaches one could consider. You could potentially use memo(), or alternatively useMemo() might be appropriate in certain situations, or in some cases restructuring the components may possibly be beneficial depending on your specific use case and requirements.

**After (one path, an escape hatch, a bold takeaway):**

> **Before you reach for `memo`, split the parts that change from the parts that don't.** Move the state down into its own component, or lift the static content up as `children`.
>
> Where that's not enough, run the Profiler and add `memo` where it shows the time goes.

## Reference docs

### Opening a page

**Before (describes the page, not the system):**

> ## Overview of the job scheduling subsystem and its retry semantics
>
> This page describes the job scheduler. Jobs are submitted via the API and are processed by workers. The following sections explain how retries work, how failures are handled, etc. Currently the scheduler uses a new backoff strategy which is described below.

**After (short name, claim, "Read this page to…"):**

> ## Job scheduler
>
> Every job runs at least once and at most five times. The scheduler retries a failed job with growing delays, then moves it to the dead-letter queue, where a person decides what happens next.
>
> Read this page to learn how a job moves from submitted to done or dead. It is for anyone writing a job or on call for one. Writing the job itself is in [Writing a job](writing-a-job.md).

Why it works: the heading names the thing; the first line is a fact the reader can rely on;
"via", "etc.", "currently", "new" and "below" are gone.

### Overlong table cell

**Before (a table cell carrying a rule):**

> | Setting | Meaning |
> |---|---|
> | `max_attempts` | The maximum number of times the scheduler will attempt to run a job before it is considered permanently failed and moved to the dead-letter queue; note that the first run counts as an attempt, so a value of 1 disables retries entirely, and values above 10 are rejected at startup because they hide real failures. |
> | `backoff` | Delay strategy. |

**After (a list for the lookup, a block for the rule):**

> The scheduler reads two settings:
>
> - `max_attempts`: how many times a job may run. Default 5.
> - `backoff`: how the delay grows between attempts. Default `exponential`.
>
> ### Attempts
>
> The first run counts as an attempt, so `max_attempts: 1` turns retries off. Values above 10 are rejected at startup, because they hide real failures.

### Samples that disagree

**Before (two pages, two spellings):**

> On the setup page:
>
> ```yaml
> # config/scheduler.yaml
> max-attempts: 5
> ```
>
> On the retries page:
>
> ```yaml
> # config/scheduler.yaml
> maxAttempts: 3
> ```

**After:** both pages use `max_attempts`, the spelling the loader reads, and the same
default, 5. The reviewer found the drift by searching every sample for the key before
writing the new one.

## Skeletons

### Explainer

```markdown
# Title (a question or a bold claim, not a topic label)

[Hook: code challenge, tiny story or confession, in the first 3 lines]

[One bold sentence scoping the post, if needed]

---

## [The question the reader is now asking]

[Concrete example or code first]

[Explanation in 1–3 sentence paragraphs]

[**Bold takeaway sentence**]

[Bridge: "This leaves us with another question: ..."]

---

## [Next question]

[Wrong-but-plausible assumption voiced, then corrected]

[Same running example, evolved]

---

## What's the moral?

[One punchy takeaway or a pointer forward. No recap.]
```

### Reference page

```markdown
# Short name (2–4 words)

[Claim: what is true, 1–3 sentences, at most 50 words]

Read this page to [learn what], if you are [who]. [What it leaves out], see [link].

[The picture that answers the page's question, with numbered steps]

## [Section name]

[Section claim]

[Body: short paragraphs, a sentence before each table, samples with their file path]

## What to read next

- [Page](link): why you would read it next.
- [Page](link): why.
- [Page](link): why.
```
