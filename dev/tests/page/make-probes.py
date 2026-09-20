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
    return document.getElementById("folder-status").textContent.indexOf("Reading") !== 0;
  }
  function drawn() {
    return document.querySelectorAll(".uplot").length > 0
      && document.getElementById("summary-body").textContent.indexOf("Reading") === -1;
  }
  var tries = 0;
  (function step() {
    if (++tries > 1200) { document.title = "GAVE UP " + document.getElementById("summary-body").textContent.slice(0, 80); return; }
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
    setTimeout(function () {
      var titles = [];
      document.querySelectorAll(".plot .u-title").forEach(function (t) { titles.push(t.textContent); });
      // Where each chart's plotting area begins and ends. They must all agree, or a
      // cursor at one x means a different moment in each chart.
      var boxes = {};
      document.querySelectorAll("#plots-body .u-over, #summary-plots .u-over").forEach(function (over) {
        boxes[over.style.left + "+" + over.style.width] = (boxes[over.style.left + "+" + over.style.width] || 0) + 1;
      });
      document.title = "REPORT " + JSON.stringify({
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
        pickerHidden: document.getElementById("plot-picker").hidden,
        problems: window.papvaultProblems,
        markupAnywhere: document.querySelectorAll("#summary-body script, #plots-body script, #summary-plots script").length
      });
    }, 300);
  })();
});
"""

for name, case, whole, clicks in [
    ("day", "plain-night", True, []),
    ("range", "five-days", False, ["2026-03-10", "2026-03-14"]),
]:
    probe = TEMPLATE % (json.dumps(carry(case, whole)), json.dumps(clicks))
    digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
    text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
    text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
    (OUT / (name + ".html")).write_text(text, encoding="utf-8")
print("probes built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
