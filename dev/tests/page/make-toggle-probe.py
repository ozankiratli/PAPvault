"""Rebuild the plot-toggle probe page from the current dist/index.html.

Choosing which plots to show used to read every file of the night again, which the
page announced by blanking itself and saying "Reading...". Z, 2026-09-22: "The plot
toggles reload the whole plot. It would be great to prevent that."

So the probe opens the Choose Plots dialog, turns one plot off and on again, and
watches the plots area throughout. What it reports is whether the page ever said it
was reading, and how the number of charts moved. A page that re-reads the card says
"Reading..." at least once; a page working from what it already holds never does.
"""
import base64, hashlib, json, pathlib, sys

ROOT = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")

CASE = "plain-night"


def carry(case):
    card = ROOT / "dev/synthetic/out/resmed" / case
    files = []
    for path in sorted(card.rglob("*")):
        if path.is_file() and path.name != "answer.json":
            rel = case + "/" + str(path.relative_to(card)).replace("\\", "/")
            files.append((rel, base64.b64encode(path.read_bytes()).decode()))
    return files


TEMPLATE = """
window.addEventListener("load", function () {
  var FILES = %s;
  var transfer = new DataTransfer();
  FILES.forEach(function (spec) {
    var raw = atob(spec[1]);
    var bytes = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) { bytes[i] = raw.charCodeAt(i); }
    transfer.items.add(new File([bytes], spec[0]));
  });
  window.papvaultProblems = [];
  window.addEventListener("error", function (e) { window.papvaultProblems.push(String(e.message)); });

  var report = { saidReading: 0, loadingSeen: 0, steps: [] };
  // Sampled the whole time, not only at the end: what is being checked is something
  // that appears and goes away again.
  setInterval(function () {
    if (document.getElementById("plots-body").textContent.indexOf("Reading") !== -1) {
      report.saidReading += 1;
    }
    if (document.getElementById("loading-dialog").open) { report.loadingSeen += 1; }
  }, 10);

  var input = document.getElementById("folder-input");

  // This probe is about the route through the folder input, which is what a browser
  // offering no directory handle takes. Chromium offers one, so it is taken away here
  // before the button is pressed; the listing route has a probe of its own.
  delete window.showDirectoryPicker;

  // Pressing Read Data must put the box up at once, before the browser's own folder
  // window even opens. The input's click is stubbed out so no native window opens in
  // a headless run; everything the page does around it is untouched.
  input.click = function () { report.nativePickerAsked = true; };
  document.getElementById("folder-pick").click();
  report.loadingOnPick = document.getElementById("loading-dialog").open === true;
  report.headingOnPick = document.getElementById("loading-dialog-title").textContent;
  // Dismissing that window without choosing must take the box away again.
  input.dispatchEvent(new Event("cancel"));
  report.loadingAfterCancel = document.getElementById("loading-dialog").open === true;

  input.files = transfer.files;
  // Z, 2026-09-22: "the gap is after I press upload and the time the counter starts
  // counting the files read." The gap is the page turning the browser's file list
  // into something it can read, which happens in the same task as this event. So the
  // box must already be up when the event handler yields, which is the moment
  // dispatchEvent returns -- before one file has been touched.
  input.dispatchEvent(new Event("change"));
  report.loadingUpBeforeAnyFile = document.getElementById("loading-dialog").open === true;
  report.statusBeforeAnyFile = document.getElementById("loading-progress").textContent;

  function charts() { return document.querySelectorAll("#plots-body .uplot").length; }
  function settled(then) {
    var waited = 0;
    (function wait() {
      if (++waited > 4000) { then(); return; }
      if (document.getElementById("plots-body").textContent.indexOf("Reading") !== -1
          || charts() === 0) { setTimeout(wait, 25); return; }
      setTimeout(then, 120);
    })();
  }

  var tries = 0;
  (function step() {
    if (++tries > 12000) { document.title = "GAVE UP " + document.getElementById("summary-body").textContent.slice(0, 80); return; }
    if (document.getElementById("folder-status").textContent.indexOf("Reading") === 0
        || charts() === 0) { setTimeout(step, 25); return; }
    setTimeout(function () {
      report.chartsAtFirst = charts();
      report.pickerInDialog = !!document.querySelector("#plots-dialog #plot-picker");
      report.dialogOpenBefore = document.getElementById("plots-dialog").open === true;

      // The button in the card's heading opens the dialog the toggles now live in.
      document.getElementById("plot-choose").click();
      report.dialogOpenAfterClick = document.getElementById("plots-dialog").open === true;

      var boxes = document.querySelectorAll("#plot-picker input[type=checkbox]");
      report.boxes = boxes.length;
      // Whatever it is called, the last one is a plot that is on; turn it off.
      var box = boxes[boxes.length - 1];
      report.readingBeforeToggle = report.saidReading;
      box.checked = false;
      box.dispatchEvent(new Event("change"));

      settled(function () {
        report.steps.push(["off", charts()]);
        box.checked = true;
        box.dispatchEvent(new Event("change"));
        settled(function () {
          report.steps.push(["on", charts()]);
          report.readingAfterToggles = report.saidReading;
          report.problems = window.papvaultProblems;
          document.title = "TOGGLE " + JSON.stringify(report);
        });
      });
    }, 300);
  })();
});
"""

probe = TEMPLATE % json.dumps(carry(CASE))
digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "toggle.html").write_text(text, encoding="utf-8")
print("toggle probe built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
