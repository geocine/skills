# Explainers

Posts, tutorials, explainers and talk scripts. The reader came from a feed, will read once,
and leaves the moment it gets dull. Write like you're explaining something interesting to a
smart friend, not documenting a system.

The core rules in `SKILL.md` still apply. This file adds what is specific to explainers.

## Voice

- Second person ("you") for the reader, first person for stories and opinions ("I wrote
  `super(props)` more times in my life than I'd like to know").
- Contractions always: "don't", "it's", "you'll".
- Admit uncertainty and tradeoffs plainly: "It took me years to see they were right."
- Time words are fine inside a story ("a few days ago"). Outside the story, write facts
  that stay true.

## Openings

Hook within the first three lines. No throat-clearing, no "In this article, we will
explore…". Hooks that work:

- **A challenge**: "Read this code. What are the values of `a` and `b` after it runs? Work
  it out in your head before reading further."
- **A story**: "It was a late evening. My colleague had just checked in the code they'd been
  writing all week."
- **A confession**: "I've been vibecoding a little app, and a few days ago I ran into a bug."
- **A promise with limits**: "**In this post, I want to share two different techniques.**
  They're surprisingly basic."

If the post has prerequisites or caveats, state them in one bold sentence up front, then
move on.

## Structure

- **One idea per section.** Headings are milestones in an argument, not a filing system.
  Questions make good headings, even long ones: "What's a mental model?", "Didn't I read about this before?"
- **Build up.** Never use a concept before establishing it. Each section must make sense
  using only what came before it.
- Use `---` rules as breathing points between beats.
- Shape long posts as a journey: lay out the questions in order ("Why do we call `super`?
  Can we *not* call it? What happens if we don't pass `props`?"), then answer them one at a
  time.
- End each section with a bridge to the next: "This leaves us with another question: why
  pass `props`?"

## Engage the reader

- Voice the reader's objection before they think it: "You might object: 'This snippet is
  much simpler than the code I write every day. What's the point?'"
- Voice the plausible-but-wrong assumption, then correct it: "You might think `super`
  needs `props` so that… That's not far from the truth, but…"
- Ask for active participation: "Try it yourself!", "Work it out before reading further."
- Build suspense before a reveal: "Can't avoid `memo` this time, right? Or can we?"
- Reassure without talking down: "Don't worry if you can't find the bug. It means you'll
  get the most out of this course."

## Endings

End with one punchy takeaway or a pointer forward, never a recap of everything covered:

> Let clean code guide you. **Then let it go.**

> With Hooks, we don't even have `super` or `this`. But that's a topic for another day.

A tutorial that lives inside a docs site still adds two or three links onward after the
takeaway.

## Explainer checklist

- [ ] The first three lines hook, with zero throat-clearing.
- [ ] Each section covers one idea and bridges to the next.
- [ ] At least one reader objection or wrong assumption is voiced and answered.
- [ ] One running example evolves through the whole post.
- [ ] The ending is one takeaway or pointer, not a recap.
