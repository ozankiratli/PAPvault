"""A probe that searches the whole rendered page for the identifying marker.

    python3 dev/tests/page/make-marker-probe.py <repo root> <out dir> [folder name]

Every synthetic card carries a distinctive string in each field that would name a
person or a machine: the EDF patient and recording fields of every header, and
`Identification.tgt`. It is there so that it can be searched for.

Two checks already look for it -- `edf-vs-answer.js` in the parsed header object, and
`card-vs-answer.js` in the loaded signals and events. Neither looks at the page. This
one does: it loads a card, renders a day, opens the folder dialog and the manual, and
then searches `document.documentElement.outerHTML`, which covers text, attribute
values and anything else in the tree, plus everything in local storage.

The third argument names the folder the card appears to come from, which on a real
card can be the machine's serial number. It defaults to the case name. Passing the
marker itself is how this check was shown to be able to fail.

The marker reaches the page base64-encoded and is decoded at run time. It has to be:
the search reads the whole document, and a probe carrying the string as a literal
would find its own copy of it.
"""
import base64, hashlib, json, pathlib, sys

ROOT, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
FOLDER = sys.argv[3] if len(sys.argv) > 3 else "plain-night"
OUT.mkdir(parents=True, exist_ok=True)
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")
card = ROOT / "dev/synthetic/out/resmed/plain-night"

answer = json.loads((card / "answer.json").read_text(encoding="utf-8"))
marker = answer["identifying_marker"]

files = []
for path in sorted(card.rglob("*")):
    if path.is_file() and path.name != "answer.json":
        rel = FOLDER + "/" + str(path.relative_to(card)).replace("\\", "/")
        files.append((rel, base64.b64encode(path.read_bytes()).decode()))

probe = """
window.addEventListener("load", function () {
  var FILES = %s;
  // Carried base64 so the marker itself is never a literal in this page:
  // the search below reads the whole document, this script included.
  var MARKER = atob(%s);
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
    if (++tries > 6000) { document.title = "GAVE UP"; return; }
    if (document.getElementById("folder-status").textContent.indexOf("Reading") === 0) { setTimeout(step, 25); return; }
    if (!document.querySelector("#plots-body .uplot")) { setTimeout(step, 25); return; }

    // Everything a reader could see or copy: the folder dialog reports what was
    // opened, and the manual is the other body of text the page builds.
    document.querySelector('[data-dialog="folder-dialog"]').click();
    document.querySelector('[data-dialog="manual-dialog"]').click();

    setTimeout(function () {
      var whole = document.documentElement.outerHTML;
      var stored = "";
      try {
        for (var i = 0; i < localStorage.length; i++) {
          var key = localStorage.key(i);
          stored += key + "=" + localStorage.getItem(key) + ";";
        }
      } catch (e) { stored = "(storage unavailable)"; }

      var at = whole.indexOf(MARKER);
      document.title = "MARKER " + JSON.stringify({
        inPage: at !== -1,
        inStorage: stored.indexOf(MARKER) !== -1,
        storedKeys: stored,
        around: at === -1 ? "" : whole.slice(Math.max(0, at - 90), at + 60).replace(/\\s+/g, " ")
      });
    }, 500);
  })();
});
""" % (json.dumps(files), json.dumps(base64.b64encode(marker.encode()).decode()))

digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "marker.html").write_text(text, encoding="utf-8")
print("marker probe built; the card appears to come from a folder named", FOLDER)
