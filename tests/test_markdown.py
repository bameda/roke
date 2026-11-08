"""The terminal Markdown renderer for the READMEs in roke's show commands."""

import sys

import pytest
from conftest import REPO

sys.path.insert(0, str(REPO))
from roke.ui.markdown import (  # noqa: E402
    BOLD,
    CODE,
    HEADINGS,
    ITALIC,
    LINK,
    RESET,
    render,
    strip_ansi,
    visible_len,
)


def test_headings_keep_their_style_after_inner_spans():
    out = render("# Settings for `roke` here")
    assert out.startswith(HEADINGS[1])
    assert f"{CODE}roke{RESET}{HEADINGS[1]} here" in out


def test_code_is_never_styled_inside():
    out = render("run `**not bold**` and `_not italic_`")
    assert f"{CODE}**not bold**{RESET}" in out
    assert BOLD not in out and ITALIC not in out


def test_emphasis_but_not_snake_case():
    out = render("**bold**, *italic*, _also_, and some_snake_case_name")
    assert f"{BOLD}bold{RESET}" in out and f"{ITALIC}italic{RESET}" in out
    assert f"{ITALIC}also{RESET}" in out and "some_snake_case_name" in out


def test_escaped_characters_stay_literal():
    assert strip_ansi(render(r"\*not italic\*")) == "*not italic*"


def test_numbered_and_bulleted_lists_and_tasks():
    out = strip_ansi(render("1. first\n2) second\n- item\n  - nested\n- [ ] todo\n- [x] done"))
    assert out.splitlines() == ["1. first", "2. second", "• item", "  ◦ nested", "☐ todo", "☑ done"]


def test_links():
    out = render("see [the guide](../docs/usage.md) and [roke](https://example.com/roke)")
    plain = strip_ansi(out)
    assert plain == "see the guide and roke (https://example.com/roke)"
    assert f"{LINK}the guide{RESET}" in out


def test_code_inside_a_link_keeps_the_link_style():
    out = render("the [`postgres` MCP](../mcps/postgres/README.md)")
    assert f"{CODE}postgres{RESET}{LINK} MCP{RESET}" in out


def test_code_blocks_are_not_styled():
    out = strip_ansi(render("```bash\necho **x** _y_\n```"))
    assert "echo **x** _y_" in out and "── bash" in out


def test_tables_are_aligned():
    md = "| Name | Value |\n|---|---:|\n| `a` | 1 |\n| longer name | 22 |"
    lines = render(md, width=80).splitlines()
    assert len({visible_len(line) for line in lines}) == 1  # every line equally wide
    assert BOLD in lines[1]  # the header
    assert strip_ansi(lines[3]).endswith(" 1 │")  # right-aligned column


def test_tables_too_wide_become_records():
    md = "| Variable | Value |\n|---|---|\n| `DATABASE_URL` | " + "x" * 90 + " |"
    plain = strip_ansi(render(md, width=60))
    assert plain.startswith("Variable  DATABASE_URL\nValue     xxx")


def test_quotes_rules_and_comments():
    plain = strip_ansi(render("> quoted\n\n---\n<!-- hidden -->text"))
    assert plain.splitlines()[0] == "│ quoted" and "─" * 10 in plain
    assert "hidden" not in plain and "text" in plain


@pytest.mark.parametrize("text,width", [("abc", 3), ("日本", 4), ("\033[1mab\033[0m", 2)])
def test_visible_len(text, width):
    assert visible_len(text) == width


def test_every_readme_renders():
    for path in REPO.glob("**/README.md"):
        if ".git" in path.parts:
            continue
        assert strip_ansi(render(path.read_text(), width=100)).strip()


def test_paragraphs_are_rewrapped_to_the_terminal():
    md = (
        "Part of the [catalog](../README.md). See\n"
        "[how it works](x.md) for what is common\n"
        "to every service."
    )
    out = strip_ansi(render(md, width=100)).splitlines()
    assert out == ["Part of the catalog. See how it works for what is common to every service."]
    narrow = strip_ansi(render(md, width=30)).splitlines()
    assert all(visible_len(line) <= 30 for line in narrow) and len(narrow) == 3


def test_list_items_continue_under_their_text():
    md = "- first item, which goes\n  on here\n- second\n12. twelve\n    and more"
    out = strip_ansi(render(md, width=16)).splitlines()
    assert out == [
        "• first item,",
        "  which goes on",
        "  here",
        "• second",
        "12. twelve and",
        "    more",
    ]


def test_quotes_and_hard_breaks():
    assert strip_ansi(render("> one\n> two")) == "│ one two"
    assert strip_ansi(render("line one  \nline two")).splitlines() == ["line one", "line two"]


def test_relative_links_through_a_resolver():
    def resolve(target):
        return f"https://example.com/{target}" if target.endswith(".md") else None

    plain = strip_ansi(render("[usage](docs/usage.md) and [a dir](examples/)", resolve=resolve))
    assert plain == "usage (https://example.com/docs/usage.md) and a dir"


def test_link_resolver_for_roke_s_repository(monkeypatch, tmp_path):
    from roke.commands import common

    monkeypatch.setattr(common, "repo_web_url", lambda: "https://github.com/owner/roke")
    resolve = common.link_resolver(REPO / "catalog" / "services" / "postgres" / "README.md")
    base = "https://github.com/owner/roke"
    assert resolve("../README.md#how-services-work") == (
        f"{base}/blob/main/catalog/services/README.md#how-services-work"
    )
    assert resolve("../../../examples/projects/") == f"{base}/tree/main/examples/projects"
    assert resolve("../../../../elsewhere.md") is None
    own = tmp_path / "README.md"
    own.write_text("x")
    assert common.link_resolver(own)("other.md") is None  # your own services
