# Auditing the promise, after the first release

**Written 2026-09-21, against the tree at `b787957`, with v0.0.1 live at https://ozankiratli.github.io/PAPvault/.** Z asked whether the published site actually keeps the two promises it is built on: that no request carries user data, and that nothing is collected about the people who use it. This is what was done, what it found, and what it could not settle.

Four Sonnet agents were used, on Z's go-ahead, one per angle: exfiltration vectors, the policy itself, stored state, and the delivery chain. **Every load-bearing claim any of them made was re-checked here against the bytes before it was used**, which is what `CLAUDE.md` requires and which mattered: one agent's central finding was true and is recorded below, and another's incidental claim about `git check-attr` was left unresolved rather than repeated.

## What the page does, observed rather than read

The strongest evidence is not a grep. Chrome's own NetLog records every URL the browser attempts and every hostname it resolves, and the site was loaded under it seven times: once live, and six times locally driving the day view, the range view, the calendar's day buttons, the manual, the legend, and the landing page with a scroll. **Every run recorded exactly one URL, the page itself, and one hostname.** No font, no CDN, no favicon fetch, no beacon.

Then the harder question, because "it does not try" is weaker than "it cannot". A probe was written that loads a synthetic card and then attempts to send the rendered summary text to an outside host eighteen ways: fetch, no-cors fetch, XHR, sendBeacon, WebSocket, EventSource, an image pixel, a script tag, a prefetch link, an iframe, a form submission, dynamic import, eval, Function, a Worker, a service worker, WebRTC and a CSS `url()`. The page reported **14 Content-Security-Policy violations** across `connect-src`, `default-src`, `frame-src`, `img-src`, `script-src` and `script-src-elem`; `eval` and `new Function` threw `EvalError`; the Worker and the service worker were refused. NetLog for that run shows **no request and no DNS lookup for the target host at all**.

To falsify any of this, rebuild and run `check/make-escape-probe.py` from the session scratchpad, or load the site under `chromium --log-net-log=... --net-log-capture-mode=Default` and search the log for a `"url"` that is not the page.

## What the host does, which is a separate question

Z asked this second and it was the right question: the page can be clean and the host can still undo it.

- **GitHub Pages does not modify the bytes.** `curl` of the live page gives `95df1589...`, 304,962 bytes, byte-identical to what the source builds at the tag.
- **It sends no header that weakens the page's own policy**, and none that would make the browser report anything: no `Content-Security-Policy`, no `X-Frame-Options`, no `NEL`, no `Report-To`, no `Reporting-Endpoints`, no `Set-Cookie`.
- **`http://` is answered with a 301 to `https://`.**
- **Only the built page is reachable.** `/` and `/index.html` return 200; `/src/app.js`, `/build.py`, `/VERSION`, `/CLAUDE.md` and `/dist/` all return 404. Nothing of the repository is published but the artifact.
- **GitHub's own 404 page pulls in nothing third-party** -- a wrong path under this origin loads one URL, from this origin.
- **A content network sits in front of it.** The response carries `via: 1.1 varnish`, `x-served-by`, `x-cache` and `x-fastly-request-id`. So the request is seen by GitHub *and* by its CDN. The manual said only GitHub; it now says both.

## Two findings

**The chosen folder's name is shown, and `CLAUDE.md` says it is not.** The rule reads: *"A folder named by a serial number is passed through, and its name is never shown or kept."* Given a card whose top folder is named `SN-23231234567`, the folder dialog reads `SN-23231234567 opened: 15 files, 5 of them holding a night's recording.` The name comes from `folderNameOf` in `src/app.js`, which takes the first path segment, and is printed by `reportCard`. A refused file reaches it a second way, by printing its whole relative path.

Nothing is transmitted and nothing is persisted; it is on the reader's own screen and gone on reload, so this is not a breach of the telemetry promise. What it touches is **screenshots**: someone reporting a problem sends the dialog, and the serial goes with it. That is the reason the rule exists. Which way to resolve it -- stop showing the name, or change the promise -- is Z's, and was left open rather than decided here.

**The origin is shared.** `localStorage` is scoped to an origin, not to a path, and `ozankiratli.github.io` also serves `/PoolSeqFlow/` and whatever else is published under that account. So every page at that origin can read PAPvault's stored keys and PAPvault could read theirs. PAPvault keeps only three there -- theme, clock format, and which plots are checked -- and none of them is derived from a card. **That makes "nothing card-derived is ever stored" a boundary rather than a tidiness rule**, and it is worth knowing before anyone proposes caching a parsed card "just for the session".

## What could not be settled

- **WebRTC.** A peer connection was made against a STUN host and an offer created: gathering began, no candidate was ever produced, and the host never appeared in the network log. Nothing left -- but **no policy violation fired either**, so the absence cannot be attributed to the policy rather than to headless Chrome's environment. It only matters for code that already runs, and nothing unhashed can run, so it is rated low and named rather than claimed.
- **Transport on a first visit.** No `Strict-Transport-Security` header is sent, at the page or at the origin root. Whether `github.io` is covered by the browsers' HSTS preload list was not checked, because that is a third-party source and would need a cleared read. The page's content is public, so interception discloses nothing; the risk is substitution of a modified page, and the only defence there is the published checksum, which helps whoever checks it.
- **Obfuscation.** A keyword search cannot prove the absence of a network call built at runtime from pieces. The tells were searched for -- `eval`, `new Function`, bracket access on the globals, `atob`, `String.fromCharCode` -- and the single `fromCharCode` is an EDF annotation delimiter in `src/edf.js`. The independent answer is that the policy blocks the call whether or not the source contains it.

## Two gaps in the checks, which is why this had to be done by hand

- **Nothing in `dev/tests/` inspects the policy's content.** The hashes cannot go stale, because `build.py` derives each from the same variable it inlines. But a hand-edit adding `'unsafe-inline'` or a `connect-src` would build clean and ship, and only a human reading the diff would catch it.
- **Nothing checks the rendered page for the identifying marker.** The synthetic cards put `SYNTHETIC-DO-NOT-DISPLAY-7Q4Z` in every identifying field precisely so it can be searched for, and two checks look for it -- but in the reader's header object and in the loaded signals, never in the DOM. That is exactly why the folder-name finding survived: the probes name their folder `plain-night`, so nothing serial-shaped was ever on screen to notice.
