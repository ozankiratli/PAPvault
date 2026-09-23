"""Rebuild the leak-duration probe page from the current dist/index.html.

It loads the one case whose leak goes on and off and reads the Leak box back out of
the rendered page. Every other check of that figure re-implements the rule it is
checking; this one reads what the page itself worked out.
"""
import base64, hashlib, json, pathlib, sys

ROOT = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")

CASE = "on-and-off-leak"


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
    // Not merely "the page has stopped saying Reading": between the folder being
    // handed over and the first file being opened it has not started saying it yet,
    // and a probe that begins clicking in that moment finds no calendar to click.
    if (document.getElementById("loading-dialog").open) { return false; }
    if (!document.querySelector(".calendar-day.has-data")) { return false; }
    return document.getElementById("folder-status").textContent.indexOf("Reading") !== 0;
  }
  function drawn() {
    return document.querySelectorAll(".uplot").length > 0
      && document.getElementById("summary-body").textContent.indexOf("Reading") === -1;
  }
  function rowsOf(tint) {
    var box = document.querySelector('.figure-box[data-tint="' + tint + '"]');
    var out = {};
    if (!box) { return out; }
    box.querySelectorAll(".figure-rows > div").forEach(function (pair) {
      out[pair.querySelector("dt").textContent] = pair.querySelector("dd").textContent;
    });
    return out;
  }
  var tries = 0;
  (function step() {
    if (++tries > 12000) { document.title = "GAVE UP " + document.getElementById("summary-body").textContent.slice(0, 80); return; }
    if (!loaded() || !drawn()) { setTimeout(step, 25); return; }
    setTimeout(function () {
      var big = [];
      document.querySelectorAll('.figure-box[data-tint="session"] .figure-big').forEach(
        function (p) { big.push(p.textContent); });
      document.title = "LEAK " + JSON.stringify({
        leak: rowsOf("leak"),
        session: rowsOf("session"),
        big: big,
        unit: (document.querySelector('.figure-box[data-tint="leak"] .figure-unit') || {}).textContent,
        problems: window.papvaultProblems
      });
    }, 300);
  })();
});
"""

probe = TEMPLATE % json.dumps(carry(CASE))
digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "leak.html").write_text(text, encoding="utf-8")
print("leak probe built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
