"""A probe that reads the event strip's painted pixels, row by row.

The strip's rows are labeled by uPlot onto the canvas, so no DOM check can tell
whether a bar sits on the row its name is on. Labels are in first-seen order,
which is earliest-event-first, and row 0 is the bottom one. So the first bar in
each row must come EARLIER as you go down the strip.
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
    if (document.querySelectorAll("#plots-body .uplot").length === 0) { setTimeout(step, 25); return; }
    setTimeout(function () {
      var strip = document.querySelector("#plots-body .uplot");
      var over = strip.querySelector(".u-over");
      var canvas = strip.querySelector("canvas");
      var scale = canvas.width / strip.querySelector(".u-wrap").offsetWidth;
      var left = Math.round(parseFloat(over.style.left) * scale);
      var top = Math.round(parseFloat(over.style.top) * scale);
      var width = Math.round(parseFloat(over.style.width) * scale);
      var height = Math.round(parseFloat(over.style.height) * scale);
      var rows = %d;
      var ctx = canvas.getContext("2d");
      var band = height / rows;
      var ctx2 = canvas.getContext("2d");
      var whole = ctx2.getImageData(left, top, width, height);
      var found = [];
      for (var r = 0; r < rows; r++) {
        var y0 = Math.floor(r * band), y1 = Math.ceil((r + 1) * band);
        var minX = null, count = 0;
        for (var y = y0; y < y1 && y < height; y++) {
          for (var x = 0; x < width; x++) {
            var at = (y * width + x) * 4;
            // The canvas is transparent where nothing was drawn, and the white
            // or dark surface behind it is CSS, not paint. So a drawn pixel is one
            // with alpha, whatever colour it is -- which black bars need.
            if (whole.data[at + 3] > 40) {
              count++;
              if (minX === null || x < minX) { minX = x; }
            }
          }
        }
        found.push([minX, count]);
      }
      document.title = "STRIP " + JSON.stringify(found);
    }, 400);
  })();
});
""" % (json.dumps(files), 4)

digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "strip.html").write_text(text, encoding="utf-8")
print("strip probe built from", hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
