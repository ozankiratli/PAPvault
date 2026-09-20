"""A probe that reads the summary's event bar chart, pixel by pixel.

Both things this checks are painted onto a canvas, so no DOM check can see them:
that the bars run longest at the top with the first palette color on the longest,
and that each count is printed to the RIGHT of its bar rather than centered on
its end. It reports, per row from the top, the bar's color and where it ends, and
where the count's leftmost and rightmost pixels are.

The card is five-days, whose four names are written 4, 3, 2 and 1 times, so the
order is strict and a tie never decides it.
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
  var CLICKS = ["2026-03-10", "2026-03-14"];
  var transfer = new DataTransfer();
  FILES.forEach(function (spec) {
    var raw = atob(spec[1]);
    var bytes = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) { bytes[i] = raw.charCodeAt(i); }
    transfer.items.add(new File(spec[2] === null ? [bytes] : [bytes, new Uint8Array(spec[2] - bytes.length)], spec[0]));
  });
  var input = document.getElementById("folder-input");
  input.files = transfer.files;
  input.dispatchEvent(new Event("change"));

  function rgbOf(text) {
    var hex = text.trim().replace("#", "");
    return [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16)];
  }
  function styleOf(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name);
  }

  var tries = 0;
  (function step() {
    if (++tries > 1200) { document.title = "GAVE UP"; return; }
    if (document.getElementById("folder-status").textContent.indexOf("Reading") === 0) { setTimeout(step, 25); return; }
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
    if (!document.querySelector("#event-plot .uplot")) { setTimeout(step, 25); return; }
    setTimeout(function () {
      var plot = document.querySelector("#event-plot .uplot");
      var over = plot.querySelector(".u-over");
      var canvas = plot.querySelector("canvas");
      var scale = canvas.width / plot.querySelector(".u-wrap").offsetWidth;
      var left = Math.round(parseFloat(over.style.left) * scale);
      var top = Math.round(parseFloat(over.style.top) * scale);
      var width = Math.round(parseFloat(over.style.width) * scale);
      var height = Math.round(parseFloat(over.style.height) * scale);
      var text = rgbOf(styleOf("--text"));
      var palette = [];
      for (var n = 1; n <= 7; n++) { palette.push([n, rgbOf(styleOf("--plot-event-" + n))]); }

      // Every bar is found by its own color and placed by the pixels it actually
      // covers, so nothing here depends on this script agreeing with the page
      // about where a row begins. A count belongs to the bar whose rows it sits in.
      var whole = canvas.getContext("2d").getImageData(left, top, width, height);
      var bars = {}, letters = [];
      for (var y = 0; y < height; y++) {
        for (var x = 0; x < width; x++) {
          var at = (y * width + x) * 4;
          if (whole.data[at + 3] <= 40) { continue; }
          var red = whole.data[at], green = whole.data[at + 1], blue = whole.data[at + 2];
          // Near the text color, not exactly it: a thin numeral is drawn with
          // subpixel antialiasing, which moves each channel a little on its own.
          // The gridlines are the only other thing drawn here and are nowhere near.
          if (Math.max(Math.abs(red - text[0]), Math.abs(green - text[1]), Math.abs(blue - text[2])) <= 80) {
            letters.push([x, y]);
            continue;
          }
          palette.forEach(function (entry) {
            if (red !== entry[1][0] || green !== entry[1][1] || blue !== entry[1][2]) { return; }
            var held = bars[entry[0]];
            if (!held) { bars[entry[0]] = { color: entry[0], barEnd: x, top: y, bottom: y }; return; }
            if (x > held.barEnd) { held.barEnd = x; }
            if (y < held.top) { held.top = y; }
            if (y > held.bottom) { held.bottom = y; }
          });
        }
      }
      var found = Object.keys(bars).map(function (key) { return bars[key]; });
      found.sort(function (a, b) { return a.top - b.top; });
      found.forEach(function (bar) {
        bar.textMin = null;
        bar.textMax = null;
        letters.forEach(function (dot) {
          if (dot[1] < bar.top || dot[1] > bar.bottom) { return; }
          if (bar.textMin === null || dot[0] < bar.textMin) { bar.textMin = dot[0]; }
          if (bar.textMax === null || dot[0] > bar.textMax) { bar.textMax = dot[0]; }
        });
        bar.gap = bar.textMin === null ? null : bar.textMin - bar.barEnd;
      });
      var legend = [];
      document.querySelectorAll("#legend-list li").forEach(function (item) {
        var swatch = item.querySelector(".legend-swatch");
        legend.push([item.children[1].textContent, swatch.style.background, item.children[2].textContent]);
      });
      document.title = "EVENTS " + JSON.stringify({ scale: scale, rows: found, legend: legend });
    }, 400);
  })();
});
""" % json.dumps(files)

digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "events.html").write_text(text, encoding="utf-8")
print("events probe built from", hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
