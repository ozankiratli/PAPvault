"""What the page keeps, what it opens, and whether a setting outlives a reload.

Three things a person used to check by hand, and all three are text:

  **What is opened.** Every read of a file is recorded, by standing in front of the
  two calls a File is ever read through. A card carrying an oximetry file is used, so
  "no oximetry file is opened" is a list that must not hold one rather than a promise.

  **What is kept.** `localStorage` is scoped to an origin and not to a path, so every
  other site published under the same account shares it with PAPvault. After a card
  has been read, the keys must be the page's own settings and nothing else, and no
  value may carry anything that came off the card. Cookies, session storage and
  IndexedDB must be empty outright.

  **What survives.** The clock format is changed, and the page is reloaded through the
  address so that no storage of the probe's own is added to the thing being counted.
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
  var after = window.location.hash === "#after";

  function storage() {
    var keys = Object.keys(window.localStorage).sort();
    var held = {};
    keys.forEach(function (key) { held[key] = window.localStorage.getItem(key); });
    return { keys: keys, held: held };
  }

  function clockOf() {
    var settings = document.getElementById("settings-dialog");
    var chosen = settings.querySelector("input[type=radio]:checked, select");
    return chosen ? (chosen.value || chosen.id) : "";
  }

  // After the reload there is no card: what is asked is whether the setting survived
  // and whether the control agrees with what is stored.
  if (after) {
    var earlier = {};
    try { earlier = JSON.parse(window.name || "{}"); } catch (trouble) { earlier = {}; }
    var report = {
      before: earlier,
      storage: storage(),
      clock: clockOf(),
      cookies: document.cookie,
      session: Object.keys(window.sessionStorage).length
    };
    var tell = function () { document.title = "SETTINGS " + JSON.stringify(report); };
    if (window.indexedDB && window.indexedDB.databases) {
      window.indexedDB.databases().then(function (held) {
        report.databases = held.length;
        tell();
      }, function () { report.databases = "refused"; tell(); });
    } else {
      report.databases = 0;
      tell();
    }
    return;
  }

  // Every read of a file, by name. A File is read through these two and nothing else.
  // A header read and a read of the whole file are different acts, and the difference
  // is the whole of what "the samples are never read" means.
  var opened = [];
  var sliced = File.prototype.slice;
  File.prototype.slice = function () {
    opened.push(this.name.split("/").pop() + " head");
    return sliced.apply(this, arguments);
  };
  var whole = File.prototype.arrayBuffer;
  File.prototype.arrayBuffer = function () {
    opened.push(this.name.split("/").pop() + " whole");
    return whole.apply(this, arguments);
  };

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
    if (++tries > 12000) { document.title = "SETTINGS gave up"; return; }
    var charts = document.querySelectorAll("#plots-body .uplot");
    if (!charts.length) {
      var day = document.querySelector(".calendar-day.has-data");
      if (day) { day.click(); }
      setTimeout(step, 25);
      return;
    }
    var picker = document.getElementById("summary-picker");
    var boxes = [];
    document.querySelectorAll("#plots-dialog input[type=checkbox]").forEach(function (box) {
      var label = box.closest("label");
      boxes.push(label ? label.textContent.trim() : box.id);
    });
    var before = document.getElementById("summary-body").textContent;

    // The clock format, changed through the control a reader would use.
    var settings = document.getElementById("settings-dialog");
    var radios = settings.querySelectorAll("input[type=radio]");
    var other = null;
    radios.forEach(function (one) { if (!one.checked && !other) { other = one; } });
    var was = clockOf();
    if (other) {
      other.checked = true;
      other.dispatchEvent(new Event("change", { bubbles: true }));
      other.click();
    }
    setTimeout(function () {
      var report = {
        phase: "before",
        opened: opened.filter(function (name, at) { return opened.indexOf(name) === at; }).sort(),
        boxes: boxes,
        storage: storage(),
        clockWas: was,
        clockNow: clockOf(),
        summaryChanged: document.getElementById("summary-body").textContent !== before,
        cookies: document.cookie,
        session: Object.keys(window.sessionStorage).length
      };
      window.name = JSON.stringify(report);
      window.location.hash = "#after";
      window.location.reload();
    }, 120);
  })();
});
"""

body = probe % json.dumps(files)
digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script></body>" % body, 1)
(OUT / "settings.html").write_text(text, encoding="utf-8")
print("settings probe built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
