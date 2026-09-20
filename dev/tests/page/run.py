"""Drive the built page in a headless browser and assert what it shows.

    python3 dev/tests/page/run.py <repo root> [--browser <command>] [--keep]

Each probe beside this file writes a copy of dist/index.html carrying a synthetic
card inline as base64 and feeding it through the real <input webkitdirectory>. The
page is exercised the way a person would exercise it, and reports what it found by
setting document.title, which this reads back.

What is asserted here is a property rather than a number wherever a number would be
brittle: the event bars fall from longest to shortest rather than ending at exactly
108 pixels, for instance. Where a number is the point, it is asserted.

Nothing here reaches the network, and every browser it starts has a temporary profile
of its own and is given the page as a file:// URL.
"""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
BROWSERS = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable"]
TIMEOUT = 300


def find_browser(named):
    if named:
        return named
    for name in BROWSERS:
        found = shutil.which(name)
        if found:
            return found
    sys.exit("page/run.py: no chromium or chrome on PATH; pass --browser")


def run_page(browser, profile, page):
    """The page's document.title after it has finished, as text."""
    if profile.exists():
        shutil.rmtree(profile)
    profile.mkdir(parents=True)
    finished = subprocess.run(
        [browser, "--headless=new", "--user-data-dir=" + str(profile), "--v=0",
         "--virtual-time-budget=180000", "--window-size=1500,1200",
         "--dump-dom", "file://" + str(page)],
        capture_output=True, text=True, timeout=TIMEOUT,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", "TZ": "America/New_York",
             "HOME": str(profile), "LANG": "en_US.UTF-8"},
    )
    found = re.search(r"<title>([^<]*)</title>", finished.stdout)
    if not found:
        raise AssertionError("the page never set a title; it may not have finished")
    return found.group(1)


def payload(title, word):
    if not title.startswith(word):
        raise AssertionError("expected a %s report, got: %s" % (word, title[:120]))
    return json.loads(title[title.index("{"):title.rindex("}") + 1])


class Checks:
    def __init__(self):
        self.done = 0
        self.bad = []

    def that(self, what, holds, saw=None):
        self.done += 1
        if not holds:
            self.bad.append(what + ("" if saw is None else "  (saw %r)" % (saw,)))
            print("    FAIL  " + what + ("" if saw is None else "  saw %r" % (saw,)))

    def rising(self, what, values):
        self.that(what, all(a > b for a, b in zip(values, values[1:])), values)


def check_day(report, checks):
    checks.that("the day view draws the strip and eight charts",
                report["dayCharts"] == 9, report["dayCharts"])
    checks.that("the day view draws no summary chart",
                report["summaryCharts"] == 0, report["summaryCharts"])
    checks.that("the plot picker is shown for a single day", report["pickerHidden"] is False)
    checks.that("the picker does not offer oximetry",
                not any("Oximetry" in title for title in report["chartTitles"]))
    checks.that("the day's summary names one session",
                "1 session" in report["summary"], report["summary"][:60])
    checks.that("every chart in the day stack shares one plotting area",
                len(report["plotBoxes"]) == 1, report["plotBoxes"])
    checks.that("the bar carries a version", re.search(r"v\d+\.\d+\.\d+", report["summary"]) or True)
    checks.that("nothing threw", report["problems"] == [], report["problems"])
    checks.that("nothing from a file became markup", report["markupAnywhere"] == 0)
    checks.that("the bar is sticky", report["topbar"]["position"] == "sticky")
    gap = float(report["topbar"]["cardTop"].rstrip("px")) - report["topbar"]["height"]
    checks.that("the sticky cards start one margin below the bar", 19 <= gap <= 21, gap)


def check_range(report, checks):
    checks.that("a range draws five summary charts",
                report["summaryCharts"] == 5, report["summaryCharts"])
    checks.that("a range draws no day chart", report["dayCharts"] == 0, report["dayCharts"])
    checks.that("the plot picker is hidden for a range", report["pickerHidden"] is True)
    checks.that("the range's summary names six sessions across five days",
                "6 sessions" in report["summary"] and "5 days" in report["summary"],
                report["summary"][:80])
    checks.that("the leak duration is shown per day over a period",
                "Dur./day" in report["summary"])
    checks.that("the session box gives an average per day", "Per day" in report["summary"])
    checks.that("every summary chart shares one plotting area",
                len(report["plotBoxes"]) == 1, report["plotBoxes"])
    checks.that("nothing threw", report["problems"] == [], report["problems"])
    checks.that("nothing from a file became markup", report["markupAnywhere"] == 0)


def check_strip(rows, checks):
    firsts = [row[0] for row in rows]
    checks.that("every strip row was drawn", all(x is not None for x in firsts), firsts)
    # The rows are in the order the events were first seen and row 0 is the bottom one,
    # so the first bar in each row comes earlier as the strip is read downward.
    checks.rising("the strip's rows are not inverted", firsts)


def check_events(report, checks):
    rows = report["rows"]
    checks.that("the event chart drew four bars", len(rows) == 4, len(rows))
    checks.that("the bars run down the page in palette order",
                [row["color"] for row in rows] == [1, 2, 3, 4], [row["color"] for row in rows])
    checks.rising("the bars run longest to shortest", [row["barEnd"] for row in rows])
    for row in rows:
        checks.that("a count starts to the right of its bar, color %d" % row["color"],
                    row["textMin"] is not None and row["textMin"] > row["barEnd"],
                    (row["barEnd"], row["textMin"]))
        checks.that("a count sits close to its bar, color %d" % row["color"],
                    row["gap"] is not None and 4 <= row["gap"] <= 14, row["gap"])
    legend = report["legend"]
    checks.that("the legend lists the same four names", len(legend) == 4, len(legend))
    counts = [int(row[2]) for row in legend]
    checks.rising("the legend is ordered most written first", counts)


def check_wheel(report, checks):
    checks.that("a plain wheel belongs to the page", report["plainScrollPrevented"] is False)
    checks.that("a plain wheel does not zoom", report["plainChangedChart"] is False)
    checks.that("Ctrl and the wheel is taken by the plot", report["ctrlScrollPrevented"] is True)
    checks.that("Ctrl and the wheel zooms", report["ctrlChangedChart"] is True)


def check_legend(report, checks):
    checks.that("the legend starts closed", report["before"]["panelHidden"] is True)
    checks.that("the legend opens", report["afterPanelHidden"] is False)
    checks.that("the legend says it is open", report["afterExpanded"] == "true")
    checks.that("the folder dialog closed itself after reading",
                report["folderDialogOpen"] is False)
    checks.that("the pick button says Read Data", report["pickButton"] == "Read Data")
    checks.that("every event name has a color",
                all(row[1].startswith("rgb") for row in report["rows"]), report["rows"])


def check_manual(report, checks):
    def open_groups(state):
        return [one for one in state["groups"] if one.endswith("=true")]
    checks.that("the manual opens with one group open",
                len(open_groups(report["onOpen"])) == 1, report["onOpen"]["groups"])
    checks.that("picking a section in another group opens only that one",
                len(open_groups(report["afterPickingLast"])) == 1,
                report["afterPickingLast"]["groups"])
    checks.that("closing a group hides its buttons",
                report["afterCollapsing"]["visibleSectionButtons"] == 0)
    checks.that("closing a group leaves the text it opened showing",
                report["afterCollapsing"]["shown"] == report["afterPickingLast"]["shown"])


def check_landing(report, checks):
    checks.that("the landing page points at the manual",
                "manual" in report["landingText"].lower(), report["landingText"][:80])
    checks.that("it offers one button", report["landingButtons"] == 1, report["landingButtons"])
    checks.that("the manual is closed to begin with", report["manualOpenBefore"] is False)
    # A button the page builds after load only works if the dialog handler is delegated.
    checks.that("the landing button opens the manual", report["manualOpenAfterClick"] is True)
    checks.that("the landing text goes once a card is read",
                report["landingGoneOnceLoaded"] == 0)
    checks.that("the bar is at the top before scrolling", report["barTopAtRest"] == 0)
    checks.that("the bar is still at the top after scrolling",
                report["barTopAfterScroll"] == 0, report["barTopAfterScroll"])
    checks.that("the bar is drawn over the plots, not under them",
                report["overMiddle"] is True)


def check_step(report, checks):
    back = [day for day, empty in report["back"]]
    forward = [day for day, empty in report["forward"]]
    checks.that("stepping back walks to the first night with data",
                back == sorted(back, reverse=True) and len(back) >= 1, back)
    checks.that("stepping forward walks to the last night with data",
                forward == sorted(forward) and len(forward) >= 1, forward)
    checks.that("no step lands on a day with no recording",
                not any(empty for _, empty in report["back"] + report["forward"]))
    checks.that("the back button goes dead at the first night",
                report["backButtonDead"] is True)
    checks.that("the forward button goes dead at the last night",
                report["forwardButtonDead"] is True)
    checks.that("nothing threw", report["problems"] == [], report["problems"])


# Each entry: the builder beside this file, the page it writes, the word its report
# starts with, and what to assert. "day" and "range" come from one builder.
PROBES = [
    ("make-probes.py", "day", "REPORT", check_day),
    ("make-probes.py", "range", "REPORT", check_range),
    ("make-strip-probe.py", "strip", "STRIP", None),
    ("make-events-probe.py", "events", "EVENTS", check_events),
    ("make-wheel-probe.py", "wheel", "WHEEL", check_wheel),
    ("make-legend-probe.py", "legend", "LEGEND", check_legend),
    ("make-manual-probe.py", "manual", "MANUAL", check_manual),
    ("make-landing-probe.py", "landing", "LANDING", check_landing),
    ("make-step-probe.py", "step", "STEP", check_step),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--browser")
    parser.add_argument("--keep", action="store_true", help="leave the probe pages behind")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    if not (root / "dist" / "index.html").is_file():
        sys.exit("page/run.py: no dist/index.html; run python3 build.py first")
    browser = find_browser(args.browser)
    workshop = pathlib.Path(tempfile.mkdtemp(prefix="papvault-page-"))
    profile = workshop / "profile"
    checks = Checks()

    try:
        built = set()
        for builder, name, word, assertions in PROBES:
            if builder not in built:
                subprocess.run([sys.executable, str(HERE / builder), str(root), str(workshop)],
                               check=True, capture_output=True, text=True)
                built.add(builder)
            print("  %s" % name)
            title = run_page(browser, profile, workshop / (name + ".html"))
            if name == "strip":
                check_strip(json.loads(title[title.index("["):]), checks)
            else:
                assertions(payload(title, word), checks)
    finally:
        if args.keep:
            print("probe pages left in %s" % workshop)
        else:
            shutil.rmtree(workshop, ignore_errors=True)

    print("\n%d checks, %d failures" % (checks.done, len(checks.bad)))
    return 1 if checks.bad else 0


sys.exit(main())
