"""The Content-Security-Policy in the built page, checked against what it must say.

    python3 dev/tests/policy.py <repo root>

The hashes in the policy cannot go stale: build.py computes each from the same string
it inlines, so the two are one source. What has no guard at all is the SHAPE of the
policy. Adding 'unsafe-inline', opening a connect-src, or turning img-src into a
wildcard would build cleanly, ship, and be caught only by somebody reading the diff.

This is that guard. It reads the built page rather than build.py, so it checks what a
visitor would actually receive.
"""
import base64
import hashlib
import pathlib
import re
import sys

# What each directive is allowed to say. A directive not named here is a finding, and
# so is a named one that says anything else.
EXPECTED = {
    "default-src": ["'none'"],
    "img-src": ["data:"],
    "base-uri": ["'none'"],
    "form-action": ["'none'"],
}
HASHED = ["script-src", "style-src"]
# Anything that would let something unhashed run, or open a host.
FORBIDDEN = ["'unsafe-inline'", "'unsafe-eval'", "'unsafe-hashes'", "'strict-dynamic'",
             "'self'", "*", "http:", "https:", "data:", "blob:", "'nonce-"]

checks = 0
bad = []


def expect(what, holds, saw=None):
    global checks
    checks += 1
    if not holds:
        bad.append(what)
        print("    FAIL  " + what + ("" if saw is None else "\n            saw: %s" % (saw,)))


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    page = (root / "dist" / "index.html").read_text(encoding="utf-8")

    metas = re.findall(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)"', page)
    expect("there is exactly one policy", len(metas) == 1, len(metas))
    if len(metas) != 1:
        return finish()
    policy = metas[0]

    said = {}
    for part in policy.split(";"):
        part = part.strip()
        if not part:
            continue
        name, _, rest = part.partition(" ")
        said[name] = rest.split()

    expect("no directive is named twice", len(said) == len([p for p in policy.split(";") if p.strip()]))

    for name, values in EXPECTED.items():
        expect("%s says exactly %s" % (name, " ".join(values)), said.get(name) == values, said.get(name))

    for name in HASHED:
        values = said.get(name, [])
        expect("%s is not empty" % name, bool(values))
        expect("%s holds nothing but sha256 hashes" % name,
               all(v.startswith("'sha256-") and v.endswith("'") for v in values), values)

    expect("the policy names no directive beyond the six expected",
           set(said) == set(EXPECTED) | set(HASHED), sorted(set(said) - set(EXPECTED) - set(HASHED)))

    for token in FORBIDDEN:
        # data: is legitimate for img-src alone, which EXPECTED already pins exactly.
        where = [n for n, v in said.items() if any(token in one for one in v) and not (token == "data:" and n == "img-src")]
        expect("no directive carries %s" % token, not where, where)

    # The policy has to arrive before anything it governs.
    at_policy = page.index("Content-Security-Policy")
    for tag in ["<style", "<script"]:
        expect("the policy comes before the first %s>" % tag, at_policy < page.index(tag),
               "policy at %d, %s at %d" % (at_policy, tag, page.index(tag)))

    # Every inlined element hashed, and every hash an element: one to one, both ways.
    for tag, directive in [("script", "script-src"), ("style", "style-src")]:
        bodies = re.findall(r"<%s>(.*?)</%s>" % (tag, tag), page, re.S)
        digests = {"'sha256-" + base64.b64encode(
            hashlib.sha256(b.encode("utf-8")).digest()).decode("ascii") + "'" for b in bodies}
        listed = set(said.get(directive, []))
        expect("every <%s> element is hashed in %s" % (tag, directive),
               digests <= listed, sorted(digests - listed))
        expect("every hash in %s belongs to a <%s> element" % (directive, tag),
               listed <= digests, sorted(listed - digests))
        expect("the count of <%s> elements matches %s" % (tag, directive),
               len(bodies) == len(said.get(directive, [])),
               "%d elements, %d hashes" % (len(bodies), len(said.get(directive, []))))

    # Nothing the browser would load on its own but the data: favicon.
    auto = re.findall(r'<(?!a\b)[a-zA-Z]+\b[^>]*?(?:src|href)\s*=\s*"([^"]+)"', page)
    remote = [u for u in auto if not u.startswith("data:")]
    expect("the page loads nothing of its own but a data: URI", not remote, remote)

    expect("the referrer policy is no-referrer",
           '<meta name="referrer" content="no-referrer">' in page)
    expect("the page refuses to run in a frame", "window.top !== window.self" in page)
    expect("every outward link carries rel=noreferrer",
           len(re.findall(r'<a\b[^>]*href="https?://', page))
           == len(re.findall(r'<a\b[^>]*rel="noreferrer"', page)))

    return finish()


def finish():
    print("\n%d checks, %d failures" % (checks, len(bad)))
    return 1 if bad else 0


sys.exit(main())
