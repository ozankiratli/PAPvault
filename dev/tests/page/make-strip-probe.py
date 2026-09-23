"""A probe that reads the event strip's painted pixels, row by row.

The strip's rows are labeled by uPlot onto the canvas, so no DOM check can tell
whether a bar sits on the row its name is on. Since 2026-09-22 the rows are in the
card's own order rather than the order the night happened to write them, and each
name is painted in the colour it was given when the card was read. So this reports,
per row from the top, the name its hover carries and the colour actually painted
there, and the check compares those against what the card's own answer implies.
"""
import base64, hashlib, json, pathlib, sys

ROOT, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")
card = ROOT / "dev/synthetic/out/resmed/plain-night"

# How many rows the strip has, from the card's own answer rather than from a number
# written here: the answer says which events the page must draw, and one row is drawn
# per distinct name. A number written here would go stale the next time the case does,
# and would then slice the strip into bands that are not its rows.
answer = json.loads((card / "answer.json").read_text(encoding="utf-8"))
drawn = answer["sessions"][0].get("shown_events")
if drawn is None:
    drawn = answer["sessions"][0]["events"] + answer["sessions"][0]["csl_events"]
rows = len(dict.fromkeys(one["text"] for one in drawn))

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
    if (++tries > 12000) { document.title = "GAVE UP"; return; }
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
      var names = [];
      strip.querySelectorAll(".name-hovers span").forEach(function (s) { names.push(s.title); });
      var rows = names.length || %d;
      var band = height / rows;
      // The dotted rule between one row and the next is drawn across the whole width,
      // so on a sparse row it outnumbers the bar. It is skipped by its own colour.
      var ruleText = getComputedStyle(document.documentElement)
        .getPropertyValue("--plot-row-line").trim().replace("#", "");
      var rule = [parseInt(ruleText.slice(0, 2), 16), parseInt(ruleText.slice(2, 4), 16),
                  parseInt(ruleText.slice(4, 6), 16)];
      var whole = canvas.getContext("2d").getImageData(left, top, width, height);
      var found = [];
      for (var r = 0; r < rows; r++) {
        var y0 = Math.floor(r * band), y1 = Math.ceil((r + 1) * band);
        var minX = null, count = 0, tally = {};
        for (var y = y0; y < y1 && y < height; y++) {
          for (var x = 0; x < width; x++) {
            var at = (y * width + x) * 4;
            // The canvas is transparent where nothing was drawn, and the white
            // or dark surface behind it is CSS, not paint. So a drawn pixel is one
            // with alpha, whatever colour it is -- which black bars need.
            if (whole.data[at + 3] > 40) {
              var red = whole.data[at], green = whole.data[at + 1], blue = whole.data[at + 2];
              if (Math.max(Math.abs(red - rule[0]), Math.abs(green - rule[1]),
                           Math.abs(blue - rule[2])) <= 12) { continue; }
              count++;
              if (minX === null || x < minX) { minX = x; }
              var key = red + "," + green + "," + blue;
              tally[key] = (tally[key] || 0) + 1;
            }
          }
        }
        // The commonest colour in the row, not the first pixel found: a bar's edge is
        // antialiased, so its outermost pixel is a shade of its colour and not the
        // colour itself.
        var best = null, most = 0;
        Object.keys(tally).forEach(function (key) {
          if (tally[key] > most) { most = tally[key]; best = key.split(",").map(Number); }
        });
        found.push({ name: names[r] === undefined ? null : names[r],
                     firstAt: minX, painted: count, rgb: best });
      }
      // Every line of pixels that is mostly the rule's colour: one per row edge, so
      // one more than there are rows once the outer two are drawn.
      var rules = 0;
      for (var y = 0; y < height; y++) {
        var ruled = 0;
        for (var x = 0; x < width; x++) {
          var i = (y * width + x) * 4;
          if (whole.data[i + 3] > 40
              && Math.max(Math.abs(whole.data[i] - rule[0]), Math.abs(whole.data[i + 1] - rule[1]),
                          Math.abs(whole.data[i + 2] - rule[2])) <= 12) { ruled++; }
        }
        if (ruled > width / 4) { rules++; }
      }
      document.title = "STRIP " + JSON.stringify({ rows: found, ruleLines: rules });
    }, 400);
  })();
});
""" % (json.dumps(files), rows)

digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "strip.html").write_text(text, encoding="utf-8")
print("strip probe built from", hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
