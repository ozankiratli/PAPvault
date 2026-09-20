# Releasing PAPvault

Two workflows, and a person between them.

1. **`release.yml`** runs when a tag is pushed. It builds the page, checks it, and
   creates a **draft** release carrying the page, its checksums, and a source tarball.
2. **`pages.yml`** runs when that release is **published**. It builds the page from the
   tag and deploys the website.

So a push to a branch changes nothing anyone can see, and the website changes only when
a release is published. What is on the site is always a version someone decided to
release.

This follows the release system Z built for PoolSeqFlow, adapted to a project that ships
one HTML file rather than a pipeline. What was read from it, and what was left behind as
not applicable, is `R-021` in `dev/READING-LOG.md`.

## Once, before the first release

Set **Settings -> Pages -> Build and deployment -> Source** to **GitHub Actions**. It
cannot be "Deploy from a branch": `dist/` is build output and is not in the repository,
so no branch holds a finished page to serve. Until this is set, `actions/configure-pages`
fails the run early and says so.

## Each release

1. **Check it by hand**, against `dev/CHECKLIST.md`, and write what was checked into
   `dev/VERIFICATION.md`. The workflows check that the page builds, builds the same
   twice, carries the version it claims, and that the tarball builds the same page. They
   do not check that the page is right.
2. **Run the bump.**

       dev/scripts/bump-version.sh 0.1.0

   It writes `VERSION`, prepends a `CHANGELOG.md` section holding every commit since the
   last tag, adds the reference-link definition at the foot, rebuilds, and prints the
   checksum. It does not commit, tag or push; it prints those commands.
3. **Write the notes** into that new `CHANGELOG.md` section, **above** its `### Commits`
   heading and not over it. The commit list stays as the record of what landed. What you
   write there is what the release body will say.
4. **Rehearse it.** Run **Create a release** by hand from the Actions tab. It builds,
   runs every check, builds the tarball and proves it rebuilds the same page, and prints
   the release body it would use -- and creates nothing, because the release step is
   gated on the run being a tag. This is how a missing changelog section is found before
   the tag exists.
5. **Commit and tag.**

       git add -A && git commit -m 'Version bump 0.1.0'
       git tag v0.1.0

6. **Push the tag.**

       git push && git push --tags

   `release.yml` runs and leaves a draft release with three files attached.
7. **Read the draft**, add anything the changelog did not carry, and **publish it**.
   That is what deploys the website: `pages.yml` starts on the release being published.
8. **Watch `pages.yml` finish**, and open the site.

### Why the release is a draft

Two reasons, and either alone would be enough.

- **A release created by a workflow's own token does not start another workflow.**
  GitHub does not raise the event, to stop workflows triggering each other in a loop. So
  a release that `release.yml` published itself would leave `pages.yml` sitting still.
  A person publishing the draft is a real event, and it fires.
- **It is the last moment to read the notes** before anyone else does.

To publish straight from the tag instead, set `draft: false` in `release.yml` and deploy
the site by running `pages.yml` by hand afterwards.

## What is attached to a release

- **`index.html`** -- the whole program in one file. Downloaded, it runs offline with no
  network at all. It is the same bytes the website serves.
- **`SHA256SUMS`** -- so a download can be checked, and so anyone can rebuild at the tag
  and compare.
- **`PAPvault-<version>.tar.gz`** -- what someone needs to build PAPvault and run it:
  `build.py`, `src/`, `lib/`, `docs/manual.md`, `VERSION`, the licence, and the source
  lists. What is left out is decided by `export-ignore` in `.gitattributes`, and it is
  the record of how PAPvault was built rather than what it is built from -- `dev/`,
  `.claude/` and `.github/` all stay in the repository for anyone who clones.

  It is built with `git archive` rather than `tar`, so what goes in comes from the git
  index rather than from whatever is lying around in the runner's working directory. The
  workflow then **extracts it and builds it**, and fails unless it produces the page byte
  for byte. A tarball that does not build is worse than no tarball.

## What the workflows check before anything is published

Each of these fails the run rather than warning:

- `VERSION` holds a three-part version, and on a tag it matches the tag exactly;
- the tag being deployed and `VERSION` agree, checked again in `pages.yml`;
- `CHANGELOG.md` has a section for that version and it is not empty, checked with the
  same script that writes the release body, so the gate cannot pass something the body
  step would then fail on;
- none of `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval(` or
  `new Function` appears in `src` or `lib`;
- `src` and `build.py` hold no byte outside ASCII;
- every script in `dev/scripts/` parses;
- two builds of the same commit give the same checksum, and that checksum is the built
  file's own;
- the built page shows the version it is being released as;
- the source tarball builds the same page, byte for byte.

These are the invariants `CLAUDE.md` states, checked at the moment it matters. They are
not a test suite and are not a substitute for step 1.

## What the workflows deliberately do not do

- **Neither runs on a push to a branch.** There is no branch you can push to that
  releases or publishes.
- **Neither can write to a branch.** `release.yml` takes `contents: write` only to
  attach files to a release; `pages.yml` takes `contents: read`.
- **A rehearsal creates nothing.** `workflow_dispatch` on `release.yml` runs everything
  and stops before the release step.

## The actions they use

Five, and their versions are what PoolSeqFlow is using, taken from the read rather than
from memory:

| Action | Version | Used by |
|---|---|---|
| `actions/checkout` | v7 | both |
| `actions/configure-pages` | v6 | `pages.yml` |
| `actions/upload-pages-artifact` | v5 | `pages.yml` |
| `actions/deploy-pages` | v5 | `pages.yml` |
| `softprops/action-gh-release` | v3 | `release.yml` |

They are pinned to a major version, which is a gap: a major-version tag is a moving
pointer, and whoever controls it can change what runs here without the repository
changing. Pinning each to a commit SHA fixes that. Four of the five are GitHub's own;
`softprops/action-gh-release` is not.
