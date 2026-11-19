"""Package a single-file design (Output: single) for reading and deployment.

Mirrors what the React site's scripts/llms.mjs and netlify.toml produce, without Node:

  <docs>/site/                         the publish folder (generated; files are overwritten, never deleted)
    index.html                         redirects to the architecture document
    <design>-architecture.html         copied from source/, report links rewritten to references/
    <design>-master-plan.html          copied from source/, same rewrite
    references/<report>.html           every architecture report a document links to
    md/architecture.md                 each document as Markdown, sections in document order
    md/master-plan.md
    md/scenarios.md                    from src/scenarios/scenarios.json, when present
    llms.txt                           llmstxt.org index: what the design is + one link per file
    llms-full.txt                      everything above in one file
    robots.txt                         search engines out; llms files and md/ stay readable
  <docs>/netlify.toml                  publish = "site", noindex + UTF-8 headers (written once)

Usage (from herdr-architecture/):
  python -I .claude/skills/system-design-from-references/scripts/package_single.py <design>-docs [--base https://site.example]
--base (or env URL) makes the llms links absolute; otherwise they are relative.
"""
import glob, html, json, os, re, shutil, sys
from html.parser import HTMLParser

args = [a for a in sys.argv[1:] if not a.startswith('--')]
if not args:
    sys.exit(__doc__)
DOCS = os.path.abspath(args[0])
BASE = (sys.argv[sys.argv.index('--base') + 1] if '--base' in sys.argv else os.environ.get('URL', '')).rstrip('/')
abs_ = lambda p: f'{BASE}/{p}' if BASE else p

def one(pattern):
    hits = glob.glob(os.path.join(DOCS, 'source', pattern))
    if len(hits) != 1:
        sys.exit(f'expected exactly one source/{pattern}, found {len(hits)}')
    return hits[0]

ARCH, PLAN = one('*-architecture.html'), one('*-master-plan.html')
SITE = os.path.join(DOCS, 'site')
REFS_SRC = [os.path.join(DOCS, 'references'), os.path.dirname(DOCS)]  # vendored copy, then originals beside the project


# ---------- tiny DOM ----------
class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []
    def cls(self): return (self.attrs.get('class') or '').split()
    def find_all(self, pred):
        for k in self.kids:
            if isinstance(k, Node):
                if pred(k): yield k
                yield from k.find_all(pred)
    def text(self):
        return ''.join(k if isinstance(k, str) else k.text() for k in self.kids if not (isinstance(k, Node) and k.tag in ('script', 'style')))

VOID = {'br', 'hr', 'img', 'meta', 'link', 'input', 'source', 'wbr', 'col', 'path', 'rect', 'line', 'circle', 'polyline', 'polygon', 'ellipse', 'use', 'stop'}

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('root', {}); self.cur = self.root
    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur); self.cur.kids.append(n)
        if tag not in VOID: self.cur = n
    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))
    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag: n = n.parent
        if n is not self.root: self.cur = n.parent
    def handle_data(self, data):
        self.cur.kids.append(data)

def parse(path):
    p = Parser(); p.feed(open(path, encoding='utf-8').read()); return p.root


# ---------- HTML -> Markdown ----------
ws = lambda s: re.sub(r'\s+', ' ', s)

def inline(n):
    if isinstance(n, str): return ws(n)
    t = n.tag
    if t in ('script', 'style', 'svg', 'button'): return ''
    inner = ''.join(inline(k) for k in n.kids)
    if t in ('b', 'strong'): return f'**{inner.strip()}**' if inner.strip() else ''
    if t in ('i', 'em'): return f'*{inner.strip()}*' if inner.strip() else ''
    if t == 'code': return '`' + n.text().strip() + '`'
    if t == 'br': return '\n'
    if t == 'a':
        href = n.attrs.get('href', '')
        if not href or 'term' in n.cls(): return inner
        return f'[{inner.strip()}]({md_href(href)})'
    return inner

def md_href(h):
    m = re.match(r'(?:\.\./)*(?:references/)?([\w-]+-architecture\.html|[\w-]+\.html)(#.*)?$', h)
    if h.startswith('#'): return h
    if m and m.group(1) in (os.path.basename(ARCH), os.path.basename(PLAN)):
        return abs_('md/' + ('architecture' if m.group(1) == os.path.basename(ARCH) else 'master-plan') + '.md') + (m.group(2) or '')
    if m: return abs_('references/' + m.group(1)) + (m.group(2) or '')
    return h

def table(n):
    rows = []
    for tr in n.find_all(lambda x: x.tag == 'tr'):
        cells = [ws(''.join(inline(k) for k in c.kids)).strip().replace('|', '\\|') for c in tr.kids if isinstance(c, Node) and c.tag in ('td', 'th')]
        if cells: rows.append(cells)
    if not rows: return ''
    w = max(len(r) for r in rows); rows = [r + [''] * (w - len(r)) for r in rows]
    out = ['| ' + ' | '.join(rows[0]) + ' |', '|' + '---|' * w] + ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
    return '\n'.join(out) + '\n\n'

def block(n, depth=0):
    if isinstance(n, str):
        s = ws(n).strip(); return s + '\n\n' if s else ''
    t, c = n.tag, n.cls()
    if t in ('script', 'style', 'nav', 'button'): return ''
    if t == 'svg': return ''
    if t == 'h2':
        num = next((k for k in n.kids if isinstance(k, Node) and 'num' in k.cls()), None)
        if num:
            rest = ''.join(k if isinstance(k, str) else k.text() for k in n.kids if k is not num)
            return f'## {ws(num.text()).strip()} {ws(rest).strip()}\n\n'
        return f'## {ws(n.text()).strip()}\n\n'
    if t in ('h3', 'h4'): return f'{"###" if t == "h3" else "####"} {ws(inline(n)).strip()}\n\n'
    if t == 'p': s = ws(inline(n)).strip(); return s + '\n\n' if s else ''
    if t == 'pre': return '```\n' + n.text().strip('\n') + '\n```\n\n'
    if t == 'table': return table(n)
    if t in ('ul', 'ol'):
        out, i = '', 0
        for li in n.kids:
            if isinstance(li, Node) and li.tag == 'li':
                i += 1
                head = ''.join(inline(k) for k in li.kids if not (isinstance(k, Node) and k.tag in ('ul', 'ol')))
                out += '  ' * depth + (f'{i}. ' if t == 'ol' else '- ') + ws(head).strip() + '\n'
                for sub in li.kids:
                    if isinstance(sub, Node) and sub.tag in ('ul', 'ol'): out += block(sub, depth + 1).rstrip('\n') + '\n'
        return out + ('\n' if depth == 0 else '')
    if t == 'figure':
        svg = next(n.find_all(lambda x: x.tag == 'svg'), None)
        cap = next(n.find_all(lambda x: x.tag == 'figcaption'), None)
        label = svg.attrs.get('aria-label', '') if svg else ''
        out = f'*Figure: {ws(label).strip()}*\n\n' if label else ''
        return out + (ws(inline(cap)).strip() + '\n\n' if cap else '')
    if t == 'div' and ('step' in c or 'kpi' in c):
        return '- ' + ' · '.join(ws(inline(k)).strip() for k in n.kids if isinstance(k, Node) and ws(inline(k)).strip()) + '\n'
    if t == 'div' and 'bytes' in c:
        fields = [' '.join(ws(x.text()).strip() for x in d.kids if isinstance(x, Node)) for d in n.kids if isinstance(d, Node)]
        return 'Layout: ' + ' | '.join(fields) + '\n\n'
    anchor = f'<a id="{n.attrs["id"]}"></a>\n\n' if t in ('section', 'div') and n.attrs.get('id') else ''
    body = ''.join(block(k, depth) for k in n.kids)
    return anchor + body + ('\n' if t == 'div' and ('flow' in c or 'kpis' in c) else '')

def doc_md(path):
    root = parse(path)
    main = next(root.find_all(lambda x: x.tag == 'main'), root)
    title = ws(next(root.find_all(lambda x: x.tag == 'title')).text()).strip()
    hero = next(main.find_all(lambda x: x.tag == 'header'), None)
    blurb = ' '.join(ws(p.text()).strip() for p in (hero.find_all(lambda x: x.tag == 'p') if hero else []))
    body = ''.join(block(s) for s in main.find_all(lambda x: x.tag == 'section' and x.attrs.get('id')) if s.parent is main or s.parent.tag != 'section')
    return title, blurb, f'# {title}\n\n> {blurb}\n\n' + re.sub(r'\n{3,}', '\n\n', body)

def scenarios_md():
    p = os.path.join(DOCS, 'src', 'scenarios', 'scenarios.json')
    if not os.path.exists(p): return None, 0, 0
    sc = json.load(open(p, encoding='utf-8'))['scenarios']
    out = '# Executable scenarios\n\n> Each scenario is a flow through typed components. Every step has an observable expectation and the kind of proof that checks it.\n\n'
    for s in sc:
        nodes = {n['id']: n for n in s['nodes']}; name = lambda i: nodes.get(i, {}).get('label', i)
        out += f"## {s['title']} (`{s['id']}`)\n\n{s['summary']}\n\n"
        out += 'Components: ' + ', '.join(f"{n['label']} ({n['component']})" for n in s['nodes']) + '.\n\n'
        if s.get('groups'): out += 'Boundaries: ' + '; '.join(f"{g['label']} [{g['style']}]: {', '.join(map(name, g['nodes']))}" for g in s['groups']) + '.\n\n'
        for i, st in enumerate(s['steps'], 1):
            text = re.sub(r'\[\[([\w-]+)\]\]', r'\1', st['text'])
            out += f"{i}. **{name(st['from'])} → {name(st['to'])}: {st['label']}.** {text}\n   - Expect: {st['expect']}\n   - Proof: {st['proof']['kind']} ({st['proof']['ref']}){' · failure path' if st.get('warn') else ''}\n"
        out += '\n'
    return out, len(sc), sum(len(s['steps']) for s in sc)


# ---------- write ----------
# never deletes anything: generated files are overwritten in place
os.makedirs(os.path.join(SITE, 'md'), exist_ok=True); os.makedirs(os.path.join(SITE, 'references'), exist_ok=True)

refs = set()
for src in (ARCH, PLAN):
    h = open(src, encoding='utf-8').read()
    refs |= set(re.findall(r'href="(?:\.\./)+(?:references/)?([\w-]+-architecture\.html|[\w-]+-features[\w-]*\.html)', h))
    h = re.sub(r'href="(?:\.\./)+(?:references/)?([\w-]+\.html)', r'href="references/\1', h)
    h = re.sub(r'href="references/(' + re.escape(os.path.basename(ARCH)) + '|' + re.escape(os.path.basename(PLAN)) + ')', r'href="\1', h)
    open(os.path.join(SITE, os.path.basename(src)), 'w', encoding='utf-8').write(h)
missing = []
for r in sorted(refs):
    if r in (os.path.basename(ARCH), os.path.basename(PLAN)): continue
    found = next((os.path.join(d, r) for d in REFS_SRC if os.path.exists(os.path.join(d, r))), None)
    if found: shutil.copyfile(found, os.path.join(SITE, 'references', r))
    else: missing.append(r)

a_title, a_blurb, a_md = doc_md(ARCH)
p_title, p_blurb, p_md = doc_md(PLAN)
s_md, n_sc, n_steps = scenarios_md()
files = {'md/architecture.md': a_md, 'md/master-plan.md': p_md}
if s_md: files['md/scenarios.md'] = s_md

name = re.sub(r'\s*(architecture|master plan|build plan).*$', '', a_title, flags=re.I).strip() or 'Design'
index = f'''# {name} design docs

> {a_blurb}

How to read it:
- Two source documents: the architecture proposal (why and what) and the build plan (how and when). Where they disagree, the plan's decisions win.
- Stable ids link everything: D# decisions, S-# seams/interfaces, I-# invariants, E# epics, M# milestones. Each is defined in the build plan.
- Every file below is Markdown generated from the same HTML a reader opens, so it is always current.

## Documents

- [Architecture proposal]({abs_('md/architecture.md')}): {a_title}, all sections in document order
- [Build plan]({abs_('md/master-plan.md')}): {p_title}, all sections in document order, with every id table
''' + (f"- [Scenarios]({abs_('md/scenarios.md')}): {n_sc} scenarios, {n_steps} steps, each with its expectation and proof\n" if s_md else '') + f'''
## HTML

- [Architecture proposal]({abs_(os.path.basename(ARCH))})
- [Build plan]({abs_(os.path.basename(PLAN))})

## Optional

- [Everything in one file]({abs_('llms-full.txt')}): both documents{' and all scenarios' if s_md else ''}
'''
if refs - {os.path.basename(ARCH), os.path.basename(PLAN)}:
    index += ''.join(f'- [{r}]({abs_("references/" + r)}): reference architecture report\n' for r in sorted(refs) if r not in missing and r not in (os.path.basename(ARCH), os.path.basename(PLAN)))
files['llms.txt'] = index
files['llms-full.txt'] = index + '\n\n---\n\n' + a_md + '\n---\n\n' + p_md + ('\n---\n\n' + s_md if s_md else '')
files['robots.txt'] = '''# Search engines stay out (pages are also sent with X-Robots-Tag: noindex).
# The llms.txt files stay readable so agents pointed at the site can use them.
User-agent: *
Allow: /llms.txt
Allow: /llms-full.txt
Allow: /md/
Disallow: /
'''
files['index.html'] = f'<!DOCTYPE html><meta charset="utf-8"><meta name="robots" content="noindex"><title>{html.escape(name)}</title><meta http-equiv="refresh" content="0; url={os.path.basename(ARCH)}"><a href="{os.path.basename(ARCH)}">{html.escape(a_title)}</a>\n'
for rel, body in files.items():
    open(os.path.join(SITE, rel), 'w', encoding='utf-8', newline='\n').write(re.sub(r'\n{3,}', '\n\n', body))

toml = os.path.join(DOCS, 'netlify.toml')
if not os.path.exists(toml):
    open(toml, 'w', encoding='utf-8', newline='\n').write('''# Netlify: publishes the pre-built site/ folder (run package_single.py, then commit site/). No build step.
[build]
  publish = "site"

# Keep every page out of search engines and AI crawlers.
[[headers]]
  for = "/*"
  [headers.values]
    X-Robots-Tag = "noindex, nofollow, noarchive, nosnippet, noimageindex"
    Referrer-Policy = "no-referrer"

# llms.txt and the Markdown pages: declare UTF-8 so dashes and arrows survive any fetcher.
[[headers]]
  for = "/llms*.txt"
  [headers.values]
    Content-Type = "text/plain; charset=utf-8"

[[headers]]
  for = "/md/*"
  [headers.values]
    Content-Type = "text/markdown; charset=utf-8"
''')

kb = lambda r: round(os.path.getsize(os.path.join(SITE, r)) / 1024)
print(f"packaged {SITE}: 2 documents, {len(refs - set(missing) - {os.path.basename(ARCH), os.path.basename(PLAN)})} reports, "
      f"{len([f for f in files if f.startswith('md/')])} Markdown files, llms-full.txt {kb('llms-full.txt')} KB"
      f"{' (absolute links to ' + BASE + ')' if BASE else ' (relative links)'}")
if missing: print('reference pages not found (linked but missing):', ', '.join(missing))
