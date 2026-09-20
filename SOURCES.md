# Sources

Everything PAPvault knows about PAP machines, their files and the platform it runs on came from somewhere, and this file says where.

**No code from any project below is in PAPvault.** What is taken is knowledge: what a file holds, where, in what order and in what units. The rules for that are in `CLAUDE.md`, under *What we take from other projects*. The libraries at the end are the one exception: other people's code, carried whole under their own licenses.

Each entry says what the source is, its license if it is software, and what it was consulted for. *Consulted* means it was read during research; it does not mean PAPvault relies on it. Every link was checked on 2026-09-19 and resolved, except where an entry says otherwise.

## OSCAR

OSCAR, the Open Source CPAP Analysis Reporter, is the free desktop program people install to keep and study their PAP data. PAPvault does not replace it: for keeping data over the long term, and for deeper analysis, OSCAR is the better tool. OSCAR sends no therapy data anywhere; its one network request is a check for new versions, which can be switched off in its preferences.

- **Source code:** [gitlab.com/CrimsonNape/OSCAR-code](https://gitlab.com/CrimsonNape/OSCAR-code), GPL-3.0, read at commit `64c5e90a26f91fb15868bcfcccde0c1e1522ac86` (2026-07-13). Consulted: the device readers under `oscar/SleepLib/loader_plugins/`, for the survey of which machines exist and what their cards hold; and `oscar/checkupdates.cpp`, for what OSCAR sends over the network.
- **What PAPvault uses from it today:** the names ResMed's machines give the signals PAPvault reads, and how the files and folders on a ResMed card are named, from `resmed_loader.cpp` at that commit. For the AirSense 10 those facts are checked against Z's own card; **for the S9 and the 11 series they are not, and OSCAR is their only source.** Each read is recorded in `dev/READING-LOG.md` (R-006), with what was taken and what was not.
- **Earlier home of the same code:** [gitlab.com/pholy/OSCAR-code](https://gitlab.com/pholy/OSCAR-code), GPL-3.0, last changed 2024-10-04. Consulted at the start of the survey, before the move was noticed.
- **A GitHub copy with its own issue tracker:** [github.com/tomasohara/OSCAR-code](https://github.com/tomasohara/OSCAR-code), GPL-3.0. Consulted: [issue 51](https://github.com/tomasohara/OSCAR-code/issues/51), on ResMed machines dividing their data at noon, and [issue 87](https://github.com/tomasohara/OSCAR-code/issues/87), on the removal of the BMC reader from the earlier repository.

## Standards

- **EDF, the European Data Format:** [edfplus.info/specs/edf.html](https://www.edfplus.info/specs/edf.html). The file format ResMed machines, among others, write their recordings in, and the source PAPvault's reading of EDF files is to be written from.
- **EDF+:** [edfplus.info/specs/edfplus.html](https://www.edfplus.info/specs/edfplus.html). The extension that adds annotations, which ResMed's event files use.

## Manufacturers and regulators

- **ResMed, SD card download instructions for the AirSense and AirCurve 10 and 11:** [document.resmed.com](https://document.resmed.com/en-us/documents/products/serviceandsupport/datamanagementdevicecompatibility/sd-card-download-instructions-amer-eng.pdf). Found during the survey as evidence that the 11 series writes to an SD card; its contents were not read.
- **U.S. Food and Drug Administration, the 2021 Philips recall:** [fda.gov](https://www.fda.gov/medical-devices/respiratory-devices/recalled-philips-ventilators-bipap-machines-and-cpap-machines). Consulted for which Philips machines were recalled, and so which older ones people may still be reading data from.
- **Philips System One 60 series manual,** a copy hosted by iFixit: [documents.cdn.ifixit.com](https://documents.cdn.ifixit.com/Ul2RH1bRXihkBXfv.pdf). Consulted for how the machine's clock is set.
- **Fisher & Paykel, the SleepStyle app:** [fphcare.com](https://www.fphcare.com/us/my-sleep-apnea/products/sleepstyle-app/), and a pairing guide hosted by a retailer: [respshop.com](https://www.respshop.com/manuals/sleepstyle-app-pairing-guide.pdf). Consulted for how SleepStyle data reaches its app.

## Other open-source projects

- **oscar-js:** [github.com/ZacSadan/oscar-js](https://github.com/ZacSadan/oscar-js), no license. A reader for Loewenstein prisma cards that runs in the browser. Consulted for facts about the prisma card's layout; having no license, it is read for facts only, and none of its text or code is reproduced.
- **edf-importer:** [github.com/tedpearson/edf-importer](https://github.com/tedpearson/edf-importer), MIT. Consulted for how AirSense 11 event files carry their events.
- **hms-cpap:** [github.com/hms-homelab/hms-cpap](https://github.com/hms-homelab/hms-cpap), MIT. Consulted: [issue 33](https://github.com/hms-homelab/hms-cpap/issues/33), for the signal and summary names on an AirCurve 11 card.
- **airsupply:** [github.com/ananthb/airsupply](https://github.com/ananthb/airsupply), GPL-3.0. Consulted for how the ResMed AirMini, which has no card, talks to its app.
- **djmed:** [github.com/Centurix/djmed](https://github.com/Centurix/djmed), no license. Consulted for facts about Yuwell cards; read for facts only.
- **Resvent iBreeze Data Puller:** [github.com/Ryush806/Resvent_iBreeze_Data_Puller](https://github.com/Ryush806/Resvent_iBreeze_Data_Puller), GPL-3.0. Consulted for how Resvent machines sample their data.

## Community

- **CPAPtalk, a thread reverse-engineering the Philips System One card:** [cpaptalk.com, topic 55722](https://www.cpaptalk.com/viewtopic.php?t=55722). Consulted for the card's folder layout.
- **CPAPtalk, on OSCAR 1.4.0 reading the DreamStation 2:** [cpaptalk.com, topic 184531](https://www.cpaptalk.com/viewtopic.php?t=184531). Consulted for when third-party reading of that machine began.
- **Apnea Board wiki:** [apneaboard.com/wiki](https://www.apneaboard.com/wiki/). It refuses automated access, so it was consulted only through the excerpts a web search shows, for which machines OSCAR supports and how it divides days.

## The platform

- **GitHub Pages, on data collection:** [docs.github.com](https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages). Consulted for what GitHub records about visitors.
- **GitHub staff, on custom response headers for Pages:** [community discussion 54257](https://github.com/orgs/community/discussions/54257). Consulted for why the page's security policy is a `<meta>` tag.
- **MDN, Content Security Policy:** [the guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP), and [`frame-ancestors`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors). Consulted for how a policy delivered in a `<meta>` tag behaves, and what it cannot do.
- **MDN, JavaScript modules:** [the guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules). Consulted for why a page opened from disk cannot load its scripts as modules.

## The reference for reading a real card

- **PAPvault's R prototype,** written by Z and kept outside the repository: the ground truth for reading an AirSense 10 card, on Z's own machine.
- **edf, the R package it reads files with:** [github.com/bwrc/edf](https://github.com/bwrc/edf), MIT according to its own description file. Version 1.0.1, installed from CRAN by Z on 2026-09-19, is the one the checks run with.

## Color schemes

Read on 2026-09-20 under `R-019` and `R-020`, to find a palette for event names that survives color blindness. What the reads established is recorded in `.claude/development-notes/drawing-the-plots.md`. PAPvault uses Okabe and Ito's palette; the others were measured and not used.

- **Vienot, F., Brettel, H., and Mollon, J. D., "Digital video colourmaps for checking the legibility of displays by dichromats",** *Color Research and Application* 24(4):243-252, 1999, [doi 10.1002/(SICI)1520-6378(199908)24:4<243::AID-COL5>3.0.CO;2-3](https://doi.org/10.1002/%28SICI%291520-6378%28199908%2924%3A4%3C243%3A%3AAID-COL5%3E3.0.CO%3B2-3). The method PAPvault's development uses to simulate protanopia, deuteranopia and tritanopia, and so to measure whether two event colors stay apart for a reader who has one of them. The page does not run it; it is how the palette is checked. Its citation was verified against bibliographic records after the agent first wrote it from recollection, which is recorded as a slip in `dev/READING-LOG.md`.
- **ColorBrewer,** Cynthia Brewer's color schemes: [colorbrewer2.org](https://colorbrewer2.org), with the data and tool at [github.com/axismaps/colorbrewer](https://github.com/axismaps/colorbrewer). *"Apache-Style Software License for ColorBrewer software and ColorBrewer Color Schemes"*, Copyright (c) 2002 Cynthia Brewer, Mark Harrower, and The Pennsylvania State University, under Apache 2.0, which is compatible with GPL-3.0. **PAPvault's signal plots use its `Dark2` scheme in the light theme and its `Set2` scheme in the dark one**, taken as published; the two pair entry for entry, which is why a signal keeps its place when the theme changes. Its eight qualitative schemes were also measured for the event colors and not used there, since none held five categories apart under color vision deficiency. **Condition 2 of the licence requires this acknowledgment in the user documentation, and `docs/manual.md` carries it verbatim:** *"This product includes color specifications and designs developed by Cynthia Brewer (http://colorbrewer.org/)."* Conditions 4 and 5 forbid using the name ColorBrewer to endorse this product or as part of its name, and it is used here only to say where the colors came from.
- **Color Universal Design,** Masataka Okabe and Kei Ito: [jfly.uni-koeln.de/color](https://jfly.uni-koeln.de/color/). **PAPvault's event colors are this palette**, read as published in the page's Figure 16, which prints a name, a hue angle, CMYK and RGB for each of its eight colors. The underlying work is Ichihara, Y. G., Okabe, M., Iga, K., Tanaka, Y., Musha, K., and Ito, K., *"Color universal design: the selection of four easily distinguishable colors for all color vision types"*, Proc. SPIE 6807, 68070O, 2008, [doi 10.1117/12.765420](https://doi.org/10.1117/12.765420), whose copy the authors host alongside the page. **The page states no formal license**, offering its brochure and slides for use in *"classes and seminars"* with the authors credited. Z ruled on 2026-09-20 that PAPvault uses the palette with both works cited, and the manual cites both. The read is `R-020`; the values are unmodified, and each theme uses the subset of them that meets PAPvault's contrast bar against its own surface.
- **Paul Tol, "Colour Schemes",** SRON/EPS/TN/09-002: [sronpersonalpages.nl/~pault](https://sronpersonalpages.nl/~pault/). **No license statement**, and the page carries only *"(c) 2009-2026 Paul Tol"*. Consulted for its terms; its schemes were not taken. Its former address, `personal.sron.nl`, no longer resolves.

## Libraries and design references

- **uPlot:** [github.com/leeoniya/uPlot](https://github.com/leeoniya/uPlot), version 1.6.32, MIT. Chosen to draw the plots, and the one library in the page. It is carried whole and unmodified in `lib/uplot/`, taken from the repository's tag `1.6.32`, which is commit `e995b061e9fc5476a6d862cd2fb2ebc7452ca012` (2025-03-14):

  | File in `lib/uplot/` | From | Bytes | SHA-256 | |---|---|---|---| | `uPlot.iife.js` | `dist/uPlot.iife.js` | 150,232 | `1b71fc5e6b5b572922ed9941ed21d067207c8e5ecac0d35de66fd65d9686e791` | | `uPlot.css` | `src/uPlot.css` | 2,048 | `9eeefb2466014dc31038e20b72693a45dde4c56c5fe6176ea314cff95b6576d1` | | `LICENSE` | `LICENSE` | 1,078 | `8f989229699b4fe2f1a0432d0e9edc338a8a911e250e2d1b01ecd770a5f5b1bd` |

  The stylesheet is taken from `src/`, since the only copy under `dist/` is minified. `sha256sum lib/uplot/*` checks all three against this table.
- **plotly.js:** [github.com/plotly/plotly.js](https://github.com/plotly/plotly.js), version 4.1.1, MIT. Tried against uPlot and not chosen.
- **TaxTriage:** [github.com/jhuapl-bio/taxtriage](https://github.com/jhuapl-bio/taxtriage), MIT. Its single-file report that opens offline is the model for PAPvault's offline page.
