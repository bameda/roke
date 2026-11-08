"""A small Markdown renderer for the terminal, for the READMEs that roke's
show commands print: headings, emphasis, code, links, lists (ordered,
unordered and tasks), block quotes, rules, fenced code and tables, in
colours that every terminal supports. Without colour it returns the text
as it is."""

import re
import shutil
import unicodedata

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
STRIKE = "\033[9m"
HEADINGS = {
    1: "\033[1;4;35m",  # bold, underlined, magenta
    2: "\033[1;34m",  # bold blue
    3: "\033[1;36m",  # bold cyan
}
HEADING = BOLD  # levels 4 to 6
CODE = "\033[33m"  # yellow
LINK = "\033[4;34m"  # underlined blue
MARK = "\033[36m"  # bullets, numbers, quote bars

ANSI = re.compile(r"\033\[[0-9;]*m")
FENCE = re.compile(r"^(\s*)(```|~~~)\s*([\w+-]*)")
HEADING_LINE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RULE = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
BULLET = re.compile(r"^(\s*)[-*+]\s+(?:\[([ xX])\]\s+)?(.*)")
NUMBERED = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)")
QUOTE = re.compile(r"^\s*>\s?(.*)")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def visible_len(text: str) -> int:
    """The width of TEXT in the terminal: without colour codes, and with
    wide characters (CJK, most emoji) taking two columns."""
    text = ANSI.sub("", text)
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def strip_ansi(text: str) -> str:
    return ANSI.sub("", text)


def inline(text: str, base: str = "", resolve=None) -> str:
    """Emphasis, code, links and strikethrough in a line. BASE is the style
    around the line (a heading's, a quote's), restored after each span.
    RESOLVE turns a relative link into a URL, or None to show only its text."""
    kept: list[str] = []

    def keep(rendered: str) -> str:
        kept.append(rendered)
        return f"\x00{len(kept) - 1}\x00"

    def span(style: str, inner: str) -> str:
        return f"{style}{inner}{RESET}{base}"

    # Code first, so nothing inside it is styled; then escaped characters.
    text = re.sub(r"(`+)(.+?)\1", lambda m: keep(span(CODE, m.group(2).strip())), text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|>~])", lambda m: keep(m.group(1)), text)
    # Images, then links: text only when the target is a relative path,
    # which leads nowhere in a terminal; text and URL otherwise.
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", lambda m: keep(f"[image: {m.group(1)}]"), text)

    def expand(text: str) -> str:
        while "\x00" in text:
            text = re.sub(r"\x00(\d+)\x00", lambda m: kept[int(m.group(1))], text)
        return text

    def link(m: re.Match) -> str:
        # Spans inside the label (code) return to the link's style, not BASE.
        label = expand(m.group(1)).replace(f"{RESET}{base}", f"{RESET}{LINK}")
        target = m.group(2).split()[0] if m.group(2).strip() else ""
        if not re.match(r"[a-z][a-z0-9+.-]*:", target):
            target = resolve(target) if resolve and target else None
            if not target:
                return keep(span(LINK, label))
        if label == target:
            return keep(span(LINK, label))
        return keep(span(LINK, label) + f" {DIM}({target}){RESET}{base}")

    text = re.sub(r"\[([^\]]+)\]\(([^)]*)\)", link, text)
    text = re.sub(r"<((?:https?|mailto):[^>\s]+)>", lambda m: keep(span(LINK, m.group(1))), text)
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: span(BOLD, m.group(1) or m.group(2)), text)
    text = re.sub(
        r"(?<![*\w])\*(?![\s*])(.+?)(?<![\s*])\*(?![*\w])|(?<![_\w])_(?![\s_])(.+?)(?<![\s_])_(?![_\w])",
        lambda m: span(ITALIC, m.group(1) or m.group(2)),
        text,
    )
    text = re.sub(r"~~(.+?)~~", lambda m: span(STRIKE, m.group(1)), text)
    return expand(text)


def _cells(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", row)]


def _table(lines: list[str], width: int, resolve=None) -> list[str]:
    """A table with aligned columns, or one record per row when it does not
    fit in the terminal."""
    header = [f"{BOLD}{inline(c, BOLD, resolve)}{RESET}" for c in _cells(lines[0])]
    aligns = []
    for c in _cells(lines[1]):
        if c.startswith(":") and c.endswith(":"):
            aligns.append("center")
        elif c.endswith(":"):
            aligns.append("right")
        else:
            aligns.append("left")
    rows = [[inline(c, "", resolve) for c in _cells(line)] for line in lines[2:]]
    columns = len(header)
    rows = [(r + [""] * columns)[:columns] for r in rows]
    aligns = (aligns + ["left"] * columns)[:columns]
    widths = [max(visible_len(r[i]) for r in [header, *rows]) for i in range(columns)]
    bar = f"{DIM}│{RESET}"

    def cell(text: str, i: int) -> str:
        pad = widths[i] - visible_len(text)
        if aligns[i] == "right":
            return " " * pad + text
        if aligns[i] == "center":
            return " " * (pad // 2) + text + " " * (pad - pad // 2)
        return text + " " * pad

    if sum(widths) + 3 * columns + 1 > width:
        out = []
        labels = [strip_ansi(h) for h in header]
        label_width = max(visible_len(h) for h in labels)
        for row in rows:
            out += [
                f"{BOLD}{labels[i].ljust(label_width)}{RESET}  {row[i]}" for i in range(columns)
            ]
            out.append("")
        return out[:-1]

    def rule(left: str, mid: str, right: str) -> str:
        return DIM + left + mid.join("─" * (w + 2) for w in widths) + right + RESET

    out = [rule("┌", "┬", "┐")]
    out.append(bar + bar.join(f" {cell(h, i)} " for i, h in enumerate(header)) + bar)
    out.append(rule("├", "┼", "┤"))
    out += [bar + bar.join(f" {cell(c, i)} " for i, c in enumerate(r)) + bar for r in rows]
    out.append(rule("└", "┴", "┘"))
    return out


def wrap(text: str, width: int, first: str = "", rest: str = "") -> list[str]:
    """TEXT in lines of at most WIDTH visible columns, the first starting with
    FIRST and the others with REST. Colour codes do not count, and a word
    longer than the line stays whole."""
    lines, line, used = [], first, visible_len(first)
    start = used
    for word in text.split():
        size = visible_len(word)
        if used > start and used + 1 + size > width:
            lines.append(line)
            line, used = rest, visible_len(rest)
            start = used
        if used > start:
            line, used = line + " ", used + 1
        line, used = line + word, used + size
    lines.append(line)
    return lines


def _starts_block(line: str) -> bool:
    """Whether LINE starts something other than the paragraph before it."""
    return bool(
        not line.strip()
        or FENCE.match(line)
        or HEADING_LINE.match(line)
        or RULE.match(line)
        or BULLET.match(line)
        or NUMBERED.match(line)
        or QUOTE.match(line)
        or TABLE_ROW.match(line)
    )


def _hard_break(line: str) -> bool:
    return line.endswith("  ") or line.endswith("\\")


def render(markdown: str, width: int | None = None, resolve=None) -> str:
    """MARKDOWN with colours for a terminal of WIDTH columns, its paragraphs
    re-wrapped to it (100 columns at most). RESOLVE turns relative links
    into URLs (see inline)."""
    width = min(width or shutil.get_terminal_size().columns, 100)
    lines = re.sub(r"<!--.*?-->", "", markdown, flags=re.S).splitlines()
    out: list[str] = []
    fence: str | None = None
    i = 0

    def gather(j: int, indent: int) -> tuple[list[str], int]:
        """The continuation lines from J: not blank, not a new block, and,
        inside a list item, indented at least INDENT columns."""
        parts = []
        while j < len(lines):
            line = lines[j]
            if _starts_block(line) or (indent and len(line) - len(line.lstrip()) < indent):
                break
            parts.append(line.strip())
            if _hard_break(line):
                j += 1
                break
            j += 1
        return parts, j

    while i < len(lines):
        line = lines[i]
        m = FENCE.match(line)
        if fence is None and m:
            fence = m.group(2)
            label = f" {m.group(3)} " if m.group(3) else ""
            out.append(f"{DIM}──{label}{'─' * max(0, 40 - len(label))}{RESET}")
            i += 1
            continue
        if fence is not None:
            if line.strip().startswith(fence):
                fence = None
                out.append(f"{DIM}{'─' * 42}{RESET}")
            else:
                out.append(f"  {CODE}{line}{RESET}")
            i += 1
            continue
        if TABLE_ROW.match(line) and i + 1 < len(lines) and TABLE_SEPARATOR.match(lines[i + 1]):
            j = i + 2
            while j < len(lines) and TABLE_ROW.match(lines[j]):
                j += 1
            out += _table(lines[i:j], width, resolve)
            i = j
            continue
        if not line.strip():
            out.append("")
            i += 1
        elif m := HEADING_LINE.match(line):
            style = HEADINGS.get(len(m.group(1)), HEADING)
            out.append(f"{style}{inline(m.group(2), style, resolve)}{RESET}")
            i += 1
        elif RULE.match(line):
            out.append(f"{DIM}{'─' * min(width, 78)}{RESET}")
            i += 1
        elif m := BULLET.match(line) or NUMBERED.match(line):
            if m.re is BULLET:
                indent, task, text = m.groups()
                if task is not None:
                    marker = f"{MARK}{'☑' if task.lower() == 'x' else '☐'}{RESET}"
                    plain = 1
                else:
                    marker = f"{MARK}{'•' if len(indent) < 2 else '◦'}{RESET}"
                    plain = 1
            else:
                indent, number, text = m.groups()
                marker, plain = f"{MARK}{number}.{RESET}", len(number) + 1
            content = len(line) - len(line.lstrip()) + 2
            more, i = gather(i + 1, content) if not _hard_break(line) else ([], i + 1)
            body = inline(" ".join([text.strip(), *more]), "", resolve)
            out += wrap(body, width, f"{indent}{marker} ", " " * (len(indent) + plain + 1))
        elif m := QUOTE.match(line):
            parts = []
            while i < len(lines) and (q := QUOTE.match(lines[i])) and q.group(1).strip():
                parts.append(q.group(1).strip())
                i += 1
            if not parts:
                i += 1
                continue
            body = f"{ITALIC}{inline(' '.join(parts), ITALIC, resolve)}{RESET}"
            out += wrap(body, width, f"{MARK}│{RESET} {ITALIC}", f"{MARK}│{RESET} {ITALIC}")
        else:
            more, i = gather(i + 1, 0) if not _hard_break(line) else ([], i + 1)
            out += wrap(inline(" ".join([line.strip(), *more]), "", resolve), width)
    return "\n".join(out)
