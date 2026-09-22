"""Nothing leaves the page, and nothing could if it tried.

    python3 dev/tests/outbound.py <repo root> [--browser <command>] [--keep]

Two questions, which are not the same question:

  1. Does the page request anything of its own? A plain load is watched with Chrome's
     own network log, which records every URL attempted and every hostname resolved.
     The pass is exactly one URL: the page.

  2. If something in the page tried to send data out, would it get out? A probe loads
     a synthetic card and then attempts to send the rendered summary to a host that is
     not the one serving the page, eighteen ways -- fetch, XHR, sendBeacon, WebSocket,
     EventSource, an image pixel, a script tag, a prefetch link, an iframe, a form, a
     dynamic import, eval, Function, a Worker, a service worker, WebRTC, a CSS url().
     The pass is that the page reports the policy refusing them AND that the network
     log shows no request and no DNS lookup for that host.

`policy.py` checks what the policy says. This checks what it does. A policy can read
correctly and still not be enforced the way it is meant to be, and only one of those
two things can be read off the file.

The host attempted is a `.invalid` name, which by standard never resolves, so nothing
is sent anywhere real even if every layer failed at once.
"""
import argparse
import html
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
BROWSERS = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable"]
AWAY = "papvault-escape-test.invalid"
TIMEOUT = 420

checks = 0
bad = []


def expect(what, holds, saw=None):
    global checks
    checks += 1
    if not holds:
        bad.append(what)
        print("    FAIL  " + what + ("" if saw is None else "\n            saw: %s" % (saw,)))


def find_browser(named):
    if named:
        return named
    for name in BROWSERS:
        found = shutil.which(name)
        if found:
            return found
    sys.exit("outbound.py: no chromium or chrome on PATH; pass --browser")


def run(browser, profile, page, netlog):
    if profile.exists():
        shutil.rmtree(profile)
    profile.mkdir(parents=True)
    finished = subprocess.run(
        [browser, "--headless=new", "--user-data-dir=" + str(profile), "--v=0",
         "--no-first-run", "--no-default-browser-check",
         # Chrome's own housekeeping would otherwise put requests in the log that have
         # nothing to do with the page.
         "--disable-background-networking", "--disable-component-update",
         "--disable-domain-reliability",
         "--log-net-log=" + str(netlog), "--net-log-capture-mode=Default",
         "--virtual-time-budget=400000", "--window-size=1500,1200",
         "--dump-dom", str(page)],
        capture_output=True, text=True, timeout=TIMEOUT,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", "TZ": "America/New_York",
             "HOME": str(profile), "LANG": "en_US.UTF-8"},
    )
    title = re.search(r"<title>([^<]*)</title>", finished.stdout)
    # A title read back out of the serialised DOM is HTML-escaped, so a report
    # carrying > or & arrives as &gt; or &amp;. Undo that before parsing.
    return (html.unescape(title.group(1)) if title else ""), reached(netlog)


def reached(netlog):
    """Every URL and hostname the browser touched, however the run ended."""
    raw = netlog.read_text(errors="replace") if netlog.exists() else ""
    urls = set(re.findall(r'"url":\s*"([^"]+)"', raw))
    hosts = set(re.findall(r'"host":\s*"([^"]+)"', raw))
    return {"urls": sorted(urls), "hosts": sorted(hosts), "raw": raw}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--browser")
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    built = root / "dist" / "index.html"
    if not built.is_file():
        sys.exit("outbound.py: no dist/index.html; run python3 build.py first")
    browser = find_browser(args.browser)
    workshop = pathlib.Path(tempfile.mkdtemp(prefix="papvault-outbound-"))
    profile = workshop / "profile"

    try:
        print("  a plain load of the built page")
        _, seen = run(browser, profile, "file://" + str(built), workshop / "plain.json")
        outside = [u for u in seen["urls"] if not u.startswith("file://")]
        expect("a plain load requests nothing of its own", not outside, outside)
        expect("a plain load resolves no hostname", not seen["hosts"], seen["hosts"])

        print("  eighteen attempts to send a card's data out")
        subprocess.run([sys.executable, str(HERE / "page" / "make-escape-probe.py"),
                        str(root), str(workshop)], check=True, capture_output=True, text=True)
        title, seen = run(browser, profile, "file://" + str(workshop / "escape.html"),
                          workshop / "escape.json")
        if "{" not in title:
            expect("the escape probe finished", False, title[:100])
            return finish()
        report = json.loads(title[title.index("{"):title.rindex("}") + 1])

        expect("the probe had a card loaded, so it was carrying real page data",
               bool(report.get("carrying")), report.get("carrying"))

        # What the page saw: the policy refusing things by name.
        blocked = {v.split()[0] for v in report["violations"]}
        for directive in ["connect-src", "img-src", "script-src-elem", "frame-src"]:
            expect("the policy refused something under %s" % directive,
                   directive in blocked, sorted(blocked))
        expect("running a string as code was refused",
               any("EvalError" in what for _, what in report["attempts"]),
               [w for _, w in report["attempts"] if "Eval" in w])

        # What actually happened: nothing reached the host, by any route.
        leaked = [u for u in seen["urls"] if AWAY in u] + [h for h in seen["hosts"] if AWAY in h]
        expect("no request reached the outside host", not leaked, leaked)
        expect("the outside host was never even looked up", AWAY not in seen["raw"])
        outside = [u for u in seen["urls"] if not u.startswith("file://")]
        expect("the run requested nothing but the page itself", not outside, outside)
    finally:
        if args.keep:
            print("  left behind in %s" % workshop)
        else:
            shutil.rmtree(workshop, ignore_errors=True)

    return finish()


def finish():
    print("\n%d checks, %d failures" % (checks, len(bad)))
    return 1 if bad else 0


sys.exit(main())
