"""A probe that opens the legend and reports what is in it, and checks each swatch
against the color the same event has in the plots."""
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
      var dock = document.getElementById("legend-dock");
      var panel = document.getElementById("legend-panel");
      var before = { dockHidden: dock.hidden, panelHidden: panel.hidden,
                     expanded: document.getElementById("legend-toggle").getAttribute("aria-expanded") };
      document.getElementById("legend-toggle").click();
      var rows = [];
      panel.querySelectorAll("li").forEach(function (li) {
        rows.push([li.children[1].textContent,
                   getComputedStyle(li.children[0]).backgroundColor,
                   li.children[2].textContent]);
      });
      document.title = "LEGEND " + JSON.stringify({
        before: before,
        afterPanelHidden: panel.hidden,
        afterExpanded: document.getElementById("legend-toggle").getAttribute("aria-expanded"),
        rows: rows,
        folderDialogOpen: document.getElementById("folder-dialog").open === true,
        pickButton: document.getElementById("folder-pick").textContent
      });
    }, 400);
  })();
});
""" % json.dumps(files)
digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "legend.html").write_text(text, encoding="utf-8")
print("legend probe built from", hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
