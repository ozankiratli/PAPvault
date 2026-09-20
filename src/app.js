"use strict";

(function () {
  const app = document.getElementById("app");

  if (window.top !== window.self) {
    const notice = document.createElement("p");
    notice.className = "notice";
    notice.textContent = "PAPvault does not run inside a frame. Open it in a tab of its own.";
    document.body.replaceChildren(notice);
    return;
  }

  const root = document.documentElement;
  const toggle = document.getElementById("theme-toggle");
  const darkIcon = document.getElementById("theme-icon-dark");
  const lightIcon = document.getElementById("theme-icon-light");
  const THEME_KEY = "papvault-theme";
  const TIME_FORMAT_KEY = "papvault-time-format";

  function readSetting(key, allowed) {
    try {
      const value = window.localStorage.getItem(key);
      return allowed.indexOf(value) === -1 ? null : value;
    } catch (e) {
      return null;
    }
  }

  function writeSetting(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (e) {
      // Storage is unavailable in some private windows; the choice then lasts for this visit.
    }
  }

  function systemTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    root.dataset.theme = theme;
    const next = theme === "dark" ? "light" : "dark";
    darkIcon.toggleAttribute("hidden", next !== "dark");
    lightIcon.toggleAttribute("hidden", next !== "light");
    toggle.setAttribute("aria-label", next === "dark" ? "Switch to Dark Mode" : "Switch to Light Mode");
  }

  applyTheme(readSetting(THEME_KEY, ["dark", "light"]) || systemTheme());

  toggle.addEventListener("click", function () {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(next);
    writeSetting(THEME_KEY, next);
    // The charts take their colors when they are built, so they are built again.
    renderPeriod();
  });

  function browserTimeFormat() {
    const options = new Intl.DateTimeFormat(undefined, { hour: "numeric" }).resolvedOptions();
    if (options.hourCycle) {
      return options.hourCycle === "h11" || options.hourCycle === "h12" ? "12" : "24";
    }
    return options.hour12 ? "12" : "24";
  }

  let timeFormat = readSetting(TIME_FORMAT_KEY, ["12", "24"]) || browserTimeFormat();

  const MONTHS = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];
  const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

  const grid = document.getElementById("calendar-grid");
  const monthLabel = document.getElementById("calendar-month");
  const dayPrev = document.getElementById("day-prev");
  const dayNext = document.getElementById("day-next");
  const summaryBody = document.getElementById("summary-body");
  const summaryPlots = document.getElementById("summary-plots");
  const eventPlot = document.getElementById("event-plot");
  const plotsBody = document.getElementById("plots-body");
  const plotPicker = document.getElementById("plot-picker");
  const legendDock = document.getElementById("legend-dock");
  const legendPanel = document.getElementById("legend-panel");
  const legendList = document.getElementById("legend-list");
  const legendToggle = document.getElementById("legend-toggle");
  const CHARTS_KEY = "papvault-charts";

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function clockTime(d, withSeconds) {
    const rest = pad(d.getMinutes()) + (withSeconds ? ":" + pad(d.getSeconds()) : "");
    if (timeFormat === "24") {
      return pad(d.getHours()) + ":" + rest;
    }
    const hour = d.getHours() % 12 === 0 ? 12 : d.getHours() % 12;
    return hour + ":" + rest + " " + (d.getHours() < 12 ? "AM" : "PM");
  }

  function dateTime(d) {
    return dayKey(d) + " " + clockTime(d);
  }

  function nextDay(d) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1);
  }

  // The calendar's days are CPAP days, each held as local midnight of its date.
  // Where a CPAP day begins is set once, in card.js, and read from there.
  const cpapDayOf = PAPvaultCard.cpapDayOf;
  const cpapDayStart = PAPvaultCard.cpapDayStart;
  const dayKey = PAPvaultCard.dayKey;

  const currentDay = cpapDayOf(new Date());
  let shown = new Date(currentDay.getFullYear(), currentDay.getMonth(), 1);
  let start = currentDay;
  let end = currentDay;
  let pending = false;

  // What reading the chosen folder found, and its sessions keyed by CPAP day.
  let card = null;
  let daysWithData = new Map();

  // The drawn charts, and a token that abandons a draw whose selection has moved on.
  let dayView = null;
  let summaryView = null;
  let eventView = null;
  let drawToken = 0;

  const DEFAULT_CHARTS = PAPvaultPlots.charts.filter(function (chart) {
    return !chart.off;
  }).map(function (chart) {
    return chart.key;
  });

  function readCharts() {
    try {
      const stored = window.localStorage.getItem(CHARTS_KEY);
      if (stored) {
        return JSON.parse(stored).filter(function (key) {
          return PAPvaultPlots.charts.some(function (chart) {
            return chart.key === key;
          });
        });
      }
    } catch (e) {
      // Storage is unavailable in some private windows; the choice then lasts for this visit.
    }
    return DEFAULT_CHARTS.slice();
  }

  let chosenCharts = readCharts();

  PAPvaultPlots.charts.forEach(function (chart) {
    const label = document.createElement("label");
    const box = document.createElement("input");
    box.type = "checkbox";
    box.checked = chosenCharts.indexOf(chart.key) !== -1;
    box.addEventListener("change", function () {
      chosenCharts = PAPvaultPlots.charts.filter(function (one) {
        return one.key === chart.key ? box.checked : chosenCharts.indexOf(one.key) !== -1;
      }).map(function (one) {
        return one.key;
      });
      writeSetting(CHARTS_KEY, JSON.stringify(chosenCharts));
      renderPeriod();
    });
    label.append(box, document.createTextNode(" " + chart.title));
    plotPicker.append(label);
  });

  function dayCount(first, last) {
    // Rounds away the hour a daylight-saving change adds to or removes from a day.
    return Math.round((last - first) / 86400000) + 1;
  }

  function choose(day) {
    if (!pending) {
      start = day;
      end = day;
      pending = true;
    } else {
      if (day < start) {
        start = day;
      } else {
        end = day;
      }
      pending = false;
    }
    render();
  }

  // The day a step of one lands on, or null where there is none. With a card loaded
  // the steps move between the days that hold a recording, since a day with none has
  // nothing to show; with no card they move by one calendar day.
  function stepTarget(step) {
    const from = step > 0 ? end : start;
    if (!daysWithData.size) {
      return new Date(from.getFullYear(), from.getMonth(), from.getDate() + step);
    }
    const here = dayKey(from);
    const keys = Array.from(daysWithData.keys()).sort();
    if (step < 0) {
      keys.reverse();
    }
    for (const key of keys) {
      if (step > 0 ? key > here : key < here) {
        const parts = key.split("-");
        return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
      }
    }
    return null;
  }

  function stepDay(step) {
    const target = stepTarget(step);
    if (!target) {
      return;
    }
    start = target;
    end = target;
    pending = false;
    shown = new Date(target.getFullYear(), target.getMonth(), 1);
    render();
  }

  function sessionsInSelection() {
    const found = [];
    for (let day = new Date(start); day <= end; day = nextDay(day)) {
      const held = daysWithData.get(dayKey(day));
      if (held) {
        for (const session of held) {
          found.push(session);
        }
      }
    }
    return found;
  }

  function line(className, words) {
    const p = document.createElement("p");
    if (className) {
      p.className = className;
    }
    p.textContent = words;
    return p;
  }

  // What the plots card holds before a folder is read: the manual first, then the
  // one thing to do next.
  function landingInto(where) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "landing-button";
    button.dataset.dialog = "manual-dialog";
    button.textContent = "Open the Manual";
    where.replaceChildren(
      line("landing-lead", "Nothing is loaded yet."),
      line("landing-words", "Start with the manual. It says what PAPvault reads from a"
        + " card and what it never touches, what every figure on this page means, and"
        + " how a day is counted. Your data is read here in your browser and is never"
        + " sent anywhere."),
      button,
      line("landing-words", "Then choose Open Folder in the top bar and pick the folder"
        + " your machine's card holds.")
    );
  }

  function hoursWords(ms) {
    const minutes = Math.round(ms / 60000);
    const hours = Math.floor(minutes / 60);
    const rest = minutes % 60;
    if (hours === 0) {
      return rest === 1 ? "1 minute" : rest + " minutes";
    }
    const hourWords = hours === 1 ? "1 hour" : hours + " hours";
    if (rest === 0) {
      return hourWords;
    }
    return hourWords + " " + (rest === 1 ? "1 minute" : rest + " minutes");
  }

  function colorOf(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  // The day's own axis and its cursor readout, to the second: zoomed in far enough,
  // every tick otherwise names the same minute.
  function formatClock(seconds) {
    return clockTime(new Date(seconds * 1000), true);
  }

  function formatDay(seconds) {
    const when = new Date(seconds * 1000);
    return MONTHS[when.getMonth()].slice(0, 3) + " " + when.getDate();
  }

  function quantile(sorted, fraction) {
    if (!sorted.length) {
      return null;
    }
    const at = (sorted.length - 1) * fraction;
    const low = Math.floor(at);
    const high = Math.ceil(at);
    return low === high ? sorted[low] : sorted[low] + (sorted[high] - sorted[low]) * (at - low);
  }

  function spreadOf(values) {
    if (!values.length) {
      return { min: null, mean: null, median: null, p95: null, max: null };
    }
    let total = 0;
    for (const value of values) {
      total += value;
    }
    values.sort(function (a, b) {
      return a - b;
    });
    return {
      min: values[0],
      mean: total / values.length,
      median: quantile(values, 0.5),
      p95: quantile(values, 0.95),
      max: values[values.length - 1],
    };
  }

  // What a CPAP day's figures are, from the sessions that began in it. Hours come
  // from session start and end times, never from counting samples. "Pressure" is
  // the therapy pressure the machine delivered, which on a ResMed card is Press.2s.
  function figuresFor(day, held) {
    let used = 0;
    let leaking = 0;
    const counts = new Map();
    const pressures = [];
    const leaks = [];
    for (const one of held) {
      used += one.session.end - one.session.start;
      for (const event of one.loaded.events) {
        counts.set(event.text, (counts.get(event.text) || 0) + 1);
      }
      const pressure = one.loaded.signals.pressure;
      if (pressure) {
        for (let i = 0; i < pressure.y.length; i++) {
          pressures.push(pressure.y[i]);
        }
      }
      const leak = one.loaded.signals.leak;
      if (leak) {
        for (let i = 0; i < leak.y.length; i++) {
          leaks.push(leak.y[i]);
          // Each sample above zero stands for the one step of recording it covers,
          // which is the span from the sample before a leak to the sample after it,
          // less one step. A run is never carried across the gap between sessions.
          if (leak.y[i] > 0) {
            leaking += leak.interval;
          }
        }
      }
    }
    const hours = used / 3600000;
    const perHour = {};
    for (const [text, count] of counts) {
      perHour[text] = hours > 0 ? count / hours : null;
    }
    return {
      key: dayKey(day),
      seconds: cpapDayStart(day).getTime() / 1000,
      hours: hours,
      sessions: held.length,
      eventsPerHour: perHour,
      eventCounts: counts,
      pressure: spreadOf(pressures),
      leak: spreadOf(leaks),
      leakingSeconds: leaking,
    };
  }

  function unitOf(held, key) {
    for (const one of held) {
      const signal = one.loaded.signals[key];
      if (signal && signal.unit) {
        return signal.unit;
      }
    }
    return "";
  }

  function showLegend(labels, counts) {
    if (!labels.length) {
      legendDock.hidden = true;
      legendPanel.hidden = true;
      legendToggle.setAttribute("aria-expanded", "false");
      return;
    }
    // The same map the plots use, so a name's color here is its color there.
    const colors = PAPvaultPlots.eventColorsFor(labels, colorOf);
    const rows = labels.map(function (text) {
      const row = document.createElement("li");
      const swatch = document.createElement("span");
      swatch.className = "legend-swatch";
      swatch.style.background = colors.get(text);
      const name = document.createElement("span");
      name.textContent = text;
      const many = document.createElement("span");
      many.className = "legend-count";
      many.textContent = counts.get(text) === undefined ? "" : String(counts.get(text));
      row.append(swatch, name, many);
      return row;
    });
    legendList.replaceChildren(...rows);
    legendDock.hidden = false;
  }

  legendToggle.addEventListener("click", function () {
    const open = legendPanel.hidden;
    legendPanel.hidden = !open;
    legendToggle.setAttribute("aria-expanded", String(open));
  });

  function clearViews() {
    if (dayView) {
      dayView.destroy();
      dayView = null;
    }
    if (summaryView) {
      summaryView.destroy();
      summaryView = null;
    }
    if (eventView) {
      eventView.destroy();
      eventView = null;
    }
    summaryPlots.replaceChildren();
    summaryPlots.hidden = true;
    eventPlot.replaceChildren();
    eventPlot.hidden = true;
    legendDock.hidden = true;
    legendPanel.hidden = true;
    legendToggle.setAttribute("aria-expanded", "false");
  }

  // Loads every session of the chosen period and draws it. A period longer than a
  // day needs no waveform, so no waveform file is opened for one.
  async function renderPeriod() {
    clearViews();
    plotPicker.hidden = true;

    if (!card) {
      summaryBody.replaceChildren(line("empty", "No data loaded."));
      landingInto(plotsBody);
      return;
    }
    const sessions = sessionsInSelection();
    if (!sessions.length) {
      summaryBody.replaceChildren(line("empty", "This folder holds no recording in this period."));
      plotsBody.replaceChildren(line("empty", "This folder holds no recording in this period."));
      return;
    }

    const oneDay = end.getTime() === start.getTime();
    const keys = oneDay ? PAPvaultPlots.signalsFor(chosenCharts) : [];
    const needed = keys.indexOf("pressure") === -1 ? keys.concat(["pressure", "leak"]) : keys.concat(["leak"]);
    const wanted = needed.filter(function (key, at) {
      return needed.indexOf(key) === at;
    });

    const mine = ++drawToken;
    summaryBody.replaceChildren(line(null, "Reading " + (sessions.length === 1
      ? "1 session" : sessions.length + " sessions") + "..."));
    plotsBody.replaceChildren(line("empty", "Reading..."));

    const held = [];
    for (const session of sessions) {
      const loaded = await PAPvaultCard.load(session, wanted);
      if (mine !== drawToken) {
        return;
      }
      held.push({ session: session, loaded: loaded });
    }

    const byDay = new Map();
    for (const one of held) {
      if (!byDay.has(one.session.dayKey)) {
        byDay.set(one.session.dayKey, []);
      }
      byDay.get(one.session.dayKey).push(one);
    }
    const figures = [];
    for (let day = new Date(start); day <= end; day = nextDay(day)) {
      const ours = byDay.get(dayKey(day));
      if (ours) {
        figures.push(figuresFor(day, ours));
      }
    }

    const events = [];
    for (const one of held) {
      for (const event of one.loaded.events) {
        events.push(event);
      }
    }
    events.sort(function (a, b) {
      return a.seconds - b.seconds;
    });

    // A name the machine wrote on any day of the period counts zero on the days it
    // wrote none, rather than leaving a gap that reads as nothing being known.
    const named = [];
    for (const event of events) {
      if (named.indexOf(event.text) === -1) {
        named.push(event.text);
      }
    }
    for (const day of figures) {
      for (const text of named) {
        if (day.eventsPerHour[text] === undefined) {
          day.eventsPerHour[text] = 0;
        }
        if (!day.eventCounts.has(text)) {
          day.eventCounts.set(text, 0);
        }
      }
    }

    // How many of each name the period holds, and the names in that order, most
    // written first. Everything that shows an event reads its order from here: the
    // summary's bars, the legend, the per-hour chart, and which color a name gets.
    const counts = new Map();
    for (const event of events) {
      counts.set(event.text, (counts.get(event.text) || 0) + 1);
    }
    const labels = named.slice().sort(function (a, b) {
      // A tie keeps the order the device wrote the names in.
      return counts.get(b) - counts.get(a) || named.indexOf(a) - named.indexOf(b);
    });

    drawSummary(held, figures, labels, counts, oneDay, figuresFor(start, held));
    if (oneDay) {
      drawDay(held, events, labels);
    } else {
      plotsBody.replaceChildren(
        line("empty", "The detailed plots show one day at a time. This period covers "
          + dayCount(start, end) + " days, so the summary above is what is shown."),
        line("plot-note", "Click a single day in the calendar to see that night in detail.")
      );
    }
  }

  function clockSpan(ms) {
    const minutes = Math.round(ms / 60000);
    return pad(Math.floor(minutes / 60)) + "h " + pad(minutes % 60) + "m";
  }

  function boxOf(tint, head, unit) {
    const box = document.createElement("div");
    box.className = "figure-box";
    box.dataset.tint = tint;
    const title = document.createElement("p");
    title.className = "figure-head";
    title.textContent = head;
    if (unit) {
      const said = document.createElement("span");
      said.className = "figure-unit";
      said.textContent = unit;
      title.append(" ", said);
    }
    box.append(title);
    return box;
  }

  function pairsInto(box, rows) {
    const list = document.createElement("dl");
    list.className = "figure-rows";
    for (const row of rows) {
      const pair = document.createElement("div");
      const name = document.createElement("dt");
      name.textContent = row[0];
      const value = document.createElement("dd");
      value.textContent = row[1];
      pair.append(name, value);
      list.append(pair);
    }
    box.append(list);
    return box;
  }

  // "given" carries the rows that are not one of the spread's own figures, already
  // written out, since a duration is not a reading of the signal.
  function spreadBox(tint, head, spread, unit, wanted, given) {
    const box = boxOf(tint, head, unit);
    if (spread.median === null) {
      box.append(line("empty", "Not recorded."));
      return box;
    }
    return pairsInto(box, wanted.map(function (row) {
      const held = given ? given[row[1]] : undefined;
      return [row[0], held === undefined ? spread[row[1]].toFixed(1) : held];
    }));
  }

  // Which figures each box carries, as Z set them.
  const PRESSURE_ROWS = [["Max", "max"], ["Min", "min"], ["Mean", "mean"],
    ["Median", "median"], ["95th", "p95"]];
  const LEAK_ROWS = [["Max", "max"], ["Mean", "mean"], ["Median", "median"],
    ["95th", "p95"]];
  // How long the leak ran above zero: the day's own over a single day, and the
  // average over the days with a recording in a longer period.
  const LEAK_DURATION = ["Dur.", "total"];
  const LEAK_DURATION_DAILY = ["Dur./day", "total"];

  function sessionBox(held, used, days, day) {
    const box = boxOf("session", days > 1 ? "Sessions" : "Session");
    const grid = document.createElement("div");
    grid.className = "figure-pair";
    const counted = document.createElement("p");
    counted.className = "figure-big";
    counted.textContent = held.length + (held.length === 1 ? " session" : " sessions");
    const spent = document.createElement("p");
    spent.className = "figure-big";
    spent.textContent = clockSpan(used);
    grid.append(counted, spent);
    box.append(grid);
    return pairsInto(box, days > 1
      ? [["Across", days + " days"],
         ["Per day", clockSpan(used / days)],
         ["From", dayKey(held[0].session.start)],
         ["To", dayKey(held[held.length - 1].session.end)]]
      : [["Day", dayKey(day)],
         ["From", clockTime(held[0].session.start)],
         ["To", clockTime(held[held.length - 1].session.end)]]);
  }

  // One day gives its figures in words and its events as a bar each. A longer
  // period gives a chart per figure, with a point or a bar for every day in it.
  function drawSummary(held, figures, labels, counts, oneDay, whole) {
    let used = 0;
    for (const one of held) {
      used += one.session.end - one.session.start;
    }
    const boxes = document.createElement("div");
    boxes.className = "figures";
    boxes.append(
      sessionBox(held, used, figures.length, start),
      spreadBox("pressure", "Pressure", whole.pressure, unitOf(held, "pressure"), PRESSURE_ROWS),
      spreadBox("leak", "Leak", whole.leak, unitOf(held, "leak"),
        LEAK_ROWS.concat([figures.length > 1 ? LEAK_DURATION_DAILY : LEAK_DURATION]),
        { total: Math.round(whole.leakingSeconds / 60 / Math.max(figures.length, 1)) + "m" })
    );
    summaryBody.replaceChildren(boxes);

    // Shown before it is drawn into: a hidden element has no width to measure.
    eventPlot.hidden = false;
    eventView = PAPvaultPlots.showDayEvents(eventPlot, {
      eventLabels: labels,
      counts: counts,
      colorOf: colorOf,
    });
    if (!eventView) {
      eventPlot.hidden = true;
      summaryBody.append(line("empty", oneDay
        ? "The device recorded no events on this day."
        : "The device recorded no events in this period."));
    }
    showLegend(labels, counts);

    if (oneDay) {
      return;
    }
    summaryPlots.hidden = false;
    summaryView = PAPvaultPlots.showSummary(summaryPlots, {
      days: figures,
      eventLabels: labels,
      units: { pressure: unitOf(held, "pressure"), leak: unitOf(held, "leak") },
      from: figures[0].seconds,
      to: figures[figures.length - 1].seconds,
      formatDate: formatDay,
      colorOf: colorOf,
    });
  }

  function drawDay(held, events, labels) {
    const from = held[0].session.start.getTime() / 1000;
    const to = held[held.length - 1].session.end.getTime() / 1000;
    plotsBody.replaceChildren();
    plotPicker.hidden = false;
    if (!chosenCharts.length) {
      plotsBody.replaceChildren(line("empty", "No plots are chosen. Pick one above."));
      return;
    }
    dayView = PAPvaultPlots.show(plotsBody, {
      sessions: held.map(function (one) {
        return one.loaded;
      }),
      events: events,
      eventLabels: labels,
      from: from,
      to: to,
      charts: chosenCharts,
      formatTime: formatClock,
      colorOf: colorOf,
    });
    if (dayView.missing.length) {
      plotsBody.append(line("empty", "Not on this card: " + dayView.missing.join(", ") + "."));
    }
    plotsBody.append(line("plot-note", "Drag sideways across a plot to zoom into it,"
      + " or hold Ctrl and use the wheel, or pinch on a trackpad. Double-click to go"
      + " back to the whole day. The cursor line follows the pointer across every"
      + " plot at once."));
  }

  function render() {
    const focused = grid.contains(document.activeElement) ? document.activeElement.getAttribute("aria-label") : null;
    monthLabel.textContent = MONTHS[shown.getMonth()] + " " + shown.getFullYear();

    const cells = WEEKDAYS.map(function (name) {
      const cell = document.createElement("span");
      cell.className = "calendar-weekday";
      cell.textContent = name;
      return cell;
    });
    for (let i = 0; i < shown.getDay(); i++) {
      cells.push(document.createElement("span"));
    }

    const daysInMonth = new Date(shown.getFullYear(), shown.getMonth() + 1, 0).getDate();
    for (let date = 1; date <= daysInMonth; date++) {
      const day = new Date(shown.getFullYear(), shown.getMonth(), date);
      const t = day.getTime();
      const button = document.createElement("button");
      button.type = "button";
      button.className = "calendar-day";
      button.textContent = String(date);
      button.setAttribute("aria-label", dayKey(day));
      if (t === currentDay.getTime()) {
        button.classList.add("current");
      }
      if (daysWithData.has(dayKey(day))) {
        button.classList.add("has-data");
      }
      const inSelection = t >= start.getTime() && t <= end.getTime();
      if (inSelection) {
        button.classList.add(t === start.getTime() || t === end.getTime() ? "selected" : "in-range");
      }
      button.setAttribute("aria-pressed", String(inSelection));
      button.addEventListener("click", function () {
        choose(day);
      });
      cells.push(button);
    }

    grid.replaceChildren(...cells);
    dayPrev.disabled = stepTarget(-1) === null;
    dayNext.disabled = stepTarget(1) === null;
    if (focused !== null) {
      const again = Array.prototype.find.call(grid.children, function (cell) {
        return cell.getAttribute("aria-label") === focused;
      });
      if (again) {
        again.focus();
      }
    }
    renderPeriod();
  }

  dayPrev.addEventListener("click", function () {
    stepDay(-1);
  });
  dayNext.addEventListener("click", function () {
    stepDay(1);
  });

  document.getElementById("calendar-prev").addEventListener("click", function () {
    shown = new Date(shown.getFullYear(), shown.getMonth() - 1, 1);
    render();
  });
  document.getElementById("calendar-next").addEventListener("click", function () {
    shown = new Date(shown.getFullYear(), shown.getMonth() + 1, 1);
    render();
  });

  const monthDialog = document.getElementById("month-dialog");
  const monthGrid = document.getElementById("month-grid");
  const yearLabel = document.getElementById("month-dialog-year");
  let pickerYear = shown.getFullYear();

  function renderMonths() {
    yearLabel.textContent = String(pickerYear);
    const buttons = MONTHS.map(function (name, month) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = name.slice(0, 3);
      button.setAttribute("aria-label", name + " " + pickerYear);
      if (pickerYear === shown.getFullYear() && month === shown.getMonth()) {
        button.classList.add("selected");
      }
      button.addEventListener("click", function () {
        shown = new Date(pickerYear, month, 1);
        monthDialog.close();
        render();
      });
      return button;
    });
    monthGrid.replaceChildren(...buttons);
  }

  monthLabel.addEventListener("click", function () {
    pickerYear = shown.getFullYear();
    renderMonths();
    monthDialog.showModal();
  });
  document.getElementById("year-prev").addEventListener("click", function () {
    pickerYear -= 1;
    renderMonths();
  });
  document.getElementById("year-next").addEventListener("click", function () {
    pickerYear += 1;
    renderMonths();
  });

  // Delegated, so a button the page builds later opens its dialog too.
  document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-dialog]");
    if (button) {
      document.getElementById(button.dataset.dialog).showModal();
    }
  });
  document.querySelectorAll("dialog.modal").forEach(function (dialog) {
    dialog.querySelector(".modal-close").addEventListener("click", function () {
      dialog.close();
    });
    dialog.addEventListener("click", function (event) {
      // Only a click on the backdrop has the dialog itself as its target; .modal-body covers the rest.
      if (event.target === dialog) {
        dialog.close();
      }
    });
  });

  document.querySelectorAll('input[name="time-format"]').forEach(function (input) {
    input.checked = input.value === timeFormat;
    input.addEventListener("change", function () {
      timeFormat = input.value;
      writeSetting(TIME_FORMAT_KEY, timeFormat);
      renderPeriod();
    });
  });

  const manualNav = document.getElementById("manual-nav");
  const manualGroups = Array.prototype.slice.call(manualNav.querySelectorAll(".manual-group"));
  const manualButtons = Array.prototype.slice.call(manualNav.querySelectorAll("button[data-section]"));
  const manualPanes = Array.prototype.slice.call(document.querySelectorAll(".manual-pane"));

  // One group is open at a time; passing nothing closes them all.
  function openManualGroup(wanted) {
    manualGroups.forEach(function (group) {
      const open = group === wanted;
      group.querySelector(".manual-group-items").hidden = !open;
      group.querySelector(".manual-group-button").setAttribute("aria-expanded", String(open));
    });
  }

  function showManualSection(id) {
    manualPanes.forEach(function (pane) {
      pane.hidden = pane.id !== id;
    });
    manualButtons.forEach(function (button) {
      if (button.dataset.section === id) {
        button.setAttribute("aria-current", "true");
        openManualGroup(button.closest(".manual-group"));
      } else {
        button.removeAttribute("aria-current");
      }
    });
  }

  manualButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      showManualSection(button.dataset.section);
    });
  });

  manualGroups.forEach(function (group) {
    group.querySelector(".manual-group-button").addEventListener("click", function () {
      const items = group.querySelector(".manual-group-items");
      openManualGroup(items.hidden ? group : null);
    });
  });

  showManualSection(manualPanes[0].id);

  // A chosen folder is held here as {file, path} pairs. No file is opened.
  let chosenFiles = [];
  const folderInput = document.getElementById("folder-input");
  const folderPick = document.getElementById("folder-pick");
  const folderDrop = document.getElementById("folder-drop");
  const folderStatus = document.getElementById("folder-status");
  const folderDialog = document.getElementById("folder-dialog");

  function folderNameOf(items) {
    for (const item of items) {
      const top = item.path.split("/")[0];
      if (top && top !== item.file.name) {
        return top;
      }
    }
    return "";
  }

  function reportCard(name, fileCount) {
    const said = [];
    const files = fileCount === 1 ? "1 file" : fileCount + " files";
    const nights = card.fileCount === 1 ? "1 of them" : card.fileCount + " of them";
    said.push(line(null, (name || "Folder") + " opened: " + files + ", " + nights
      + " holding a night's recording. Nothing else was opened."));

    if (!card.sessions.length) {
      said.push(line("empty", "No recording was found. PAPvault looks for a DATALOG folder"
        + " holding one folder per day."));
    } else {
      const sessions = card.sessions.length === 1 ? "1 session" : card.sessions.length + " sessions";
      const days = daysWithData.size === 1 ? "1 day" : daysWithData.size + " days";
      said.push(line(null, sessions + " on " + days + ", from "
        + dateTime(card.sessions[0].start) + " to "
        + dateTime(card.sessions[card.sessions.length - 1].end) + "."));
    }

    if (card.asideCount) {
      const sets = card.asideCount === 1 ? "1 set of files" : card.asideCount + " sets of files";
      const held = card.asideFiles === 1 ? "1 file" : card.asideFiles + " files";
      said.push(line("empty", sets + " (" + held + ") hold no flow and were stamped"
        + " away from any night, which is what a machine writes when it is unplugged and"
        + " plugged back in. They are not counted as nights, and nothing in them sets a"
        + " night's start or end."));
    }

    for (const bad of card.refused) {
      said.push(line("empty", "Not read: " + bad.path + " -- " + bad.why));
    }
    folderStatus.replaceChildren(...said);
  }

  async function readChosenCard(items) {
    const name = folderNameOf(items);
    folderStatus.replaceChildren(line(null, "Reading..."));
    try {
      card = await PAPvaultCard.read(items, function (done, total) {
        folderStatus.replaceChildren(line(null, "Reading the recordings: " + done + " of " + total + "."));
      });
    } catch (error) {
      card = null;
      daysWithData = new Map();
      folderStatus.replaceChildren(line("empty", "That folder could not be read."));
      render();
      return;
    }
    daysWithData = PAPvaultCard.byDay(card.sessions);
    reportCard(name, items.length);
    // Reading is done, so the dialog gets out of the way. It stays open when there
    // was nothing to read, or when a file was refused, since that is what it is
    // reporting and closing it would hide the report.
    if (card.sessions.length && !card.refused.length) {
      folderDialog.close();
    }
    // The calendar opens on the last day the card holds, since that is the night
    // a reader has just come from.
    if (card.sessions.length) {
      const last = card.sessions[card.sessions.length - 1].day;
      shown = new Date(last.getFullYear(), last.getMonth(), 1);
      start = last;
      end = last;
      pending = false;
    }
    render();
  }

  function showChoice(items) {
    chosenFiles = items;
    if (!items.length) {
      folderStatus.replaceChildren(line("empty", "That folder holds no files."));
      return;
    }
    readChosenCard(items);
  }

  folderPick.addEventListener("click", function () {
    folderInput.click();
  });

  folderInput.addEventListener("change", function () {
    const items = Array.prototype.map.call(folderInput.files, function (file) {
      return { file: file, path: file.webkitRelativePath || file.name };
    });
    showChoice(items);
  });

  function readEntries(reader) {
    return new Promise(function (resolve, reject) {
      reader.readEntries(resolve, reject);
    });
  }

  // A directory reader hands back one batch at a time, and an empty batch ends the listing.
  async function collect(entry, prefix) {
    if (entry.isFile) {
      const file = await new Promise(function (resolve, reject) {
        entry.file(resolve, reject);
      });
      return [{ file: file, path: prefix + entry.name }];
    }
    const reader = entry.createReader();
    let items = [];
    let batch = await readEntries(reader);
    while (batch.length) {
      for (const child of batch) {
        items = items.concat(await collect(child, prefix + entry.name + "/"));
      }
      batch = await readEntries(reader);
    }
    return items;
  }

  folderDrop.addEventListener("dragover", function (event) {
    event.preventDefault();
    folderDrop.classList.add("over");
  });

  folderDrop.addEventListener("dragleave", function () {
    folderDrop.classList.remove("over");
  });

  folderDrop.addEventListener("drop", function (event) {
    event.preventDefault();
    folderDrop.classList.remove("over");
    const transfer = event.dataTransfer;
    const entries = [];
    // The entries have to be taken while this event is being handled.
    for (const item of transfer ? transfer.items : []) {
      const entry = item.webkitGetAsEntry ? item.webkitGetAsEntry() : null;
      if (entry) {
        entries.push(entry);
      }
    }
    if (!entries.length) {
      folderStatus.replaceChildren(line("empty", "That drop held no folder this browser can open."));
      return;
    }
    folderStatus.replaceChildren(line(null, "Listing the folder..."));
    Promise.all(entries.map(function (entry) {
      return collect(entry, "");
    })).then(function (lists) {
      showChoice([].concat.apply([], lists));
    }).catch(function () {
      folderStatus.replaceChildren(line("empty", "That folder could not be listed."));
    });
  });

  const calendar = document.getElementById("calendar");
  const calendarCard = document.getElementById("calendar-card");
  const cardSlot = document.getElementById("calendar-card-slot");
  const dialogSlot = document.getElementById("calendar-dialog-slot");
  const calendarDialog = document.getElementById("calendar-dialog");
  const calendarButton = document.getElementById("open-calendar");
  const narrow = window.matchMedia("(max-width: 649.98px)");

  function placeCalendar() {
    root.classList.toggle("narrow", narrow.matches);
    calendarButton.hidden = !narrow.matches;
    calendarCard.hidden = narrow.matches;
    if (narrow.matches) {
      dialogSlot.append(calendar);
    } else {
      if (calendarDialog.open) {
        calendarDialog.close();
      }
      cardSlot.append(calendar);
    }
  }

  narrow.addEventListener("change", placeCalendar);

  // The height the sticky cards start below. It is measured rather than written
  // down, since the bar wraps to two rows on a narrow screen.
  function measureTopbar() {
    root.style.setProperty("--topbar-height",
      document.querySelector(".topbar").getBoundingClientRect().height + "px");
  }

  let resizing = 0;
  window.addEventListener("resize", function () {
    window.clearTimeout(resizing);
    resizing = window.setTimeout(function () {
      measureTopbar();
      if (dayView) {
        dayView.resize();
      }
      if (summaryView) {
        summaryView.resize();
      }
    }, 150);
  });

  placeCalendar();
  render();
  app.hidden = false;
  measureTopbar();
})();
