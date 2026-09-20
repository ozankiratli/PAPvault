"use strict";

// Draws one CPAP day as a stack of charts on a single time axis: one cursor line
// across all of them, one zoom shared between them, and the device's own events
// shaded on every chart. Nothing here reads a file or knows what a day is.
var PAPvaultPlots = (function () {
  const CURSOR_SYNC = uPlot.sync("papvault-day");
  const SUMMARY_SYNC = uPlot.sync("papvault-summary");

  // Every chart in a stack gets the same left axis width, so their plotting areas
  // line up and a cursor at one x means the same place in all of them. The width
  // grows to fit the event names a device wrote, up to a cap.
  const AXIS_WIDTH = 64;
  const AXIS_WIDTH_CAP = 170;
  const LABEL_FONT = "11px system-ui, -apple-system, Segoe UI, Roboto, sans-serif";
  const CHART_HEIGHT = 150;
  // Set here, because uPlot reserves room on the right only for a chart whose time
  // axis is shown, which would leave the bottom chart narrower than the rest. A day
  // stack starts from this and widens the right side to fit its own time labels.
  const PLOT_PADDING = [10, 18, 0, 0];
  const EVENT_ROW_HEIGHT = 22;
  const EVENT_OPACITY = 0.22;
  // A band is filled faintly across the plot and edged with a solid line at the
  // moment the event began, so a short event is still visible at a whole night's
  // width, where its duration is well under one pixel.
  const EVENT_EDGE = 2;
  const EVENT_LEAST = 3;
  // How far a count starts from the end of its bar.
  const COUNT_GAP = 6;
  // How much clear room to leave between one time label and the next, and how many
  // moments across the range are measured to find the widest label.
  const AXIS_LABEL_GAP = 18;
  const SPACE_SAMPLES = 12;

  // How wide the left axis has to be for these names, and how far a name may run
  // before it is cut short to fit.
  function axisWidthFor(labels, cap) {
    if (!labels.length) {
      return { width: AXIS_WIDTH, fit: function (text) { return text; } };
    }
    const ctx = document.createElement("canvas").getContext("2d");
    ctx.font = LABEL_FONT;
    let widest = 0;
    for (const text of labels) {
      widest = Math.max(widest, ctx.measureText(text).width);
    }
    const ceiling = Math.max(AXIS_WIDTH, Math.min(AXIS_WIDTH_CAP, cap || AXIS_WIDTH_CAP));
    const width = Math.max(AXIS_WIDTH, Math.min(ceiling, Math.ceil(widest) + 16));
    const room = width - 16;
    return {
      width: width,
      fit: function (text) {
        if (ctx.measureText(text).width <= room) {
          return text;
        }
        let kept = text;
        while (kept.length > 1 && ctx.measureText(kept + "...").width > room) {
          kept = kept.slice(0, -1);
        }
        return kept + "...";
      },
    };
  }

  // One entry per chart, in the order they are stacked. A chart's series share its
  // y axis. "off" starts the chart unchecked.
  const CHARTS = [
    { key: "flow", title: "Flow", series: [
      { signal: "flow", name: "Flow", color: "--plot-flow" }] },
    { key: "pressure", title: "Pressure", series: [
      { signal: "maskPressure", name: "Mask Pressure", color: "--plot-mask-pressure" },
      { signal: "pressure", name: "Pressure", color: "--plot-pressure" },
      { signal: "eprPressure", name: "EPR Pressure", color: "--plot-epr-pressure" }] },
    { key: "leak", title: "Leak Rate", series: [
      { signal: "leak", name: "Leak", color: "--plot-leak" }] },
    { key: "respRate", title: "Respiratory Rate", series: [
      { signal: "respRate", name: "Respiratory Rate", color: "--plot-resp-rate" }] },
    { key: "flowLim", title: "Flow Limitation", series: [
      { signal: "flowLim", name: "Flow Limitation", color: "--plot-flow-lim" }] },
    { key: "snore", title: "Snore", series: [
      { signal: "snore", name: "Snore", color: "--plot-snore" }] },
    { key: "tidVol", title: "Tidal Volume", series: [
      { signal: "tidVol", name: "Tidal Volume", color: "--plot-tid-vol" }] },
    { key: "minVent", title: "Minute Ventilation", series: [
      { signal: "minVent", name: "Minute Ventilation", color: "--plot-min-vent" }] },
    // Disabled until there is a card to test it against: ResMed records oximetry only
    // on the AirSense 10, and a compatible oximeter is hard to come by (Z, 2026-09-20).
    // Nothing offers it, so no oximetry file is opened.
    { key: "oximetry", title: "Oximetry", off: true, disabled: true, series: [
      { signal: "pulse", name: "Pulse", color: "--plot-pulse" },
      { signal: "spo2", name: "SpO2", color: "--plot-spo2" }] },
  ];

  const OFFERED = CHARTS.filter(function (chart) {
    return !chart.disabled;
  });

  function chartNamed(key) {
    return CHARTS.find(function (chart) {
      return chart.key === key;
    }) || null;
  }

  // The card signal keys the chosen charts need, so no file is opened for a chart
  // that is not shown.
  function signalsFor(keys) {
    const wanted = [];
    for (const key of keys) {
      const chart = chartNamed(key);
      if (!chart || chart.disabled) {
        continue;
      }
      for (const spec of chart.series) {
        if (wanted.indexOf(spec.signal) === -1) {
          wanted.push(spec.signal);
        }
      }
    }
    return wanted;
  }

  // One chart's columns across every session of the day, with a break between
  // sessions so the line does not run across the gap between them.
  function columnsFor(chart, sessions) {
    const x = [];
    const columns = chart.series.map(function () {
      return [];
    });
    let found = false;

    for (const loaded of sessions) {
      let longest = null;
      for (const spec of chart.series) {
        const held = loaded.signals[spec.signal];
        if (held && (!longest || held.x.length > longest.x.length)) {
          longest = held;
        }
      }
      if (!longest) {
        continue;
      }
      if (found) {
        x.push(longest.x[0] - longest.interval);
        for (const column of columns) {
          column.push(null);
        }
      }
      found = true;
      const length = longest.x.length;
      for (let i = 0; i < length; i++) {
        x.push(longest.x[i]);
      }
      chart.series.forEach(function (spec, index) {
        const held = loaded.signals[spec.signal];
        const column = columns[index];
        for (let i = 0; i < length; i++) {
          column.push(held && i < held.y.length ? held.y[i] : null);
        }
      });
    }
    return found ? { data: [x].concat(columns), reach: x.length } : null;
  }

  function unitOf(chart, sessions) {
    for (const loaded of sessions) {
      for (const spec of chart.series) {
        const held = loaded.signals[spec.signal];
        if (held && held.unit) {
          return held.unit;
        }
      }
    }
    return "";
  }

  // One color per event name, in the order the names are handed over, cycling when
  // a card carries more names than the palette holds. How many there are is a
  // property of the theme, since each theme carries the subset that reads against
  // its own surface.
  function eventColorsFor(labels, colorOf) {
    const count = Math.max(1, parseInt(colorOf("--plot-event-count"), 10) || 1);
    const colors = new Map();
    labels.forEach(function (text, index) {
      colors.set(text, colorOf("--plot-event-" + (index % count + 1)));
    });
    return colors;
  }

  // The device's own events, shaded across whatever chart is being drawn, each in
  // the color of its own name.
  function eventBands(events, colors, colorOf) {
    return {
      hooks: {
        draw: [function (u) {
          if (!events.length) {
            return;
          }
          const ctx = u.ctx;
          ctx.save();
          ctx.beginPath();
          ctx.rect(u.bbox.left, u.bbox.top, u.bbox.width, u.bbox.height);
          ctx.clip();
          const least = Math.ceil(EVENT_LEAST * devicePixelRatio);
          const edge = Math.ceil(EVENT_EDGE * devicePixelRatio);
          for (const event of events) {
            const from = u.valToPos(event.seconds, "x", true);
            const to = u.valToPos(event.seconds + Math.max(event.duration, 0), "x", true);
            ctx.fillStyle = colors.get(event.text) || colorOf("--plot-event");
            ctx.globalAlpha = EVENT_OPACITY;
            ctx.fillRect(from, u.bbox.top, Math.max(to - from, least), u.bbox.height);
            ctx.globalAlpha = 1;
            ctx.fillRect(from, u.bbox.top, edge, u.bbox.height);
          }
          ctx.restore();
        }],
      },
    };
  }

  // A y range always has some span in it. A signal that never changes -- which a
  // machine held at one pressure writes every night -- otherwise gives uPlot a zero
  // span, and it builds axis splits until the array will not grow any further.
  function paddedRange(fromZero) {
    return function (u, least, most) {
      if (!Number.isFinite(least) || !Number.isFinite(most)) {
        return [0, 1];
      }
      let low = fromZero ? 0 : least;
      let high = most;
      if (high - low < 1e-9) {
        const pad = Math.abs(high) > 1e-9 ? Math.abs(high) * 0.1 : 0.5;
        // A figure that is never negative does not gain a negative axis from padding.
        low = fromZero || least >= 0 ? Math.max(0, low - pad) : low - pad;
        high += pad;
      }
      return high - low < 1e-9 ? [low, low + 1] : [low, high];
    };
  }

  // The widest label the time axis will draw, measured across the range it covers.
  // It settles two things: how far apart uPlot may place the ticks, and how far the
  // last one, centered on the very end of the range, hangs past the plot.
  function widestTimeLabel(options) {
    const ctx = document.createElement("canvas").getContext("2d");
    ctx.font = LABEL_FONT;
    let widest = 0;
    for (let i = 0; i <= SPACE_SAMPLES; i++) {
      const at = options.from + (options.to - options.from) * (i / SPACE_SAMPLES);
      widest = Math.max(widest, ctx.measureText(options.formatTime(at)).width);
    }
    return Math.ceil(widest);
  }

  function axesFor(options, showTimes) {
    return [
      {
        show: showTimes,
        space: options.timeSpace,
        size: 34,
        stroke: options.colorOf("--muted"),
        grid: { stroke: options.colorOf("--border"), width: 1 },
        ticks: { stroke: options.colorOf("--border") },
        values: function (u, splits) {
          return splits.map(options.formatTime);
        },
      },
      {
        size: options.axisWidth,
        stroke: options.colorOf("--muted"),
        grid: { stroke: options.colorOf("--border"), width: 1 },
        ticks: { stroke: options.colorOf("--border") },
      },
    ];
  }

  // The strip above the charts: one row per distinct event text, keeping the words
  // the device wrote and never grouping two of them together.
  function buildStrip(parent, events, options, width) {
    const labels = [];
    for (const event of events) {
      if (labels.indexOf(event.text) === -1) {
        labels.push(event.text);
      }
    }
    if (!labels.length) {
      return null;
    }
    const row = new Map(labels.map(function (text, index) {
      return [text, index];
    }));

    const holder = document.createElement("div");
    holder.className = "plot";
    parent.append(holder);

    const config = {
      width: width,
      height: labels.length * EVENT_ROW_HEIGHT + 28,
      padding: options.padding,
      title: "Events, as the device named them",
      cursor: { sync: { key: CURSOR_SYNC.key, scales: ["x", null] }, y: false },
      legend: { show: false },
      scales: { x: { time: false }, y: { range: [0, labels.length] } },
      axes: [
        Object.assign(axesFor(options, false)[0], { show: false }),
        {
          size: options.axisWidth,
          stroke: options.colorOf("--muted"),
          grid: { show: false },
          ticks: { show: false },
          splits: function () {
            return labels.map(function (ignored, index) {
              return index + 0.5;
            });
          },
          values: function () {
            return labels.map(options.fitLabel);
          },
        },
      ],
      series: [{}, { show: false }],
      hooks: {
        draw: [function (u) {
          const ctx = u.ctx;
          ctx.save();
          ctx.beginPath();
          ctx.rect(u.bbox.left, u.bbox.top, u.bbox.width, u.bbox.height);
          ctx.clip();
          const least = Math.ceil(EVENT_LEAST * devicePixelRatio);
          const height = u.bbox.height / labels.length;
          for (const event of events) {
            const from = u.valToPos(event.seconds, "x", true);
            const to = u.valToPos(event.seconds + Math.max(event.duration, 0), "x", true);
            // Row 0 sits at the bottom, because the y axis that names the rows
            // counts upward from there.
            const top = u.bbox.top + (labels.length - 1 - row.get(event.text)) * height;
            ctx.fillStyle = options.eventColors.get(event.text) || options.colorOf("--plot-event");
            ctx.fillRect(from, top + height * 0.14, Math.max(to - from, least), height * 0.72);
          }
          ctx.restore();
        }],
      },
    };
    const chart = new uPlot(config, [[options.from, options.to], [null, null]], holder);
    chart.setScale("x", { min: options.from, max: options.to });
    return chart;
  }

  function buildChart(parent, chart, sessions, options, width, showTimes) {
    const columns = columnsFor(chart, sessions);
    if (!columns) {
      return null;
    }
    const unit = unitOf(chart, sessions);
    const holder = document.createElement("div");
    holder.className = "plot";
    parent.append(holder);

    const series = [
      { label: "Time", value: function (u, raw) {
        return raw === null ? "" : options.formatTime(raw);
      } },
    ];
    chart.series.forEach(function (spec, index) {
      series.push({
        label: spec.name,
        stroke: options.colorOf(spec.color),
        width: 1.25,
        points: { show: false },
        spanGaps: false,
        show: columns.data[index + 1].some(function (value) {
          return value !== null;
        }),
      });
    });

    const config = {
      width: width,
      height: CHART_HEIGHT + (showTimes ? 30 : 0),
      padding: options.padding,
      title: unit ? chart.title + " (" + unit + ")" : chart.title,
      cursor: {
        sync: { key: CURSOR_SYNC.key, scales: ["x", null] },
        drag: { x: true, y: false },
      },
      legend: { live: true },
      scales: { x: { time: false }, y: { range: paddedRange(false) } },
      axes: axesFor(options, showTimes),
      series: series,
      plugins: [eventBands(options.events, options.eventColors, options.colorOf)],
      hooks: {
        setScale: [function (u, key) {
          if (key === "x" && u.papvaultSpread) {
            u.papvaultSpread(u.scales.x.min, u.scales.x.max);
          }
        }],
      },
    };
    const built = new uPlot(config, columns.data, holder);
    built.setScale("x", { min: options.from, max: options.to });
    return built;
  }

  // One chart's zoom becomes every chart's zoom, and the wheel zooms about the pointer.
  function link(charts, options) {
    let spreading = false;
    const spread = function (min, max) {
      if (spreading) {
        return;
      }
      spreading = true;
      for (const chart of charts) {
        if (chart.scales.x.min !== min || chart.scales.x.max !== max) {
          chart.setScale("x", { min: min, max: max });
        }
      }
      spreading = false;
    };

    for (const chart of charts) {
      chart.papvaultSpread = spread;
      chart.over.addEventListener("wheel", function (event) {
        // Plain scrolling belongs to the page. Zooming is the wheel with Ctrl held,
        // which is also what a trackpad pinch sends.
        if (!event.ctrlKey) {
          return;
        }
        event.preventDefault();
        const box = chart.over.getBoundingClientRect();
        const at = chart.posToVal(event.clientX - box.left, "x");
        const min = chart.scales.x.min;
        const max = chart.scales.x.max;
        const factor = event.deltaY < 0 ? 0.8 : 1.25;
        let from = at - (at - min) * factor;
        let to = at + (max - at) * factor;
        if (to - from >= options.to - options.from) {
          from = options.from;
          to = options.to;
        } else {
          if (from < options.from) {
            to += options.from - from;
            from = options.from;
          }
          if (to > options.to) {
            from -= to - options.to;
            to = options.to;
          }
        }
        spread(from, to);
      }, { passive: false });

      chart.over.addEventListener("dblclick", function () {
        spread(options.from, options.to);
      });
    }
  }

  // Draws the stack into an empty container and hands back what it could not draw.
  function show(container, given) {
    const width = Math.max(container.clientWidth, 320);
    const names = [];
    for (const event of given.events) {
      if (names.indexOf(event.text) === -1) {
        names.push(event.text);
      }
    }
    const axis = axisWidthFor(names);
    const labelWidth = widestTimeLabel(given);
    const options = Object.assign({}, given, {
      axisWidth: axis.width,
      fitLabel: axis.fit,
      timeSpace: labelWidth + AXIS_LABEL_GAP,
      // One padding for every chart in the stack, so their plotting areas still line
      // up, wide enough on the right for half of the last label.
      padding: [PLOT_PADDING[0], Math.max(PLOT_PADDING[1], Math.ceil(labelWidth / 2) + 6),
        PLOT_PADDING[2], PLOT_PADDING[3]],
      // The caller's order, where it gave one, so a name is the same color here as
      // it is in the summary and the legend.
      eventColors: eventColorsFor(given.eventLabels || names, given.colorOf),
    });
    container.style.setProperty("--plot-axis", axis.width + "px");
    const built = [];
    const drawn = [];
    const strip = buildStrip(container, options.events, options, width);
    if (strip) {
      built.push(strip);
    }

    const chosen = OFFERED.filter(function (chart) {
      return options.charts.indexOf(chart.key) !== -1;
    });
    chosen.forEach(function (chart, index) {
      const made = buildChart(container, chart, options.sessions, options,
        width, index === chosen.length - 1);
      if (made) {
        built.push(made);
        drawn.push(chart.key);
      }
    });

    link(built, options);

    return {
      drawn: drawn,
      missing: chosen.filter(function (chart) {
        return drawn.indexOf(chart.key) === -1;
      }).map(function (chart) {
        return chart.title;
      }),
      resize: function () {
        const now = Math.max(container.clientWidth, 320);
        for (const chart of built) {
          chart.setSize({ width: now, height: chart.height });
        }
      },
      destroy: function () {
        for (const chart of built) {
          chart.destroy();
        }
        container.replaceChildren();
      },
    };
  }

  // One entry per summary chart, in the order they are stacked. Each reads its
  // columns off the per-day figures it is handed.
  const SUMMARIES = [
    {
      key: "usage", title: "Hours Used", bars: true,
      series: [{ name: "Hours used", color: "--plot-usage", of: function (day) { return day.hours; } }],
    },
    {
      key: "sessions", title: "Sessions", bars: true,
      series: [{ name: "Sessions", color: "--plot-sessions", of: function (day) { return day.sessions; } }],
    },
    { key: "events", title: "Events per Hour", perLabel: true, series: [] },
    {
      key: "pressure", title: "Pressure",
      series: [
        { name: "Median", color: "--plot-mask-pressure", of: function (day) { return day.pressure.median; } },
        { name: "95th percentile", color: "--plot-mask-pressure", dash: [6, 4], of: function (day) { return day.pressure.p95; } },
      ],
    },
    {
      key: "leak", title: "Leak",
      series: [
        { name: "Median", color: "--plot-leak", of: function (day) { return day.leak.median; } },
        { name: "95th percentile", color: "--plot-leak", dash: [6, 4], of: function (day) { return day.leak.p95; } },
      ],
    },
  ];

  function summaryAxes(options, showDates) {
    return [
      {
        show: showDates,
        size: 34,
        stroke: options.colorOf("--muted"),
        grid: { stroke: options.colorOf("--border"), width: 1 },
        ticks: { stroke: options.colorOf("--border") },
        splits: function () {
          const step = Math.max(1, Math.ceil(options.days.length / 8));
          return options.days.filter(function (ignored, index) {
            return index % step === 0;
          }).map(function (day) {
            return day.seconds;
          });
        },
        values: function (u, splits) {
          return splits.map(options.formatDate);
        },
      },
      {
        size: options.axisWidth,
        stroke: options.colorOf("--muted"),
        grid: { stroke: options.colorOf("--border"), width: 1 },
        ticks: { stroke: options.colorOf("--border") },
      },
    ];
  }

  function buildSummary(parent, summary, options, width, showDates) {
    const x = options.days.map(function (day) {
      return day.seconds;
    });
    const specs = summary.perLabel
      ? options.eventLabels.map(function (text, index) {
        return {
          name: text,
          color: options.eventColors.get(text) || options.colorOf("--plot-event"),
          literal: true,
          of: function (day) {
            return day.eventsPerHour[text] === undefined ? null : day.eventsPerHour[text];
          },
        };
      })
      : summary.series;
    if (!specs.length) {
      return null;
    }

    const columns = specs.map(function (spec) {
      return options.days.map(function (day) {
        const value = spec.of(day);
        return value === undefined || value === null || !Number.isFinite(value) ? null : value;
      });
    });
    const anything = columns.some(function (column) {
      return column.some(function (value) {
        return value !== null;
      });
    });
    if (!anything) {
      return null;
    }

    // The unit comes from the file the figure was computed from, never from here.
    const unit = (options.units || {})[summary.key] || "";
    const holder = document.createElement("div");
    holder.className = "plot";
    parent.append(holder);

    const series = [{ label: "Day", value: function (u, raw) {
      return raw === null ? "" : options.formatDate(raw);
    } }];
    specs.forEach(function (spec) {
      const drawn = {
        label: spec.name,
        stroke: spec.literal ? spec.color : options.colorOf(spec.color),
        width: 1.5,
        points: { show: options.days.length < 40 },
      };
      if (spec.dash) {
        drawn.dash = spec.dash;
      }
      if (summary.bars) {
        drawn.fill = drawn.stroke;
        drawn.paths = uPlot.paths.bars({ size: [0.6, 40] });
      }
      series.push(drawn);
    });

    const built = new uPlot({
      width: width,
      height: CHART_HEIGHT + (showDates ? 30 : 0),
      padding: PLOT_PADDING,
      title: summary.title + (unit ? " (" + unit + ")" : ""),
      cursor: { sync: { key: SUMMARY_SYNC.key, scales: ["x", null] }, drag: { x: true, y: false } },
      legend: { live: true },
      scales: { x: { time: false }, y: { range: paddedRange(summary.bars) } },
      axes: summaryAxes(options, showDates),
      series: series,
      hooks: {
        setScale: [function (u, key) {
          if (key === "x" && u.papvaultSpread) {
            u.papvaultSpread(u.scales.x.min, u.scales.x.max);
          }
        }],
      },
    }, [x].concat(columns), holder);
    built.setScale("x", { min: options.from, max: options.to });
    return built;
  }

  // One horizontal bar per event name, longest at the top: its length is how many
  // times the device wrote that name, and the number is printed at its end.
  function showDayEvents(container, given) {
    const names = given.eventLabels;
    if (!names.length) {
      return null;
    }
    // A lower floor than the stacks use, since this chart lives in the narrow
    // summary card rather than the wide plots card.
    const width = Math.max(container.clientWidth, 240);
    // In a narrow card the names may not take more than half of it, or there is
    // no room left for the bars they label.
    const axis = axisWidthFor(names, width * 0.5);
    const colors = eventColorsFor(names, given.colorOf);
    const counts = names.map(function (name) {
      return given.counts.get(name) || 0;
    });
    const most = Math.max.apply(null, counts);
    container.style.setProperty("--plot-axis", axis.width + "px");

    const holder = document.createElement("div");
    holder.className = "plot";
    container.append(holder);

    const chart = new uPlot({
      width: width,
      height: names.length * (EVENT_ROW_HEIGHT + 8) + 56,
      padding: PLOT_PADDING,
      title: "Events, as the device named them",
      legend: { show: false },
      cursor: { show: false },
      scales: {
        x: { time: false, range: [0, most * 1.2 + 0.5] },
        y: { range: [0, names.length] },
      },
      axes: [
        {
          size: 34,
          stroke: given.colorOf("--muted"),
          grid: { stroke: given.colorOf("--border"), width: 1 },
          ticks: { stroke: given.colorOf("--border") },
          values: function (u, splits) {
            return splits.map(function (value) {
              return Number.isInteger(value) ? String(value) : "";
            });
          },
        },
        {
          size: axis.width,
          stroke: given.colorOf("--muted"),
          grid: { show: false },
          ticks: { show: false },
          splits: function () {
            return names.map(function (ignored, index) {
              return index + 0.5;
            });
          },
          values: function () {
            // The splits count up from the bottom while the names run down from
            // the top, so the labels are handed back the other way round.
            return names.slice().reverse().map(axis.fit);
          },
        },
      ],
      series: [{}, { show: false }],
      hooks: {
        draw: [function (u) {
          const ctx = u.ctx;
          ctx.save();
          const row = u.bbox.height / names.length;
          const zero = u.valToPos(0, "x", true);
          ctx.font = Math.round(11 * devicePixelRatio) + "px " + LABEL_FONT.slice(5);
          // Both are set here because the context arrives from uPlot's own axis
          // drawing, which leaves the count centered on the end of its bar.
          ctx.textAlign = "left";
          ctx.textBaseline = "middle";
          names.forEach(function (name, index) {
            const top = u.bbox.top + index * row;
            const end = u.valToPos(counts[index], "x", true);
            ctx.fillStyle = colors.get(name);
            ctx.fillRect(zero, top + row * 0.18, Math.max(end - zero, 1), row * 0.64);
            ctx.fillStyle = given.colorOf("--text");
            ctx.fillText(String(counts[index]), end + COUNT_GAP * devicePixelRatio, top + row / 2);
          });
          ctx.restore();
        }],
      },
    }, [[0, most], [null, null]], holder);

    return {
      resize: function () {
        chart.setSize({ width: Math.max(container.clientWidth, 320), height: chart.height });
      },
      destroy: function () {
        chart.destroy();
        container.replaceChildren();
      },
    };
  }

  // The summary stack: one point or bar per CPAP day in the chosen period.
  function showSummary(container, given) {
    const width = Math.max(container.clientWidth, 320);
    // Half a day either side, so the first and last bar stand whole inside the
    // chart, and so one chosen day is a scale with a span rather than a point.
    const HALF_DAY = 43200;
    const from = given.from - HALF_DAY;
    const to = given.to + HALF_DAY;
    const options = Object.assign({}, given, {
      axisWidth: AXIS_WIDTH,
      from: from,
      to: to,
      eventColors: eventColorsFor(given.eventLabels || [], given.colorOf),
    });
    container.style.setProperty("--plot-axis", AXIS_WIDTH + "px");
    const built = [];
    const drawn = [];
    SUMMARIES.forEach(function (summary, index) {
      const made = buildSummary(container, summary, options, width, index === SUMMARIES.length - 1);
      if (made) {
        built.push(made);
        drawn.push(summary.key);
      }
    });
    link(built, options);
    return {
      drawn: drawn,
      resize: function () {
        const now = Math.max(container.clientWidth, 320);
        for (const chart of built) {
          chart.setSize({ width: now, height: chart.height });
        }
      },
      destroy: function () {
        for (const chart of built) {
          chart.destroy();
        }
        container.replaceChildren();
      },
    };
  }

  return {
    show: show,
    showSummary: showSummary,
    showDayEvents: showDayEvents,
    eventColorsFor: eventColorsFor,
    signalsFor: signalsFor,
    charts: OFFERED,
    summaries: SUMMARIES,
  };
})();
