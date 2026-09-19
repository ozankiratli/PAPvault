# Platform traps

**This file is kept current.** It is appended to as traps are found, with a date on each entry, since a trap does not expire. It is one of the two exceptions to the dating rule in `README.md`.

Each entry is something that produced a wrong result once, with the symptom it showed and what to do instead.

## A zsh variable holding a command runs as one word

*Found 2026-09-18.* The shell here is zsh, which does not split an unquoted variable into words the way bash does. `C="chromium --headless ..."; $C --screenshot=...` looked for a program named by the whole string, and exited 127, command not found.

Use a shell function (`shot() { chromium --headless ... "$@"; }`) or an array, or write the steps as a bash script and run it with `bash`.

## The Edit and Write tools rewrite `\u` escapes

*Found 2026-09-19.* Writing a JavaScript escape such as `"\u263E"` in an Edit tool's replacement text put the character itself in the file, not the six ASCII characters of the escape. Writing `"\\u263E"` instead put two backslashes in the file, which JavaScript reads as a literal backslash followed by `u263E`, so the page would have shown the escape as text.

Neither form yields a single backslash. What worked was a one-line `sed` on that line, announced beforehand (`sed -i '25s/\\\\u/\\u/g' src/app.js`), followed by `od -c` on the line to see the bytes. After writing any escape, check the bytes; `grep -nP '[^\x00-\x7F]'` catches the first failure and not the second.

The Write tool does the same. When this file was created, its own first example above arrived as the moon character, and was put back with a `sed` that matched the character by its UTF-8 bytes (`sed -i '15s/\xe2\x98\xbe/\\u263E/'`).

## Headless Chromium ignores `--lang` for dates and times

*Found 2026-09-19.* Started with `--lang=de-DE`, headless Chromium on Linux still reported `navigator.language` as `en-US` and formatted times in 12-hour form, so a check of the page's locale default came back 12-hour for German and British English alike, and could not have failed. The locale `Intl` uses comes from the environment: start it with `LANG=de_DE.UTF-8` (and set `LANG` explicitly for any run whose output depends on the locale). Before trusting such a run, print `Intl.DateTimeFormat().resolvedOptions()` from inside the page.

## A probe page is a copy of the build it was made from

*Found 2026-09-19.* Probe pages are made by copying `dist/index.html` and adding scripts, so they hold the page as it was built at that moment. A screenshot of one made before the last `python3 build.py` showed the old text buttons after the icons had replaced them. Regenerate every probe page after each build, and check that it holds something only the new build has before looking at what it shows.
