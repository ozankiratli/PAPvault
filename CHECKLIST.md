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
