"""A probe that hands the page a directory handle instead of a folder input.

Where a browser offers showDirectoryPicker the page lists a card by name and makes a
file only for a recording. No picker can be driven from a probe, so this stands one in:
a tree of handles shaped like the browser's, built from a committed card, which counts
every getFile it is asked for. That count is the check -- what the page never opens is
as much the point as what it reads.
"""
import base64, hashlib, json, pathlib, sys
ROOT, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
card = ROOT / "dev/synthetic/out/resmed/plain-night"
files = []
for path in sorted(card.rglob("*")):
    if path.is_file() and path.name != "answer.json":
        rel = str(path.relative_to(card)).replace("\\", "/")
        files.append((rel, base64.b64encode(path.read_bytes()).decode()))
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")
probe = """
window.addEventListener("load", function () {
  var FILES = %s;
  var opened = [];

  function fileOf(spec) {
    var raw = atob(spec[1]);
    var bytes = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) { bytes[i] = raw.charCodeAt(i); }
    return new File([bytes], spec[0].split("/").pop());
  }

  // A tree of handles shaped like the one a browser hands back, built from the card.
  function tree(name) {
    var root = { kind: "directory", name: name, children: {} };
    FILES.forEach(function (spec) {
      var parts = spec[0].split("/");
      var at = root;
      for (var i = 0; i < parts.length - 1; i++) {
        if (!at.children[parts[i]]) {
          at.children[parts[i]] = { kind: "directory", name: parts[i], children: {} };
        }
        at = at.children[parts[i]];
      }
      var leaf = parts[parts.length - 1];
      at.children[leaf] = {
        kind: "file", name: leaf,
        getFile: function () { opened.push(spec[0]); return Promise.resolve(fileOf(spec)); }
      };
    });
    return root;
  }

  function handleOf(node) {
    if (node.kind === "file") { return node; }
    return {
      kind: "directory", name: node.name,
      values: function () {
        return Object.keys(node.children).sort().map(function (key) {
          return handleOf(node.children[key]);
        });
      }
    };
  }

  var root = handleOf(tree("SN-SYNTHETIC"));
  window.showDirectoryPicker = function () { return Promise.resolve(root); };
  document.getElementById("folder-pick").click();

  var tries = 0;
  (function step() {
    if (++tries > 4000) { document.title = "LISTING gave up"; return; }
    var said = document.getElementById("folder-status").textContent;
    if (!said || said.indexOf("No folder") === 0 || said.indexOf("Reading") === 0) {
      setTimeout(step, 25); return;
    }
    var day = document.querySelector(".calendar-day.has-data");
    if (day && !document.querySelectorAll("#plots-body .uplot").length) {
      day.click(); setTimeout(step, 25); return;
    }
    document.title = "LISTING " + JSON.stringify({
      handed: FILES.length,
      opened: opened.length,
      openedNames: opened.slice().sort(),
      said: said.slice(0, 160),
      days: document.querySelectorAll(".calendar-day.has-data").length,
      charts: document.querySelectorAll("#plots-body .uplot").length
    });
  })();
});
"""
body = probe % json.dumps(files)
digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script></body>" % body, 1)
(OUT / "listing.html").write_text(text, encoding="utf-8")
print("built with", len(files), "files")
