#!/usr/bin/env python3
"""Build PAPvault into one self-contained HTML file.

Inlines the two stylesheets and the four scripts listed in main() into
src/index.html, renders docs/manual.md into the manual dialog, fills in a
Content-Security-Policy that allows exactly those six by hash, writes
dist/index.html, and prints the SHA-256 of what it wrote.

Each is its own element with its own hash, so the policy names the library
separately from the page's own code. The scripts are inlined in the order
they are listed, which is the order they depend on each other in.

The manual is written in a small subset of Markdown:

    # Heading      a group in the manual's navigation, which collapses
    ## Heading     a section: one button, one pane
    > text         a pull quote
    - text         a bulleted list
    1. text        a numbered list
    text           a paragraph

and within a line, **bold**, `code`, and [text](https://example.com). A link
to anything but a plain https address stops the build. Everything else is
text, and every character of it is escaped before it reaches the page.
"""

import base64
import hashlib
import html as html_module
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
LIB = ROOT / "lib"
MANUAL = ROOT / "docs" / "manual.md"
VERSION = ROOT / "VERSION"
OUT = ROOT / "dist" / "index.html"

CSP_MARKER = '<meta http-equiv="Content-Security-Policy" content="">'
UPLOT_STYLE_MARKER = '<link rel="stylesheet" href="../lib/uplot/uPlot.css">'
STYLE_MARKER = '<link rel="stylesheet" href="style.css">'
UPLOT_SCRIPT_MARKER = '<script src="../lib/uplot/uPlot.iife.js"></script>'
EDF_SCRIPT_MARKER = '<script src="edf.js"></script>'
CARD_SCRIPT_MARKER = '<script src="card.js"></script>'
PLOTS_SCRIPT_MARKER = '<script src="plots.js"></script>'
SCRIPT_MARKER = '<script src="app.js"></script>'
MANUAL_MARKER = "<!-- manual -->"
VERSION_MARKER = "<!-- version -->"


def read(name):
    return (SRC / name).read_text(encoding="utf-8")


def read_lib(name):
    return (LIB / name).read_text(encoding="utf-8")


def csp_hash(text):
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return "'sha256-" + base64.b64encode(digest).decode("ascii") + "'"


def fail(message):
    sys.exit("build: " + message)


def inline(text):
    escaped = html_module.escape(text, quote=False)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https://[^)\s\"']+)\)",
        r'<a href="\2" rel="noreferrer">\1</a>',
        escaped,
    )
    if "](" in escaped:
        fail(f"docs/manual.md has a link that is not a plain https address: {text!r}")
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)


def section_id(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return "manual-" + slug


def render_manual(text):
    """Turn the manual's Markdown into the navigation and the panes.

    Each `#` heading becomes a group the reader can collapse, holding the `##`
    sections under it as buttons. The script opens one group at a time.
    """
    groups = []
    panes = []
    body = []
    listing = None

    def group_for_sections():
        # A manual that opens with a section rather than a group still gets one,
        # unnamed, so every section button has somewhere to live.
        if not groups:
            groups.append({"title": "", "id": "manual-group-0", "items": []})
        return groups[-1]

    def close_list():
        nonlocal listing
        if listing:
            body.append("</" + listing + ">")
            listing = None

    def close_section():
        close_list()
        if panes:
            panes[-1] = panes[-1] + "\n".join(body) + "\n</section>"
        del body[:]

    for line in text.splitlines():
        line = line.strip()
        if not line:
            close_list()
        elif line.startswith("## "):
            close_section()
            title = line[3:].strip()
            group_for_sections()["items"].append(
                f'<button type="button" data-section="{section_id(title)}">{inline(title)}</button>')
            panes.append(f'<section class="manual-pane" id="{section_id(title)}">\n<h3>{inline(title)}</h3>\n')
        elif line.startswith("# "):
            close_section()
            groups.append({
                "title": line[2:].strip(),
                "id": "manual-group-%d" % len(groups),
                "items": [],
            })
        elif not panes:
            fail(f"docs/manual.md has text before its first section: {line!r}")
        elif line.startswith("> "):
            close_list()
            body.append(f'<p class="pull">{inline(line[2:].strip())}</p>')
        elif line.startswith("- "):
            if listing != "ul":
                close_list()
                body.append("<ul>")
                listing = "ul"
            body.append(f"<li>{inline(line[2:].strip())}</li>")
        elif re.match(r"^\d+\. ", line):
            if listing != "ol":
                close_list()
                body.append("<ol>")
                listing = "ol"
            body.append(f"<li>{inline(line.split('. ', 1)[1].strip())}</li>")
        else:
            close_list()
            body.append(f"<p>{inline(line)}</p>")

    close_section()
    if not panes:
        fail("docs/manual.md holds no sections")

    nav = []
    for group in groups:
        if not group["items"]:
            continue
        buttons = "\n".join(group["items"])
        if not group["title"]:
            nav.append(buttons)
            continue
        nav.append(
            '<div class="manual-group">\n'
            f'<button type="button" class="manual-group-button" aria-expanded="false"'
            f' aria-controls="{group["id"]}" data-group="{group["id"]}">{inline(group["title"])}</button>\n'
            f'<div class="manual-group-items" id="{group["id"]}" hidden>\n'
            + buttons
            + "\n</div>\n</div>"
        )

    return (
        '<nav class="manual-nav" id="manual-nav" aria-label="Manual sections">\n'
        + "\n".join(nav)
        + '\n</nav>\n<div class="manual-panes">\n'
        + "\n".join(panes)
        + "\n</div>"
    )


def replace_once(html, marker, replacement):
    count = html.count(marker)
    if count != 1:
        fail(f"expected {marker!r} once in src/index.html, found it {count} times")
    return html.replace(marker, replacement)


def main():
    html = read("index.html")
    # Each entry is one inlined element: its name for a message, its text, and the marker it replaces.
    # The hashes in the policy and the elements in the page are both taken from these two lists.
    styles = [
        ("lib/uplot/uPlot.css", "\n" + read_lib("uplot/uPlot.css"), UPLOT_STYLE_MARKER),
        ("src/style.css", "\n" + read("style.css"), STYLE_MARKER),
    ]
    scripts = [
        ("lib/uplot/uPlot.iife.js", "\n" + read_lib("uplot/uPlot.iife.js"), UPLOT_SCRIPT_MARKER),
        ("src/edf.js", "\n" + read("edf.js"), EDF_SCRIPT_MARKER),
        ("src/card.js", "\n" + read("card.js"), CARD_SCRIPT_MARKER),
        ("src/plots.js", "\n" + read("plots.js"), PLOTS_SCRIPT_MARKER),
        ("src/app.js", "\n" + read("app.js"), SCRIPT_MARKER),
    ]

    for name, text, _ in styles:
        if "</style" in text.lower():
            fail(f"{name} contains '</style', which would end the inlined element early")
    for name, text, _ in scripts:
        for sequence in ("</script", "<!--"):
            if sequence in text.lower():
                fail(f"{name} contains {sequence!r}, which would change how the inlined element is parsed")

    policy = "; ".join([
        "default-src 'none'",
        "script-src " + " ".join(csp_hash(text) for _, text, _ in scripts),
        "style-src " + " ".join(csp_hash(text) for _, text, _ in styles),
        "img-src data:",
        "base-uri 'none'",
        "form-action 'none'",
    ])

    version = VERSION.read_text(encoding="utf-8").strip()
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        fail(f"VERSION holds {version!r}, which is not a three-part version")
    html = replace_once(html, VERSION_MARKER, "v" + html_module.escape(version, quote=False))
    html = replace_once(html, MANUAL_MARKER, render_manual(MANUAL.read_text(encoding="utf-8")))
    html = replace_once(html, CSP_MARKER, f'<meta http-equiv="Content-Security-Policy" content="{policy}">')
    for _, text, marker in styles:
        html = replace_once(html, marker, f"<style>{text}</style>")
    for _, text, marker in scripts:
        html = replace_once(html, marker, f"<script>{text}</script>")

    data = html.encode("utf-8")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(data)
    print(f"{hashlib.sha256(data).hexdigest()}  {OUT.relative_to(ROOT)}  v{version}")


if __name__ == "__main__":
    main()
