"""A probe for the calendar's previous-day and next-day buttons.

Uses five-days, whose card holds recordings on the 10th to the 14th of March 2026
and nothing on the 15th, so both ends of the run are inside the month on screen.

It walks backwards to the first day, checks the button has gone dead there, walks
forwards to the last, checks the same, and reports the selected day at every step
along with what the summary card said. A step must land on a day that holds a
recording, so the summary must never read that the folder holds nothing.
"""
import base64, hashlib, json, pathlib, sys

ROOT, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")
card = ROOT / "dev/synthetic/out/resmed/five-days"
files = []
for path in sorted(card.rglob("*")):
    if not path.is_file() or path.name == "answer.json":
        continue
    data = path.read_bytes()
    rel = "five-days/" + str(path.relative_to(card)).replace("\\", "/")
    if path.name.endswith("_BRP.edf"):
        files.append((rel, base64.b64encode(data[:8192]).decode(), len(data)))
    else:
        files.append((rel, base64.b64encode(data).decode(), None))

probe = """
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

  var back = document.getElementById("day-prev");
  var on = document.getElementById("day-next");
  var report = { back: [], forward: [], rows: [], problems: null };

  function selected() {
    var cell = document.querySelector(".calendar-day.selected");
    return cell ? cell.getAttribute("aria-label") : null;
  }
  function emptyMessage() {
    return document.getElementById("summary-body").textContent.indexOf("no recording") !== -1;
  }
  function settled() {
    return document.getElementById("summary-body").textContent.indexOf("Reading") === -1;
  }

  function whenSettled(then) {
    (function wait() {
      if (!settled()) { setTimeout(wait, 25); return; }
      then();
    })();
  }

  // Where each step button's arrow and its words sit inside it: the arrow against
  // its own edge, the words centred in the whole button.
  function stepButton(id) {
    var button = document.getElementById(id);
    var box = button.getBoundingClientRect();
    var arrow = button.querySelector(".step-arrow").getBoundingClientRect();
    var words = null;
    button.childNodes.forEach(function (node) {
      if (node.nodeType !== 3 || !node.textContent.trim()) { return; }
      var range = document.createRange();
      range.selectNode(node);
      words = range.getBoundingClientRect();
    });
    return {
      width: Math.round(box.width),
      arrowFromLeft: Math.round(arrow.left + arrow.width / 2 - box.left),
      wordsOffCentre: words === null ? null
        : Math.round((words.left + words.width / 2) - (box.left + box.width / 2))
    };
  }

  // The names down the day's event strip, top first. They come from the hover bands,
  // which carry one per row in the order they are drawn.
  function stripRows() {
    var out = [];
    document.querySelectorAll("#plots-body .name-hovers span").forEach(function (s) {
      out.push(s.title);
    });
    return out.join(" | ");
  }

  var steps = 0;
  function walkBack() {
    if (++steps > 40) { document.title = "LOOPED"; return; }
    if (back.disabled) {
      report.backStoppedAt = selected();
      report.backButtonDead = true;
      steps = 0;
      walkForward();
      return;
    }
    back.click();
    whenSettled(function () {
      report.back.push([selected(), emptyMessage()]);
      report.rows.push(stripRows());
      walkBack();
    });
  }

  function walkForward() {
    if (++steps > 40) { document.title = "LOOPED"; return; }
    if (on.disabled) {
      report.forwardStoppedAt = selected();
      report.forwardButtonDead = true;
      report.problems = window.papvaultProblems;
      report.buttons = { prev: stepButton("day-prev"), next: stepButton("day-next") };
      document.title = "STEP " + JSON.stringify(report);
      return;
    }
    on.click();
    whenSettled(function () {
      report.forward.push([selected(), emptyMessage()]);
      report.rows.push(stripRows());
      walkForward();
    });
  }

  var tries = 0;
  (function ready() {
    if (++tries > 12000) { document.title = "GAVE UP"; return; }
    // A card is loaded when the calendar has days to step between. Waiting merely for
    // the page to stop saying "Reading" is not enough: it has not started saying it
    // yet in the moment between the folder being handed over and the first file being
    // opened, and a walk begun in that moment steps through empty days forever.
    if (document.getElementById("loading-dialog").open) { setTimeout(ready, 25); return; }
    if (!document.querySelector(".calendar-day.has-data")) { setTimeout(ready, 25); return; }
    if (document.getElementById("folder-status").textContent.indexOf("Reading") === 0) { setTimeout(ready, 25); return; }
    if (!settled()) { setTimeout(ready, 25); return; }
    report.opensOn = selected();
    walkBack();
  })();
});
""" % json.dumps(files)

digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "step.html").write_text(text, encoding="utf-8")
print("step probe built from", hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
