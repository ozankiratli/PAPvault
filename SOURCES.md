# Sources

Everything PAPvault knows about PAP machines, their files and the platform it runs on came from somewhere, and this file says where.

**No code from any project below is in PAPvault.** What is taken is knowledge: what a file holds, where, in what order and in what units. The rules for that are in `CLAUDE.md`, under *What we take from other projects*. The libraries at the end are the one exception: other people's code, carried whole under their own licenses.

Each entry says what the source is, its license if it is software, and what it was consulted for. *Consulted* means it was read during research; it does not mean PAPvault relies on it. Every link was checked on 2026-09-19 and resolved, except where an entry says otherwise.

## OSCAR

OSCAR, the Open Source CPAP Analysis Reporter, is the free desktop program people install to keep and study their PAP data. PAPvault does not replace it: for keeping data over the long term, and for deeper analysis, OSCAR is the better tool. OSCAR sends no therapy data anywhere; its one network request is a check for new versions, which can be switched off in its preferences.

- **Source code:** [gitlab.com/CrimsonNape/OSCAR-code](https://gitlab.com/CrimsonNape/OSCAR-code), GPL-3.0, read at commit `64c5e90a26f91fb15868bcfcccde0c1e1522ac86` (2026-07-13). Consulted: the device readers under `oscar/SleepLib/loader_plugins/`, for the survey of which machines exist and what their cards hold; and `oscar/checkupdates.cpp`, for what OSCAR sends over the network.
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
- **edf, the R package it reads files with:** [github.com/bwrc/edf](https://github.com/bwrc/edf), version 1.0.0, MIT according to its own description file.

## Libraries and design references

- **uPlot:** [github.com/leeoniya/uPlot](https://github.com/leeoniya/uPlot), version 1.6.32, MIT. Chosen to draw the plots; it enters the repository with the first plot.
- **plotly.js:** [github.com/plotly/plotly.js](https://github.com/plotly/plotly.js), version 4.1.1, MIT. Tried against uPlot and not chosen.
- **TaxTriage:** [github.com/jhuapl-bio/taxtriage](https://github.com/jhuapl-bio/taxtriage), MIT. Its single-file report that opens offline is the model for PAPvault's offline page.
