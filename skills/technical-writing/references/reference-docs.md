# Reference docs

READMEs, docs pages, design docs, specs, runbooks and API guides. The reader arrives from a
search or a sidebar, reads a section, leaves and comes back. The test for every page is one
question: **could someone on their first day read this page and know what to do next?**

The core rules in `SKILL.md` still apply. This file adds what is specific to reference docs.

## Page shape

1. **A claim** in one to three short sentences, at most 50 words. It states what is true,
   not what the page contains. "A feature is written once, in one folder. Every product
   that names it gets the control, the checks and the tests." Credits to prior work come
   last, not first.
2. **"Read this page to…"**: one paragraph saying who it is for, what they will learn, and
   what the page leaves out, with a link to where that lives.
3. **The picture that answers the page's question**, if one exists: a diagram of what runs
   where, a sequence of what happens in order, a screenshot or wireframe of a screen, a
   table of options. Number the steps in a diagram and repeat the numbers in the text. A
   drawing the reader cannot explain back has failed, however tidy it is.
4. **The body**, in sections with short headings.
5. **"What to read next"**: three to five links, each with a clause saying why.

Every section inside a page also opens with its own claim. A section that opens with a
table, a figure or a history of the old system has no claim yet.

A page description (the line under a title in an index, sidebar or card) is one short line,
about ten words.

## Headings

Headings are two to four words and carry no ids. The detail moves into the first line:

| Not | But |
|---|---|
| Device pages: geometry, layout and rendering | Device pages |
| Contracts (C-1 to C-14) | Contracts |
| Why a monorepo is the right base for agents (evidence to 2026) | Why a monorepo |
| Prior art: what A, B, C, D and E teach | Prior art |

Ids belong in tables and in references to a row, never in titles.

## Ids

When a doc numbers its things (decisions, requirements, endpoints, error codes):

- **The prefix matches the word the docs use.** A decision is `D-`, a contract is `C-`. A
  prefix nobody can expand from the word is a defect.
- Name the kind of thing first, then derive the prefix from the name.
- Never renumber a published id. Append instead.

## Sentences

- Assertive present tense: "The scheduler owns every job's state", not "we could
  consider having the scheduler own…". Open questions go in one named place (an open-questions
  or risks section) with an owner, not scattered through the text as hedges.
- Timeless: no "currently", "new", "soon", "recently". The page is read for years.
- "You" for instructions. First person only for a decision record's "we chose".
- A section number in running text is shown as the section's name, as a link.

## Long content

- **Long registers are an index plus blocks.** Sixty decisions in one table is
  unreadable. Group entries by subject (five to eight groups), give each entry a heading
  with its full text, and generate the one-line index from the blocks. Never hand-write
  the summary, because hand-written lines drift from the text they summarize.
- **Measure before trimming.** Reading load falls when structure changes: split by
  subject, move detail under headings, partition a long table by category.
- A sample shows one layer doing its own job. If the core is pure, its sample does not
  call the network; if the job is saved before a worker picks it up, the sample's order
  shows that.

## The onboarding pages

A doc set for a system people will build on needs three pages besides the reference:

- **Developer guide**, second in the reading order. The system as a few parts (what each
  does and never does), how the parts talk, one user action followed end to end with a
  numbered sequence, the eight to ten words that carry the design, "where your code goes"
  (to do this → you change → read), and a reading order.
- **Adding a <thing>**, one page per kind of thing people add. It opens with what is
  written once, then numbered steps, each with its file path and real code on the running
  example, what happens at run time, the rules, and what to do when nothing fits. If the
  reader must choose something, the page says how to choose, with the questions in order.
- **How the work gets done**: who does each step, and what stays with a person and why. If
  agents do part of the work, say who starts each step and who judges what tests cannot.

## Reference checklist

- [ ] Every heading is two to four words, with no ids, colons or parentheses.
- [ ] Every page and every section opens with a claim.
- [ ] Every page has "Read this page to…" and ends with "What to read next".
- [ ] No "currently", "new", "soon"; no hedges outside the open-questions section.
- [ ] Every id prefix expands to the word the docs use.
- [ ] Every term used is in the glossary, if the docs have one.
- [ ] Long registers are split into groups with an index generated from them.
