"""The published website, checked against the source it is supposed to be.

    python3 dev/tests/live.py [<url>] [--version <x.y.z>]

Run once after a release, and not before: everything here asks whether what is being
served is what was published, which has no answer until it is. It is the one part of
`dev/tests/` that reaches the network, so it is not in `run.sh`.

It asks four things:

  1. **What the host sends.** The design assumes the page arrives with no security
     header of its own, so its own `<meta>` policy is the one in force. A policy, a
     framing rule, a reporting header or a cookie from the host fails the run: a
     reporting header is collection even though the page is not the one doing it.

     What the host merely chooses -- whether it sends `Strict-Transport-Security`, for
     instance -- is printed rather than failed. The page cannot set a response header
     on this host, so no re-release could change it, and a check that fails for
     something outside the release teaches a person to skim the output. What is
     printed belongs in the release record, where a person can see what moved.

  2. **That nothing of the repository is served.** Only the built page is public;
     `src/`, `build.py`, `VERSION` and `CLAUDE.md` must all be 404.

  3. **That the served bytes are the bytes the source builds.** The page is fetched
     and its checksum compared with the local build, which is what makes the claim
     "rebuild it yourself and compare" a thing anyone can do rather than a promise.

  4. **That the page says which version it is.** A page that cannot be told apart from
     the one before it makes every other check ambiguous.

What it deliberately does not do is open a browser. Whether the policy is enforced is
answered by `outbound.py`, which attempts eighteen ways out of the page and watches
the browser's own network log; that runs against the same bytes this check proves are
the ones being served. What this adds is that the bytes are the same and that nothing
above them weakens the assumptions.
"""
import argparse
import hashlib
import http.client
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = "https://ozankiratli.github.io/PAPvault/"
TIMEOUT = 30
# Sent by the host rather than by the page. Each would change what is in force, or
# would make the browser report somewhere, so each is a finding.
UNWANTED = ["content-security-policy", "content-security-policy-report-only",
            "x-frame-options", "nel", "report-to", "reporting-endpoints", "set-cookie"]
# Nothing of the repository but the built page is served.
HIDDEN = ["src/app.js", "build.py", "VERSION", "CLAUDE.md"]

checks = 0
bad = []


def note(what, saw):
    """Something worth knowing that is not a failure: the host's to send, not ours."""
    print("    note  %s: %s" % (what, saw if saw is not None else "not sent"))


def expect(what, holds, saw=None):
    global checks
    checks += 1
    if not holds:
        bad.append(what)
        print("    FAIL  " + what + ("" if saw is None else "\n            saw: %s" % (saw,)))


def fetched(url, method="GET"):
    """The status, headers and body of one request, without following a redirect."""
    asked = urllib.request.Request(url, method=method,
                                   headers={"User-Agent": "PAPvault-live-check"})
    class Still(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *ignored):
            return None
    opener = urllib.request.build_opener(Still)
    try:
        with opener.open(asked, timeout=TIMEOUT) as answer:
            return answer.status, dict(answer.headers.items()), answer.read()
    except urllib.error.HTTPError as answer:
        return answer.code, dict(answer.headers.items()), answer.read()
    except (urllib.error.URLError, http.client.HTTPException, OSError) as trouble:
        return None, {"error": str(trouble)}, b""


def headerNamed(headers, name):
    for key, value in headers.items():
        if key.lower() == name:
            return value
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="?", default=SITE)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    built = root / "dist" / "index.html"
    if not built.is_file():
        sys.exit("live.py: no dist/index.html; run python3 build.py first")
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    url = args.url if args.url.endswith("/") else args.url + "/"

    print("  what the host sends")
    status, headers, body = fetched(url)
    if status is None:
        expect("the site answers", False, headers.get("error"))
        return finish()
    expect("the site answers 200", status == 200, status)
    expect("it is served as html, in utf-8",
           (headerNamed(headers, "content-type") or "").lower().replace(" ", "")
           == "text/html;charset=utf-8", headerNamed(headers, "content-type"))
    for name in UNWANTED:
        expect("the host sends no %s of its own" % name,
               headerNamed(headers, name) is None, headerNamed(headers, name))
    # Neither of these can be changed by releasing again: the page cannot set a
    # response header, and what the host sends is the host's. They are printed so a
    # release record carries them and a person can see what moved since last time.
    note("strict-transport-security", headerNamed(headers, "strict-transport-security"))
    note("access-control-allow-origin", headerNamed(headers, "access-control-allow-origin"))
    note("server", headerNamed(headers, "server"))

    plain = urllib.parse.urlunparse(("http",) + tuple(urllib.parse.urlparse(url))[1:])
    status, headers, _ = fetched(plain, method="HEAD")
    expect("plain http is redirected rather than served",
           status in (301, 302, 307, 308), status)
    expect("and it is redirected to https",
           (headerNamed(headers, "location") or "").startswith("https://"),
           headerNamed(headers, "location"))

    print("  nothing of the repository but the page")
    for path in HIDDEN:
        status, _, _ = fetched(urllib.parse.urljoin(url, path), method="HEAD")
        expect("%s is not served" % path, status == 404, status)

    print("  the page that is served is the page the source builds")
    served = hashlib.sha256(body).hexdigest()
    here = hashlib.sha256(built.read_bytes()).hexdigest()
    expect("the served page is byte for byte the local build", served == here,
           "served %s, built %s" % (served[:16], here[:16]))
    expect("the served page says which version it is",
           (">v%s<" % version).encode("ascii") in body, "VERSION says " + version)

    return finish()


def finish():
    print("\n%d checks, %d failures" % (checks, len(bad)))
    return 1 if bad else 0


sys.exit(main())
