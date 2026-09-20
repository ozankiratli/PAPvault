#!/usr/bin/env python3
"""Build PAPvault into one self-contained HTML file.

Inlines src/style.css and src/app.js into src/index.html, renders
docs/manual.md into the manual dialog, fills in a Content-Security-Policy
that allows exactly the one style and the one script by hash, writes
dist/index.html, and prints the SHA-256 of what it wrote.

The manual is written in a small subset of Markdown:

    # Heading      a group in the manual's navigation
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
MANUAL = ROOT / "docs" / "manual.md"
OUT = ROOT / "dist" / "index.html"

CSP_MARKER = '<meta http-equiv="Content-Security-Policy" content="">'
STYLE_MARKER = '<link rel="stylesheet" href="style.css">'
SCRIPT_MARKER = '<script src="app.js"></script>'
MANUAL_MARKER = "<!-- manual -->"


def read(name):
    return (SRC / name).read_text(encoding="utf-8")


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
    """Turn the manual's Markdown into the navigation and the panes."""
    nav = []
    panes = []
    body = []
    listing = None

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
            nav.append(f'<button type="button" data-section="{section_id(title)}">{inline(title)}</button>')
            panes.append(f'<section class="manual-pane" id="{section_id(title)}">\n<h3>{inline(title)}</h3>\n')
        elif line.startswith("# "):
            close_section()
            nav.append(f'<p class="manual-group">{inline(line[2:].strip())}</p>')
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
    style = "\n" + read("style.css")
    script = "\n" + read("app.js")

    if "</style" in style.lower():
        fail("src/style.css contains '</style', which would end the inlined element early")
    for sequence in ("</script", "<!--"):
        if sequence in script.lower():
            fail(f"src/app.js contains {sequence!r}, which would change how the inlined element is parsed")

    policy = "; ".join([
        "default-src 'none'",
        "script-src " + csp_hash(script),
        "style-src " + csp_hash(style),
        "img-src data:",
        "base-uri 'none'",
        "form-action 'none'",
    ])

    html = replace_once(html, MANUAL_MARKER, render_manual(MANUAL.read_text(encoding="utf-8")))
    html = replace_once(html, CSP_MARKER, f'<meta http-equiv="Content-Security-Policy" content="{policy}">')
    html = replace_once(html, STYLE_MARKER, f"<style>{style}</style>")
    html = replace_once(html, SCRIPT_MARKER, f"<script>{script}</script>")

    data = html.encode("utf-8")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(data)
    print(f"{hashlib.sha256(data).hexdigest()}  {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
