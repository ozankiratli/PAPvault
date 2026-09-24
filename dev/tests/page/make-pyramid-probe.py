"""Rebuild the reduction probe page from the current dist/index.html.

A day's flow is a sample every 40 milliseconds, so a night of it is hundreds of
thousands of points and drawing them all is what made the charts slow. The stack
therefore holds the samples and a few reductions of them, each covering the whole
night, and hands over whichever one has about two points per pixel for the window on
screen. The whole of a level goes over and never a window of it: the last attempt at
this sliced the data to the visible scale, which made the data follow the scale and
broke zooming.

So this probe opens a night, reports how many points each chart was given and how
many samples stand behind them, drags a selection across the flow chart to zoom in,
and reports both again. What it is really asking is whether zooming still works at
all, which is the way the sliced version failed.
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
        if not path.is_file() or path.name == "answer.json":
            continue
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
  var input = document.getElementById("folder-input");
  input.files = transfer.files;
  input.dispatchEvent(new Event("change"));

  function loaded() {
    if (document.getElementById("loading-dialog").open) { return false; }
    if (!document.querySelector(".calendar-day.has-data")) { return false; }
    return document.getElementById("folder-status").textContent.indexOf("Reading") !== 0;
  }
  function drawn() { return document.querySelectorAll("#plots-body .uplot").length > 0; }

  // A chart's title carries its unit in brackets, and "Flow" is a prefix of
  // "Flow Limitation", so the name is taken as the words before the bracket.
  function named(title) { return title.split(" (")[0]; }
  function flowChart() {
    var found = null;
    uPlot.sync("papvault-day").plots.forEach(function (u) {
      var title = (u.root.querySelector(".u-title") || {}).textContent || "";
      if (named(title) === "Flow") { found = u; }
    });
    return found;
  }

  // Every chart's drawn point count and which level it is on, plus the span of the
  // window. A chart whose samples are few enough is never reduced and stays on 0.
  function state() {
    var charts = [];
    uPlot.sync("papvault-day").plots.forEach(function (u) {
      charts.push({
        title: (u.root.querySelector(".u-title") || {}).textContent || "",
        points: u.data[0].length,
        level: u.papvaultLevel === undefined ? null : u.papvaultLevel
      });
    });
    var flow = flowChart();
    return {
      charts: charts,
      span: flow ? flow.scales.x.max - flow.scales.x.min : null,
      first: flow ? flow.data[0][0] : null,
      last: flow ? flow.data[0][flow.data[0].length - 1] : null
    };
  }

  // A plain drag across the middle of the flow chart, which is how a reader zooms.
  // Every event goes to the chart's own overlay and carries movementX, which uPlot
  // drops a mousemove for want of.
  function dragZoom(u, then) {
    var box = u.over.getBoundingClientRect();
    var y = box.top + box.height / 2;
    var from = box.left + box.width * 0.4;
    var to = box.left + box.width * 0.75;
    var last = from;
    function send(kind, x) {
      u.over.dispatchEvent(new MouseEvent(kind, {
        bubbles: true, cancelable: true, button: 0, buttons: 1,
        clientX: x, clientY: y, movementX: x - last, movementY: 0 }));
      last = x;
    }
    send("mousedown", from);
    send("mousemove", from + (to - from) * 0.5);
    send("mousemove", to);
    send("mouseup", to);
    setTimeout(then, 500);
  }

  var tries = 0;
  (function step() {
    if (++tries > 40000) {
      document.title = "GAVE UP " + document.querySelectorAll("#plots-body .uplot").length;
      return;
    }
    if (!loaded()) { setTimeout(step, 25); return; }
    if (!document.querySelector(".calendar-day.has-data").classList.contains("selected")) {
      document.querySelector(".calendar-day.has-data").click();
      setTimeout(step, 25);
      return;
    }
    if (!drawn()) { setTimeout(step, 25); return; }
    setTimeout(function () {
      var whole = state();
      var u = flowChart();
      if (!u) { document.title = "GROUPED no flow chart"; return; }
      dragZoom(u, function () {
        var zoomed = state();
        document.title = "PYRAMID " + JSON.stringify({
          whole: whole,
          zoomed: zoomed,
          problems: window.papvaultProblems
        });
      });
    }, 400);
  })();
});
"""

probe = TEMPLATE % json.dumps(carry(CASE))
digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "pyramid.html").write_text(text, encoding="utf-8")
print("pyramid probe built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
