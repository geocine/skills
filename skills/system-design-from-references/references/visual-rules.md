# Visual rules and audit

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
