# Writing style

Read this before writing a page, and again before the Phase 6 audit. These rules came from
readers of the Synapse Next docs: people who had to build from them and found the words too
long, the structure hard to navigate and the drawings pretty but not explanatory. The test
for every page is one question: **could a developer on their first day read this page and
know what to do next?**

## Names: short, plain, one word per thing

- **A name names the thing. The explanation goes under it.** Page titles and headings are two
  to four words. The sentence that was squeezed into the heading becomes the first line of
  the text.

  | Not | But |
  |---|---|
  | Device pages: geometry, layout and rendering | Device pages |
  | Contracts (S-1 to S-14) | Contracts |
  | Why a monorepo is the right base for agents (evidence to 2026) | Why a monorepo |
  | Prior art: what A, B, C, D and E teach | Prior art |

- **No ids in titles or headings.** Ids belong in tables and references.
- **One word per concept, everywhere.** Pick the word once and use it in the sidebar, the
  headings, the body and the id. Three words for one thing ("seam", "contract", "interface")
  reads as three things. If a word changes, change it everywhere in the same pass, including
  the id prefix.
- **The id prefix matches the word.** A pattern is `FP-`, a contract is `C-`. A prefix nobody
  can expand from the word is a defect.
- **No private labels.** `W1`, `H1`, `F2` for scenarios or flows mean nothing to a reader.
  A scenario is known by its title ("The user changes DPI on a wired mouse"), and other text
  refers to it by that name, as a link.
- **Prefer the reader's word to the builder's.** "Background service" is not better than
  "daemon" if the body says daemon throughout and another process is the real Windows
  service: check that a friendlier name does not collide with something else in the system.
- **Define every term where it is first used, and in the glossary.** A word used 200 times
  and never defined ("codec") is the most common defect. Abbreviations get their long form
  once ("codec, short for coder-decoder").

## Every page has the same shape

1. **A claim** in one to three short sentences (at most 50 words). It states what is true,
   not what the page contains. "A feature is written once, in one folder. Every product that
   names it gets the control, the checks and the tests." If the design credits a reference,
   the credit comes last, not first.
2. **"Read this page to…"** One paragraph: who it is for, what they will learn, and what the
   page leaves out with a link to where that lives.
3. **The drawing that answers the page's question** (see `visual-rules.md`, "Which drawing").
4. **The body**, in sections with short headings.
5. **"What to read next"**: three to five links, each with a clause saying why.

Every section inside a page also opens with its own claim. A section that opens with a
table, a figure or a description of the old system has no claim yet.

A page description (the line under the title in an index or sidebar card) is one short line,
about ten words.

## The pages a design always has

Beyond the section skeletons in `design-docs.md`, three pages exist because readers asked
"how would a new developer know how this works?":

- **Developer guide**, second in the reading order. The system as a small number of
  divisions (what each does and never does), how the divisions talk (one row per link:
  what crosses it, which contract), one user action followed end to end as a sequence
  drawing with a numbered list, the eight to ten words that carry the design, "where your
  code goes" (to do this → you change → read), and a reading order.
- **Adding a <thing>** as a full walkthrough, one page per kind of thing. It opens with the
  claim that makes the design worth it (what is written once), then: what you write and what
  the build gives back for each file; numbered steps, each with its file path and real code
  on the running example; which running part uses which file; what happens at run time; the
  rules; what to do when nothing fits. If something must be chosen (a pattern, a family),
  the page says how to choose, with the questions in order.
- **How the work gets done** (for a rewrite: the porting strategy). What is moved in what
  order and why that order, one unit of work as a swimlane with a lane for the person and a
  lane for the agent, and a table of what stays with a person and why. "AI-first" never
  means unattended: say who starts each step and who judges what proof cannot.

If the system has a user interface, an architecture page for it shows **what the screens
look like** (wireframes), who decides each part of a screen, the layers, and the path from
a definition to pixels.

## Sentences and words

- Assertive present tense: "The daemon owns every device handle." Hedges go to the risk
  register.
- Short sentences, one idea each. Condition first: "When a check is red, the agent tries
  again."
- No "simply", "just", "easily". No "via" (through). No "once" meaning "after". No Latin
  abbreviations.
- Never refer by position: no "above", "below", "the following table". Name the target and
  link it.
- A section number in running text is shown as the section's name. The source may keep the
  number; the reader sees the name.
- Describe the system being replaced with respect: say what it does today and what changes,
  never that it is bad.
- Timeless: no "currently", "new", "soon".

## Tables, lists and long text

- **A table is for looking up or comparing.** Every table has a sentence before it, ending
  in a colon, that says what it shows.
- **One line per cell.** A cell over about 40 words is a paragraph in the wrong place. Give
  that row its own heading and put the text under it, or keep a one-line cell and move the
  detail to a block.
- **A two-column table of name and description is a list**, or headed blocks when each
  description is a rule.
- **Long registers are an index plus blocks.** Sixty decisions in one table is unreadable.
  Group them by subject (five to eight groups, a page each). Each entry is a heading with
  the full text and its basis. Generate the one-line index from the blocks; never write the
  summary by hand, because hand-written lines drift from the text they summarise.
- **Before trimming sentences, measure where the words are.** In a specification most words
  sit in fact-dense cells, and trimming prose saves a few percent. Reading load falls when
  structure changes: split by subject, move detail under headings, partition a long table
  by category.
- A directory layout is a tree component (nested list, folder and file icons, a notes
  column), never box-drawing characters in a code block.

## Code samples

- Every sample is introduced by a sentence ending in a colon and carries its file path as
  its first line.
- **Samples must agree with each other.** Before writing a sample, read the samples the docs
  already have for the same types, keys and files, and match them: the same key spelling
  (`polling_rate`, not `polling-rate`), the same trait form, the same effect order. A sample
  that contradicts another page teaches the wrong thing with more authority than prose.
- A sample shows one layer doing its own job. If the core is pure, its sample does not call
  the codec; if intent is stored before the device is written, the sample's order shows it.
- Names the design has not fixed are marked as illustrative, once, in the sentence that
  introduces the example. Do not invent ids, constructors or fields silently.

## Checks to run on the text (Phase 6)

Count these on every page and fix what fails. A script is quicker than reading:

| Check | Pass |
|---|---|
| Page and section open with a claim | every one |
| Headings over four words | none without a reason |
| Ids or private labels in titles and headings | none |
| Terms used but not in the glossary | none |
| Words for the same concept | one |
| Table cells over 40 words | none |
| Tables with no sentence before them | none |
| "above", "below", bare section numbers in prose | none |
| Code samples that disagree on a name, key or order | none |
| Pages with no "What to read next" | none |
