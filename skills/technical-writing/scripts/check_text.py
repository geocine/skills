#!/usr/bin/env python3
"""List candidate writing problems in a Markdown or HTML file.

Usage: python -I check_text.py FILE [FILE ...]

Reports candidates, not verdicts: read each hit before calling it a defect.
Skips front matter, fenced code, inline code, blockquotes (quoted examples),
text in double quotes (words mentioned, not used), <pre>, <code>, <script>
and <style>. Line numbers for HTML count lines of the extracted text. Exit code is 0 when nothing is found, 1 otherwise.
"""
import html
import re
import sys
from pathlib import Path

BANNED = [
    (r"\bsimply\b", "'simply'"),
    (r"\bjust\b", "'just' (fine as 'fair' or 'exactly'; not as a minimizer)"),
    (r"\bobviously\b", "'obviously'"),
    (r"\bclearly\b", "'clearly'"),
    (r"\beas(y|ily)\b", "'easy/easily' (about the reader's effort?)"),
    (r"\bleverag(e|es|ed|ing)\b", "'leverage'"),
    (r"\butiliz(e|es|ed|ing)\b", "'utilize'"),
    (r"\bdelv(e|es|ed|ing)\b", "'delve'"),
    (r"\bvia\b", "'via' (write 'through')"),
    (r"\b(e\.g\.|i\.e\.|etc\.)", "Latin abbreviation"),
]
POSITION = r"\b(above|below|the following (table|list|section|code|example)|as mentioned earlier)\b"
TIME = r"\b(currently|soon|recently)\b"
HEDGE = r"\b(it could be argued|may possibly|might potentially|in some cases it may)\b"
MAX_HEADING_WORDS = 4
MAX_PARAGRAPH_SENTENCES = 4
MAX_CELL_WORDS = 40


def html_to_lines(text):
    text = re.sub(r"(?is)<(script|style|pre|code|svg|blockquote)\b.*?</\1>", " ", text)
    text = re.sub(r"(?i)<h([1-6])\b[^>]*>", lambda m: "\n\n" + "#" * int(m.group(1)) + " ", text)
    text = re.sub(r"(?i)</h[1-6]>", "\n\n", text)
    text = re.sub(r"(?i)<(p|li|div|section|tr|br)\b[^>]*>", "\n\n", text)
    text = re.sub(r"(?i)<t[dh]\b[^>]*>", " | ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text).splitlines()


def strip_markdown(lines):
    """Yield (line_number, text, kind) with code and quotes removed."""
    in_fence = False
    in_front = False
    in_quote = False
    for n, line in enumerate(lines, 1):
        s = line.strip()
        if n == 1 and s == "---":
            in_front = True
            continue
        if in_front:
            if s == "---":
                in_front = False
            continue
        # A quote never runs past a block boundary, so one stray mark cannot hide the rest.
        if not s or re.match(r"(```|~~~|>|#|\||[-*+]\s|\d+\.\s)", s):
            in_quote = False
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or s.startswith(">"):
            yield n, "", "blank"
            continue
        s = re.sub(r"`[^`]*`", "CODE", s)
        if in_quote:
            close = s.find('"')
            s = s if close < 0 else "QUOTE" + s[close + 1:]
            in_quote = close < 0
            if in_quote:
                yield n, "QUOTE", "text"
                continue
        s = re.sub(r'"[^"]*"|“[^”]*”', "QUOTE", s)
        if s.count('"') % 2:
            s, in_quote = s[: s.rfind('"')] + "QUOTE", True
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
        if not s:
            kind = "blank"
        elif s.startswith("#"):
            kind = "heading"
        elif s.startswith("|"):
            kind = "table"
        elif re.match(r"([-*+]|\d+\.)\s", s):
            kind = "item"
        else:
            kind = "text"
        yield n, s, kind


def sentences(text):
    text = re.sub(r"\b(e\.g|i\.e|etc|vs|Dr|Mr|Ms)\.", "X", text)
    return [p for p in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(*])", text) if p.strip()]


def check(path):
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    lines = html_to_lines(raw) if path.lower().endswith((".html", ".htm")) else raw.splitlines()
    hits = []
    para, para_start = [], None

    def flush():
        if para:
            count = len(sentences(" ".join(para)))
            if count > MAX_PARAGRAPH_SENTENCES:
                hits.append((para_start, f"paragraph has {count} sentences (max {MAX_PARAGRAPH_SENTENCES})"))

    for n, s, kind in strip_markdown(lines):
        if kind in ("text",):
            if not para:
                para_start = n
            para.append(s)
        else:
            flush()
            para = []
        if kind == "blank":
            continue
        if kind == "heading":
            words = re.sub(r"^#+\s*", "", s)
            words = re.sub(r"^\d+(\.\d+)*\s*", "", words).split()
            if len(words) > MAX_HEADING_WORDS:
                hits.append((n, f"heading has {len(words)} words (reference docs: 2-4): {' '.join(words)}"))
            if re.search(r"\b[A-Z]{1,3}-?\d+\b|\(.*\)|:", " ".join(words)):
                hits.append((n, "heading carries an id, a parenthesis or a colon (reference docs)"))
        if kind == "table" and not re.match(r"^\|[\s|:-]+\|?$", s):
            for cell in s.strip("|").split("|"):
                count = len(cell.split())
                if count > MAX_CELL_WORDS:
                    hits.append((n, f"table cell has {count} words (max {MAX_CELL_WORDS})"))
        low = s.lower()
        for pattern, label in BANNED:
            if re.search(pattern, low):
                hits.append((n, f"banned word: {label}"))
        if re.search(POSITION, low):
            hits.append((n, "refers by position: name and link the target"))
        if re.search(TIME, low):
            hits.append((n, "time word: fine in a story, not in reference docs"))
        if re.search(HEDGE, low):
            hits.append((n, "hedge"))
    flush()
    return hits


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    found = False
    for path in argv[1:]:
        for n, message in sorted(check(path)):
            found = True
            print(f"{path}:{n}: {message}")
    if not found:
        print("no candidates found")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
