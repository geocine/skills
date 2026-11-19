async () => {
  // Returns { ok, fail: [...] }. Run at desktop width, then again at 390px wide.
  const fail = [], $ = (s, r = document) => [...r.querySelectorAll(s)];
  await document.fonts.ready;
  if (!document.fonts.check('16px Inter')) fail.push('font: Inter not loaded');
  const de = document.documentElement;
  if (de.scrollWidth > de.clientWidth + 1) fail.push(`page scrolls sideways: ${de.scrollWidth} > ${de.clientWidth}`);
  const hit = (a, b, p = 0) => a.x < b.x + b.width - p && b.x < a.x + a.width - p && a.y < b.y + b.height - p && b.y < a.y + a.height - p;
  const inside = (a, b, p = 2) => a.x >= b.x + p && a.y >= b.y + p && a.x + a.width <= b.x + b.width - p && a.y + a.height <= b.y + b.height - p;
  $('svg[viewBox]').forEach((svg, si) => {
    const tag = svg.getAttribute('aria-label') || `svg#${si}`;
    if (!svg.getAttribute('role') || !svg.getAttribute('aria-label')) fail.push(`${tag}: needs role="img" and aria-label`);
    // screen coordinates, so boxes placed with transform="translate()" compare correctly
    const cr = el => { const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, width: r.width, height: r.height }; };
    const ts = $('text', svg).filter(t => t.textContent.trim());
    for (let i = 0; i < ts.length; i++) for (let j = i + 1; j < ts.length; j++)
      if (hit(cr(ts[i]), cr(ts[j]), 1)) fail.push(`${tag}: text overlaps "${ts[i].textContent}" / "${ts[j].textContent}"`);
    $('g', svg).forEach(g => {
      const r = g.querySelector(':scope > rect'); if (!r) return;
      const rb = r.getBBox();
      $(':scope > text', g).forEach(t => { if (!inside(t.getBBox(), rb)) fail.push(`${tag}: "${t.textContent}" spills out of or touches its box`); });
    });
    const boxes = $('g.nd > rect, g.n > rect', svg).map(cr);
    $('path.ar, path.arw, line.ar, line.arw', svg).forEach(p => {
      const L = p.getTotalLength(), M = p.getScreenCTM();
      const ends = [p.getPointAtLength(0), p.getPointAtLength(L)].map(q => new DOMPoint(q.x, q.y).matrixTransform(M));
      ends.forEach((e, k) => {
        const near = boxes.some(b => e.x >= b.x - 3 && e.x <= b.x + b.width + 3 && e.y >= b.y - 3 && e.y <= b.y + b.height + 3);
        if (!near) fail.push(`${tag}: arrow ${p.dataset.e || ''} ${k ? 'end' : 'start'} at ${Math.round(e.x)},${Math.round(e.y)} touches no box`);
      });
      const m = (p.getAttribute('marker-end') || '').match(/#([^)]+)/);
      if (m && !document.getElementById(m[1])) fail.push(`${tag}: missing marker #${m[1]}`);
    });
  });
  $('a[href^="#"]').forEach(a => { const id = a.getAttribute('href').slice(1); if (id && !document.getElementById(id)) fail.push(`broken anchor #${id}`); });
  $('a.term').forEach(a => { const t = document.getElementById(a.getAttribute('href').slice(1)); if (!t || !['DT', 'TR'].includes(t.tagName)) fail.push(`term "${a.textContent}" has no glossary entry (<dt> or <tr>)`); });
  const h2 = $('main h2[id]').length + $('main section[id] > h2:not([id])').length, toc = $('.toc a').length;
  if (h2 !== toc) fail.push(`TOC has ${toc} links for ${h2} sections`);
  const btns = $('.theme-toggle button');
  if (btns.length !== 3) fail.push('theme toggle missing');
  const node = document.querySelector('g.nd > rect, g.n > rect'), look = () => getComputedStyle(document.body).backgroundColor + '|' + (node ? getComputedStyle(node).fill : '');
  const seen = new Set();
  for (const b of btns) { b.click(); await new Promise(r => requestAnimationFrame(r)); seen.add(look()); }
  if (btns.length && seen.size < 2) fail.push('theme toggle does not change body background / box fill');
  const sys = btns.find(b => b.dataset.v === 'system'); sys && sys.click();
  const tg = document.querySelector('.theme-toggle');
  if (tg) $('h1, .brand, .toc a').forEach(e => { if (hit(tg.getBoundingClientRect(), e.getBoundingClientRect())) fail.push(`theme toggle covers "${e.textContent.trim().slice(0, 30)}" at ${innerWidth}px`); });
  return { width: innerWidth, ok: fail.length === 0, fail: fail.slice(0, 40), more: Math.max(0, fail.length - 40) };
}
