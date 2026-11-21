"""Regenerate assets/doc-template.html from the Synapse Next documents, so new designs share
their exact CSS, theme toggle, arrow markers and id-linking script."""
import sys
SRC, OUT = sys.argv[1], sys.argv[2]
plan = open(SRC + '/synapse-next-master-plan.html', encoding='utf-8').read()
arch = open(SRC + '/synapse-next-architecture.html', encoding='utf-8').read()

head = plan[:plan.index('</head>') + 7]
t0 = head.index('<title>'); t1 = head.index('</title>') + 8
head = head[:t0] + '<title>__TITLE__</title>' + head[t1:]

# Docs-site layout for a single HTML file: the Synapse Next site's sidebar (document switcher,
# section TOC with the active section, legend with typed boundaries), figure hover and glossary
# term cards. Same classes and behaviour as architecture-report/template.html.
LAYOUT = r'''<style>
/* docs-site layout */
.layout{display:grid;grid-template-columns:256px minmax(0,1fr);min-height:100vh}
.side{position:sticky;top:0;height:100vh;overflow-y:auto;border-right:1px solid var(--line);padding:22px 14px 28px;font-size:13.5px;background:var(--bg)}
.brand{display:block;font-weight:700;font-size:15px;letter-spacing:-.01em;color:var(--fg);margin:0 0 4px}
.side-h{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--mute);font-weight:600;margin:18px 0 6px}
.docs a,.toc a{display:flex;gap:8px;align-items:baseline;color:var(--mute);padding:3px 6px;border-radius:5px;line-height:1.4}
.docs a[aria-current="page"]{color:var(--fg);font-weight:600}
.toc a i{font:600 11px/1.6 var(--mono);font-style:normal;opacity:.8;min-width:18px}
.docs a:hover,.toc a:hover{color:var(--fg);text-decoration:none}.toc a.active{color:var(--fg);font-weight:600;background:var(--code)}
.side nav{display:block}.side .legend{flex-direction:column;gap:6px;margin:0}
.layout>main{max-width:940px;margin:0 auto;padding:56px 40px 112px;min-width:0;width:100%}
.lg-b-process{background:var(--code);border-color:var(--line2)!important}.lg-b-code{border-style:dotted!important;border-color:var(--ui)!important}
.lg-b-trust{border-style:dashed!important;border-color:var(--warn)!important}.lg-b-machine{border-style:dashed!important;border-color:var(--mute)!important}
.lg-b-network{border-style:dotted!important;border-color:var(--mute)!important}
@media (max-width:960px){.layout{display:block}.side{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line);padding:56px 16px 16px}
.side nav{display:flex;flex-wrap:wrap;gap:2px 6px}.side .legend{flex-direction:row}.layout>main{padding:40px 16px 96px}.theme-toggle{position:absolute}}
@media print{.side{display:none}.layout{display:block}}
/* typed boundaries: <g class="bd b-process|b-code|b-trust|b-machine|b-network"><rect/><text/></g> */
svg .bd rect{fill:none;stroke-width:1.5}svg .bd text{font-size:11.5px;font-weight:600;fill:var(--mute)}
svg .b-process rect{fill:var(--code);stroke:var(--line2)}svg .b-code rect{stroke:var(--ui);stroke-dasharray:2 3}svg .b-code text{fill:var(--ui)}
svg .b-trust rect{stroke:var(--warn);stroke-dasharray:7 4}svg .b-trust text{fill:var(--warn)}
svg .b-machine rect{stroke:var(--mute);stroke-dasharray:14 5}svg .b-network rect{stroke:var(--mute);stroke-dasharray:2 4}
/* figure hover: <g class="n .." data-n="id" data-d="detail">, edges and labels carry data-e="from to" */
svg .n[data-n]{cursor:pointer}svg .n rect,svg .ar,svg .arw,svg .lbl{transition:opacity .15s}
svg.dim .n:not(.on):not(.peer){opacity:.55}svg.dim .ar:not(.on),svg.dim .arw:not(.on),svg.dim .lbl:not(.on){opacity:.35}svg .n.on rect{stroke-width:2.4}
/* glossary terms: <a class="term" href="#g-x"> to a glossary row <tr id="g-x"> */
a.term{color:inherit;text-decoration:underline dotted color-mix(in srgb,var(--acc) 70%,transparent);text-underline-offset:3px;text-decoration-thickness:1.5px;cursor:pointer}
a.term:hover,a.term[aria-expanded="true"]{text-decoration-style:solid;color:var(--acc)}
.tip{position:fixed;z-index:50;max-width:min(340px,calc(100vw - 24px));background:var(--card);color:var(--fg);border:1px solid var(--line2);border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.18);padding:11px 14px;font-size:13px;line-height:1.5}
.tip:not(.pin){pointer-events:none}.tip.pin{max-height:min(70vh,520px);overflow:auto}
.tip b{display:block;font-size:13.5px;font-weight:650;margin:0 0 3px;padding-right:22px}.tip p{margin:4px 0;max-width:none}.tip ul{margin:6px 0 0;padding:0;list-style:none}
.tip small{display:block;margin-top:6px;color:var(--mute);font-size:12px}
.tip .x{position:absolute;top:7px;right:7px;width:24px;height:24px;border:0;border-radius:6px;background:none;color:var(--mute);font-size:17px;cursor:pointer}.tip .x:hover{background:var(--code);color:var(--fg)}
</style>
<script>
document.addEventListener("DOMContentLoaded",function(){
 var $=function(s,r){return(r||document).querySelectorAll(s)},T=function(e){return e?(e.textContent||"").replace(/\s+/g," ").trim():""};
 /* section TOC from <section id><h2><span class="num">n</span>Title</h2>, with the active section */
 var toc=document.querySelector(".toc"),links={},secs=[];
 if(toc)$("main section[id]").forEach(function(s){var h=s.querySelector("h2");if(!h)return;var n=h.querySelector(".num"),a=document.createElement("a");
  a.href="#"+s.id;a.innerHTML="<i></i><span></span>";a.firstChild.textContent=T(n);a.lastChild.textContent=h.dataset.toc||T(h).slice(T(n).length).trim();toc.appendChild(a);links[s.id]=a;secs.push(s)});
 if(toc&&"IntersectionObserver"in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;var id=e.target.closest("section").id;
   $(".toc a.active").forEach(function(a){a.classList.remove("active")});links[id]&&links[id].classList.add("active")})},{rootMargin:"0px 0px -70% 0px"});
  secs.forEach(function(s){io.observe(s.querySelector("h2"))})}
 /* one floating card: hover previews, click pins; Esc, x or outside click closes */
 var tip=document.createElement("div");tip.className="tip";tip.hidden=true;document.body.appendChild(tip);var pinned=null;
 function place(el){var r=el.getBoundingClientRect(),w=tip.offsetWidth,h=tip.offsetHeight,x=Math.min(Math.max(8,r.left),innerWidth-w-8),y=r.bottom+8;if(y+h>innerHeight-8)y=Math.max(8,r.top-h-8);tip.style.left=x+"px";tip.style.top=y+"px"}
 function show(el,html,pin){tip.innerHTML=html;tip.classList.toggle("pin",!!pin);tip.hidden=false;place(el);
  if(pin){var x=document.createElement("button");x.className="x";x.type="button";x.setAttribute("aria-label","Close");x.textContent="×";x.onclick=close;tip.prepend(x);pinned=el;el.setAttribute("aria-expanded","true")}}
 function hide(){if(!pinned)tip.hidden=true}
 function close(){if(pinned)pinned.removeAttribute("aria-expanded");pinned=null;tip.hidden=true}
 document.addEventListener("keydown",function(e){if(e.key==="Escape")close()});
 document.addEventListener("click",function(e){if(pinned&&!tip.contains(e.target)&&e.target.closest("a.term")!==pinned)close()});
 addEventListener("scroll",function(){if(!tip.hidden&&!pinned)tip.hidden=true},{passive:true});
 function def(a){var t=document.getElementById((a.getAttribute("href")||"").slice(1));if(!t)return null;
  if(t.tagName==="TR"){var c=t.querySelectorAll("td");return"<b>"+(c[0]?c[0].innerHTML:"")+"</b><p>"+(c[1]?c[1].innerHTML:"")+"</p>"}
  if(t.tagName==="DT"){var d=t.nextElementSibling;return"<b>"+t.innerHTML+"</b><p>"+(d?d.innerHTML:"")+"</p>"}return null}
 $("a.term").forEach(function(a){
  a.addEventListener("mouseenter",function(){if(!pinned){var d=def(a);d&&show(a,d+"<small>Click to pin</small>")}});
  a.addEventListener("mouseleave",hide);
  a.addEventListener("click",function(e){var d=def(a);if(!d)return;e.preventDefault();e.stopPropagation();close();show(a,d+'<small><a href="'+a.getAttribute("href")+'">Glossary entry</a></small>',true)})});
 $("figure svg").forEach(function(svg){
  $(".n[data-n]",svg).forEach(function(n){var id=n.dataset.n,ed=[].filter.call($("[data-e]",svg),function(e){return e.dataset.e.split(" ").indexOf(id)>=0});
   if(!ed.length)return;n.setAttribute("tabindex","0");
   function on(){svg.classList.add("dim");n.classList.add("on");var li=[];
    ed.forEach(function(e){e.classList.add("on");var p=e.dataset.e.split(" "),o=p[0]===id?p[1]:p[0],pn=svg.querySelector('.n[data-n="'+o+'"]');pn&&pn.classList.add("peer");
     if(e.classList.contains("lbl")){var t=pn&&pn.querySelector(".tt");li.push("<li>"+(p[0]===id?"→ ":"← ")+(t?T(t):o)+": "+T(e)+"</li>")}});
    var tt=n.querySelector(".tt");if(!pinned)show(n,"<b>"+(tt?T(tt):id)+"</b>"+(n.dataset.d?"<p>"+n.dataset.d+"</p>":"")+(li.length?"<ul>"+li.join("")+"</ul>":""))}
   function off(){svg.classList.remove("dim");$(".on,.peer",svg).forEach(function(e){e.classList.remove("on","peer")});hide()}
   n.addEventListener("mouseenter",on);n.addEventListener("mouseleave",off);n.addEventListener("focus",on);n.addEventListener("blur",off)})});
});
</script>
'''
head = head.replace('</head>', LAYOUT + '</head>')
defs = arch[arch.index('<svg width="0" height="0"'):]
defs = defs[:defs.index('</svg>') + 6]
tail = plan[plan.index('</main>'):].replace('synapse 4|', 'current system|').replace('</main>', '</main>\n</div>', 1)


def box(cls, x, y, w, h, title, sub=None, nid=None, detail=None):
    attrs = (' data-n="%s"' % nid if nid else '') + (' data-d="%s"' % detail if detail else '')
    s = '<g class="n %s"%s transform="translate(%d,%d)"><rect width="%d" height="%d" rx="6"/>' % (cls, attrs, x, y, w, h)
    s += '<text class="tt" x="12" y="22">%s</text>' % title
    if sub: s += '<text class="ts" x="12" y="40">%s</text>' % sub
    return s + '</g>'


fig = (
    '<svg viewBox="0 0 900 240" role="img" aria-label="__CLAIM: the settings UI sends a request over C-1 to the router inside the daemon process; the router hands it to the keyboard actor, which writes a report to the device and persists the applied value to the store.__">\n'
    '<g class="bd b-process"><rect x="200" y="20" width="470" height="200" rx="10"/><text x="216" y="42">daemon · one process</text></g>\n'
    + box('ui', 20, 70, 150, 56, 'Settings UI', 'client · view only', 'ui', 'Shows state; never touches a device.') + '\n'
    + box('mw', 220, 70, 200, 56, 'Router', 'feature → device', 'router', 'Stateless; resolves the target actor.') + '\n'
    + box('mw', 450, 70, 200, 56, 'Keyboard actor', 'one per device', 'kb', 'The only writer for its device (I-1).') + '\n'
    + box('store', 450, 150, 200, 50, 'Store', 'intent + applied', 'store') + '\n'
    + box('native', 720, 70, 160, 56, 'Device', 'USB HID', 'dev') + '\n'
    + '<path class="ar" data-e="ui router" d="M170 98 H218" marker-end="url(#ah)"/><path class="ar" data-e="router kb" d="M420 98 H448" marker-end="url(#ah)"/>'
    + '<path class="ar" data-e="kb dev" d="M650 98 H718" marker-end="url(#ah)"/><path class="ar d" data-e="kb store" d="M550 126 V148" marker-end="url(#ah)"/>\n'
    + '<text class="lbl" data-e="ui router" x="194" y="88" text-anchor="middle">C-1</text><text class="lbl" data-e="kb dev" x="684" y="88" text-anchor="middle">report</text>'
    + '<text class="lbl" data-e="kb store" x="560" y="141">persist</text>\n'
    + '</svg>'
)

body = '''<body>

''' + defs + '''

<!--
  TEMPLATE for documents produced by the system-design-from-references skill.
  Copy this file, replace every __PLACEHOLDER__, delete the sections you do not need, and keep
  the markup patterns: they are the Synapse Next documents' own, so the CSS above styles them.

  Diagram vocabulary (inside <svg>):
    <g class="n KIND" transform="translate(x,y)"><rect width height rx="6"/>
      <text class="tt" x="12" y="22">Title</text><text class="ts" x="12" y="40">subtitle</text>
      (each further subtitle line +16; height = last baseline + 12 or more, so text never touches the edge)
    KIND: ui (UI and clients) · mw (core) · svc (supporting services) · store (state and IPC)
          native (hardware, sidecars, privileged) · warnb (warning / problem)
    arrows: <path class="ar" d="..." marker-end="url(#ah)"/>   add class "d" for async/dashed
            <path class="arw" ... marker-end="url(#ahw)"/>      warning-coloured arrow
    arrow labels: <text class="lbl">  (has a halo, safe over lines)   band label: <text class="bl">
    typed boundaries: <g class="bd b-process|b-code|b-trust|b-machine|b-network"><rect/><text/></g>
      (older untyped forms: <rect class="band">, <rect class="frame">, <line class="wall">)
    sequence diagrams: <line class="life"> lifelines, <text class="tm"> timings
    hover: data-n="id" data-d="one-line detail" on a box <g>; data-e="from to" on its arrows and
      arrow labels. Hover dims the rest lightly and shows one card listing the box's connections.
  Draw order: boundaries, boxes, arrows, labels. Arrow ends touch box edges.

  Layout: the sidebar lists both documents (mark the current one aria-current="page"); its TOC is
  built from <section id><h2><span class="num">; keep only the legend entries a document uses.
  Glossary terms: <a class="term" href="#g-x">word</a> -> glossary row <tr id="g-x">; hover
  previews, click pins.

  Content vocabulary: p.statement · p.lede · div.tablewrap > table.dense · div.cards > div.card
    div.kpis > div.kpi · div.contract (with span.sid, ol.steps, p.purpose) · div.flow > div.step
    pre > code with span.k (keyword) .t (type) .s (string) .c (comment) .f (function)
    div.bytes (wire layout) · p.note · table.dense.glossary
  Ids D#, C-#, I-#, E#, M# in the first cell of a table row become link targets; mentions of them
  anywhere in the text are linked with a popover card by the script at the end.
-->

<div class="layout">
<aside class="side">
  <a class="brand" href="#top">__DESIGN NAME__</a>
  <div class="side-h">Documents</div>
  <nav class="docs" aria-label="Documents">
    <a href="__DESIGN__-architecture.html" aria-current="page">Architecture</a>
    <a href="__DESIGN__-master-plan.html">Build plan</a>
  </nav>
  <div class="side-h">On this page</div>
  <nav class="toc" aria-label="Sections"></nav>
  <div class="side-h">Legend</div>
  <div class="legend" aria-label="Diagram colour key">
    <span><i class="lg-ui"></i>UI and clients</span>
    <span><i class="lg-mw"></i>Core</span>
    <span><i class="lg-svc"></i>Supporting services</span>
    <span><i class="lg-store"></i>State and IPC</span>
    <span><i class="lg-native"></i>Hardware, sidecars, privileged</span>
    <span><i class="lg-b-process"></i>Process boundary</span>
    <span><i class="lg-b-trust"></i>Trust boundary</span>
    <span><i class="lg-b-machine"></i>Machine boundary</span>
  </div>
</aside>
<main id="top">
<header class="hero">
  <h1>__TITLE__</h1>
  <p class="sub"><b>__DOCUMENT ROLE: "Architecture: what we build and why." or "Build plan: how and when."__</b> The companion document is <a href="__OTHER__.html">__OTHER TITLE__</a>.</p>
  <p class="sub">__Two or three assertive sentences: what the system is, its shape, and the one idea that makes it work. Name an <a class="term" href="#g-actor">actor</a> as a glossary term.__</p>
</header>

<!-- 1 -->
<section id="system">
<h2><span class="num">1</span>System</h2>
<p class="statement">__One paragraph that states the design as fact.__</p>
<figure>
''' + fig + '''
<figcaption>__What the picture proves, in one or two sentences, citing ids (D1, I-1).__</figcaption>
</figure>
<div class="tablewrap"><table class="dense">
<tr><th>Component</th><th>Owns</th><th>Guarantees</th><th>Appears in diagrams as</th></tr>
<tr><td><b>Device actor</b></td><td>__one device: its links and settings__</td><td>__one command at a time__</td><td>Keyboard actor, Mouse actor</td></tr>
<tr><td><b>Router</b></td><td>__nothing; it is stateless__</td><td>__every request reaches exactly one actor__</td><td>Router</td></tr>
</table></div>
<div class="cards">
  <div class="card"><h4>__Point__</h4><p>__One short paragraph.__</p></div>
  <div class="card"><h4>__Point__</h4><p>__One short paragraph.__</p></div>
  <div class="card"><h4>__Point__</h4><p>__One short paragraph.__</p></div>
</div>
</section>

<!-- 2 -->
<section id="decisions">
<h2><span class="num">2</span>Decisions</h2>
<p class="lede">Every decision adopts a mechanism described in the reference architecture reports, or a blend of them; the target's constraints only choose between them.</p>
<div class="tablewrap"><table class="dense">
<tr><th>#</th><th>Decision</th><th>Basis</th><th>Owner</th></tr>
<tr><td>D1</td><td><b>__Topic.__</b> __The decision, stated as fact.__</td><td>__name-architecture.html#section__</td><td>__Area__</td></tr>
<tr><td>D2</td><td><b>__Topic.__</b> __The decision.__</td><td>__name-architecture.html#section; other-architecture.html#section__</td><td>__Area__</td></tr>
</table></div>
</section>

<!-- 3 -->
<section id="interfaces">
<h2><span class="num">3</span>Interfaces</h2>
<p class="lede">__Every contract between components, what crosses it, and how it versions.__</p>
<div class="contract" id="s1">
<h4><span class="sid">C-1</span>__UI ↔ daemon__</h4>
<p class="purpose"><b>Purpose:</b> __what crosses this contract and why it exists.__</p>
<pre><code><span class="k">pub enum</span> <span class="t">Request</span> {
    <span class="t">SetSetting</span> { device: <span class="t">DeviceId</span>, key: <span class="t">Key</span>, value: <span class="t">Value</span> },   <span class="c">// replaces any older value for the same key</span>
}</code></pre>
</div>
<div class="tablewrap"><table class="dense">
<tr><th>#</th><th>Contract</th><th>Encoding</th><th>Versioning</th></tr>
<tr><td>C-1</td><td>__UI ↔ daemon__</td><td>__length-prefixed protobuf__</td><td>__additive only; N and N-1 both served__</td></tr>
</table></div>
<div class="tablewrap"><table class="dense">
<tr><th>#</th><th>Invariant</th><th>Proved by</th></tr>
<tr><td>I-1</td><td>__One writer per device.__</td><td>__property test + scenario w1__</td></tr>
</table></div>
</section>

<!-- 4 -->
<section id="walkthroughs">
<h2><span class="num">4</span>Walkthroughs</h2>
<p class="lede">__The running example, traced hop by hop.__</p>
<div class="contract" id="w1">
<h4>__The user changes one setting on the example product__</h4>
<ol class="steps">
<li>__The UI sends a request over C-1.__</li>
<li>__The router resolves the device and hands the request to its actor (D1).__</li>
<li>__The actor writes the report; the store records the applied value (I-1).__</li>
</ol>
<p class="purpose"><b>If the device doesn't answer:</b> __what the user sees and what retries.__</p>
</div>
<div class="flow">
  <div class="step"><b>__Stage__</b><span>__what happens__</span></div>
  <div class="step"><b>__Stage__</b><span>__what happens__</span></div>
  <div class="step"><b>__Stage__</b><span>__what happens__</span></div>
</div>
</section>

<!-- 5 -->
<section id="roadmap">
<h2><span class="num">5</span>Milestones and gates</h2>
<div class="kpis">
  <div class="kpi"><b>__≤ 1 day__</b><span>__metric and when it applies__</span></div>
  <div class="kpi"><b>__≥ 95%__</b><span>__metric and when it applies__</span></div>
</div>
<div class="tablewrap"><table class="dense">
<tr><th>#</th><th>Milestone</th><th>Weeks</th><th>Exit criteria</th></tr>
<tr><td>M1</td><td>__First device end to end__</td><td>__4–8__</td><td>__observable criteria__</td></tr>
</table></div>
<div class="tablewrap"><table class="dense">
<tr><th>#</th><th>Epic</th><th>Lane</th><th>Depends on</th><th>Done when</th></tr>
<tr><td>E1</td><td>__Core runtime__</td><td>__A__</td><td>__–__</td><td>__The setting-change scenario runs green in the simulator__</td></tr>
</table></div>
</section>

<!-- A -->
<section id="glossary">
<h2><span class="num">A</span>Glossary</h2>
<div class="tablewrap"><table class="dense glossary">
<tr><th>Term</th><th>Meaning</th></tr>
<tr id="g-actor"><td><b>Actor</b></td><td>__One task that owns one thing (here, one device) and handles its messages one at a time.__</td></tr>
<tr id="g-acronym"><td><b>__ACRONYM__</b></td><td>__Expansion: what it means here__</td></tr>
</table></div>
</section>

<!-- B -->
<section id="sources">
<h2><span class="num">B</span>References</h2>
<ul>
<li><a href="__name__-architecture.html">__Reference report__</a>: __what it taught this design__</li>
</ul>
<p class="note">Clean room: every decision in this design comes from the reference architecture reports above; no reference source code was read by the design side.</p>
</section>

'''
open(OUT, 'w', encoding='utf-8').write(head + '\n' + body + tail)
print('wrote', OUT, len(head + body + tail), 'bytes')
