"""The calendar marks what is being picked, and the bar names what is selected.

The rule is that a click means one night and a range is asked for. What made that
worth a probe of its own is that three other probes passed the whole time they were
selecting the wrong thing: they asserted the result of a range and had stopped
selecting one. This asserts the states themselves -- how many days the grid marks,
and what the bar says -- at each step of the sequence a reader takes.

The states, in the order they are driven: a day picked; the button pressed; the first
day of a range; that same day again; both ends in; a second range with the button left
alone; the button pressed off.
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

  function days() {
    return Array.prototype.slice.call(
      document.querySelectorAll(".calendar-day.has-data"));
  }
  function marked() {
    return document.querySelectorAll(
      ".calendar-day.selected, .calendar-day.in-range").length;
  }
  function said() {
    return document.getElementById("topbar-chosen").textContent.trim();
  }
  function ranging() {
    return document.getElementById("choose-range").getAttribute("aria-pressed");
  }

  var out = { steps: [] };
  function note(what) {
    out.steps.push([what, ranging(), marked(), said(),
      document.getElementById("calendar-hint").textContent.trim().slice(0, 40)]);
  }

  var tries = 0;
  (function step() {
    if (++tries > 20000) { document.title = "CALENDAR gave up"; return; }
    if (document.getElementById("loading-dialog").open || days().length < 12) {
      setTimeout(step, 25);
      return;
    }
    var some = days();
    var one = some[3], two = some[9], three = some[5], four = some[7];

    var acts = [
      function () { one.click(); },
      function () { note("a day picked"); },
      function () { document.getElementById("choose-range").click(); },
      function () { note("the button pressed"); },
      function () { two.click(); },
      function () { note("one end of a range"); },
      function () { two.click(); },
      function () { note("that same day again"); },
      function () { two.click(); },
      function () { three.click(); },
      function () { note("both ends in"); },
      function () { four.click(); },
      function () { three.click(); },
      function () { note("a second range, button untouched"); },
      function () { document.getElementById("choose-range").click(); },
      function () { note("the button pressed off"); },
      function () { document.title = "CALENDAR " + JSON.stringify(out); }
    ];
    var doing = 0;
    (function next() {
      if (doing === acts.length) { return; }
      acts[doing++]();
      setTimeout(next, 60);
    })();
  })();
});
"""

body = probe % json.dumps(files)
digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script></body>" % body, 1)
(OUT / "calendar.html").write_text(text, encoding="utf-8")
print("calendar probe built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
