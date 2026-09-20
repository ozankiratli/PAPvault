"""A probe that opens the Manual and exercises its collapsible groups."""
import base64, hashlib, pathlib, sys
ROOT, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
page = (ROOT / "dist/index.html").read_text(encoding="utf-8")
probe = """
window.addEventListener("load", function () {
  document.querySelector('[data-dialog="manual-dialog"]').click();
  function state() {
    var groups = [];
    document.querySelectorAll(".manual-group").forEach(function (g) {
      groups.push(g.querySelector(".manual-group-button").textContent.trim()
        + "=" + g.querySelector(".manual-group-button").getAttribute("aria-expanded"));
    });
    var shown = [];
    document.querySelectorAll(".manual-pane").forEach(function (p) { if (!p.hidden) shown.push(p.id); });
    return { groups: groups, shown: shown,
             visibleSectionButtons: Array.prototype.filter.call(
               document.querySelectorAll("button[data-section]"),
               function (b) { return b.offsetParent !== null; }).length };
  }
  var report = { onOpen: state() };
  // Pick a section in the last group; only that group should end up open.
  var groups = document.querySelectorAll(".manual-group");
  var last = groups[groups.length - 1];
  last.querySelector(".manual-group-button").click();
  var target = last.querySelectorAll("button[data-section]");
  target[target.length - 1].click();
  report.afterPickingLast = state();
  // Clicking an open group's header again closes it.
  last.querySelector(".manual-group-button").click();
  report.afterCollapsing = state();
  document.title = "MANUAL " + JSON.stringify(report);
});
"""
digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "manual.html").write_text(text, encoding="utf-8")
