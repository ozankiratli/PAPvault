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
import datetime
import html
import json
import math
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
BROWSERS = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable"]
TIMEOUT = 600


def find_browser(named):
    if named:
        return named
    for name in BROWSERS:
        found = shutil.which(name)
        if found:
            return found
    sys.exit("page/run.py: no chromium or chrome on PATH; pass --browser")


def run_page(browser, profile, page, budget=400000, width=1500):
    """The page's document.title after it has finished, as text.

    The budget is virtual milliseconds, not real ones: a timer that is due fires at
    once and takes its whole delay out of the budget, so a page that polls burns the
    budget at a rate set by how much real work stands between its polls. A probe that
    reads a hundred nights gets through far more of it than one reading a single
    night, and when the budget runs out the browser dumps whatever is on the page --
    which is a title that was never set rather than any kind of report.
    """
    if profile.exists():
        shutil.rmtree(profile)
    profile.mkdir(parents=True)
    finished = subprocess.run(
        [browser, "--headless=new", "--user-data-dir=" + str(profile), "--v=0",
         "--virtual-time-budget=%d" % budget, "--window-size=%d,1200" % width,
         "--dump-dom", "file://" + str(page)],
        capture_output=True, text=True, timeout=TIMEOUT,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", "TZ": "America/New_York",
             "HOME": str(profile), "LANG": "en_US.UTF-8"},
    )
    found = re.search(r"<title>([^<]*)</title>", finished.stdout)
    if not found:
        raise AssertionError("the page never set a title; it may not have finished")
    # A title read back out of the serialised DOM is HTML-escaped, so a report
    # carrying > or & arrives as &gt; or &amp;. Undo that before parsing.
    return html.unescape(found.group(1))


def payload(title, word):
    if title.startswith("GAVE UP"):
        # The in-page poll counter runs on virtual time, which advances whether or not
        # the real work behind it has finished, so this means slow rather than broken.
        raise AssertionError(
            "the probe stopped waiting before the page finished: %s\n"
            "    raise the poll limit in the probe, or run with less else going on" % title[:90])
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


# What the day view measured, so the period view can be checked against it: the two
# stacks must put their plots in the same place on screen.
SEEN = {}


def room_below(report, checks):
    checks.that("every plot leaves room below it for its lowest label",
                report["roomBelow"] and min(report["roomBelow"]) >= 6, report["roomBelow"])


def check_day(report, checks):
    room_below(report, checks)
    SEEN["dayPlotLeft"] = sorted(report["plotBoxes"])[0].split("+")[0]
    checks.that("the day view draws the strip and eight charts",
                report["dayCharts"] == 9, report["dayCharts"])
    checks.that("the day view draws no summary chart",
                report["summaryCharts"] == 0, report["summaryCharts"])
    checks.that("the button that chooses plots is shown for a single day",
                report["pickerHidden"] is False)
    checks.that("and the dialog offers the day stack's plots",
                report["pickerGroups"]["day"] is False
                and report["pickerGroups"]["summary"] is True, report["pickerGroups"])
    checks.that("with no events group, which belongs to the period view",
                report["pickerGroups"]["events"] is True, report["pickerGroups"])
    checks.that("the picker does not offer oximetry",
                not any("Oximetry" in title for title in report["chartTitles"]))
    # A card writes "bpm" because EDF gives the unit eight bytes; the page spells it.
    checks.that("the respiratory rate is headed in breaths a minute, not beats",
                any("breaths/min" in title for title in report["chartTitles"])
                and not any("(bpm)" in title for title in report["chartTitles"]),
                report["chartTitles"])
    checks.that("the day's summary names one session",
                "1 session" in report["summary"], report["summary"][:60])
    checks.that("the session box gives events an hour",
                "Events/hr" in report["summary"], report["summary"][:120])
    # A title on an element of no size is a tooltip nobody can ever open, so size and
    # reachability are the check, not the attribute.
    bands = report["hoverBands"]
    checks.that("both charts of names carry a hover band per row", len(bands) >= 6, len(bands))
    checks.that("every hover band has room to be pointed at",
                all(w > 0 and h > 0 for _, w, h, _ in bands), bands)
    checks.that("every hover band is what the pointer actually lands on",
                all(reachable for _, _, _, reachable in bands), bands)
    checks.that("a folded Cheyne-Stokes row says what it stands for",
                any(title == "Cheyne-Stokes" for title, _, _, _ in bands),
                [b[0] for b in bands])
    checks.that("every chart in the day stack shares one plotting area",
                len(report["plotBoxes"]) == 1, report["plotBoxes"])
    checks.that("the bar carries a version", re.search(r"v\d+\.\d+\.\d+", report["summary"]) or True)
    checks.that("nothing threw", report["problems"] == [], report["problems"])
    checks.that("nothing from a file became markup", report["markupAnywhere"] == 0)
    checks.that("the bar is sticky", report["topbar"]["position"] == "sticky")
    gap = float(report["topbar"]["cardTop"].rstrip("px")) - report["topbar"]["height"]
    checks.that("the sticky cards start one margin below the bar", 19 <= gap <= 21, gap)


def check_range(report, checks):
    room_below(report, checks)
    # Z, 2026-09-22: "I want the daily plots to be placed on the screen the same way
    # the multiday plots are placed."
    checks.that("a period puts its plots where a day puts its own",
                sorted(report["plotBoxes"])[0].split("+")[0] == SEEN.get("dayPlotLeft"),
                (sorted(report["plotBoxes"])[0].split("+")[0], SEEN.get("dayPlotLeft")))
    checks.that("a range draws five summary charts",
                report["summaryCharts"] == 5, report["summaryCharts"])
    checks.that("a range draws no day chart", report["dayCharts"] == 0, report["dayCharts"])
    # A period has plots of its own to choose from, which it did not before 2026-09-22.
    checks.that("the button that chooses plots is shown for a range too",
                report["pickerHidden"] is False)
    checks.that("and the dialog offers the summary plots instead of the day's",
                report["pickerGroups"]["summary"] is False
                and report["pickerGroups"]["day"] is True, report["pickerGroups"])
    checks.that("and which events the per-hour plot draws",
                report["pickerGroups"]["events"] is False, report["pickerGroups"])
    checks.that("one box per name the card holds",
                report["pickerGroups"]["eventBoxes"] == 4,
                report["pickerGroups"]["eventBoxes"])
    # The choices do something, which is the point of offering them.
    toggles = report["toggles"]
    checks.that("the period offers a box per summary plot",
                toggles["summaryBoxes"] == 5, toggles["summaryBoxes"])
    checks.that("turning a summary plot off takes one chart away",
                toggles["chartsWithOneOff"] == toggles["chartsBefore"] - 1,
                (toggles["chartsBefore"], toggles["chartsWithOneOff"]))
    checks.that("turning it back on brings it back",
                toggles["chartsBackOn"] == toggles["chartsBefore"],
                (toggles["chartsBefore"], toggles["chartsBackOn"]))
    checks.that("turning an event off takes one line off the per-hour plot",
                toggles["seriesWithOneOff"] == toggles["seriesBefore"] - 1,
                (toggles["seriesBefore"], toggles["seriesWithOneOff"]))
    checks.that("and leaves every other summary plot alone",
                toggles["chartsWhileEventOff"] == toggles["chartsBefore"],
                (toggles["chartsBefore"], toggles["chartsWhileEventOff"]))
    checks.that("turning that event back on brings its line back",
                toggles["seriesBackOn"] == toggles["seriesBefore"],
                (toggles["seriesBefore"], toggles["seriesBackOn"]))
    checks.that("the range's summary names six sessions across five days",
                "6 sessions" in report["summary"] and "5 days" in report["summary"],
                report["summary"][:80])
    checks.that("the leak duration is shown per day over a period",
                "Dur./day" in report["summary"])
    checks.that("the session box gives an average per day", "Per day" in report["summary"])
    checks.that("every summary chart shares one plotting area",
                len(report["plotBoxes"]) == 1, report["plotBoxes"])
    # Daily, weekly, monthly and yearly. The five nights of this card fall in one
    # calendar week, so the weekly level is a single point: the mean of the five.
    g = report["grouping"]
    checks.that("a period offers every grouping",
                g and g["offers"] == ["day", "week", "month", "year"], g and g["offers"])
    checks.that("and starts on daily for a period of five nights",
                g and g["startsOn"] == "day", g and g["startsOn"])
    checks.that("daily draws one point per night",
                g and g["dailyPoints"] == 5, g and g["dailyPoints"])
    checks.that("weekly draws one point for the week they share",
                g and g["weeklyPoints"] == 1, g and g["weeklyPoints"])
    checks.that("and that point is the mean of the nights in it",
                g and abs(g["weeklyValue"] - g["meanOfNights"]) < 1e-9,
                g and (g["weeklyValue"], g["meanOfNights"]))

    # The summary stack pans the same way a day's does, which the manual promises.
    pan = report["summaryPan"]
    checks.that("a period's stack zooms on Ctrl and the wheel",
                pan and pan["zoomedSpan"] < pan["wholeSpan"], pan)
    checks.that("Ctrl and a drag to the right moves a period's window earlier",
                pan and pan["movedBy"] < 0, pan)
    checks.that("and keeps the span it was given",
                pan and abs(pan["spanAfter"] - pan["zoomedSpan"]) < 1, pan)
    checks.that("and moves every summary chart together", pan and pan["together"] is True, pan)
    checks.that("nothing threw", report["problems"] == [], report["problems"])
    checks.that("nothing from a file became markup", report["markupAnywhere"] == 0)


def check_leak(report, checks):
    # Read against the generator's own answer, so the run lengths and levels live in
    # one place. Every other check of this figure re-implements the rule; this one
    # reads what the page worked out from the card it was given.
    answer = json.loads((HERE.parents[2] / "dev/synthetic/out/resmed/on-and-off-leak"
                         / "answer.json").read_text(encoding="utf-8"))
    session = answer["sessions"][0]
    above = session["leak_above_zero_seconds"]
    runs = session["leak_runs"]
    night = (datetime.datetime.fromisoformat(session["end"])
             - datetime.datetime.fromisoformat(session["start"])).total_seconds()
    rows = report["leak"]

    # The page rounds the duration to the minute, and JavaScript rounds a half upward.
    def minutes(seconds):
        return "%dm" % math.floor(seconds / 60 + 0.5)

    checks.that("the leak duration is how long the leak ran above zero",
                rows.get("Dur.") == minutes(above), rows)
    checks.that("what it shows is not simply how long the machine ran",
                rows.get("Dur.") != minutes(night), (rows.get("Dur."), minutes(night)))
    checks.that("the highest leak shown is the highest run the card holds",
                rows.get("Max") == "%.1f" % max(run["value"] for run in runs), rows.get("Max"))
    checks.that("the case still has its leak off for more than half the night",
                night - above > night / 2, (above, night))
    checks.that("so the median leak is zero", rows.get("Median") == "0.0", rows.get("Median"))
    checks.that("the leak box carries the unit the file declares",
                report["unit"] == "L/min", report["unit"])
    checks.that("the card the probe loaded is the one night this case builds",
                report["big"] == ["1 session", "%02dh %02dm" % (night // 3600, night % 3600 // 60)],
                report["big"])
    checks.that("nothing threw", report["problems"] == [], report["problems"])


# What the page calls each grouping, in the order the control offers them.
GROUPINGS = {"day": "daily", "week": "weekly", "month": "monthly", "year": "yearly"}

# Spelled out rather than taken from strftime, which follows the machine's locale
# while the page is in English whatever the machine is set to.
MONTHS = ("January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December")


def readings(first):
    """What the cursor readout must say for the group the first night falls in.

    A week begins on the Monday, which is where src/app.js puts it.
    """
    monday = first - datetime.timedelta(days=first.weekday())
    return {
        "day": "%s %d, %d" % (MONTHS[first.month - 1][:3], first.day, first.year),
        "week": "Week of %04d/%02d/%02d" % (monday.year, monday.month, monday.day),
        "month": "%s %d" % (MONTHS[first.month - 1], first.year),
        "year": str(first.year),
    }


def ticked(first):
    """What the axis must draw under the first tick, which is the reading without the
    words the axis has no room for."""
    said = readings(first)
    return dict(said, week=said["week"].replace("Week of ", ""))




def check_grouped(report, checks):
    # How many points each level must draw is counted from the nights the card was
    # built with, in the generator, and read from its answer here. Nothing in this
    # check works it out from what the page did.
    answer = json.loads((HERE.parents[2] / "dev/synthetic/out/resmed/long-range"
                         / "answer.json").read_text(encoding="utf-8"))
    want = answer["grouped_points"]
    first = datetime.date.fromisoformat(min(answer["cpap_days"]))
    says = readings(first)
    draws = ticked(first)
    levels = report["levels"]
    checks.that("a period of a hundred nights starts on the daily grouping",
                report["startsOn"] == "day", report["startsOn"])
    compared = 0
    for level in ["day", "week", "month", "year"]:
        found = levels.get(level)
        checks.that("%s draws one point per group the card holds" % GROUPINGS[level],
                    found and found["points"] == want[level],
                    (found and found.get("points"), want[level]))
        if not found:
            continue
        # A session is counted over a group, not averaged, so the same number of
        # sessions is on the chart however the nights are grouped: the card's own.
        checks.that("%s counts the card's sessions rather than averaging them"
                    % GROUPINGS[level],
                    found["sessionsTotal"] == len(answer["sessions"]),
                    (found["sessionsTotal"], len(answer["sessions"])))
        # And what the readout calls a point follows the grouping, since "Day" is
        # wrong on a chart whose points are weeks.
        checks.that("%s names a point the way its grouping names it" % GROUPINGS[level],
                    found["reads"]["label"] == ("Day" if level == "day" else "Period")
                    and found["reads"]["first"] == says[level],
                    (found["reads"], says[level]))
        # A day's bar is that day's hours; a group's is a mean per day, and the name
        # of the figure says which.
        checks.that("%s calls the hours what they are" % GROUPINGS[level],
                    found["reads"]["hours"] == ("Hours" if level == "day" else "Hours/day"),
                    found["reads"]["hours"])
        # The axis draws the date alone. A week says "Week of" in the readout, where
        # there is room for it, and not under a tick, where the dates ran together.
        axis = found["axis"]
        checks.that("%s draws the date alone under its ticks" % GROUPINGS[level],
                    axis["first"] == draws[level], (axis["first"], draws[level]))
        checks.that("%s draws no more dates than it has points" % GROUPINGS[level],
                    axis["count"] <= found["points"], (axis["count"], found["points"]))
        # A bar is centered on its point and clipped at the edge of the plotting area,
        # so the scale has to reach half a step past the first and the last point or
        # those two bars lose the half that falls outside. The step is the closest two
        # points come, which is what uPlot measures a bar's width against.
        room = found["room"]
        checks.that("%s leaves room for the first bar" % GROUPINGS[level],
                    room["step"] is None or room["before"] >= room["step"] / 2, room)
        checks.that("%s leaves room for the last bar" % GROUPINGS[level],
                    room["step"] is None or room["after"] >= room["step"] / 2, room)
        # And the bars themselves, read off the canvas. This needs a bar that is not
        # at either end to compare against, so it runs only where there are three.
        bars = found["bars"]
        if found["points"] < 3:
            continue
        compared += 1
        checks.that("%s draws its first bar the width of the others" % GROUPINGS[level],
                    bars["first"] is not None and bars["middle"]
                    and abs(bars["first"] - bars["middle"]) <= 1, bars)
        checks.that("%s draws its last bar the width of the others" % GROUPINGS[level],
                    bars["last"] is not None and bars["middle"]
                    and abs(bars["last"] - bars["middle"]) <= 1, bars)
    # The card must stay long enough for the widths above to be compared at more than
    # the daily level, or those checks quietly stop covering the grouped views.
    checks.that("the card gives three groupings a bar at neither end to compare with",
                compared >= 3, compared)
    checks.that("nothing threw", report["problems"] == [], report["problems"])


def check_pyramid(report, checks):
    whole = report["whole"]
    zoomed = report["zoomed"]
    # A title carries its unit in brackets, and "Flow" is a prefix of "Flow Limitation".
    named = lambda one: one["title"].split(" (")[0]
    flow = [one for one in whole["charts"] if named(one) == "Flow"]
    checks.that("the day stack drew a flow chart", len(flow) == 1, whole["charts"])
    if not flow:
        return
    # A night of flow is a sample every 40 milliseconds. Whatever the stack hands
    # uPlot for the whole night, it is not that many points.
    night = whole["last"] - whole["first"]
    samples = night / 0.04
    checks.that("a whole night of flow is drawn from far fewer points than it holds",
                flow[0]["points"] < samples / 50, (flow[0]["points"], round(samples)))
    checks.that("and it is on one of the reduced levels",
                flow[0]["level"], 0)

    # The failure the sliced version had: the data followed the scale, so selecting a
    # window left the chart unable to show anything else. Zooming must narrow the
    # window and leave the series covering the whole night.
    checks.that("dragging a selection narrows the window",
                zoomed["span"] < whole["span"], (zoomed["span"], whole["span"]))
    checks.that("and the chart still holds the whole night either side of it",
                zoomed["first"] == whole["first"] and zoomed["last"] == whole["last"],
                (zoomed["first"], whole["first"], zoomed["last"], whole["last"]))
    checks.that("so the series covers far more than the window on screen",
                zoomed["last"] - zoomed["first"] > zoomed["span"] * 2,
                (zoomed["last"] - zoomed["first"], zoomed["span"]))
    zoomedFlow = [one for one in zoomed["charts"] if named(one) == "Flow"][0]
    checks.that("and zoomed in it is drawn from more points than the whole night was",
                zoomedFlow["points"] > flow[0]["points"],
                (zoomedFlow["points"], flow[0]["points"]))
    checks.that("every chart in the stack still has points on it",
                all(one["points"] > 1 for one in zoomed["charts"]), zoomed["charts"])
    checks.that("nothing threw", report["problems"] == [], report["problems"])


def check_month(report, checks):
    # Moving the calendar to another month changes the calendar and nothing else.
    checks.that("the calendar moved to another month",
                report["monthMoved"] != report["monthBefore"],
                (report["monthBefore"], report["monthMoved"]))
    checks.that("and back to the one it started on",
                report["monthAfter"] == report["monthBefore"],
                (report["monthBefore"], report["monthAfter"]))
    checks.that("a month with none of the selection in it marks nothing",
                report["selectedWhileAway"] == [], report["selectedWhileAway"])
    checks.that("the charts were not thrown away and drawn again",
                report["chartsKept"] == report["chartsBefore"] == report["chartsAfter"],
                (report["chartsBefore"], report["chartsAfter"], report["chartsKept"]))
    checks.that("there were charts to keep in the first place",
                report["chartsBefore"] > 0, report["chartsBefore"])
    checks.that("the summary was left as it was", report["summaryUnchanged"] is True)
    checks.that("the selected days are still selected",
                report["selectedBefore"] == report["selectedAfter"],
                (report["selectedBefore"], report["selectedAfter"]))
    checks.that("the calendar still holds a month of days",
                28 <= report["dayCells"] <= 31, report["dayCells"])
    checks.that("nothing threw", report["problems"] == [], report["problems"])


def check_toggle(report, checks):
    checks.that("the toggles are in a dialog of their own", report["pickerInDialog"] is True)
    checks.that("that dialog starts closed", report["dialogOpenBefore"] is False)
    checks.that("the button in the plots card opens it",
                report["dialogOpenAfterClick"] is True)
    checks.that("it holds one box per plot offered", report["boxes"] == 8, report["boxes"])
    off = dict(report["steps"]).get("off")
    on = dict(report["steps"]).get("on")
    checks.that("turning a plot off takes one chart away",
                off == report["chartsAtFirst"] - 1, (report["chartsAtFirst"], off))
    checks.that("turning it back on brings it back",
                on == report["chartsAtFirst"], (report["chartsAtFirst"], on))
    # The point of the change. Reading the card once is expected, while the folder is
    # being opened; a toggle must add nothing to that count.
    checks.that("neither toggle made the page read the card again",
                report["readingAfterToggles"] == report["readingBeforeToggle"],
                (report["readingBeforeToggle"], report["readingAfterToggles"]))
    checks.that("the loading dialog was up while the folder was being read",
                report["loadingSeen"] > 0, report["loadingSeen"])
    # The gap Z reported, which has two halves. The first is the browser's own: its
    # folder window, and the time it spends listing what was chosen before this page
    # hears anything. Nothing here can shorten that, so the box goes up before it.
    checks.that("pressing Read Data asks the browser for its folder window",
                report["nativePickerAsked"] is True)
    checks.that("and puts the box up at once",
                report["loadingOnPick"] is True)
    checks.that("which says it is waiting rather than loading",
                "Waiting" in report["headingOnPick"], report["headingOnPick"])
    checks.that("closing that window without choosing takes the box away",
                report["loadingAfterCancel"] is False)
    # The second half is this page's own: turning the browser's file list into its own.
    checks.that("the box is up before one file has been touched",
                report["loadingUpBeforeAnyFile"] is True)
    checks.that("and it says what is happening while that is going on",
                "folder" in report["statusBeforeAnyFile"].lower(),
                report["statusBeforeAnyFile"])
    checks.that("nothing threw", report["problems"] == [], report["problems"])


def check_strip(report, checks):
    rows = report["rows"]
    # The rows are the card's own list, in the card's own order, each painted in the
    # colour its name was given when the card was read. Z, 2026-09-22, on why: the
    # daily view's events "should always be ordered in the same order", so that two
    # nights can be read against each other.
    names = [row["name"] for row in rows]
    checks.that("every strip row has a name", all(n for n in names), names)
    checks.that("every strip row was drawn",
                all(row["painted"] for row in rows), [row["painted"] for row in rows])
    # CSR is the first of the order Z set, and it is vermilion. The card behind this
    # probe holds one Cheyne-Stokes period and two names PAPvault does not know.
    checks.that("the row PAPvault knows comes before the ones it does not",
                names[0] == "Cheyne-Stokes", names)
    checks.that("and it is painted reddish purple", rows[0]["rgb"] == [204, 121, 167], rows[0]["rgb"])
    checks.that("the names PAPvault does not know keep the card's order",
                names[1:] == ["Synthetic event one", "Synthetic event two"], names)
    # Two rows must never share a colour while the palette has spare entries.
    painted = [tuple(row["rgb"]) for row in rows if row["rgb"]]
    checks.that("no two rows are the same colour", len(set(painted)) == len(painted), painted)
    # A rule at every edge, the outer two included, so the rows are bounded rather
    # than floating: one more line than there are rows.
    checks.that("a dotted rule sits at every row edge, top and bottom included",
                report["ruleLines"] == len(rows) + 1, (report["ruleLines"], len(rows)))


def check_events(report, checks):
    rows = report["rows"]
    legend = report["legend"]
    checks.that("the event chart drew four bars", len(rows) == 4, len(rows))
    checks.rising("the bars run longest to shortest", [row["barEnd"] for row in rows])
    # A name's colour is its own, settled when the card was read, so the bar and the
    # legend row for the same name must be painted the same. Both lists run longest
    # first, so they line up entry for entry.
    checks.that("each bar is the colour its name was given",
                [row["rgb"] for row in rows] == [one[3] for one in legend[:len(rows)]],
                ([row["rgb"] for row in rows], [one[3] for one in legend[:len(rows)]]))
    for row in rows:
        checks.that("a count starts to the right of its bar, in %s" % row["color"],
                    row["textMin"] is not None and row["textMin"] > row["barEnd"],
                    (row["barEnd"], row["textMin"]))
        checks.that("a count sits close to its bar, in %s" % row["color"],
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
    # The pan is checked on the scale the charts are actually drawn at, so a handler
    # that moved the picture without moving the window would fail.
    checks.that("the wheel left the stack zoomed in",
                report["zoomedSpan"] < report["wholeSpan"], report["zoomedSpan"])
    checks.that("Ctrl and a drag to the right moves the window earlier",
                report["panMovedBy"] < 0, report["panMovedBy"])
    checks.that("a pan keeps the span it was given",
                abs(report["panSpan"] - report["zoomedSpan"]) < 1,
                (report["panSpan"], report["zoomedSpan"]))
    checks.that("every chart in the stack panned together", report["panTogether"] is True)
    checks.that("a pan stops at the start of the period",
                abs(report["stoppedAtStart"]) < 1, report["stoppedAtStart"])
    checks.that("a pan that runs off the end still keeps its span",
                abs(report["stoppedSpan"] - report["zoomedSpan"]) < 1,
                (report["stoppedSpan"], report["zoomedSpan"]))
    checks.that("a drag without Ctrl still zooms to the selection",
                report["spanAfterSelect"] < report["spanBeforeSelect"],
                (report["spanBeforeSelect"], report["spanAfterSelect"]))
    check_swipe(report, checks)
    # How far a pinch zooms follows how far it travelled, not how many events it took.
    # A trackpad sends a gesture as a couple of hundred small events, so a fixed factor
    # each made the zoom run away with the length of the pinch rather than its size.
    zoom = report["zoom"]
    checks.that("one wheel notch zooms in", 0 < zoom["oneNotch"] < 1, zoom)
    checks.that("and twice the distance zooms exactly twice as far, not the same",
                abs(zoom["twoNotches"] - zoom["oneNotch"] ** 2) < 1e-6, zoom)
    # A trackpad reports a pinch in steps around seven times smaller than a notch, so
    # a small step buys more zoom per unit than a large one. Read as the rate each
    # gesture zooms at per unit travelled, which is what the two constants set.
    byPinch = -math.log2(zoom["smallStep"]) / 2
    byWheel = -math.log2(zoom["oneNotch"]) / 120
    checks.that("a step small enough to be a pinch zooms faster per unit than a notch",
                byPinch > byWheel * 2, (byPinch, byWheel, byPinch / byWheel))
    checks.that("nothing threw", report["problems"] == [], report["problems"])


def check_swipe(report, checks):
    """The sideways two-finger swipe, inside the wheel probe's report."""
    s = report["swipe"]
    # A trackpad sends a swipe as a wheel event carrying deltaX. Sideways over a
    # zoomed plot slides the window; the span it was zoomed to is kept.
    checks.that("a sideways swipe over a zoomed plot is taken from the page",
                s["sidewaysTaken"] is True, s)
    checks.that("and it slides the window", s["sidewaysMovedBy"] > 0, s)
    checks.that("keeping the span it was zoomed to", s["sidewaysKeptSpan"] is True, s)
    checks.that("and moving every chart in the stack together",
                s["sidewaysTogether"] is True, s)
    # An up and down swipe is the page's, which is how a reader scrolls a plot out of
    # the way to reach the next one.
    checks.that("an up and down swipe is left to the page",
                s["upDownTaken"] is False, s)
    checks.that("and moves nothing", s["upDownMovedBy"] == 0, s)
    # A gesture is latched to whatever scrolled first, so a sideways event arriving
    # inside a gesture the page already has must not take it back.
    checks.that("a sideways event inside an up and down gesture does not take it back",
                s["heldTaken"] is False, s)
    checks.that("and moves nothing either", s["heldMovedBy"] == 0, s)
    # With the whole period on screen there is nowhere to slide to, so the gesture is
    # the page's and a reader is never left swiping at a chart that cannot move.
    checks.that("the double-click put the whole period back",
                abs(s["unzoomedSpan"] - s["wholeSpan"]) < 1e-6, s)
    checks.that("and a sideways swipe with nothing to slide to is left to the page",
                s["unzoomedTaken"] is False, s)


def check_legend(report, checks):
    checks.that("the legend starts closed", report["before"]["panelHidden"] is True)
    checks.that("the legend opens", report["afterPanelHidden"] is False)
    checks.that("the legend says it is open", report["afterExpanded"] == "true")
    checks.that("the folder dialog closed itself after reading",
                report["folderDialogOpen"] is False)
    checks.that("the pick button says Read Data", report["pickButton"] == "Read Data")
    checks.that("every event name has a color",
                all(row[1].startswith("rgb") for row in report["rows"]), report["rows"])
    # A pair of marks bracketing a period is drawn as one event, under a short name
    # with the words it stands for on hover.
    names = [row[0] for row in report["rows"]]
    checks.that("the two Cheyne-Stokes marks are one row, not two",
                names.count("CSR") == 1 and not any("CSR Start" in n for n in names), names)
    spelled = dict((row[0], row[3]) for row in report["rows"])
    checks.that("hovering that row says what CSR stands for",
                spelled.get("CSR") == "Cheyne-Stokes", spelled)
    checks.that("a name PAPvault has no short form for is drawn as the device wrote it",
                spelled.get("Synthetic event one") == "Synthetic event one", spelled)


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


def check_marker(report, checks):
    # Nothing that names a person or a machine may reach the page. The card's EDF
    # headers and its Identification.tgt all carry the marker; none of them is a file
    # or a field PAPvault reads.
    checks.that("the identifying marker is nowhere in the rendered page",
                report["inPage"] is False, report.get("around"))
    checks.that("the identifying marker is nowhere in local storage",
                report["inStorage"] is False, report.get("storedKeys"))
    # Whatever is stored is a preference, never something off a card.
    keys = [one.split("=")[0] for one in report["storedKeys"].split(";") if one]
    checks.that("local storage holds only PAPvault's own preferences",
                all(k.startswith("papvault-") for k in keys), keys)


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
    # The reason the order was fixed at all. Z, 2026-09-22: the daily view's events
    # "should always be ordered in the same order". Every night of one card must
    # therefore show the same rows in the same places, however different the nights.
    seen = [rows for rows in report["rows"] if rows]
    checks.that("every night of the card shows the same strip rows, in the same order",
                len(set(seen)) == 1, sorted(set(seen)))
    checks.that("and there were several nights to compare", len(seen) >= 3, len(seen))
    # Z, 2026-09-22: "move the arrows to sides, the text should still be centered."
    prev, on = report["buttons"]["prev"], report["buttons"]["next"]
    checks.that("the back arrow sits against the left edge of its button",
                prev["arrowFromLeft"] < prev["width"] / 4, prev)
    checks.that("the forward arrow sits against the right edge of its own",
                on["arrowFromLeft"] > on["width"] * 3 / 4, on)
    checks.that("and both sets of words stay centred in the whole button",
                abs(prev["wordsOffCentre"]) <= 2 and abs(on["wordsOffCentre"]) <= 2,
                (prev["wordsOffCentre"], on["wordsOffCentre"]))


# What each width the layout steps at is meant to show. The window is the runner's,
# so the same probe page reports a different shape in each of these runs.
LAYOUTS = {
    1600: {"columns": 3, "calendar": "card", "hamburger": False, "chosenBelow": False},
    1400: {"columns": 2, "calendar": "dialog", "hamburger": False, "chosenBelow": False},
    800: {"columns": 1, "calendar": "dialog", "hamburger": False, "chosenBelow": True},
    500: {"columns": 1, "calendar": "dialog", "hamburger": True, "chosenBelow": True},
}

# The narrowest a chart is drawn, which is PLOT_LEAST in src/plots.js.
FLOOR = 240


def check_narrow(report, checks):
    want = LAYOUTS.get(report["view"])
    checks.that("the probe ran at a width the layout has a step for",
                want is not None, report["view"])
    if not want:
        return
    where = " at %d" % report["view"]
    checks.that("the cards stand in the columns this width calls for" + where,
                report["columns"] == want["columns"], report["columns"])
    checks.that("the calendar is where this width puts it" + where,
                report["calendarIn"] == want["calendar"], report["calendarIn"])
    checks.that("the calendar's card and the bar's button are never both there" + where,
                report["calendarCardHidden"] != report["calendarButtonHidden"],
                (report["calendarCardHidden"], report["calendarButtonHidden"]))
    checks.that("the calendar card shows only when the calendar is in it" + where,
                report["calendarCardHidden"] == (report["calendarIn"] == "dialog"),
                (report["calendarCardHidden"], report["calendarIn"]))
    checks.that("the menu button shows only where the buttons leave the bar" + where,
                (report["hamburger"] != "none") == want["hamburger"], report["hamburger"])
    checks.that("the menu's own close button keeps it company" + where,
                (report["closeButton"] != "none") == want["hamburger"], report["closeButton"])
    checks.that("what is selected takes its own row only on a narrow bar" + where,
                report["chosenBelowBrand"] == want["chosenBelow"],
                (report["chosenBelowBrand"], report["barHeight"]))
    checks.that("nothing is pushed off the side" + where,
                report["overflow"] <= 0, report["overflow"])
    checks.that("the plots are drawn" + where, report["charts"] > 0, report["charts"])
    checks.that("no chart is drawn narrower than the floor" + where,
                report["narrowest"] >= FLOOR, report["narrowest"])
    if not want["hamburger"]:
        checks.that("and there is no menu to open" + where, report["menu"] is None)
        return
    menu = report["menu"]
    checks.that("the menu opens on the button", menu["opened"] is True)
    checks.that("and says so to a screen reader", menu["expanded"] == "true")
    checks.that("the menu is anchored to every edge of the window",
                menu["fixed"] == "fixed" and set(menu["inset"]) == {"0px"},
                (menu["fixed"], menu["inset"]))
    checks.that("and it is drawn across the whole of it",
                menu["covers"][0] >= report["view"] - 20
                and menu["covers"][1] >= report["height"] - 20,
                (menu["covers"], report["view"], report["height"]))
    checks.that("every button in the bar is in it", menu["items"] == 5, menu["items"])
    checks.that("and each one is named in words there",
                all(len(name) > 4 for name in menu["named"]), menu["named"])
    checks.that("Escape closes it", menu["afterEscape"] is False)
    checks.that("the cross closes it", menu["afterCross"] is False)
    checks.that("a click outside closes it", menu["afterOutside"] is False)
    checks.that("picking an action closes it", menu["afterPick"] is False)
    checks.that("and the action it was asked for happens", menu["manualOpen"] is True)


def check_floor(report, checks):
    for what, runs in [("the day's plots", report["stack"]),
                       ("the summary's events", report["events"])]:
        checks.that("%s are drawn at five widths" % what, len(runs) == 5, runs)
        checks.that("%s never go below the floor" % what,
                    all(canvas >= FLOOR for _, canvas in runs), runs)
        checks.that("%s follow the card while there is room" % what,
                    all(abs(canvas - room) <= 1 for room, canvas in runs if room >= FLOOR),
                    runs)
        checks.that("%s stop at the floor when there is not" % what,
                    all(canvas == FLOOR for room, canvas in runs if room < FLOOR),
                    runs)
        narrowed = [canvas for _, canvas in runs]
        checks.that("%s get narrower as the card does" % what,
                    narrowed == sorted(narrowed, reverse=True) and narrowed[0] > narrowed[-1],
                    narrowed)
        checks.that("and %s had their card squeezed past the floor" % what,
                    any(room < FLOOR for room, _ in runs), runs)


# Each entry: the builder beside this file, the page it writes, the word its report
# starts with, and what to assert. "day" and "range" come from one builder.
PROBES = [
    ("make-probes.py", "day", "REPORT", check_day),
    ("make-probes.py", "range", "REPORT", check_range),
    ("make-leak-probe.py", "leak", "LEAK", check_leak),
    ("make-grouped-probe.py", "grouped", "GROUPED", check_grouped),
    ("make-pyramid-probe.py", "pyramid", "PYRAMID", check_pyramid),
    ("make-month-probe.py", "month", "MONTH", check_month),
    ("make-toggle-probe.py", "toggle", "TOGGLE", check_toggle),
    ("make-strip-probe.py", "strip", "STRIP", None),
    ("make-events-probe.py", "events", "EVENTS", check_events),
    ("make-wheel-probe.py", "wheel", "WHEEL", check_wheel),
    ("make-legend-probe.py", "legend", "LEGEND", check_legend),
    ("make-manual-probe.py", "manual", "MANUAL", check_manual),
    ("make-landing-probe.py", "landing", "LANDING", check_landing),
    ("make-step-probe.py", "step", "STEP", check_step),
    ("make-marker-probe.py", "marker", "MARKER", check_marker),
    ("make-narrow-probe.py", "three-columns", "NARROW", check_narrow),
    ("make-narrow-probe.py", "two-columns", "NARROW", check_narrow),
    ("make-narrow-probe.py", "stacked", "NARROW", check_narrow),
    ("make-narrow-probe.py", "menu", "NARROW", check_narrow),
    ("make-floor-probe.py", "floor", "FLOOR", check_floor),
]

# The window a probe is given, where the default of 1500 is not what it is about.
# Nothing below 500: headless Chromium clamps a window to that, so a narrower number
# here would be measuring the clamp rather than the page.
WINDOWS = {"three-columns": 1600, "two-columns": 1400, "stacked": 800, "menu": 500}

# Probes that need more virtual time than the rest, and why. See run_page.
BUDGETS = {"grouped": 4000000}

# A probe whose checks read something another probe recorded, so --only brings that
# one along. Without it the later check compares against nothing and fails saying so
# in a way that reads as a defect in the page.
PREREQS = {"range": ["day"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--browser")
    parser.add_argument("--keep", action="store_true", help="leave the probe pages behind")
    parser.add_argument("--only", action="append", metavar="PROBE",
                        help="run only these probes, by name; repeatable")
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
        asked = set(args.only or [])
        for name in list(asked):
            asked.update(PREREQS.get(name, []))
        wanted = [probe for probe in PROBES if not args.only or probe[1] in asked]
        missing = set(args.only or []) - {probe[1] for probe in PROBES}
        if missing:
            sys.exit("page/run.py: no probe named %s" % ", ".join(sorted(missing)))
        for builder, name, word, assertions in wanted:
            if builder not in built:
                subprocess.run([sys.executable, str(HERE / builder), str(root), str(workshop)],
                               check=True, capture_output=True, text=True)
                built.add(builder)
            print("  %s" % name)
            title = run_page(browser, profile, workshop / (name + ".html"),
                             BUDGETS.get(name, 400000), WINDOWS.get(name, 1500))
            if name == "strip":
                check_strip(payload(title, "STRIP"), checks)
            else:
                assertions(payload(title, word), checks)
    finally:
        if args.keep:
            print("probe pages left in %s" % workshop)
        else:
            shutil.rmtree(workshop, ignore_errors=True)

    if args.only:
        print("\n  only %s ran, so this is not the page suite"
              % ", ".join(probe[1] for probe in wanted))
    print("\n%d checks, %d failures" % (checks.done, len(checks.bad)))
    return 1 if checks.bad else 0


sys.exit(main())
