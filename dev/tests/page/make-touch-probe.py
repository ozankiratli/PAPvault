"""A probe that works the day stack with fingers, and reports the window each left.

A phone has no wheel, no Ctrl and no hover, so the same three things are done with
touches: one finger slides the window, two zoom about the point between them, and two
taps put the whole period back. None of it can be felt from here, but all of it can be
measured: every gesture is dispatched as the touch events a browser would send, and
the window it leaves behind is read once the page has settled.

The fingers land above the plotting area, where the title and the axis are, because
that is where they landed on a real phone when the handlers were bound to the plotting
rectangle alone and nothing happened.

Timing matters twice here. uPlot settles a scale after the event that asked for it, so
a window read in the same breath as the gesture is the window from before it. And a
gesture that ever had two fingers must not read as a tap, however still the point
between them stayed, or two pinches in a row put the whole period back.
"""
import base64, hashlib, json, pathlib, sys
ROOT, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")
card = ROOT / "dev/synthetic/out/resmed/plain-night"
files = []
for path in sorted(card.rglob("*")):
    if path.is_file() and path.name != "answer.json":
        rel = "plain-night/" + str(path.relative_to(card)).replace("\\", "/")
        files.append((rel, base64.b64encode(path.read_bytes()).decode()))

probe = """
window.addEventListener("load", function () {
  var FILES = %s;
  var thrown = [];
  window.addEventListener("error", function (e) { thrown.push(String(e.message)); });
  var transfer = new DataTransfer();
  FILES.forEach(function (spec) {
    var raw = atob(spec[1]);
    var bytes = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) { bytes[i] = raw.charCodeAt(i); }
    transfer.items.add(new File([bytes], spec[0]));
  });
  var input = document.getElementById("folder-input");
  input.files = transfer.files;
  input.dispatchEvent(new Event("change"));

  var tries = 0;
  (function step() {
    if (++tries > 12000) { document.title = "GAVE UP"; return; }
    var charts = document.querySelectorAll("#plots-body .uplot");
    if (charts.length < 2) {
      var day = document.querySelector(".calendar-day.has-data");
      if (day && !charts.length) { day.click(); }
      setTimeout(step, 25);
      return;
    }
    drive(charts[1]);
  })();

  function drive(flow) {
    var box = flow.querySelector(".u-over").getBoundingClientRect();
    var stack = uPlot.sync("papvault-day").plots;
    var span = function () { return Math.round(stack[0].scales.x.max - stack[0].scales.x.min); };
    var at = function () { return Math.round(stack[0].scales.x.min); };
    // Above the plotting area: on the title and the axis, not on the lines.
    var y = box.top - 6;

    function finger(part, id) {
      return new Touch({ identifier: id, target: flow,
        clientX: box.left + box.width * part, clientY: y });
    }
    function fire(kind, touches) {
      var e = new TouchEvent(kind, { bubbles: true, cancelable: true,
        touches: touches, targetTouches: touches, changedTouches: touches });
      flow.dispatchEvent(e);
      return e.defaultPrevented;
    }

    var out = { whole: span(), steps: [], thrown: thrown };

    var acts = [
      // Fingers moving apart by three times their distance: zoom in by three.
      function () {
        fire("touchstart", [finger(0.4, 1), finger(0.6, 2)]);
        out.preventedPinch = fire("touchmove", [finger(0.2, 1), finger(0.8, 2)]);
        fire("touchend", []);
      },
      function () { out.steps.push(["pinched apart", span(), at()]); },
      // A second pinch straight after the first. Its middle barely moves, so this is
      // where a pinch counted as a tap would put the whole period back.
      function () {
        fire("touchstart", [finger(0.45, 1), finger(0.55, 2)]);
        fire("touchmove", [finger(0.35, 1), finger(0.65, 2)]);
        fire("touchend", [finger(0.65, 2)]);
        fire("touchend", []);
      },
      function () { out.steps.push(["pinched again", span(), at()]); },
      // One finger dragged left: the window moves and keeps its span.
      function () {
        fire("touchstart", [finger(0.7, 1)]);
        out.preventedDrag = fire("touchmove", [finger(0.3, 1)]);
        fire("touchend", []);
      },
      function () { out.steps.push(["dragged", span(), at()]); },
      // Two taps in quick succession: the whole period again.
      function () {
        fire("touchstart", [finger(0.5, 1)]);
        fire("touchend", []);
        fire("touchstart", [finger(0.5, 1)]);
        fire("touchend", []);
      },
      function () { out.steps.push(["tapped twice", span(), at()]); },
      // Up and down belongs to the page, so a vertical drag must leave the window be.
      function () {
        out.held = [span(), at()];
        fire("touchstart", [finger(0.5, 1)]);
        out.preventedVertical = fire("touchmove", [new Touch({ identifier: 1, target: flow,
          clientX: box.left + box.width * 0.5, clientY: y + 80 })]);
        fire("touchend", []);
      },
      function () {
        out.steps.push(["dragged down the page", span(), at()]);
        out.cursorShows = !!document.querySelector("#plots-body .u-legend .u-value");
        document.title = "TOUCH " + JSON.stringify(out);
      }
    ];

    var doing = 0;
    (function next() {
      if (doing === acts.length) { return; }
      acts[doing++]();
      setTimeout(next, 60);
    })();
  }
});
"""

body = probe % json.dumps(files)
digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script></body>" % body, 1)
(OUT / "touch.html").write_text(text, encoding="utf-8")
print("touch probe built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
