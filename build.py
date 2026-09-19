#!/usr/bin/env python3
"""Build PAPvault into one self-contained HTML file.

Inlines src/style.css and src/app.js into src/index.html, fills in a
Content-Security-Policy that allows exactly those two by hash, writes
dist/index.html, and prints the SHA-256 of what it wrote.
"""

import base64
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "dist" / "index.html"

CSP_MARKER = '<meta http-equiv="Content-Security-Policy" content="">'
STYLE_MARKER = '<link rel="stylesheet" href="style.css">'
SCRIPT_MARKER = '<script src="app.js"></script>'


def read(name):
    return (SRC / name).read_text(encoding="utf-8")


def csp_hash(text):
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return "'sha256-" + base64.b64encode(digest).decode("ascii") + "'"


def fail(message):
    sys.exit("build: " + message)


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

    html = replace_once(html, CSP_MARKER, f'<meta http-equiv="Content-Security-Policy" content="{policy}">')
    html = replace_once(html, STYLE_MARKER, f"<style>{style}</style>")
    html = replace_once(html, SCRIPT_MARKER, f"<script>{script}</script>")

    data = html.encode("utf-8")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(data)
    print(f"{hashlib.sha256(data).hexdigest()}  {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
