---
name: technical-writing
description: Write, rewrite and review technical writing so a busy reader can follow it and act on it. Covers two modes, explainers (blog posts, tutorials, explainers, talks; conversational, hook first) and reference docs (READMEs, docs pages, design docs, specs, runbooks, API guides; claim first, built for skimming), with shared rules for both (short names, one word per concept, short paragraphs, code before theory, samples that agree). Use when drafting, editing or reviewing any long-form technical text, or when the user asks to make writing clearer, shorter, more engaging, easier to follow or ADHD-friendly.
---

# Technical writing

The reader has limited attention and a job to do. **Every paragraph must earn the next one,
and every page must leave the reader knowing what to do next.**

## Pick the mode first

Two kinds of technical text need different openings, voices and endings. Decide which one
you are writing before the first sentence:

| | Explainer | Reference doc |
|---|---|---|
| Examples | blog post, tutorial, explainer, talk script, launch post | README, docs page, design doc, spec, runbook, API guide |
| Read | once, top to bottom | many times, by jumping to a section |
| Opens with | a hook: a challenge, a story, a confession | a claim: what is true, in at most 50 words |
| Voice | "you" and "I", contractions, opinions | assertive present tense, "you" for instructions |
| Ends with | one punchy takeaway | "What to read next" links |
| Rules | [references/explainers.md](references/explainers.md) | [references/reference-docs.md](references/reference-docs.md) |

A README is a reference doc whose first screen may borrow an explainer hook. A tutorial
inside a docs site is an explainer that still ends with links onward. When in doubt, ask
how the reader arrives: from a feed (explainer) or from a search or sidebar (reference).

Read the file for your mode before you write. The core rules that follow apply to both.

## Core rules

### Names

- **A name names the thing. The explanation goes under it.** Keep headings short; the
  sentence that wanted to be a heading becomes the first line of the text. Reference docs
  cap headings at four words; explainers may use a question as a heading.
- **One word per concept, everywhere.** "Seam", "contract" and "interface" for one thing
  read as three things. If a word changes, change it everywhere in the same pass.
- **Define every term where it is first used.** First use gets a plain gloss or a concrete
  example. Abbreviations get their long form once: "CRDT, short for conflict-free
  replicated data type".
- **No private labels.** `W1`, `F2`, "flow B" mean nothing to a reader. Call a thing by its
  name, and link to it.
- **Prefer the reader's word to the builder's**, unless the friendlier word collides with
  something else in the system.

### Sentences

- Active voice: "The scheduler retries the job", not "the job is retried".
- One idea per sentence. Put the condition first: "When the check fails, the build stops."
- Say what you believe. Cut hedges ("it could be argued", "in some cases it may be
  possible"). If something is uncertain, say what is unknown and why, once.
- Never refer by position ("above", "below", "the following table", "as mentioned
  earlier"). Name the target and link it, or repeat the snippet.
- Banned words: "simply", "just" (as a minimizer), "obviously", "clearly", "easy" or
  "easily" (about the reader's effort), "leverage", "utilize", "delve", "via" (write
  "through"), Latin abbreviations ("e.g.", "i.e.", "etc."; write "for example", "that is",
  or finish the list).
- Describe the thing being replaced with respect: what it does today and what changes,
  never that it is bad.

### Paragraphs and emphasis

- Paragraphs are one to three sentences, four at most. If a paragraph holds two ideas,
  split it.
- A one-sentence paragraph is the emphasis tool. Use it for turns and conclusions.
- **Bold whole sentences** for the takeaways a skimmer must not miss, at most one or two
  per section. Reading only the bold text should give a correct summary.
- *Italics* stress the one word the reader would stress out loud.
- Never bold or italicize for decoration.

### Concrete before abstract

- Show the example, the code or the drawing first; explain it after.
- Use one running example through the whole piece and evolve it. A new example per
  section makes the reader rebuild context each time.
- Cut what the reader already knows ("PDF is a common file format…") and anything that
  does not serve the one thing this piece teaches. Link out instead.
- Recommend one path. Mention an escape hatch only if it matters.

### Code samples

- Introduce each sample with a sentence ending in a colon. In reference docs, the sample's
  first line is a comment with its file path.
- Keep samples minimal. Replace what is not the point with a comment
  (`// 10 lines of input validation`).
- Annotate key lines with short plain comments ("// correct", "// forgot to pass props").
  No emoji.
- **Samples must agree with each other.** Before writing one, read the samples that
  already exist for the same types, keys and files, and match their spelling, signatures
  and order of effects. A sample that contradicts another page teaches the wrong thing
  with more authority than prose.
- Mark names you made up as illustrative, once, in the sentence that introduces the
  sample.
- When the text returns to a snippet after several paragraphs, paste it again.

### Tables and lists

- **A table is for looking up or comparing.** Put a sentence before it, ending in a colon,
  that says what it shows.
- One line per cell. A cell over about 40 words is a paragraph in the wrong place: give
  that row its own heading and the text under it.
- A two-column table of name and description is a list.
- A directory layout is a nested list or tree, with a short note per entry.

## Reviewing a draft

1. Decide the mode of the draft, and say so if it mixes the two.
2. Run `python -I <this skill's folder>/scripts/check_text.py <file>` (Markdown or HTML). It lists candidate
   problems: long paragraphs, banned words, long headings, references by position, long
   table cells, and in reference docs, long headings and time words. It skips code,
   blockquotes and words in double quotes, but it cannot judge meaning, so read each hit
   before calling it a defect.
3. Walk the checklist for the mode, item by item, and cite the rule each problem breaks.
   The two problems reviewers miss most are paragraph length and passive voice as the
   default.
4. Before trimming sentences, measure where the words are. In dense docs, most words sit
   in tables and lists, and trimming prose saves a few percent. Restructure instead: split
   by subject, move detail under headings, partition long tables.
5. **Every rewrite must itself pass the checklist.** It's tempting to write "highest-leverage"
   or "easy to misuse" inside the very fix that removes those words. Run the script on your
   rewrite too.

## Checklist

Both modes:

- [ ] Each heading names one thing, with no private labels.
- [ ] Each concept has one word, defined where it is first used.
- [ ] Every paragraph has at most four sentences, and most have three or fewer.
- [ ] Bold text alone gives a correct summary.
- [ ] Examples and code come before their explanation, and all samples agree.
- [ ] No banned words, no hedges, no "above" or "below".
- [ ] Every table has a sentence before it, and no cell runs past about 40 words.

Then the checklist for the mode, at the end of [references/explainers.md](references/explainers.md)
or [references/reference-docs.md](references/reference-docs.md).

## Files

- [references/explainers.md](references/explainers.md): voice, hooks, structure, engaging
  the reader and endings for posts and tutorials.
- [references/reference-docs.md](references/reference-docs.md): page shape, claims, long
  registers and the onboarding pages for docs and design docs.
- [examples.md](examples.md): before/after rewrites for both modes, and a skeleton for each.
- [scripts/check_text.py](scripts/check_text.py): finds candidate problems in a Markdown or
  HTML file.
