---
name: adhd-friendly-tech-writing
description: Write and rewrite technical content in a concise, conversational, ADHD-friendly style. Use when drafting, editing, or reviewing blog posts, tutorials, explainers, READMEs, or any long-form technical writing, or when the user asks to make writing clearer, more concise, more engaging, or easier to follow.
---

# ADHD-Friendly Technical Writing

Write like you're explaining something interesting to a smart friend — not documenting a system. The reader has limited attention. Every paragraph must earn the next one.

## Voice

- Second person ("you"), first person for stories and opinions ("I wrote `super(props)` more times in my life than I'd like to know").
- Contractions always: "don't", "it's", "you'll".
- Direct and honest. Admit uncertainty and tradeoffs plainly: "It took me years to see they were right."
- No hedging filler ("it could be argued that", "in some cases it may be possible"). If you believe it, say it. If you don't, say why not.
- Banned words: "simply", "just" (as minimizer), "obviously", "clearly", "easy" (about the reader's effort), "leverage", "utilize", "delve".

## Openings

Hook within the first three lines. No throat-clearing, no "In this article, we will explore...". Good hooks:

- A challenge: "Read this code. What are the values of `a` and `b` after it runs? Work it out in your head before reading further."
- A story: "It was a late evening. My colleague has just checked in the code that they've been writing all week."
- A confession: "I've been vibecoding a little app, and a few days ago I ran into a bug."
- A promise with scope limits: "**In this post, I want to share two different techniques.** They're surprisingly basic."

If the post has prerequisites or caveats, state them in one bold sentence up front, then move on.

## Structure

- **One idea per section.** Section headers are milestones in an argument, not a filing system. Questions make good headers: "What's a Mental Model?", "Didn't I read about this before?"
- **Build progressively.** Never use a concept before establishing it. Each section should be understandable using only what came before.
- Use `---` horizontal rules as breathing points between beats within a flow.
- Structure long posts as a journey with numbered steps or escalating questions ("Why do we call `super`? Can we *not* call it? If we have to call it, what happens if we don't pass `props`?"), then answer them one at a time.
- End sections with a bridge to the next: "This leaves us with another question: why pass `props`?"

## Paragraphs and Emphasis

- Paragraphs are 1–3 sentences. Never more than 4.
- A one-sentence paragraph is your emphasis tool. Use it for turns and punchlines:

  > The code worked.
  >
  > But it was repetitive.

- **Bold** whole sentences for the takeaways a skimmer must not miss — at most one or two per section. Skimming only the bold text should give a correct summary of the post.
- *Italics* stress a single word the reader would stress out loud: "code like this can be *very* difficult to think about", "that's *what it does*".
- Never use bold or italics decoratively.

## Code

- Show the code first, explain after. Concrete before abstract, always.
- Snippets are minimal and self-contained. Strip everything that isn't the point; replace it with a comment ("// 10 repetitive lines of math").
- Annotate key lines with short plain-word comments where it helps ("// correct", "// disallowed, see below", "// we forgot to pass props"). Never use emoji.
- When you return to a snippet after several paragraphs, paste it again. Never make the reader scroll back.
- Evolve one running example through the post rather than introducing new examples per section.

## Engage the Reader

- Voice the reader's objection before they think it: "You might object: 'This snippet is much simpler than the code I'm writing every day. What's the point?'"
- Voice the plausible-but-wrong assumption, then correct it: "You might think that passing `props` down to `super` is necessary so that... And that's not far from truth — but..."
- Invite active participation: "Try it yourself!", "Work it out in your head before reading further."
- Build suspense at the reveal: "Can't avoid `memo` this time, right? Or can we?" — optionally followed by spaced `…` lines before the answer.
- Reassure without condescending: "Don't worry if you can't find the bug at all — it just means you'll get the most out of this course!"

## Endings

End with one punchy takeaway or a forward pointer — not a summary of everything covered.

> Let clean code guide you. **Then let it go.**

> With Hooks, we don't even have `super` or `this`. But that's a topic for another day.

## Anti-Patterns

- Walls of text. If a paragraph has two ideas, split it.
- Exhaustive completeness. Cut anything that doesn't serve the one thing this post teaches; link out or say "that's a topic for another day."
- Explaining what the smart reader already knows ("PDF files are a common file format that contains text and images...").
- Passive voice as the default. "React assigns props on the instance" — not "props are assigned on the instance."
- Listing every alternative. Recommend one path; mention an escape hatch only if it matters.
- Jargon without an anchor. First use of a term gets a plain-words gloss or a concrete example.

## Self-Check Before Finishing

- [ ] Does the first three lines hook, with zero throat-clearing?
- [ ] Can a skimmer reading only bold text get the correct takeaway?
- [ ] Is every paragraph ≤ 3 sentences (4 max)?
- [ ] Does each section cover exactly one idea and bridge to the next?
- [ ] Does code appear before its explanation?
- [ ] Did you voice at least one reader objection or wrong assumption?
- [ ] Is the ending a single punchy takeaway, not a recap?
- [ ] Zero banned words ("simply", "obviously", "just", "leverage"...)?

## Additional Resources

- For before/after rewrites and a post skeleton, see [examples.md](examples.md)
