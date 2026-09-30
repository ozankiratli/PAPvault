# Publishing a release

**Written 2026-09-29, against the tree at `cfacb45`.** This is the reasoning behind `dev/RELEASING.md`, which was carrying it and is now the steps alone. Anything here that describes the workflows describes them as they stood on this date.

## Where the shape came from

The release system is the one Z built for PoolSeqFlow, adapted to a project that ships one HTML file rather than a pipeline. What was read from it, and what was left behind as not applicable, is `R-021` in `dev/READING-LOG.md`.

## The settings that have to exist before a tag can publish anything

Two, both in the repository's own Settings on GitHub, and neither of them in the repository.

**Settings -> Pages -> Build and deployment -> Source** must be **GitHub Actions**. It cannot be "Deploy from a branch": `dist/` is build output and is not in the repository, so no branch holds a finished page to serve. Until this is set, `actions/configure-pages` fails the run early and says so.

**Settings -> Environments -> `github-pages` -> Deployment branches and tags** must allow the release tags. Set it to **Selected branches and tags** and add two rules:

| Type | Pattern | What it is for |
|---|---|---|
| Tag | `v*` | every release |
| Branch | `main` | running the workflow by hand |

That is what makes "the site changes only on a release" a rule GitHub enforces rather than a habit. `pages.yml` only listens for tags, but if that were ever widened by accident the environment would still refuse the deployment.

**The `main` rule is a way in, so know what it does.** Running `pages.yml` by hand against `main` deploys whatever `main` holds at that moment, released or not. It is there to recover from a deployment that failed for a reason outside the repository, and it is the one path that can put an unreleased state on the website. Run it against the tag instead wherever that will do.

**This was found by it failing.** On 2026-09-20 the repository refused a deployment from the `v0.0.1` tag before those rules existed: *"Tag "v0.0.1" is not allowed to deploy to github-pages due to environment protection rules."* What the environment allowed before that was not recorded, so the table above is the thing to set, not a description of what GitHub starts with. The build half of a run succeeds whether or not it is right, so the failure shows up as a workflow that ran, went green on `build`, and stopped at `deploy`.

## Why immutability is the setting that makes the rest mean anything

The repository has release immutability turned on, so once a release is published its tag and its files are fixed and cannot be replaced.

PAPvault's claim is that anyone can rebuild the page from the source at a tag and get the same bytes. If the tag could be moved, or the attached `index.html` swapped, the checksum in `SHA256SUMS` would be a statement about a moment rather than about a version. Immutability is what turns it into a fact someone can check a year later.

What it costs is that **nothing can be patched in place.** A wrong file, a wrong checksum or a release body naming the wrong version is fixed by releasing again with the next patch number, never by editing what is there. That is what makes **the rehearsal** the safety net rather than a courtesy: it is the last point at which a mistake is still an ordinary commit. There is nothing after the tag that can be taken back.

## Why the tarball is built the way it is

It is built with `git archive` rather than `tar`, so what goes in comes from the git index rather than from whatever is lying around in the runner's working directory. The workflow then extracts it and builds it, and fails unless it produces the page byte for byte. A tarball that does not build is worse than no tarball.

What it leaves out is decided by `export-ignore` in `.gitattributes`: `dev/`, `.claude/` and `.github/` are the record of how PAPvault was built rather than what it is built from, and they stay in the repository for anyone who clones.

## What the workflows check before anything is published

Each of these fails the run rather than warning:

- `VERSION` holds a three-part version, and on a tag it matches the tag exactly;
- the tag being deployed and `VERSION` agree, checked again in `pages.yml`;
- `CHANGELOG.md` has a section for that version and it is not empty, checked with the same script that writes the release body, so the gate cannot pass something the body step would then fail on;
- two builds of the same commit give the same checksum, and that checksum is the built file's own;
- the built page shows the version it is being released as;
- the source tarball builds the same page, byte for byte.

**Every one of those is about the release**, not about the code: whether the thing being published is what it says it is. The checks on the code are `dev/tests/run.sh`, and they run on the machine the change was made on. Z, 2026-09-20: *"We will test only if it builds there. All the other tests should be on this machine."* So `.github/workflows/build.yml` asks a pull request one question -- does it still build, the same twice -- and nothing else runs on a runner.

## What the workflows deliberately do not do

- **Neither runs on a push to a branch.** There is no branch anyone can push to that releases or publishes.
- **Neither can write to a branch.** `release.yml` takes `contents: write` only to attach files to a release; `pages.yml` takes `contents: read`.
- **A rehearsal creates nothing.** `workflow_dispatch` on `release.yml` runs everything and stops before the release step.

## The actions they use, and why they are not pinned to commits

Five, pinned to a major version tag:

| Action | Version | Used by |
|---|---|---|
| `actions/checkout` | v7 | all three |
| `actions/configure-pages` | v6 | `pages.yml` |
| `actions/upload-pages-artifact` | v5 | `pages.yml` |
| `actions/deploy-pages` | v5 | `pages.yml` |
| `softprops/action-gh-release` | v3 | `release.yml` |

Four are GitHub's own; `softprops/action-gh-release` is not, and it runs in `release.yml` alone, so the path that publishes the website carries no third-party code.

**A major version tag is a pointer its owner can move**, which is how an action ships a fix without anyone editing a workflow. Pinning each to a commit instead was proposed on 2026-09-21 and the commits were resolved, and **Z decided against it**: PAPvault's own releases are immutable, so every published `index.html` and its `SHA256SUMS` are fixed and cannot be replaced. That leaves a permanent reference nobody can alter, and the `rebuild` entry in `dev/CHECKLIST.md` is the check that uses it -- rebuild at the tag, compare with what is served. Tampering in the runner does not have to be prevented if it is detectable against something that cannot change.

The residual, stated so it is not discovered later: the website is deployed by `pages.yml` separately from the release, so a page swapped there would still differ from the release asset rather than matching it -- which is what makes the comparison work, and also means the comparison has to actually be run. It is a per-release human check, not a continuous one.

If that is ever revisited, the commits are resolved from the public API over plain https, since there is no `gh` on this machine:

    https://api.github.com/repos/<owner>/<repo>/git/ref/tags/<tag>

An annotated tag needs one more hop through `/git/tags/<sha>` to reach the commit.
