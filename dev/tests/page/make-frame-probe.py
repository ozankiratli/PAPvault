"""The page refuses to run inside a frame.

A `<meta>` policy cannot forbid framing -- only a header can, and GitHub Pages sends
none -- so the page checks for itself and replaces everything with a notice. That is
the one wall with no second line behind it, which is why it is checked rather than
assumed.

The wrapper here is an ordinary file of our own, so it carries no policy and needs no
hash. It frames a copy of the built page and then reads what is inside the frame,
which one file may do to another only when the browser is told to allow it: run.py
passes `--allow-file-access-from-files` for this probe alone.
"""
import hashlib, pathlib, shutil, sys
ROOT, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
built = ROOT / "dist/index.html"
shutil.copyfile(built, OUT / "framed.html")

wrapper = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>FRAME waiting</title></head>
<body>
<iframe id="inside" src="framed.html" width="900" height="300"></iframe>
<script>
window.addEventListener("load", function () {
  var frame = document.getElementById("inside");
  var tries = 0;
  (function step() {
    if (++tries > 400) { document.title = "FRAME gave up"; return; }
    var inside = null;
    try { inside = frame.contentDocument; } catch (blocked) { inside = null; }
    if (!inside || !inside.body) { setTimeout(step, 25); return; }
    var words = inside.body.textContent.trim();
    if (!words) { setTimeout(step, 25); return; }
    document.title = "FRAME " + JSON.stringify({
      reachable: true,
      words: words.slice(0, 120),
      // What must be gone: every part of the interface, not merely hidden.
      app: !!inside.getElementById("app"),
      calendar: !!inside.getElementById("calendar"),
      folderInput: !!inside.getElementById("folder-input"),
      elements: inside.body.children.length
    });
  })();
});
</script>
</body>
</html>
"""
(OUT / "frame.html").write_text(wrapper, encoding="utf-8")
print("frame probe built from dist/index.html sha256:",
      hashlib.sha256(built.read_bytes()).hexdigest())
