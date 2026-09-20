#!/usr/bin/env bash
#
# Run PAPvault's checks.
#
#     dev/tests/run.sh              everything
#     dev/tests/run.sh --no-page    everything but the headless browser
#
# This does not decide whether a release is good. `dev/CHECKLIST.md` is what decides
# that, and a person runs it. What this does is notice when something that used to
# work has stopped, which is the part a person cannot do after every change.
#
# It needs python3, node and a chromium. Nothing else, and nothing from a package
# manager. It reaches no network.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PAGE=1
for arg in "$@"; do
    case "$arg" in
        --no-page) PAGE=0 ;;
        *) echo "usage: $0 [--no-page]" >&2; exit 1 ;;
    esac
done

passed=0
failed=0

step() {
    local what="$1"
    shift
    printf '\n== %s\n' "$what"
    if "$@"; then
        passed=$((passed + 1))
    else
        failed=$((failed + 1))
        printf '   ^^ FAILED: %s\n' "$what"
    fi
}

# ---------------------------------------------------------------- what ships ----

no_markup() {
    if grep -rn "innerHTML\|outerHTML\|insertAdjacentHTML\|document\.write\|eval(\|new Function" src lib; then
        echo "one of the sinks CLAUDE.md forbids is in the source"
        return 1
    fi
    echo "  ok  none of them appears in src or lib"
}

ascii_only() {
    if LC_ALL=C grep -rnP '[^\x00-\x7F]' src build.py; then
        echo "a byte outside ASCII is in the code that ships"
        return 1
    fi
    echo "  ok  src and build.py are ASCII throughout"
}

scripts_parse() {
    local one
    for one in dev/scripts/*.sh dev/tests/*.sh; do
        bash -n "$one" || return 1
        echo "  ok  $one"
    done
}

deterministic() {
    local first second served
    first="$(python3 build.py | tee /dev/stderr | cut -d' ' -f1)" || return 1
    second="$(python3 build.py | cut -d' ' -f1)" || return 1
    if [ "$first" != "$second" ]; then
        echo "two builds of one tree gave different bytes"
        return 1
    fi
    served="$(sha256sum dist/index.html | cut -d' ' -f1)"
    if [ "$first" != "$served" ]; then
        echo "the build reported a checksum that is not the file's own"
        return 1
    fi
    echo "  ok  twice the same, and it is the file's own checksum"
}

shows_its_version() {
    local version
    version="$(tr -d '[:space:]' < VERSION)"
    if ! grep -q ">v${version}<" dist/index.html; then
        echo "the built page does not show v${version}"
        return 1
    fi
    echo "  ok  the page shows v${version}"
}

# ------------------------------------------------------------- what it reads ----

synthetic_cards() {
    python3 dev/synthetic/resmed.py || return 1
    # Twice, because a generator that does not write the same bytes every time cannot
    # carry an answer.
    local before after
    before="$(find dev/synthetic/out -type f ! -name answer.json -exec sha256sum {} + | sort | sha256sum)"
    python3 dev/synthetic/resmed.py > /dev/null || return 1
    after="$(find dev/synthetic/out -type f ! -name answer.json -exec sha256sum {} + | sort | sha256sum)"
    if [ "$before" != "$after" ]; then
        echo "the generator wrote different bytes the second time"
        return 1
    fi
    echo "  ok  the same cards both times"
}

step "nothing from a file becomes markup or code" no_markup
step "what ships is ASCII" ascii_only
step "the shell scripts parse" scripts_parse
step "the build is deterministic" deterministic
step "the page carries its own version" shows_its_version
step "the synthetic cards build, and build the same twice" synthetic_cards
step "the parser against the synthetic answers" node dev/tests/edf-vs-answer.js "$ROOT"
step "the card reader against the synthetic answers" node dev/tests/card-vs-answer.js "$ROOT"
step "the CPAP day at every edge it has" node dev/tests/day-boundary.js "$ROOT"
step "cards the committed cases cannot be" node dev/tests/cards/derived.js "$ROOT"

if [ "$PAGE" = "1" ]; then
    step "the built page in a headless browser" python3 dev/tests/page/run.py "$ROOT"
else
    printf '\n== the built page in a headless browser\n   skipped\n'
fi

printf '\n----------------------------------------\n'
printf '%d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
