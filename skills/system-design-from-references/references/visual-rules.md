# Visual rules and audit

## Which drawing

A drawing earns its place when the reader can say what happens after looking at it. A
drawing that is only tidy boxes fails that test, however good it looks. Start from the
question the page answers and pick the kind of drawing that answers it:

| The reader asks | Draw | It must show |
|---|---|---|
| What runs where, and what may cross? | **System design** drawing: processes as boxes inside typed boundary frames | Each box: name, `[kind · technology]`, one line of responsibility. Each arrow: a number, what crosses, and the contract id. One arrow per boundary crossing. |
| What happens, in what order? | **Sequence** drawing: one lifeline per part, grouped in frames by process | Numbered messages named as the real request, reply or event; a bar where a part is busy; a note for the main failure. The same steps as a numbered list under the drawing. |
| Who does what? | **Swimlane**: one lane per actor (person, agent, tool, proof) | Numbered steps in lanes; the loop that repeats without a person; the hand-offs. |
| How does this behave over time? | **Timing** drawing: time left to right, input rows above, output row last | Held spans as bars, marked moments as vertical lines with a label. For analog input, the value as a curve with its threshold lines. One drawing per rule. |
| What does the screen look like? | **Wireframe**: structure only, no styling | Each region labelled with who decides it (shell, layout data, a feature). |
| What do I write, and what uses it? | **Two-row map**: the running system on top, the author's files under the part that uses each | A verb on every vertical arrow (drawn from, checked against, calls). |
| How do the layers stack? | **Layer stack**: one full-width row per layer | Columns for what it holds and who writes it. |
| What is in this folder? | The **tree component**, not a drawing | Names, and a note per entry. |

Rules that apply to all of them:

- **Number the arrows** and repeat the numbers in the text. Readers follow numbers; they do
  not follow colour.
- **Do not let line style carry meaning** where arrows are animated (the docs site animates
  them as moving dashes): solid against dashed is then invisible. Use numbers, direction and
  labels.
- **A drawing and its list agree.** When a sequence is drawn and also listed, they have the
  same steps in the same order. Other drawings of the same flow elsewhere in the docs agree
  too: three drawings of one click that differ on when a value is stored is a defect.
- **The caption says how to read it** ("Read the numbers in order", "Time runs left to
  right") and states the one thing to take away.
- Look at every new drawing rendered before calling it done. Labels collide in ways the
  markup does not show.

## Diagrams

- **One figure, one claim.** Small, discussable diagrams; split anything over ~12 boxes.
- **Draw order**: boxes, then arrows, then labels on top. Arrow ends must touch the box edge
  they point at; labels sit beside arrows, never on top of a box.
- **Label arrows** with what moves (`set_dpi`, `frame · latest-wins`, `polls 30s`).
- **Legend** whenever colour or line style encodes something (component kind, sync vs async).
- **Typed boundaries**: every grouping rectangle says what kind of boundary it is —
  code, process, trust/privilege, machine, network — and the style differs per type.
- **Component identity**: a small tag on each box says which component type it is an
  instance of (actor, bus, store, io, service, client…), so every box maps to one component.
- **No clipped text**: text never touches or crosses a box edge; leave ≥ 6 px padding below
  the last line. Grow the box, don't shrink the font.
- **Theme**: colours as CSS variables with light and dark values; text and strokes readable
  on both.
- `<figure>` + `<figcaption>` stating the claim; `role="img"` and an `aria-label` that
  carries the same claim.
- No left-border accent stripes on cards; restrained colour; high signal-to-noise.

## Interactions (sites)

- Hover dims the other boxes only lightly (≈ 0.55 boxes, 0.35 arrows), shows one compact
  floating card positioned in the viewport (never inside the figure, never causing a
  scrollbar), and no card for boxes with no arrows. No native `title` tooltips on top.
- Scenario players: step controls, the moving pill must never cover a label.
- A player is compact: a scrubber in the control bar, then one line per step (number, name,
  route, proof status) that jumps to the step, then the detail of the current step only.
  The step list sits above the detail panel so it does not move as the detail changes
  length. The full text of every step stays in the Markdown copy.
- Inner pages open with a breadcrumb: group, sidebar heading, page, item.
- Two dividers never stack: a block that draws its own top line does not also get a
  heading with a top line.

## Audit (run in a real browser on every page and every player step)

For the two HTML documents, run the shared check script instead of this snippet:
`evaluate_script` with `sourcePath` = `../architecture-report/verify.js` (from this skill's
folder), at desktop width and at `390x844x2,mobile,touch`. It covers text overlap and
clipping, arrow ends touching boxes, anchors, glossary terms, the TOC, sideways scroll and
the theme toggle, and returns only failures.

For scenario players on the docs site, step through each player and paste this into the
page console (or run through a browser automation tool). It reports text
that overflows its box, text that touches a box bottom, and overlapping labels.

```js
(() => {
  const out = [];
  for (const svg of document.querySelectorAll('svg')) {
    const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim());
    const rects = [...svg.querySelectorAll('rect')];
    for (const t of texts) {
      const tb = t.getBoundingClientRect();
      const g = t.closest('g'); const own = g && g.querySelector(':scope > rect');
      if (own) {
        const rb = own.getBoundingClientRect();
        if (tb.right > rb.right - 2 || tb.left < rb.left + 2) out.push(['spills', t.textContent]);
        if (rb.bottom - tb.bottom < 4) out.push(['touches bottom', t.textContent]);
      } else {
        for (const r of rects) {
          const rb = r.getBoundingClientRect();
          const overlap = tb.left < rb.right && tb.right > rb.left && tb.top < rb.bottom && tb.bottom > rb.top;
          if (overlap && !(tb.left >= rb.left && tb.right <= rb.right && tb.top >= rb.top && tb.bottom <= rb.bottom))
            out.push(['crosses a box edge', t.textContent]);
        }
      }
    }
    for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++) {
      const a = texts[i].getBoundingClientRect(), b = texts[j].getBoundingClientRect();
      if (a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top)
        out.push(['overlaps', texts[i].textContent + ' / ' + texts[j].textContent]);
    }
  }
  for (const el of document.querySelectorAll('td, th, p, li, .card *'))
    if (el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflow !== 'visible') out.push(['clipped', el.textContent.slice(0, 60)]);
  return out.length ? out : 'clean';
})();
```

Boundary-band labels that intentionally sit on a band edge will show up as "crosses a box
edge"; check those by eye, then tighten the check if it is noisy. Step through every
scenario player and run it per step. Also check arrow endpoints visually at least once per
figure.
