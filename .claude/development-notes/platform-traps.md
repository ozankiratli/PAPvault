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

## Canvas text is not drawn in the color you asked for

*Found 2026-09-20.* A probe that reads a canvas looked for pixels whose color was exactly the color the page had filled its text with. It found the numerals `4`, `3` and `2` and reported that the `1` on the fourth bar was missing, when a screenshot of the same page showed it plainly. Chromium draws text with subpixel antialiasing, which gives each of the three channels its own coverage, so a thin glyph can have no pixel at the exact color asked for. A wider numeral has at least one fully covered pixel and matches; a `1` at eleven pixels may have none.

A filled rectangle does not have this problem: its interior is the exact color, and only its edges vary, and then only in alpha.

So match text by nearness rather than by equality -- the probe here takes any drawn pixel within 80 of the text color on every channel, which is far from the only other thing drawn in that area, the gridlines. Before trusting a pixel check that reports something missing, screenshot the same page and look.

## A headless screenshot comes back blank after a programmatic scroll

*Found 2026-09-20.* A probe scrolled the page with `window.scrollTo(0, 900)` and then the run was screenshotted to see the sticky bar over the plots. Every such capture was the page background and nothing else, at two virtual time budgets and from two different probe pages, while a `--dump-dom` run of the same page reported the scroll had happened and the layout was right. A capture taken without scrolling, of the same page, came out correctly.

Do not read a blank capture as a blank page. Measure the rendered geometry from inside the page instead -- `getBoundingClientRect()` for where something sits, `document.elementFromPoint` and `elementsFromPoint` for what is drawn on top of what -- or make the window taller than the content so that nothing has to scroll.
