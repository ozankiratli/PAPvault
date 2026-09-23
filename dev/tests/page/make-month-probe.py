"""Rebuild the calendar-month probe page from the current dist/index.html.

Moving the calendar to another month changes nothing about the period that is
selected, so the plots must not be rebuilt. The probe stamps every chart element
it can see, walks the calendar two months forward and one back, and reports
whether the stamped elements are still the ones on the page.

A rebuilt chart is a new element, so a stamp that is gone is a chart that was
thrown away and drawn again -- which is what the page used to do.
"""
import base64, hashlib, json, pathlib, sys

ROOT = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")

CASE = "five-days"


def carry(case):
    card = ROOT / "dev/synthetic/out/resmed" / case
    files = []
    for path in sorted(card.rglob("*")):
        if not path.is_file() or path.name == "answer.json":
            continue
        data = path.read_bytes()
        rel = case + "/" + str(path.relative_to(card)).replace("\\", "/")
        # The waveform is not read for what this probe does, so only its header is
        # carried and the rest is zeroes of the same length.
        if path.name.endswith("_BRP.edf"):
            files.append((rel, base64.b64encode(data[:8192]).decode(), len(data)))
        else:
            files.append((rel, base64.b64encode(data).decode(), None))
    return files


TEMPLATE = """
window.addEventListener("load", function () {
  var FILES = %s;
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
  function selection() {
    var out = [];
    document.querySelectorAll(".calendar-day.selected, .calendar-day.in-range").forEach(
      function (cell) { out.push(cell.getAttribute("aria-label")); });
    return out;
  }
  var tries = 0;
  (function step() {
    if (++tries > 12000) { document.title = "GAVE UP " + document.getElementById("summary-body").textContent.slice(0, 80); return; }
    if (!loaded() || !drawn()) { setTimeout(step, 25); return; }
    setTimeout(function () {
      // Stamp what is on the page now. A chart that is rebuilt comes back as a new
      // element, which carries no stamp.
      var before = document.querySelectorAll(".uplot");
      for (var i = 0; i < before.length; i++) { before[i].papvaultStamp = i; }
      var was = {
        month: document.getElementById("calendar-month").textContent,
        charts: before.length,
        summary: document.getElementById("summary-body").textContent,
        selected: selection()
      };

      // Two months forward and two back, so it ends where it started and the selected
      // day is on screen again to be compared.
      document.getElementById("calendar-next").click();
      document.getElementById("calendar-next").click();
      var moved = {
        month: document.getElementById("calendar-month").textContent,
        selected: selection()
      };
      document.getElementById("calendar-prev").click();
      document.getElementById("calendar-prev").click();

      var after = document.querySelectorAll(".uplot");
      var kept = 0;
      for (var j = 0; j < after.length; j++) {
        if (after[j].papvaultStamp !== undefined) { kept++; }
      }
      document.title = "MONTH " + JSON.stringify({
        monthBefore: was.month,
        monthMoved: moved.month,
        selectedWhileAway: moved.selected,
        monthAfter: document.getElementById("calendar-month").textContent,
        chartsBefore: was.charts,
        chartsAfter: after.length,
        chartsKept: kept,
        summaryUnchanged: was.summary === document.getElementById("summary-body").textContent,
        selectedBefore: was.selected,
        selectedAfter: selection(),
        dayCells: document.querySelectorAll(".calendar-day").length,
        problems: window.papvaultProblems
      });
    }, 300);
  })();
});
"""

probe = TEMPLATE % json.dumps(carry(CASE))
digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "month.html").write_text(text, encoding="utf-8")
print("month probe built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
