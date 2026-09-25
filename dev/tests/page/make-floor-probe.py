"""A probe that narrows the cards and reports how wide the charts are drawn.

It squeezes the plots card and the summary card in turn, tells the page the window
changed, and reads the canvas back. This is how a chart's floor is reached without a
narrow window, which headless Chromium will not open.
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

  var WIDTHS = [500, 400, 340, 282, 240];
  var stack = [];
  var events = [];

  function wide(what) {
    var found = document.querySelector(what);
    return found ? Math.round(found.getBoundingClientRect().width) : 0;
  }

  // Each width is given to the card, the window's own event is fired, and what the
  // chart came out at is recorded beside the room it was given.
  function squeeze(what, room, into, after) {
    var step = 0;
    (function one() {
      if (step === WIDTHS.length) { after(); return; }
      document.querySelector(what).style.width = WIDTHS[step] + "px";
      step++;
      window.dispatchEvent(new Event("resize"));
      setTimeout(function () {
        into.push([wide(room), wide(room + " canvas")]);
        one();
      }, 400);
    })();
  }

  var tries = 0;
  (function step() {
    if (++tries > 12000) { document.title = "GAVE UP"; return; }
    if (document.querySelectorAll("#plots-body .uplot").length === 0) { setTimeout(step, 25); return; }
    if (!document.querySelector("#event-plot canvas")) { setTimeout(step, 25); return; }
    squeeze(".plots-card", "#plots-body", stack, function () {
      squeeze(".summary-card", "#event-plot", events, function () {
        document.title = "FLOOR " + JSON.stringify({
          stack: stack,
          events: events,
          charts: document.querySelectorAll("#plots-body .uplot").length
        });
      });
    });
  })();
});
"""

body = probe % json.dumps(files)
digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script></body>" % body, 1)
(OUT / "floor.html").write_text(text, encoding="utf-8")
print("floor probe built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
