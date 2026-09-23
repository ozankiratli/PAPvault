"""Rebuild the day and range probe pages from the current dist/index.html."""
import base64, hashlib, json, pathlib, sys

ROOT = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")

def carry(case, whole_waveform):
    card = ROOT / "dev/synthetic/out/resmed" / case
    files = []
    for path in sorted(card.rglob("*")):
        if not path.is_file() or path.name == "answer.json":
            continue
        data = path.read_bytes()
        rel = case + "/" + str(path.relative_to(card)).replace("\\", "/")
        if path.name.endswith("_BRP.edf") and not whole_waveform:
            files.append((rel, base64.b64encode(data[:8192]).decode(), len(data)))
        else:
            files.append((rel, base64.b64encode(data).decode(), None))
    return files

TEMPLATE = """
window.addEventListener("load", function () {
  var FILES = %s;
  var CLICKS = %s;
  var TOGGLES = %s;
  var transfer = new DataTransfer();
  FILES.forEach(function (spec) {
    var raw = atob(spec[1]);
    var bytes = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) { bytes[i] = raw.charCodeAt(i); }
    transfer.items.add(new File(spec[2] === null ? [bytes] : [bytes, new Uint8Array(spec[2] - bytes.length)], spec[0]));
  });
  window.papvaultProblems = [];
  window.addEventListener("error", function (e) { window.papvaultProblems.push(String(e.message)); });
  var input = document.getElementById("folder-input");
  input.files = transfer.files;
  input.dispatchEvent(new Event("change"));

  function loaded() {
    // Not merely "the page has stopped saying Reading": between the folder being
    // handed over and the first file being opened it has not started saying it yet,
    // and a probe that begins clicking in that moment finds no calendar to click.
    if (document.getElementById("loading-dialog").open) { return false; }
    if (!document.querySelector(".calendar-day.has-data")) { return false; }
    return document.getElementById("folder-status").textContent.indexOf("Reading") !== 0;
  }
  function drawn() {
    return document.querySelectorAll(".uplot").length > 0
      && document.getElementById("summary-body").textContent.indexOf("Reading") === -1;
  }
  function summaryCharts() { return document.querySelectorAll("#summary-plots .uplot").length; }

  // How many lines the Events per Hour chart draws, from its own legend. Its first
  // legend entry is the x axis, which is not one of them.
  function eventSeries() {
    var found = null;
    document.querySelectorAll("#summary-plots .plot").forEach(function (plot) {
      var title = plot.querySelector(".u-title");
      if (title && title.textContent.indexOf("Events per Hour") === 0) { found = plot; }
    });
    return found ? Math.max(0, found.querySelectorAll(".u-legend .u-series").length - 1) : null;
  }

  function afterRedraw(then) {
    var waited = 0;
    (function wait() {
      if (++waited > 4000) { then(); return; }
      if (!drawn()) { setTimeout(wait, 25); return; }
      setTimeout(then, 150);
    })();
  }

  // The choices a period offers: which summary plots to draw, and which of the
  // machine's events the per-hour plot draws.
  function exerciseToggles(then) {
    var out = { chartsBefore: summaryCharts(), seriesBefore: eventSeries() };
    var charts = document.querySelectorAll("#summary-picker input[type=checkbox]");
    out.summaryBoxes = charts.length;
    var one = charts[0];
    one.checked = false;
    one.dispatchEvent(new Event("change"));
    afterRedraw(function () {
      out.chartsWithOneOff = summaryCharts();
      one.checked = true;
      one.dispatchEvent(new Event("change"));
      afterRedraw(function () {
        out.chartsBackOn = summaryCharts();
        var events = document.querySelectorAll("#event-picker input[type=checkbox]");
        var box = events[0];
        box.checked = false;
        box.dispatchEvent(new Event("change"));
        afterRedraw(function () {
          out.seriesWithOneOff = eventSeries();
          out.chartsWhileEventOff = summaryCharts();
          box.checked = true;
          box.dispatchEvent(new Event("change"));
          afterRedraw(function () {
            out.seriesBackOn = eventSeries();
            window.papvaultToggles = out;
            then();
          });
        });
      });
    });
  }

  var tries = 0;
  (function step() {
    if (++tries > 12000) { document.title = "GAVE UP " + document.getElementById("summary-body").textContent.slice(0, 80); return; }
    if (!loaded()) { setTimeout(step, 25); return; }
    if (CLICKS.length) {
      CLICKS.forEach(function (iso) {
        var cell = document.querySelector('.calendar-day[aria-label="' + iso + '"]');
        if (cell) { cell.click(); }
      });
      CLICKS = [];
      tries = 0;
      setTimeout(step, 25);
      return;
    }
    if (!drawn()) { setTimeout(step, 25); return; }
    if (TOGGLES && !window.papvaultToggles) {
      exerciseToggles(function () { setTimeout(step, 25); });
      return;
    }
    setTimeout(function () {
      var titles = [];
      document.querySelectorAll(".plot .u-title").forEach(function (t) { titles.push(t.textContent); });
      // Where each chart's plotting area begins and ends. They must all agree, or a
      // cursor at one x means a different moment in each chart.
      var boxes = {};
      document.querySelectorAll("#plots-body .u-over, #summary-plots .u-over").forEach(function (over) {
        boxes[over.style.left + "+" + over.style.width] = (boxes[over.style.left + "+" + over.style.width] || 0) + 1;
      });
      // How much canvas is left below each plotting area. A y axis label is centred on
      // its tick, so a chart whose lowest tick sits on the canvas edge has the bottom
      // half of that label cut off -- which is what a plain 0 looked like.
      var roomBelow = [];
      document.querySelectorAll("#plots-body .uplot, #summary-plots .uplot").forEach(function (u) {
        var over = u.querySelector(".u-over");
        var wrap = u.querySelector(".u-wrap");
        if (!over || !wrap) { return; }
        roomBelow.push(Math.round(wrap.offsetHeight
          - (parseFloat(over.style.top) + parseFloat(over.style.height))));
      });
      document.title = "REPORT " + JSON.stringify({
        roomBelow: roomBelow,
        summary: document.getElementById("summary-body").textContent,
        chartTitles: titles,
        summaryCharts: document.querySelectorAll("#summary-plots .uplot").length,
        dayCharts: document.querySelectorAll("#plots-body .uplot").length,
        plotBoxes: boxes,
        // The bar's real height against the offset the sticky cards were given. If
        // the variable and the bar disagree, a card either overlaps it or floats.
        topbar: (function () {
          var bar = document.querySelector(".topbar");
          var card = document.querySelector(".summary-card");
          return {
            height: Math.round(bar.getBoundingClientRect().height),
            position: getComputedStyle(bar).position,
            cardTop: getComputedStyle(card).top,
            cardPosition: getComputedStyle(card).position
          };
        })(),
        // Every hover band over a chart's row names: its words, its size, and whether
        // the pointer would actually reach it. A band of no size carries a title that
        // nothing can ever show, which is how this broke the first time.
        hoverBands: (function () {
          var out = [];
          document.querySelectorAll(".name-hovers span").forEach(function (s) {
            var b = s.getBoundingClientRect();
            var hit = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
            out.push([s.title, Math.round(b.width), Math.round(b.height), hit === s]);
          });
          return out;
        })(),
        pickerHidden: document.getElementById("plot-choose").hidden,
        // Which group of choices the dialog offers: a day's stack and a period's
        // summaries are different plots, so the dialog shows one or the other.
        pickerGroups: {
          day: document.getElementById("plot-picker").hidden,
          summary: document.getElementById("summary-picker").hidden,
          events: document.getElementById("event-picker-slot").hidden,
          eventBoxes: document.querySelectorAll("#event-picker input[type=checkbox]").length
        },
        problems: window.papvaultProblems,
        toggles: window.papvaultToggles || null,
        markupAnywhere: document.querySelectorAll("#summary-body script, #plots-body script, #summary-plots script").length
      });
    }, 300);
  })();
});
"""

for name, case, whole, clicks, toggles in [
    ("day", "plain-night", True, [], False),
    ("range", "five-days", False, ["2026-03-10", "2026-03-14"], True),
]:
    probe = TEMPLATE % (json.dumps(carry(case, whole)), json.dumps(clicks),
                        json.dumps(toggles))
    digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
    text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
    text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
    (OUT / (name + ".html")).write_text(text, encoding="utf-8")
print("probes built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
