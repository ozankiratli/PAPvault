"""Rebuild the grouped-view probe page from the current dist/index.html.

The weekly, monthly and yearly views cannot be drawn from a card of five nights in
one calendar week: every level above daily collapses to a single point. So this probe
loads `long-range` -- a hundred nights over a hundred and five days, crossing a year's
end -- selects the whole span, steps through every grouping and reports, for each one,
how many points were drawn, how much room the scale leaves past the first and the last
of them, and the drawn width of the first, a middle and the last bar of Hours Used.

The widths are read off the chart's own canvas rather than worked out from the options
it was built with. A bar is centered on its point and clipped at the edge of the
plotting area, so one whose point sits on that edge loses the half that falls outside
it, and nothing in the options says so: it has to be looked at. A cut bar comes back
about half the width of a middle one, which is what Z reported seeing.
"""
import base64, hashlib, json, pathlib, sys

ROOT = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")

CASE = "long-range"


def carry(case):
    card = ROOT / "dev/synthetic/out/resmed" / case
    files = []
    for path in sorted(card.rglob("*")):
        if not path.is_file() or path.name == "answer.json":
            continue
        rel = case + "/" + str(path.relative_to(card)).replace("\\", "/")
        files.append((rel, base64.b64encode(path.read_bytes()).decode()))
    return files


def span(case):
    answer = json.loads((ROOT / "dev/synthetic/out/resmed" / case
                         / "answer.json").read_text(encoding="utf-8"))
    days = sorted(answer["cpap_days"])
    return days[0], days[-1]


TEMPLATE = """
window.addEventListener("load", function () {
  var FILES = %s;
  var FIRST = %s;
  var LAST = %s;
  var MONTHS = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];
  var transfer = new DataTransfer();
  FILES.forEach(function (spec) {
    var raw = atob(spec[1]);
    var bytes = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) { bytes[i] = raw.charCodeAt(i); }
    transfer.items.add(new File([bytes], spec[0]));
  });
  window.papvaultProblems = [];
  window.addEventListener("error", function (e) { window.papvaultProblems.push(String(e.message)); });
  var input = document.getElementById("folder-input");
  input.files = transfer.files;
  input.dispatchEvent(new Event("change"));

  function loaded() {
    if (document.getElementById("loading-dialog").open) { return false; }
    if (!document.querySelector(".calendar-day.has-data")) { return false; }
    return document.getElementById("folder-status").textContent.indexOf("Reading") !== 0;
  }
  function drawn() {
    return document.querySelectorAll("#summary-plots .uplot").length > 0
      && document.getElementById("summary-body").textContent.indexOf("Reading") === -1;
  }

  // The span crosses four months, so the day to click is rarely the month on screen.
  function shownMonth() {
    var words = document.getElementById("calendar-month").textContent.trim().split(" ");
    return { month: MONTHS.indexOf(words[0]), year: parseInt(words[1], 10) };
  }
  function pickDay(iso) {
    var bits = iso.split("-");
    var year = parseInt(bits[0], 10);
    var month = parseInt(bits[1], 10) - 1;
    for (var guard = 0; guard < 60; guard++) {
      var at = shownMonth();
      var away = (year - at.year) * 12 + (month - at.month);
      if (!away) { break; }
      document.getElementById(away > 0 ? "calendar-next" : "calendar-prev").click();
    }
    var cell = document.querySelector('.calendar-day[aria-label="' + iso + '"]');
    if (!cell) { return false; }
    cell.click();
    return true;
  }

  function chartTitled(word) {
    var found = null;
    uPlot.sync("papvault-summary").plots.forEach(function (u) {
      var title = (u.root.querySelector(".u-title") || {}).textContent || "";
      if (title.indexOf(word) === 0) { found = u; }
    });
    return found;
  }

  // How wide a bar is drawn, in canvas pixels. The color under the bar's own center
  // is the one to follow, so the walk stops where the fill stops whatever else the
  // chart has drawn. A bar clipped at the edge of the plotting area stops there.
  function barWidth(u, index) {
    var left = Math.round(u.bbox.left);
    var width = Math.round(u.bbox.width);
    var y = Math.round(u.bbox.top + u.bbox.height) - 3;
    var center = Math.round(u.valToPos(u.data[0][index], "x", true));
    if (center < left || center >= left + width) { return null; }
    var row = u.ctx.getImageData(left, y, width, 1).data;
    function at(x) {
      var i = (x - left) * 4;
      return row[i] + "," + row[i + 1] + "," + row[i + 2] + "," + row[i + 3];
    }
    var color = at(center);
    if (color === "0,0,0,0") { return 0; }
    var from = center;
    var to = center;
    while (from > left && at(from - 1) === color) { from--; }
    while (to < left + width - 1 && at(to + 1) === color) { to++; }
    return to - from + 1;
  }

  // The chart carrying the dates is the last of the stack; the ones above it draw no
  // time axis at all.
  function dateChart() {
    var nodes = document.querySelectorAll("#summary-plots .uplot");
    var last = nodes[nodes.length - 1];
    var found = null;
    uPlot.sync("papvault-summary").plots.forEach(function (one) {
      if (one.root === last) { found = one; }
    });
    return found;
  }

  // The dates drawn under the chart: the first of them, and how many there are.
  function axisOf() {
    var u = dateChart();
    if (!u) { return null; }
    var splits = u.axes[0].splits(u);
    return { first: u.axes[0].values(u, splits)[0], count: splits.length };
  }

  function measure() {
    var u = chartTitled("Hours Used");
    if (!u) { return null; }
    var xs = u.data[0];
    // Sessions are counted over a group rather than averaged, so their total is the
    // same at every grouping and is the number of sessions on the card.
    var sessions = chartTitled("Sessions");
    var last = xs.length - 1;
    // The closest two points come, which is what uPlot measures a bar's width
    // against. A month is not a fixed length, so the mean gap is not it.
    var step = null;
    for (var i = 1; i < xs.length; i++) {
      if (step === null || xs[i] - xs[i - 1] < step) { step = xs[i] - xs[i - 1]; }
    }
    return {
      points: xs.length,
      // What the cursor readout says a point is: the name in front of it, and the
      // reading itself for the first point.
      reads: {
        label: (u.root.querySelector(".u-legend .u-series th") || {}).textContent || null,
        first: u.series[0].value(u, xs[0]),
        // What the hours are called, which says whether a point is a day or a mean
        // of days.
        hours: u.series[1].label
      },
      axis: axisOf(),
      sessionsTotal: sessions
        ? sessions.data[1].reduce(function (sum, one) { return sum + (one || 0); }, 0)
        : null,
      room: { before: xs[0] - u.scales.x.min, after: u.scales.x.max - xs[last], step: step },
      bars: { first: barWidth(u, 0), middle: barWidth(u, Math.floor(last / 2)),
              last: barWidth(u, last) }
    };
  }

  var LEVELS = ["day", "week", "month", "year"];
  function eachLevel(index, out, then) {
    if (index >= LEVELS.length) { then(out); return; }
    var pick = document.getElementById("grouping");
    pick.value = LEVELS[index];
    pick.dispatchEvent(new Event("change"));
    setTimeout(function () {
      out[LEVELS[index]] = measure();
      eachLevel(index + 1, out, then);
    }, 600);
  }

  var tries = 0;
  var picked = 0;
  (function step() {
    // Polls, not milliseconds. This has to stay inside the virtual time run.py gives
    // this probe, or the browser stops the page first and the report is never set.
    if (++tries > 100000) {
      document.title = "GAVE UP picked=" + picked
        + " month=" + document.getElementById("calendar-month").textContent
        + " cells=" + document.querySelectorAll(".calendar-day").length
        + " " + document.getElementById("summary-body").textContent.slice(0, 60);
      return;
    }
    if (!loaded()) { setTimeout(step, 25); return; }
    if (picked < 2) {
      // One click each, and only the one that failed is tried again. A third click on
      // the calendar starts the selection over, so retrying the pair would fight the
      // page rather than wait for it. The counter is reset once both have landed and
      // not before, or a pick that never succeeds loops silently until the browser
      // stops the page, and the report says nothing at all.
      if (pickDay(picked ? LAST : FIRST)) {
        picked++;
        if (picked === 2) { tries = 0; }
      }
      setTimeout(step, 25);
      return;
    }
    if (!drawn()) { setTimeout(step, 25); return; }
    setTimeout(function () {
      // Read before the levels are stepped through, or it reports the last one set.
      var startsOn = document.getElementById("grouping").value;
      eachLevel(0, {}, function (levels) {
        document.title = "GROUPED " + JSON.stringify({
          levels: levels,
          startsOn: startsOn,
          summary: document.getElementById("summary-body").textContent.slice(0, 80),
          problems: window.papvaultProblems
        });
      });
    }, 400);
  })();
});
"""

first, last = span(CASE)
probe = TEMPLATE % (json.dumps(carry(CASE)), json.dumps(first), json.dumps(last))
digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "grouped.html").write_text(text, encoding="utf-8")
print("grouped probe built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
