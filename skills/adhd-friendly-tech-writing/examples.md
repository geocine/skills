# Examples: Before / After Rewrites

## Example 1: Opening a tutorial

**Before (throat-clearing, corporate):**

> In this article, we will explore the concept of memoization in React. Memoization is an important optimization technique that can significantly improve the performance of your application. We will cover what memoization is, when to use it, and best practices for implementing it effectively.

**After (hook + scope promise):**

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
> Every keystroke re-renders `<ExpensiveTree />`. I could put `memo()` on it and call it a day — but there are two better things to try first.

Why it works: code appears before theory, the problem is felt immediately, and the promise is scoped ("two things") instead of encyclopedic.

## Example 2: Explaining a concept

**Before (abstract, dense, passive):**

> Variable assignment semantics in JavaScript are determined by the type of the value being assigned. Primitive values are copied by value, whereas objects are copied by reference, which means that mutations performed through one reference will be observable through all other references to the same object. This is a frequent source of bugs for developers unfamiliar with these semantics.

**After (challenge + short beats + reveal):**

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

Why it works: the reader commits to an answer first, the wrong mental model is named and corrected, and one concrete example carries the whole idea.

## Example 3: Delivering a recommendation

**Before (hedged, exhaustive):**

> There are several approaches one could consider. You could potentially use memo(), or alternatively useMemo() might be appropriate in certain situations, or in some cases restructuring the components may possibly be beneficial depending on your specific use case and requirements.

**After (one path, escape hatch, bold takeaway):**

> **Before you reach for `memo`, try splitting the parts that change from the parts that don't.** Move the state down into its own component, or lift the static content up as `children`.
>
> Then, where it's not enough, run the Profiler and sprinkle those memo's.

## Post Skeleton

A typical post in this style:

```markdown
# Title (a question or a bold claim, not a topic label)

[Hook: code challenge, tiny story, or confession — first 3 lines]

[One bold sentence scoping the post, if needed]

---

## [Question the reader is now asking]

[Concrete example / code first]

[Explanation in 1–3 sentence paragraphs]

[**Bold takeaway sentence**]

[Bridge: "This leaves us with another question: ..."]

---

## [Next question]

[Wrong-but-plausible assumption voiced, then corrected]

[Same running example, evolved]

---

## What's the moral?

[One punchy takeaway or forward pointer. No recap.]
```
