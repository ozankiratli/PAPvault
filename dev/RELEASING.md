# Releasing PAPvault

Two workflows, and a person between them.

1. **`release.yml`** runs when a tag is pushed. It builds the page, checks it, and publishes a GitHub release carrying the page, its checksums, and a source tarball.
2. **`pages.yml`** runs when a tag is pushed. It builds the page and deploys the website.

Both start from the same push, and neither waits on the other. Push the tag and the site goes up and the release appears. A push to a branch does neither.

This follows the release system Z built for PoolSeqFlow, adapted to a project that ships one HTML file rather than a pipeline. What was read from it, and what was left behind as not applicable, is `R-021` in `dev/READING-LOG.md`.

## Once, before the first release

Two settings, both in the repository's own Settings, and both needed before a tag can publish anything.

**Settings -> Pages -> Build and deployment -> Source** must be **GitHub Actions**. It cannot be "Deploy from a branch": `dist/` is build output and is not in the repository, so no branch holds a finished page to serve. Until this is set, `actions/configure-pages` fails the run early and says so.

**Settings -> Environments -> `github-pages` -> Deployment branches and tags** must allow the release tags. Set it to **Selected branches and tags** and add two rules:

| Type | Pattern | What it is for |
|---|---|---|
| Tag | `v*` | every release |
| Branch | `main` | running the workflow by hand |

This is what makes "the site changes only on a release" a rule GitHub enforces rather than a habit. `pages.yml` only listens for tags, but if that were ever widened by accident, the environment would still refuse the deployment.

On 2026-09-20 this repository refused a deployment from the `v0.0.1` tag before those rules existed: *"Tag "v0.0.1" is not allowed to deploy to github-pages due to environment protection rules."* What the environment allowed before that was not recorded, so treat the table above as the thing to set, not as a description of what GitHub starts with.

The build half of a run succeeds whether or not this is right, so the failure shows up as a workflow that ran, went green on `build`, and stopped at `deploy`.

## Each release

1. **Run the checks** with `dev/tests/run.sh`, on this machine. Then **check it by hand**, against `dev/CHECKLIST.md`, and write what was checked into `dev/VERIFICATION.md`. The workflows check that the page builds, builds the same twice, carries the version it claims, and that the tarball builds the same page. They do not check that the page is right.
2. **Run the bump.**

       dev/scripts/bump-version.sh 0.1.0

   It writes `VERSION`, prepends a `CHANGELOG.md` section holding every commit since the last tag, adds the reference-link definition at the foot, rebuilds, and prints the checksum. It does not commit, tag or push; it prints those commands.
3. **Write the notes** into that new `CHANGELOG.md` section, **above** its `### Commits` heading and not over it. The commit list stays as the record of what landed. What you write there is what the release body will say.
4. **Rehearse it**, after committing but before tagging. From the Actions tab, open **Create a release** and run it against the branch you committed to. A release needs a tag and there is no tag yet, so **no release can be created** -- the workflow knows it is running on a branch and skips that one step. Everything else runs: the changelog is extracted, the page is built twice and compared, the tarball is built and rebuilt to prove it gives the same page, and the release body it would have used is printed in the log for you to read. This is how a missing changelog section or a version that disagrees with itself is found while it can still be fixed with an ordinary commit.
5. **Commit and tag.**

       git add -A && git commit -m 'Version bump 0.1.0'
       git tag v0.1.0

6. **Push the tag.** This is the only step that publishes anything.

       git push && git push --tags

   The tag push starts both workflows. `release.yml` publishes the release with its three files; `pages.yml` deploys the site. Neither waits on the other and neither needs anything from you. `git push` is there so `main` is not left behind -- it triggers nothing.
7. **Watch both finish**, and open the site. **There is no step after this**: nothing to publish by hand, no draft to approve, no workflow to start.

### Releases are immutable

The repository has release immutability turned on, so once a release is published its tag and its files are fixed and cannot be replaced.

That is the right setting for this project, and it is what makes the rest of it mean anything. PAPvault's claim is that anyone can rebuild the page from the source at a tag and get the same bytes. If the tag could be moved, or the attached `index.html` swapped, the checksum in `SHA256SUMS` would be a statement about a moment rather than about a version. Immutability is what turns it into a fact someone can check a year later.

What it costs is that **nothing can be patched in place.** A wrong file, a wrong checksum or a release body naming the wrong version is fixed by releasing again with the next patch number, never by editing what is there. That makes **step 4, the rehearsal**, the safety net rather than a courtesy: it is the last point at which a mistake is still an ordinary commit. There is nothing after the tag that can be taken back.

## What is attached to a release

- **`index.html`** -- the whole program in one file. Downloaded, it runs offline with no network at all. It is the same bytes the website serves.
- **`SHA256SUMS`** -- so a download can be checked, and so anyone can rebuild at the tag and compare.
- **`PAPvault-<version>.tar.gz`** -- what someone needs to build PAPvault and run it: `build.py`, `src/`, `lib/`, `docs/manual.md`, `VERSION`, the licence, and the source lists. What is left out is decided by `export-ignore` in `.gitattributes`, and it is the record of how PAPvault was built rather than what it is built from -- `dev/`, `.claude/` and `.github/` all stay in the repository for anyone who clones.

  It is built with `git archive` rather than `tar`, so what goes in comes from the git index rather than from whatever is lying around in the runner's working directory. The workflow then **extracts it and builds it**, and fails unless it produces the page byte for byte. A tarball that does not build is worse than no tarball.

## What the workflows check before anything is published

Each of these fails the run rather than warning:

- `VERSION` holds a three-part version, and on a tag it matches the tag exactly;
- the tag being deployed and `VERSION` agree, checked again in `pages.yml`;
- `CHANGELOG.md` has a section for that version and it is not empty, checked with the same script that writes the release body, so the gate cannot pass something the body step would then fail on;
- two builds of the same commit give the same checksum, and that checksum is the built file's own;
- the built page shows the version it is being released as;
- the source tarball builds the same page, byte for byte.

**Every one of those is about the release**, not about the code: whether the thing being published is what it says it is. The checks on the code are `dev/tests/run.sh`, and they run on the machine the change was made on. Z, 2026-09-20: *"We will test only if it builds there. All the other tests should be on this machine."* So `.github/workflows/build.yml` asks a pull request one question -- does it still build, the same twice -- and nothing else runs on a runner.

None of this is a substitute for step 1.

## What the workflows deliberately do not do

- **Neither runs on a push to a branch.** There is no branch you can push to that releases or publishes.
- **Neither can write to a branch.** `release.yml` takes `contents: write` only to attach files to a release; `pages.yml` takes `contents: read`.
- **A rehearsal creates nothing.** `workflow_dispatch` on `release.yml` runs everything and stops before the release step.

## The actions they use

Five, and their versions are what PoolSeqFlow is using, taken from the read rather than from memory:

| Action | Version | Used by |
|---|---|---|
| `actions/checkout` | v7 | both |
| `actions/configure-pages` | v6 | `pages.yml` |
| `actions/upload-pages-artifact` | v5 | `pages.yml` |
| `actions/deploy-pages` | v5 | `pages.yml` |
| `softprops/action-gh-release` | v3 | `release.yml` |

They are pinned to a major version, which is a gap: a major-version tag is a moving pointer, and whoever controls it can change what runs here without the repository changing. Pinning each to a commit SHA fixes that. Four of the five are GitHub's own; `softprops/action-gh-release` is not.
