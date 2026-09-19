# The empty page

**Written 2026-09-19, against the tree at `5f75ba2`.** The page, the build and the local server as first built, before any feature that reads a file.

Z, 2026-09-18: *"Build the empty page. If you need a server to start, start it at port 8765. Record the decision. Even though none of the test servers are running, I think 8765 is free."*

## What was built, and why it has this shape

**Three source files and a build.** `src/index.html`, `src/style.css` and `src/app.js` are the source. `build.py` replaces three markers in the HTML: the stylesheet link with the CSS, the script tag with the JavaScript, and an empty `<meta>` policy with one that allows exactly those two by their SHA-256. It writes `dist/index.html` and prints that file's checksum. The build stops with a message if a marker is not found exactly once, or if the inlined text contains `</style`, `</script` or `<!--`, any of which would change where the browser thinks the element ends.

**The policy as built:** `default-src 'none'`, one hash each in `script-src` and `style-src`, `img-src data:`, `base-uri 'none'`, `form-action 'none'`. There is no `connect-src`, so connections fall back to `default-src 'none'`. `img-src data:` exists for the icon alone: it is a `data:` URI, so the browser never asks the host for `/favicon.ico`.

**The interface starts hidden.** The script removes `hidden` only when the page is not inside a frame. In a frame that allows scripts, the page replaces itself with a notice. In one that does not, the script never runs and only the no-JavaScript notice shows. A CSS rule keeps `hidden` in force over the layout's own `display` rules, without which the interface would show in a frame anyway.

**The theme follows the system on a first visit**, and a button switches it. The choice is kept in the browser's `localStorage`, which never leaves the browser; where storage is unavailable, as in some private windows, the choice lasts for the visit.

**System fonts only.** A web font would be one more file to fetch from somewhere or to inline.

**A classic script, not a module**, because a module cannot load from a page opened from disk (`security.md`).

**The Date and Time buttons are disabled placeholders**, in the top right corner where the brief puts them. A footer links to the source.

**`dist/` is not tracked.** How the built file reaches GitHub Pages is decided at the first deploy.

**`.gitignore` was replaced**, at Z's word: *"replace gitignore."* It had begun as GitHub's R template. The new one ignores `CPAP_old/`, `dist/`, `__pycache__/` and Claude Code's per-machine settings, and also every EDF file and the folders and files of a ResMed card wherever they appear, so a copied card cannot be staged by accident. `git check-ignore -q --no-index <path>` shows what it catches: on 2026-09-19 it ignored a probe path for each pattern and none of the tracked files.

**The local server is on port 8765**, as Z set it. The agent records the PID of any server it starts and stops only that one; a browser it starts for a check is headless, with its own profile directory, and exits on its own. Both rules are in `CLAUDE.md`.

## What the agent checked

These are the agent's own checks, made on 2026-09-19 against the files above. They are not Z's verification, which is recorded in `VERIFICATION.md`.

- **The build is deterministic.** Two runs printed the same checksum, `db109a9326224a5c1e14e0eb020691925c60b0295beeb48994f28a30a61b0c48`.
- **The markup grep can fail.** Over `src/` it found nothing. Over a probe file holding one line for each of the six forbidden calls, plus `retrieval(x)` and `evaluate(x)`, it found the six and neither of the other two.
- **The page runs under its own policy.** Served on port 8765 and rendered by headless Chromium with `--dump-dom` and `--enable-logging=stderr`, the page came back with `data-theme` set and `#app` no longer hidden, so the script ran, and the log held no policy error.
- **That log would have shown a policy error.** Two scratch copies of the built file, opened from disk: one with an injected inline script that has no hash, which was refused, leaving the title unchanged; one with a hashed probe calling `fetch("https://example.com/")`, which the browser blocked, logging *"Connecting to 'https://example.com/' violates the following Content Security Policy directive: "default-src 'none'"."*. Opened from disk, both also stand for the offline page.
- **It looks right.** Screenshots in light mode, dark mode (`--force-dark-mode`), and of a local page framing it twice. The plain frame showed the refusal; the sandboxed frame, with scripts disabled, showed only the no-JavaScript notice.
- **It asked the server for nothing else.** The server's log held requests for `/` and nothing else, no icon among them.

The command behind the third check, for anyone who wants to repeat it against a running server: `chromium --headless=new --user-data-dir=<empty directory> --enable-logging=stderr --v=0 --virtual-time-budget=3000 --dump-dom http://127.0.0.1:8765/`
