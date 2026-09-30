"""The library carried in the page is the one its author published, unmodified.

    python3 dev/tests/vendored.py <repo root>

PAPvault's claim is that it carries one library, whole, at a version named in the
open, and that nobody has to take that on trust. That claim rests on three things,
and this asks all three of a machine rather than of a person reading two lists side
by side:

  1. **The bytes.** Every file in `lib/` is checksummed against the table in
     `SOURCES.md`, which records what was taken and from which commit of which tag.
  2. **Nothing else is down there.** A file in `lib/` that the table does not name is
     a library nobody approved, whether or not it ever reaches the page.
  3. **The page says so.** The built page names the library, its version and its
     license where a reader can see them, since a credit nobody ships is not a credit.

The table is the source, and this check is the thing that keeps it honest: a file
changed without the table changing with it fails here, and so does a table entry
whose file is gone.
"""
import argparse
import hashlib
import pathlib
import re
import sys

checks = 0
bad = []


def expect(what, holds, saw=None):
    global checks
    checks += 1
    if not holds:
        bad.append(what)
        print("    FAIL  " + what + ("" if saw is None else "\n            saw: %s" % (saw,)))


def tabled(sources):
    """What SOURCES.md says lib/ holds: file name -> (bytes, sha256)."""
    found = {}
    for name, size, digest in re.findall(
            r"\|\s*`([^`]+)`\s*\|\s*`[^`]*`\s*\|\s*([\d,]+)\s*\|\s*`([0-9a-f]{64})`\s*\|",
            sources):
        found[name] = (int(size.replace(",", "")), digest)
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    args = parser.parse_args()
    root = pathlib.Path(args.root).resolve()

    sources = (root / "SOURCES.md").read_text(encoding="utf-8")
    table = tabled(sources)
    expect("SOURCES.md carries a table of what is vendored", bool(table))
    if not table:
        return finish()

    carried = sorted(path for path in (root / "lib").rglob("*") if path.is_file())
    named = {path.name for path in carried}
    expect("every file in lib/ is named in the table",
           named == set(table), sorted(named ^ set(table)))

    for path in carried:
        wanted = table.get(path.name)
        if not wanted:
            continue
        raw = path.read_bytes()
        expect("%s is the size the table records" % path.name,
               len(raw) == wanted[0], "%d against %d" % (len(raw), wanted[0]))
        expect("%s is the file the table records" % path.name,
               hashlib.sha256(raw).hexdigest() == wanted[1],
               hashlib.sha256(raw).hexdigest())

    built = root / "dist" / "index.html"
    if not built.is_file():
        expect("the page is built, so its credits can be read", False)
        return finish()
    page = built.read_text(encoding="utf-8", errors="replace")
    expect("the page names the library", "uPlot" in page)
    expect("and the version it carries", "1.6.32" in page)
    expect("and the license it is under", "MIT" in page)

    return finish()


def finish():
    print("\n%d checks, %d failures" % (checks, len(bad)))
    return 1 if bad else 0


sys.exit(main())
