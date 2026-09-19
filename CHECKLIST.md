# Checklist

**Z runs this list before each release.** Each entry says what to check, how, and what a failure looks like; a check with no stated failure is not a check. The agent proposes an entry with the change that adds the behavior it protects, and the entry joins the list when Z commits it. What a run of the list found is written in `VERIFICATION.md`, in Z's words.

Entries are named, not numbered, so a record can point at one and keep pointing at it.

## `headers` -- what GitHub Pages sends

**Protects:** the design assumption that the page arrives with no security header of its own, so the `<meta>` policy is the one in force.

**How:** `curl -sSI <PAPvault URL>`, and compare with the headers recorded at the previous run.

**Failure:** `content-type` is anything but `text/html; charset=utf-8`. A header that was not there at the previous run is recorded and raised, whether or not it looks harmful.

## `policy-blocks` -- the policy is in force

**Protects:** the promise that nothing leaves the page.

**How:** open the deployed page, and in the browser console run `fetch('https://example.com')`.

**Failure:** the request goes out, or fails for any reason other than a Content-Security-Policy violation reported in the console.

## `no-outbound` -- nothing leaves the page

**Protects:** the promise that nothing leaves the page, and that the site collects nothing.

**How:** open the deployed page in a fresh private window with the developer tools' network panel open, reload, and use every control on the page.

**Failure:** any request other than the page itself, apart from a link the tester follows on purpose.

## `framed` -- the page refuses to run inside a frame

**Protects:** the one gap a `<meta>` policy leaves, since it cannot forbid framing.

**How:** save `<iframe src="<PAPvault URL>" width="900" height="300"></iframe>` as a local HTML file and open it.

**Failure:** anything of PAPvault's interface appears in the frame, rather than the notice that it does not run inside one.

## `no-markup` -- nothing from a file becomes markup or code

**Protects:** the rule that text read from a file reaches the page only as text.

**How:** `grep -rnE 'innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\(|new Function' src`

**Failure:** any line printed.

## `rebuild` -- the served file is the one the source builds

**Protects:** the claim that anyone can rebuild the page and get the file that is served.

**How:** in a clean checkout of the release commit, run `python3 build.py` twice, then `curl -sS <PAPvault URL> | sha256sum`.

**Failure:** the two builds print different checksums, or the served file's checksum differs from the build's.
