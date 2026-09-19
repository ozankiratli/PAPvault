# Security

**Written 2026-09-18, against the tree at `4db9efc`.** Nothing had been built. This is the design as agreed before the first line of the page, with the evidence each technical claim in it rests on. The rules themselves are in `CLAUDE.md`, under *Security*.

Z, 2026-09-18: *"we should be careful with JS. It should be completely open source. We also need to work on the security. I mean JS injection attacks would be terrible."*

The agent proposed five measures; Z accepted each in turn: *"1) Correct. 2) I like this idea. 3) Yes. 4) Agreed 5) My GitHub account is secure with TFA and all. I will be the only maintainer of this project, so it should be fine."*

## What is protected, and from what

Two things are protected: a person's health data, which never leaves their machine, and the grounds a skeptical user has for believing that. Four routes to the first were considered.

**A crafted file.** A card is a folder of files anyone can write, and one can be shared as a "sample". EDF headers and event annotations carry free text, so a file is a way to put text in front of the page's code. The defense is that such text only ever reaches the page as text, and that the parser checks every size and offset against the real file, so a file that lies about its own length is reported rather than read past.

**A library that turns hostile.** Whatever a library does, it does with the page's full access to the data. So libraries are few, each approved by name, stored unminified so they can be read, and pinned so they cannot change underneath a review. Nothing is fetched from a CDN when the page runs.

**A change to what is served.** Whoever can push to the repository changes what every visitor runs. Z is the sole maintainer, with two-factor authentication on the account, and the agent never pushes. The offline file takes the host out of the picture after the first download, and the published checksum lets anyone check that the file they have is the one the source builds.

**The build.** A build with a package manager behind it inherits every package in that manager's tree. This one is a single script on the Python standard library, and it is deterministic, so anyone can re-run it and compare the result byte for byte.

Across all four, the Content-Security-Policy is the second wall. If an injection gets past the first defense, the script it carries matches no hash in the policy and does not run. If a library misbehaves, it has nowhere to send anything.

## Why the design has the shape it has

**One file.** MDN, *JavaScript modules*: *"if you try to load the HTML file locally (i.e., with a `file://` URL), you'll run into CORS errors due to JavaScript module security requirements."* A page opened from disk cannot load its scripts as separate modules, so the offline page inlines everything into one file. Serving the same file online leaves one artifact to review and one checksum to publish, not two.

**A `<meta>` policy.** GitHub Pages does not let a site set response headers. A GitHub staff answer on 2023-05-02 ([github.com/orgs/community/discussions/54257](https://github.com/orgs/community/discussions/54257)): *"We don't support this feature today so a `meta` tag unfortunately is the only way."* The same person answered on 2024-07-10 that it *"is not an area that is being prioritized at the moment."* This is a community answer rather than GitHub's documentation, so it is the thing to re-check on the first deployed page: read the response headers the page actually arrives with.

**The headers GitHub Pages actually sends.** Measured on 2026-09-18 with `curl -sSI https://ozankiratli.github.io/`, Z's own site on the same infrastructure. No security header of any kind: no policy, no framing protection, no referrer policy, no `nosniff`. `content-type: text/html; charset=utf-8`, which is correct. `access-control-allow-origin: *`, so any site can read the page's code, which is public on GitHub anyway; user data never comes from the server. `cache-control: max-age=600`, so a deploy can take ten minutes to reach everyone. Each need that would normally be a header is met another way:

| Need | Normally | Here |
|---|---|---|
| hashed scripts, no outbound connection | Content-Security-Policy | `<meta http-equiv>`, first in `<head>`, since it governs only what comes after it |
| links out do not reveal where they came from | Referrer-Policy | `<meta name="referrer" content="no-referrer">` |
| no embedding by another site | `frame-ancestors`, X-Frame-Options | not available; the page refuses to run inside a frame |
| no camera, location and the like | Permissions-Policy | not needed: the page never asks, and no outside code runs that could |

**No cross-origin isolation.** The header problem most often met on GitHub Pages is the pair of cross-origin isolation headers that `SharedArrayBuffer` and threaded WebAssembly require, and it is the one Z had met there before: *"I think this design is sound. it was cross-origin isolation."* The usual workaround is a service worker that adds the headers back, and a page opened from disk cannot register a service worker, so it would also break the offline file. The design needs neither: plain JavaScript, no threads. A feature that would need them is a decision for Z, not a workaround.

**The first deploy is checked, not assumed.** The header read above is repeated against PAPvault's own URL, and a deliberate violation of the policy is confirmed to show in the browser as blocked. That is the first entry for Z's checklist.

**Hashes, not `'unsafe-inline'`.** A single file has only inline scripts and styles. `'unsafe-inline'` would allow any inline script, an injected one included; a hash allows only the exact script that was reviewed. The build computes the hashes from the files it inlines, so the policy and the scripts are derived from one source and cannot drift apart.

## What it does not cover

This is said plainly, because a security design that implies more than it delivers is worse than a smaller one that says where it stops.

- **Framing, at the header level.** `frame-ancestors`, the directive that stops another site embedding a page, *"is not supported in the `<meta>` element"* (MDN), so nothing stops another site putting PAPvault in a frame. The page refuses to run when it finds itself in one, so what a framing site gets is an empty page. Even without that there was little to exploit: the framing site cannot read into the frame, and PAPvault has no account and no action that sends anything.
- **The host's own logs.** GitHub records each visit; see `product-brief.md`.
- **The visitor's browser and machine.** A browser extension with access to the page, or a compromised machine, sees whatever the page shows. No page can defend against the environment it runs in.
