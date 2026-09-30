# Releasing PAPvault

Two workflows, and a person between them.

1. **`release.yml`** runs when a tag is pushed. It builds the page, checks it, and publishes a GitHub release carrying the page, its checksums, and a source tarball.
2. **`pages.yml`** runs when a tag is pushed. It builds the page and deploys the website.

Both start from the same push, and neither waits on the other. Push the tag and the site goes up and the release appears. A push to a branch does neither.

## What is attached to a release

- **`index.html`** -- the whole program in one file. Downloaded, it runs offline with no network at all. It is the same bytes the website serves.
- **`SHA256SUMS`** -- so a download can be checked, and so anyone can rebuild at the tag and compare.
- **`PAPvault-<version>.tar.gz`** -- what someone needs to build PAPvault and run it: `build.py`, `src/`, `lib/`, `docs/manual.md`, `VERSION`, the licence, and the source lists. It is built from the git index, and the workflow builds it again and fails unless it produces the page byte for byte.

**A published release cannot be changed.** Release immutability is on, so a wrong file, a wrong checksum or a release body naming the wrong version is fixed by releasing again with the next patch number, never by editing what is there.

## Each release

1. **Run the checks** with `dev/tests/run.sh`, on this machine. 
2. Then **use** `dev/CHECKLIST.md` to  **check it by hand**. Write what was checked into `dev/VERIFICATION.md`. 
3. **Run the bump.**

       dev/scripts/bump-version.sh 0.1.0

   It writes `VERSION`, prepends a `CHANGELOG.md` section holding every commit since the last tag, adds the reference-link definition at the foot, rebuilds, and prints the checksum. It does not commit, tag or push; it prints those commands.
4. **Write the notes** into that new `CHANGELOG.md` section, **above** its `### Commits` heading and not over it. The commit list stays as the record of what landed. What is written there is what the release body will say.
5. **Commit and push the branch.**

       git add -A && git commit -m 'Version bump 0.1.0'
       git push

6. **Rehearse it**, before tagging: from the Actions tab, run **Create a release** against that branch, which runs every check and prints the release body but creates no release, since there is no tag yet.
7. **Tag it.**

       git tag v0.1.0

8. **Push the tag.** This is the only step that publishes anything.

       git push --tags

   The tag push starts both workflows. `release.yml` publishes the release with its three files; `pages.yml` deploys the site.
9. **Watch both finish**, and open the site.
10. **Check what was published**, once, against what was built.

        python3 dev/tests/live.py

    It asks the site for its headers, checks that plain http is redirected and that nothing of the repository is served, fetches the page and compares its checksum with the local build, and checks it shows the version it was released as. This is the one part of `dev/tests/` that reaches the network, which is why it is here and not in `run.sh`. Then open the site in a browser and run `fetch('https://example.com')` in the console: it must fail as a Content-Security-Policy violation and nothing else. That one line is by hand because the machine's proof that the policy is enforced runs against a file, and only this says it holds over https. **There is no step after this**: nothing to publish by hand, no draft to approve, no workflow to start.

Why the workflows are built this way, what they check and refuse, the repository settings a first release needs, and why the actions are pinned to major versions rather than to commits are in `.claude/development-notes/publishing-a-release.md`.
