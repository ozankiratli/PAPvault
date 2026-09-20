"""A probe that wheels over a plot with and without Ctrl.

Without Ctrl the page must keep the event, so it scrolls; with Ctrl the page must
take it and the chart must redraw. The redraw is checked by comparing the canvas
before and after, so a handler that swallows the event without zooming fails too.
"""
import base64, hashlib, json, pathlib, sys
ROOT, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
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
  var tries = 0;
  (function step() {
    if (++tries > 1200) { document.title = "GAVE UP"; return; }
    if (document.querySelectorAll("#plots-body .uplot").length < 3) { setTimeout(step, 25); return; }
    setTimeout(function () {
      var charts = document.querySelectorAll("#plots-body .uplot");
      var flow = charts[1];
      var over = flow.querySelector(".u-over");
      var canvas = flow.querySelector("canvas");
      var box = over.getBoundingClientRect();
      function wheel(withCtrl) {
        var e = new WheelEvent("wheel", {
          deltaY: -120, bubbles: true, cancelable: true,
          clientX: box.left + box.width / 2, clientY: box.top + box.height / 2,
          ctrlKey: withCtrl
        });
        over.dispatchEvent(e);
        return e.defaultPrevented;
      }
      var plain = canvas.toDataURL();
      var plainPrevented = wheel(false);
      var afterPlain = canvas.toDataURL();
      var ctrlPrevented = wheel(true);
      setTimeout(function () {
        var afterCtrl = canvas.toDataURL();
        // Every chart must have moved together, not just the one wheeled over.
        var others = 0;
        charts.forEach(function (c, i) { if (i > 1 && c.querySelector("canvas")) { others++; } });
        document.title = "WHEEL " + JSON.stringify({
          plainScrollPrevented: plainPrevented,
          plainChangedChart: afterPlain !== plain,
          ctrlScrollPrevented: ctrlPrevented,
          ctrlChangedChart: afterCtrl !== afterPlain,
          chartsInStack: charts.length
        });
      }, 200);
    }, 400);
  })();
});
""" % json.dumps(files)
digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "wheel.html").write_text(text, encoding="utf-8")
