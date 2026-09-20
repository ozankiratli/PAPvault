<!-- The standing tail of every GitHub release body: the part that does not change from
     release to release. The part that does is this version's CHANGELOG.md section, which
     dev/scripts/changelog-section.sh extracts and publish.yml puts above this.

     @VERSION@ is substituted by publish.yml. This lives in a file rather than inside the
     workflow because it is markdown full of backticks and fenced blocks, which a YAML block
     scalar and a shell heredoc each mangle in their own way.
-->

## Use it

Open <https://ozankiratli.github.io/PAPvault/> and choose your card's folder. Nothing is
uploaded: the page reads the files in your browser and has nowhere to send them.

## Or run it offline

`index.html` below is the whole program in one file. Download it, open it in a browser,
and it works with no network at all.

```bash
curl -LO https://github.com/ozankiratli/PAPvault/releases/download/v@VERSION@/index.html
sha256sum -c SHA256SUMS
```

## Check that this is what the source builds

```bash
git clone https://github.com/ozankiratli/PAPvault
cd PAPvault && git checkout v@VERSION@
python3 build.py
```

It prints the SHA-256 of what it built. It will be the one in `SHA256SUMS`, because the
build uses nothing but the Python standard library and the same input gives the same bytes.

## What it does not do

PAPvault shows what your machine recorded and adds no judgment of its own: no score, no
normal range, no verdict. It collects nothing about you. For keeping years of data and
studying them deeply, use [OSCAR](https://www.sleepfiles.com/OSCAR/).

The full changelog is in `CHANGELOG.md` in the repository.
