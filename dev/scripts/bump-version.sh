#!/usr/bin/env bash
#
# Bump PAPvault's version and start its CHANGELOG entry from the git log.
#
# Usage: dev/scripts/bump-version.sh <new-version>          e.g. 0.1.0
#
# Writes the new number into VERSION, which is the only place it lives: the build
# reads it, prints it beside the checksum, puts it in the page's top bar and fills it
# into the manual. Then it prepends a CHANGELOG section listing every commit since the
# last release tag under a "### Commits" heading, with the matching reference-link
# definition at the foot of the file.
#
# Does not commit, tag or push. It prints those commands for you.
#
# Write the release notes ABOVE the "### Commits" heading, not over it: the commit
# list stays in the changelog as the record of what actually landed.

set -euo pipefail

NEW="${1-}"
if [[ ! "$NEW" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Usage: $0 <new-version>   (e.g. 0.1.0)" >&2
    exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

VERSION_FILE="VERSION"
LOG="CHANGELOG.md"
for f in "$VERSION_FILE" "$LOG"; do
    [ -f "$f" ] || { echo "ERROR: $f not found in $ROOT" >&2; exit 1; }
done

CURRENT="$(tr -d '[:space:]' < "$VERSION_FILE")"
[ -n "$CURRENT" ] || { echo "ERROR: $VERSION_FILE is empty" >&2; exit 1; }
[ "$NEW" != "$CURRENT" ] || { echo "ERROR: $VERSION_FILE is already at $NEW" >&2; exit 1; }
grep -q "^## \[$NEW\]" "$LOG" && { echo "ERROR: $LOG already has a [$NEW] section" >&2; exit 1; }

# Everything since the most recent tag, or the whole history for a first release.
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
    RANGE="$LAST_TAG..HEAD"
else
    RANGE="HEAD"
fi

COMMITS="$(git log --no-merges --reverse --pretty='- (%h) %s' "$RANGE")"
if [ -z "$COMMITS" ]; then
    echo "ERROR: no commits since ${LAST_TAG:-the start of history} - nothing to release" >&2
    exit 1
fi

ENTRY="## [$NEW] - $(date +%F)

### Commits

$COMMITS

---
"

# Inserted above the newest existing section. The entry reaches awk through ENVIRON
# rather than -v, because -v processes escape sequences and would rewrite a commit
# subject that happens to contain \t or \n.
ENTRY="$ENTRY" awk '
    !inserted && /^## \[/ { print ENVIRON["ENTRY"]; inserted = 1 }
    { print }
    END { if (!inserted) print ENVIRON["ENTRY"] }
' "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"

# Every `## [x.y.z]` heading is a Markdown reference link and renders as literal
# brackets without a definition. The base URL is taken from the newest existing one,
# so it follows the repository rather than being written down twice.
LINKBASE="$(sed -n 's|^\[[0-9][0-9.]*\]: \(https://.*\)/v[0-9][0-9.]*$|\1|p' "$LOG" | head -1)"
[ -n "$LINKBASE" ] || LINKBASE="https://github.com/ozankiratli/PAPvault/releases/tag"
LINK="[$NEW]: $LINKBASE/v$NEW"

if grep -qE '^\[[0-9]+\.[0-9]+\.[0-9]+\]: ' "$LOG"; then
    LINK="$LINK" awk '
        !inserted && /^\[[0-9]+\.[0-9]+\.[0-9]+\]: / { print ENVIRON["LINK"]; inserted = 1 }
        { print }
    ' "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
else
    printf '\n%s\n' "$LINK" >> "$LOG"
fi

printf '%s\n' "$NEW" > "$VERSION_FILE"
[ "$(tr -d '[:space:]' < "$VERSION_FILE")" = "$NEW" ] || {
    echo "ERROR: could not write $NEW to $VERSION_FILE" >&2; exit 1; }

# The build is what puts the version into the page, so run it here rather than leaving
# a stale dist/ behind, and show the checksum this version currently has.
BUILT="$(python3 build.py)"

echo "$CURRENT -> $NEW"
echo "  $VERSION_FILE      : written"
echo "  $LOG   : $(printf '%s\n' "$COMMITS" | wc -l) commits since ${LAST_TAG:-the start}, link definition added"
echo "  built        : $BUILT"
echo
echo "Write this version's notes into $LOG, above its '### Commits' heading. Then:"
echo "  git add -A && git commit -m 'Version bump $NEW'"
echo "  git tag v$NEW"
echo
echo "Pushing the tag is what publishes. Nothing here has pushed anything."
