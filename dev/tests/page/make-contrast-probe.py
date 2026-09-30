"""The colors the page actually paints, in both themes, so their contrast can be read.

A palette can be chosen carefully and still fail where two rules meet: a muted color
on a card rather than on the page behind it, a selected day whose background came from
one theme and whose text came from the other. What matters is the pair a reader sees,
so the pairs are read off the running page rather than off the stylesheet, and the
ratios are worked out where they can be printed.

A background of `transparent` is not a background: the color that shows through is
whatever the nearest ancestor paints, which is what is walked for here.
"""
import base64, hashlib, json, pathlib, sys
ROOT, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")
card = ROOT / "dev/synthetic/out/resmed/long-range"
files = []
for path in sorted(card.rglob("*")):
    if path.is_file() and path.name != "answer.json":
        rel = "long-range/" + str(path.relative_to(card)).replace("\\", "/")
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

  function behind(node) {
    for (var at = node; at && at !== document.documentElement; at = at.parentElement) {
      var paint = getComputedStyle(at).backgroundColor;
      if (paint && paint !== "transparent" && !paint.startsWith("rgba(0, 0, 0, 0")) {
        return paint;
      }
    }
    return getComputedStyle(document.documentElement).backgroundColor;
  }

  function pair(what, node) {
    if (!node) { return [what, null, null]; }
    return [what, getComputedStyle(node).color, behind(node)];
  }

  function reading() {
    document.getElementById("manual-dialog").showModal();
    var current = document.querySelector("#manual-nav button[aria-current=true]")
      || document.querySelector("#manual-nav button[data-section]");
    var out = [
      pair("a selected day", document.querySelector(".calendar-day.selected")),
      pair("a day in a range", document.querySelector(".calendar-day.in-range")),
      pair("a day holding a recording", document.querySelector(".calendar-day.has-data")),
      pair("the manual's current section", current),
      pair("a link", document.querySelector("footer a")),
      pair("the muted note under a card", document.querySelector(".note, .empty")),
      pair("what is selected, in the bar", document.getElementById("topbar-chosen")),
      pair("a plot's title", document.querySelector(".u-title"))
    ];
    document.getElementById("manual-dialog").close();
    return out;
  }

  // In three parts, because selecting a range takes the day's plots off the page and
  // a loop that waits for them again would undo the range it just made.
  var part = 0;
  var tries = 0;
  (function step() {
    if (++tries > 20000) { document.title = "CONTRAST gave up at part " + part; return; }
    var some = document.querySelectorAll(".calendar-day.has-data");
    if (part === 0) {
      if (document.getElementById("loading-dialog").open || some.length < 3) {
        setTimeout(step, 25);
        return;
      }
      some[1].click();
      part = 1;
      setTimeout(step, 60);
      return;
    }
    if (part === 1) {
      if (!document.querySelectorAll("#plots-body .uplot").length) {
        setTimeout(step, 25);
        return;
      }
      document.getElementById("choose-range").click();
      some[0].click();
      some[some.length - 1].click();
      part = 2;
      setTimeout(step, 120);
      return;
    }
    if (!document.querySelector(".calendar-day.in-range")
        || !document.querySelector(".u-title")) {
      setTimeout(step, 25);
      return;
    }
    var root = document.documentElement;
    var themes = {};
    themes[root.dataset.theme || "light"] = reading();
    document.getElementById("theme-toggle").click();
    setTimeout(function () {
      themes[root.dataset.theme || "dark"] = reading();
      document.title = "CONTRAST " + JSON.stringify({ themes: themes });
    }, 150);
  })();
});
"""

body = probe % json.dumps(files)
digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script></body>" % body, 1)
(OUT / "contrast.html").write_text(text, encoding="utf-8")
print("contrast probe built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
