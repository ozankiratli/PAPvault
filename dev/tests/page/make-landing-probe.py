"""A probe for the page before anything is read, and for the bar staying put.

Loads a card so the page is long enough to scroll, but reports the landing state
first: what the plots card says with nothing loaded, and whether the button it
builds there opens the manual. A button the page creates after load is only bound
if the dialog handler is delegated, so this fails if it goes back to being bound
once per element.

Then it scrolls and measures the bar again. Sticky is not the same as fixed: inside
a flex column the bar can stop holding, and the only way to know is to scroll.
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
  var report = {};
  var body = document.getElementById("plots-body");
  report.landingText = body.textContent.replace(/\\s+/g, " ").trim().slice(0, 260);
  report.landingButtons = body.querySelectorAll("button[data-dialog]").length;

  var manual = document.getElementById("manual-dialog");
  report.manualOpenBefore = manual.open;
  var button = body.querySelector("button[data-dialog]");
  if (button) { button.click(); }
  report.manualOpenAfterClick = manual.open;
  if (manual.open) { manual.close(); }

  var bar = document.querySelector(".topbar");
  report.barTopAtRest = Math.round(bar.getBoundingClientRect().top);

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
      report.pageHeight = document.documentElement.scrollHeight;
      window.scrollTo(0, 900);
      report.scrolledTo = Math.round(window.scrollY);
      report.barTopAfterScroll = Math.round(bar.getBoundingClientRect().top);
      // What is on top where the plots scroll past the bar. A plot found here means
      // the bar is holding its place but painting underneath the cards.
      report.overBrand = bar.contains(document.elementFromPoint(40, 20));
      report.overMiddle = bar.contains(document.elementFromPoint(700, 30));
      report.underBarAtMiddle = (document.elementsFromPoint(700, 30)[1] || {}).className;
      report.landingGoneOnceLoaded = document.getElementById("plots-body")
        .querySelectorAll("button[data-dialog]").length;
      document.title = "LANDING " + JSON.stringify(report);
    }, 400);
  })();
});
""" % json.dumps(files)

digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "landing.html").write_text(text, encoding="utf-8")
print("landing probe built from", hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
