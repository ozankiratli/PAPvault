"""The top bar stays reachable, and the plots pass under it rather than over it.

A night's plots run several screens long, so the folder, the calendar, the manual and
the theme have to be reachable from the bottom of them. Two things can go wrong and
only one of them is visible in a stylesheet: the bar can scroll away, or it can stay
and have a chart drawn on top of it. The second is asked of the page rather than of
the rules -- what does the pointer actually land on at the bar's own middle.
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

  var tries = 0;
  (function step() {
    if (++tries > 12000) { document.title = "STICKY gave up"; return; }
    var charts = document.querySelectorAll("#plots-body .uplot");
    if (charts.length < 2) {
      var day = document.querySelector(".calendar-day.has-data");
      if (day) { day.click(); }
      setTimeout(step, 25);
      return;
    }
    var bar = document.querySelector(".topbar");
    var before = bar.getBoundingClientRect();
    window.scrollTo(0, document.documentElement.scrollHeight);
    setTimeout(function () {
      var after = bar.getBoundingClientRect();
      var middle = document.elementFromPoint(after.left + after.width / 2,
                                             after.top + after.height / 2);
      // Just below the bar is where a plot should be, and it must be under the bar
      // rather than over it.
      var under = document.elementFromPoint(after.left + after.width / 2, after.bottom + 4);
      var card = document.querySelector(".summary-card").getBoundingClientRect();
      document.title = "STICKY " + JSON.stringify({
        scrolled: Math.round(window.scrollY),
        page: Math.round(document.documentElement.scrollHeight),
        barTop: Math.round(after.top),
        barMoved: Math.round(after.top - before.top),
        barHeight: Math.round(after.height),
        atBar: middle ? (middle.closest(".topbar") ? "the bar" : middle.tagName) : "nothing",
        belowBar: under ? under.tagName : "nothing",
        cardTop: Math.round(card.top),
        sticky: getComputedStyle(bar).position
      });
    }, 120);
  })();
});
"""

body = probe % json.dumps(files)
digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script></body>" % body, 1)
(OUT / "sticky.html").write_text(text, encoding="utf-8")
print("sticky probe built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
