"""A probe that wheels over a plot with and without Ctrl, then drags it both ways.

Without Ctrl the page must keep the wheel event, so it scrolls; with Ctrl the page
must take it and the chart must redraw. The redraw is checked by comparing the canvas
before and after, so a handler that swallows the event without zooming fails too.

Then, zoomed in, a drag with Ctrl held must slide the window without changing its
span, a drag without Ctrl must still zoom to the selection, and a drag long enough to
run off the start must stop there rather than past it.

The scale is read off the running charts, which uPlot hands back through the sync key
the stack registers them under -- the same objects the page is driving, not a copy.
"""
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
  window.papvaultProblems = [];
  window.addEventListener("error", function (e) { window.papvaultProblems.push(String(e.message)); });
  var input = document.getElementById("folder-input");
  input.files = transfer.files;
  input.dispatchEvent(new Event("change"));
  var tries = 0;
  (function step() {
    if (++tries > 12000) { document.title = "GAVE UP"; return; }
    if (document.querySelectorAll("#plots-body .uplot").length < 3) { setTimeout(step, 25); return; }
    setTimeout(function () {
      var charts = document.querySelectorAll("#plots-body .uplot");
      var flow = charts[1];
      var over = flow.querySelector(".u-over");
      var canvas = flow.querySelector("canvas");
      var box = over.getBoundingClientRect();
      function wheel(withCtrl) {
        var e = new WheelEvent("wheel", {
          deltaY: -120, bubbles: true, cancelable: true,
          clientX: box.left + box.width / 2, clientY: box.top + box.height / 2,
          ctrlKey: withCtrl
        });
        over.dispatchEvent(e);
        return e.defaultPrevented;
      }
      var stack = uPlot.sync("papvault-day").plots;
      var spanOf = function (u) { return u.scales.x.max - u.scales.x.min; };
      var whole = { min: stack[0].scales.x.min, max: stack[0].scales.x.max };

      // Every event is dispatched on the overlay and bubbles from there, which is how
      // it reaches uPlot's own listener on the overlay, uPlot's mouseup on the
      // document, and the page's pan listeners on the window, all from one dispatch.
      function drag(withCtrl, by) {
        var y = box.top + box.height / 2;
        var from = box.left + box.width / 2;
        var last = from;
        // movementX has to be set. uPlot drops a mousemove that reports no movement,
        // to get past a Chrome bug that sends a stray one after a mousedown, and a
        // constructed MouseEvent reports none unless it is told to.
        function send(kind, x) {
          over.dispatchEvent(new MouseEvent(kind, {
            bubbles: true, cancelable: true, button: 0, buttons: 1,
            clientX: x, clientY: y, ctrlKey: withCtrl, movementX: x - last, movementY: 0
          }));
          last = x;
        }
        send("mousedown", from);
        send("mousemove", from + by * 0.5);
        send("mousemove", from + by);
        send("mouseup", from + by);
      }

      var plain = canvas.toDataURL();
      var plainPrevented = wheel(false);
      var afterPlain = canvas.toDataURL();
      var ctrlPrevented = wheel(true);
      setTimeout(function () {
        var afterCtrl = canvas.toDataURL();
        // Every chart must have moved together, not just the one wheeled over.
        var others = 0;
        charts.forEach(function (c, i) { if (i > 1 && c.querySelector("canvas")) { others++; } });

        var zoomed = { min: stack[0].scales.x.min, max: stack[0].scales.x.max };
        drag(true, 120);
        setTimeout(function () {
          var panned = { min: stack[0].scales.x.min, max: stack[0].scales.x.max };
          var together = stack.every(function (u) {
            return u.scales.x.min === panned.min && u.scales.x.max === panned.max;
          });
          // Far enough to run off the start of the period, which it must not do.
          drag(true, box.width * 40);
          setTimeout(function () {
            var stopped = { min: stack[0].scales.x.min, max: stack[0].scales.x.max };
            var spanBeforeSelect = spanOf(stack[0]);
            drag(false, box.width / 4);
            setTimeout(function () {
              // A two-finger swipe arrives as a wheel event carrying deltaX. Which of
              // the page and the plot takes a gesture is settled on its first event
              // and held, so each run below is started after a wait longer than the
              // gap that ends a gesture.
              function swipe(dx, dy) {
                var e = new WheelEvent("wheel", {
                  deltaX: dx, deltaY: dy, bubbles: true, cancelable: true,
                  clientX: box.left + box.width / 2, clientY: box.top + box.height / 2
                });
                over.dispatchEvent(e);
                return e.defaultPrevented;
              }
              var where = function () {
                return { min: stack[0].scales.x.min, max: stack[0].scales.x.max };
              };
              // Read before any swiping moves the scale it measures.
              var spanAfterSelect = spanOf(stack[0]);
              var beforeSwipe = where();
              var sidewaysTaken = swipe(60, 0);
              setTimeout(function () {
                var afterSideways = where();
                // Read here and not in the report: by then the double-click below has
                // put every scale back, and the answer would be about that instead.
                var sidewaysTogether = stack.every(function (u) {
                  return u.scales.x.min === afterSideways.min
                    && u.scales.x.max === afterSideways.max;
                });
                setTimeout(function () {
                  var upDownTaken = swipe(0, 60);
                  var afterUpDown = where();
                  setTimeout(function () {
                    // The first event of this one is up and down, so the page has the
                    // gesture; a sideways event inside it must not take it back.
                    var beforeHeld = where();
                    swipe(0, 60);
                    var heldTaken = swipe(90, 0);
                    setTimeout(function () {
                      var afterHeld = where();
                      over.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
                      setTimeout(function () {
                        var unzoomed = where();
                        var unzoomedTaken = swipe(60, 0);
                        // How far a pinch zooms must follow how far it travelled, not
                        // how many events it took to get there. One event of twice the
                        // distance must land on the square of one event's factor; a
                        // fixed factor per event gives the same number for both.
                        over.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
                        setTimeout(function () {
                        var openSpan = spanOf(stack[0]);
                        wheel(true);
                        setTimeout(function () {
                        var oneNotch = spanOf(stack[0]) / openSpan;
                        over.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
                        setTimeout(function () {
                        var e = new WheelEvent("wheel", {
                          deltaY: -240, bubbles: true, cancelable: true, ctrlKey: true,
                          clientX: box.left + box.width / 2, clientY: box.top + box.height / 2
                        });
                        over.dispatchEvent(e);
                        setTimeout(function () {
                        var twoNotches = spanOf(stack[0]) / openSpan;
                        over.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
                        setTimeout(function () {
                        // A step small enough to be a pinch rather than a notch. One
                        // event either way, so nothing is waiting on a frame.
                        var small = new WheelEvent("wheel", {
                          deltaY: -2, bubbles: true, cancelable: true, ctrlKey: true,
                          clientX: box.left + box.width / 2, clientY: box.top + box.height / 2
                        });
                        over.dispatchEvent(small);
                        setTimeout(function () {
                        var smallStep = spanOf(stack[0]) / openSpan;
                        setTimeout(function () {
                          document.title = "WHEEL " + JSON.stringify({
                            swipe: {
                              sidewaysTaken: sidewaysTaken,
                              sidewaysMovedBy: afterSideways.min - beforeSwipe.min,
                              sidewaysKeptSpan:
                                Math.abs((afterSideways.max - afterSideways.min)
                                  - (beforeSwipe.max - beforeSwipe.min)) < 1e-6,
                              sidewaysTogether: sidewaysTogether,
                              upDownTaken: upDownTaken,
                              upDownMovedBy: afterUpDown.min - afterSideways.min,
                              heldTaken: heldTaken,
                              heldMovedBy: afterHeld.min - beforeHeld.min,
                              unzoomedTaken: unzoomedTaken,
                              unzoomedSpan: unzoomed.max - unzoomed.min,
                              wholeSpan: whole.max - whole.min
                            },
                            zoom: { oneNotch: oneNotch, twoNotches: twoNotches,
                                    smallStep: smallStep },
                            problems: window.papvaultProblems,
                plainScrollPrevented: plainPrevented,
                plainChangedChart: afterPlain !== plain,
                ctrlScrollPrevented: ctrlPrevented,
                ctrlChangedChart: afterCtrl !== afterPlain,
                chartsInStack: charts.length,
                zoomedSpan: zoomed.max - zoomed.min,
                wholeSpan: whole.max - whole.min,
                panMovedBy: panned.min - zoomed.min,
                panSpan: panned.max - panned.min,
                panTogether: together,
                stoppedAtStart: stopped.min - whole.min,
                stoppedSpan: stopped.max - stopped.min,
                            spanBeforeSelect: spanBeforeSelect,
                            spanAfterSelect: spanAfterSelect
                          });
                        }, 200);
                        }, 200);
                        }, 200);
                        }, 200);
                        }, 200);
                        }, 200);
                        }, 200);
                      }, 300);
                    }, 200);
                  }, 300);
                }, 300);
              }, 200);
            }, 200);
          }, 200);
        }, 200);
      }, 200);
    }, 400);
  })();
});
""" % json.dumps(files)
digest = base64.b64encode(hashlib.sha256(probe.encode()).digest()).decode()
text = page.replace("script-src ", "script-src 'sha256-%s' " % digest, 1)
text = text.replace("</body>", "<script>%s</script>\n</body>" % probe, 1)
(OUT / "wheel.html").write_text(text, encoding="utf-8")
