"""Probes that report what the page looks like at one width each.

One page per width, all carrying the same card and the same script: the window the
runner opens decides which of the layout's steps the page is on. At the narrowest of
them the script also drives the menu, since that width is the only one that has one.

The widths live in run.py, beside the names, because the window size is the runner's
to set. Anything below 500 is out of reach: headless Chromium clamps a window to 500
css pixels wide, which platform-traps.md records.
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

  function shown(id) { return getComputedStyle(document.getElementById(id)).display; }
  function box(what) { return document.querySelector(what).getBoundingClientRect(); }

  // The menu the buttons hang in below 500, opened and closed every way it can be.
  function menuReport() {
    var hamburger = document.getElementById("open-menu");
    var panel = document.getElementById("topbar-actions");
    var root = document.documentElement;
    hamburger.click();
    var open = panel.getBoundingClientRect();
    var style = getComputedStyle(panel);
    var report = {
      opened: root.classList.contains("menu-open"),
      expanded: hamburger.getAttribute("aria-expanded"),
      covers: [Math.round(open.width), Math.round(open.height)],
      // Where it is anchored, rather than where it is drawn: the panel arrives with
      // a transition on it, which has not run under virtual time.
      inset: [style.top, style.right, style.bottom, style.left],
      fixed: style.position,
      named: [],
      items: 0
    };
    panel.querySelectorAll(".icon-button:not([hidden])").forEach(function (button) {
      if (button.id === "close-menu") { return; }
      report.items++;
      report.named.push(getComputedStyle(button, "::after").content);
    });
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    report.afterEscape = root.classList.contains("menu-open");
    hamburger.click();
    document.getElementById("close-menu").click();
    report.afterCross = root.classList.contains("menu-open");
    hamburger.click();
    document.querySelector(".cards").dispatchEvent(new MouseEvent("click", { bubbles: true }));
    report.afterOutside = root.classList.contains("menu-open");
    hamburger.click();
    document.querySelector("#topbar-actions [data-dialog='manual-dialog']").click();
    report.afterPick = root.classList.contains("menu-open");
    report.manualOpen = document.getElementById("manual-dialog").open === true;
    document.getElementById("manual-dialog").close();
    return report;
  }

  var tries = 0;
  (function step() {
    if (++tries > 12000) { document.title = "GAVE UP"; return; }
    if (document.getElementById("loading-dialog").open) { setTimeout(step, 25); return; }
    if (!document.querySelector(".calendar-day.has-data")) { setTimeout(step, 25); return; }
    if (!document.getElementById("topbar-chosen").textContent) {
      document.querySelector(".calendar-day.has-data").click();
      setTimeout(step, 25);
      return;
    }
    if (document.querySelectorAll("#plots-body .uplot").length === 0) { setTimeout(step, 25); return; }
    if (!document.querySelector("#event-plot canvas")) { setTimeout(step, 25); return; }
    var cards = document.querySelector(".cards");
    var chosen = box(".topbar-chosen");
    var report = {
      view: window.innerWidth,
      height: window.innerHeight,
      columns: getComputedStyle(cards).gridTemplateColumns.split(" ").length,
      calendarIn: document.getElementById("calendar-card-slot")
        .contains(document.getElementById("calendar")) ? "card" : "dialog",
      calendarCardHidden: document.getElementById("calendar-card").hidden,
      calendarButtonHidden: document.getElementById("open-calendar").hidden,
      hamburger: shown("open-menu"),
      closeButton: shown("close-menu"),
      chosenBelowBrand: Math.round(chosen.top) >= Math.round(box(".brand").bottom),
      chosenWidth: Math.round(chosen.width),
      barHeight: Math.round(box(".topbar").height),
      overflow: document.documentElement.scrollWidth - window.innerWidth,
      charts: document.querySelectorAll("#plots-body .uplot").length,
      narrowest: 0,
      menu: null
    };
    document.querySelectorAll("#plots-body canvas, #event-plot canvas").forEach(function (one) {
      var wide = Math.round(one.getBoundingClientRect().width);
      if (!report.narrowest || wide < report.narrowest) { report.narrowest = wide; }
    });
    if (window.innerWidth <= 500) { report.menu = menuReport(); }
    document.title = "NARROW " + JSON.stringify(report);
  })();
});
"""

body = probe % json.dumps(files)
digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script></body>" % body, 1)
for name in ["three-columns", "two-columns", "stacked", "menu"]:
    (OUT / (name + ".html")).write_text(text, encoding="utf-8")
print("narrow probes built from dist/index.html sha256:",
      hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
