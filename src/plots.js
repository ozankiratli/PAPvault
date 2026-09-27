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
  const AXIS_WIDTH = 48;
  const AXIS_WIDTH_CAP = 140;
  const LABEL_FONT = "11px system-ui, -apple-system, Segoe UI, Roboto, sans-serif";
  const CHART_HEIGHT = 150;
  // uPlot reserves room on the right only for a chart whose time axis is shown, so
  // every chart is given it here. A day stack starts from this and widens the right
  // side to fit its own time labels.
  //
  // The bottom is not zero: a y axis label is drawn centred on its tick, so the
  // lowest one -- a plain 0 on every signal that cannot go below it -- needs half its
  // own height below the plotting area or the canvas ends through the middle of it.
  // Only a chart showing the time axis has that room for free.
  const PLOT_PADDING = [10, 18, 9, 0];
  // A wheel gesture is one run of events; this long without one ends it.
  const GESTURE_GAP = 200;
  // How far a gesture travels to halve or double the window, in the units a wheel
  // reports. The zoom follows that distance and not the number of events it arrives
  // in. A trackpad reports a pinch in steps around seven times smaller than the ones
  // a wheel notch or a two-finger scroll sends, so the two have their own distances
  // and a gesture is read as a pinch when its first real step is under PINCH_STEP.
  const PINCH_TRAVEL = 32;
  const WHEEL_TRAVEL = 75;
  const PINCH_STEP = 3;
  // Below this a step carries no direction worth reading: a trackpad opens every
  // pinch with a few tenths of a unit before the fingers have moved.
  const ZOOM_TRACE = 0.5;
  const EVENT_ROW_HEIGHT = 22;
  // How far a finger may travel and still count as a tap rather than a drag, and how
  // long a second tap has to arrive in to be a double one.
  const TAP_SLOP = 8;
  const DOUBLE_TAP = 320;
  // The narrowest a chart is ever drawn. Below it the card scrolls sideways rather
  // than the plot growing narrower still.
  const PLOT_LEAST = 240;
  const EVENT_OPACITY = 0.22;
  // A band is filled faintly across the plot and edged with a solid line at the time
  // the file recorded, which is where the event ended, so a short event is still
  // visible at a whole night's width, where its duration is well under one pixel.
  // Everything is anchored at that line and grows to the left of it, which is where
  // the event was.
  const EVENT_EDGE = 2;
  const EVENT_LEAST = 3;
  // How far a count starts from the end of its bar.
  const COUNT_GAP = 6;
  // How much clear room to leave between one time label and the next, and how many
  // moments across the range are measured to find the widest label.
  const AXIS_LABEL_GAP = 18;
  const SPACE_SAMPLES = 12;

  // A drag with Ctrl held -- Command on an Apple keyboard -- slides the window rather
  // than zooming it. An Apple keyboard sends Ctrl with the right button, so a pan is
  // the left button and one of the two keys.
  function isPan(event) {
    return event.button === 0 && (event.ctrlKey || event.metaKey);
  }

  // uPlot's own filter on the one event a pan takes from it, so the drag that pans
  // never starts a zoom selection. Every other event it binds is left as it was.
  const PAN_BIND = {
    mousedown: function (u, target, handle, onlyTarget) {
      return function (event) {
        if (event.button !== 0 || (onlyTarget !== false && event.target !== target)) {
          return;
        }
        if (!isPan(event)) {
          handle(event);
        }
      };
    },
  };

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
    // Off and disabled, so nothing offers it and no oximetry file is opened.
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
  // At a step of one this is every sample. At a wider step each run of that many
  // samples becomes two points, the lowest and the highest in it, placed at the first
  // and last moment of the run, so a line drawn from them covers the same ground as
  // the samples it stands for and every step ends where the samples end. A run
  // holding no number at all becomes two nulls, which is the break between sessions.
  function columnsFor(chart, sessions, step) {
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
      if (!step || step < 2) {
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
        continue;
      }
      for (let at = 0; at < length; at += step) {
        x.push(longest.x[at], longest.x[Math.min(at + step, length) - 1]);
      }
      chart.series.forEach(function (spec, index) {
        const held = loaded.signals[spec.signal];
        const column = columns[index];
        const values = held ? held.y : null;
        for (let at = 0; at < length; at += step) {
          const end = Math.min(at + step, length);
          let low = null;
          let high = null;
          for (let i = at; values && i < end && i < values.length; i++) {
            const value = values[i];
            if (value === null || !Number.isFinite(value)) {
              continue;
            }
            if (low === null || value < low) {
              low = value;
            }
            if (high === null || value > high) {
              high = value;
            }
          }
          column.push(low, high);
        }
      });
    }
    return found ? { data: [x].concat(columns), reach: x.length } : null;
  }

  // The steps a chart is reduced at, coarsest last. Two points come out of each run
  // of samples, so a step of 8 draws a quarter of them and a step of 512 a 256th.
  // Each step halves the points of the one before it, so whatever is on screen is
  // drawn from between one and two points per pixel rather than whatever the gaps in
  // a coarser ladder allowed.
  const STEPS = [4, 8, 16, 32, 64, 128, 256, 512, 1024];
  // The most points worth drawing across one pixel. Two of them are one run of
  // samples, drawn as a stroke from its lowest to its highest.
  const PER_PIXEL = 2;

  // One chart at every step that is worth holding: the samples themselves first, then
  // the reductions, each covering the whole period rather than a window of it.
  // A level holding fewer points than the plot has room for is never the one chosen:
  // at the whole period it would be thinner than the chart can use, and any narrower
  // window needs more points still. So the ladder stops there.
  function pyramidFor(chart, sessions, room) {
    const whole = columnsFor(chart, sessions, 1);
    if (!whole) {
      return null;
    }
    const levels = [{ step: 1, data: whole.data, points: whole.reach }];
    for (const step of STEPS) {
      if (whole.reach <= room || Math.floor(whole.reach / step) * 2 < room) {
        break;
      }
      const made = columnsFor(chart, sessions, step);
      levels.push({ step: step, data: made.data, points: made.reach });
    }
    return levels;
  }

  // Which level to draw at: the coarsest whose points across the window on screen
  // still reach the density asked for. Level 0 is the samples, and is the answer
  // whenever nothing coarser has enough left.
  function levelFor(levels, span, widthPx) {
    const xs = levels[0].data[0];
    const reach = xs[xs.length - 1] - xs[0];
    if (!(span > 0) || !(reach > 0)) {
      return 0;
    }
    const room = Math.max(widthPx, 1) * PER_PIXEL;
    const showing = span / reach;
    for (let at = levels.length - 1; at > 0; at--) {
      if (levels[at].points * showing >= room) {
        return at;
      }
    }
    return 0;
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

  // What an event name is drawn as. The caller decides; without one, the device's own
  // word is drawn. Nothing here is the identity of an event -- that stays the text the
  // file carried, which is what colors and counts are keyed on.
  function nameOf(options, text) {
    return options.labelOf ? options.labelOf(text) : text;
  }

  // The words a drawn name stands for, from the caller. Without one, a name stands
  // for itself and no hover is added.
  function spellingOf(options, text) {
    return options.spellOf ? options.spellOf(text) : text;
  }

  // uPlot paints its axis labels onto the canvas, so there is no element to hover for
  // a row's name. This lays one transparent band per row over the axis column, each
  // carrying what its name stands for. Rows are given top down, since that is how a
  // reader sees them, whatever order the chart's splits run in.
  //
  // Called from a draw hook, and placed from u.bbox rather than from the over
  // element's inline styles: those are still empty while the chart is being built,
  // and a band of no width is a band nothing can hover.
  function nameHovers(u, topDown, options) {
    const wrap = u.over.parentNode;
    if (!wrap || !topDown.length) {
      return;
    }
    let holder = u.papvaultNameHovers;
    if (!holder) {
      holder = document.createElement("div");
      holder.className = "name-hovers";
      topDown.forEach(function (text, index) {
        const band = document.createElement("span");
        band.style.top = (index / topDown.length * 100) + "%";
        band.style.height = (100 / topDown.length) + "%";
        band.title = spellingOf(options, text);
        holder.append(band);
      });
      wrap.append(holder);
      u.papvaultNameHovers = holder;
    }
    // u.bbox is in canvas pixels, which are CSS pixels times the device ratio.
    const ratio = devicePixelRatio || 1;
    holder.style.left = "0px";
    holder.style.top = (u.bbox.top / ratio) + "px";
    holder.style.width = (u.bbox.left / ratio) + "px";
    holder.style.height = (u.bbox.height / ratio) + "px";
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
            // Anchored at "to", the moment the file recorded, so the solid line stays
            // on that mark and the shading covers the span before it however narrow
            // the span is drawn.
            const wide = Math.max(to - from, least);
            ctx.fillStyle = colors.get(event.text) || colorOf("--plot-event");
            ctx.globalAlpha = EVENT_OPACITY;
            ctx.fillRect(to - wide, u.bbox.top, wide, u.bbox.height);
            ctx.globalAlpha = 1;
            ctx.fillRect(to - edge, u.bbox.top, edge, u.bbox.height);
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

  // The widest date label the period will draw, in pixels.
  function widestDateLabel(options) {
    const ctx = document.createElement("canvas").getContext("2d");
    ctx.font = LABEL_FONT;
    let widest = 0;
    for (const day of options.days) {
      widest = Math.max(widest, ctx.measureText(options.formatDate(day.seconds)).width);
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
  // the device wrote and never grouping two of them together. The caller's order is
  // the card's, so a row is in the same place on every night of it; a name only this
  // night holds is added after those.
  function buildStrip(parent, events, options, width) {
    const labels = (options.eventLabels || []).slice();
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
      cursor: { sync: { key: CURSOR_SYNC.key, scales: ["x", null] }, y: false, bind: PAN_BIND },
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
            // The splits count up from the bottom, and the first name is drawn at the
            // top, so the labels are handed back the other way round.
            return labels.slice().reverse().map(function (text) {
              return options.fitLabel(nameOf(options, text));
            });
          },
        },
      ],
      series: [{}, { show: false }],
      hooks: {
        draw: [function (u) {
          nameHovers(u, labels, options);
          const ctx = u.ctx;
          ctx.save();
          ctx.beginPath();
          ctx.rect(u.bbox.left, u.bbox.top, u.bbox.width, u.bbox.height);
          ctx.clip();
          const least = Math.ceil(EVENT_LEAST * devicePixelRatio);
          const height = u.bbox.height / labels.length;
          // A dotted rule between one row and the next, so a bar is read against the
          // name beside it rather than the one above.
          ctx.save();
          ctx.strokeStyle = options.colorOf("--plot-row-line");
          ctx.lineWidth = Math.max(1, Math.round(devicePixelRatio));
          ctx.setLineDash([Math.max(1, Math.round(devicePixelRatio)),
            Math.max(3, Math.round(3 * devicePixelRatio))]);
          // One at every edge, the outer two included, so the strip reads as a set of
          // rows rather than as bars floating above the charts.
          for (let i = 0; i <= labels.length; i++) {
            // Kept inside the plotting area, or the first and the last would fall on
            // its own edge and be clipped away.
            const edge = Math.min(Math.max(Math.round(u.bbox.top + i * height), u.bbox.top),
              u.bbox.top + u.bbox.height - 1);
            const at = edge + 0.5;
            ctx.beginPath();
            ctx.moveTo(u.bbox.left, at);
            ctx.lineTo(u.bbox.left + u.bbox.width, at);
            ctx.stroke();
          }
          ctx.restore();
          for (const event of events) {
            const from = u.valToPos(event.seconds, "x", true);
            const to = u.valToPos(event.seconds + Math.max(event.duration, 0), "x", true);
            // The first name is the top row, so the rows read in the order the card
            // set and a night can be read against the night before it.
            const top = u.bbox.top + row.get(event.text) * height;
            const wide = Math.max(to - from, least);
            ctx.fillStyle = options.eventColors.get(event.text) || options.colorOf("--plot-event");
            ctx.fillRect(to - wide, top + height * 0.14, wide, height * 0.72);
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
    const levels = pyramidFor(chart, sessions, Math.max(width, 1) * PER_PIXEL);
    if (!levels) {
      return null;
    }
    // The level the period it opens on calls for, so the first draw is not the one
    // that costs the most.
    const opening = levelFor(levels, options.to - options.from, width);
    const columns = levels[opening];
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
        bind: PAN_BIND,
      },
      legend: { live: true },
      scales: { x: { time: false }, y: { range: paddedRange(false) } },
      axes: axesFor(options, showTimes),
      series: series,
      plugins: [eventBands(options.events, options.eventColors, options.colorOf)],
      hooks: {
        setScale: [function (u, key) {
          if (key !== "x") {
            return;
          }
          if (u.papvaultSpread) {
            u.papvaultSpread(u.scales.x.min, u.scales.x.max);
          }
          swapLevel(u, levels);
        }],
      },
    };
    const built = new uPlot(config, columns.data, holder);
    built.papvaultLevel = opening;
    built.setScale("x", { min: options.from, max: options.to });
    return built;
  }

  // Hands the chart the level its window now calls for. The whole of that level goes
  // over, never a window of it, so the scale the reader chose is untouched and the
  // chart can still be zoomed back out to the period it was built with.
  // setData without a rescale draws nothing on its own, so the redraw is what puts it
  // on screen, and it runs outside the commit that asked for it.
  function swapLevel(u, levels) {
    if (levels.length < 2) {
      return;
    }
    const wide = u.over.clientWidth || u.width;
    if (levelFor(levels, u.scales.x.max - u.scales.x.min, wide) === u.papvaultLevel) {
      return;
    }
    // Handing a level over is a setData across the whole of it, which is work in
    // proportion to its length, and a gesture crosses several levels on its way in.
    // So the swap waits for the scale to be still, and a gesture that passes through
    // a level on its way somewhere else never pays for it.
    clearTimeout(u.papvaultSwap);
    u.papvaultSwap = setTimeout(function () {
      if (!u.root.isConnected) {
        return;
      }
      const want = levelFor(levels, u.scales.x.max - u.scales.x.min,
        u.over.clientWidth || u.width);
      if (want === u.papvaultLevel) {
        return;
      }
      u.papvaultLevel = want;
      u.setData(levels[want].data, false);
      u.redraw();
    }, GESTURE_GAP);
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

    // A window of the width it already has, put where it was asked for and no further
    // than the ends of the period the stack was given. The drag and the wheel zoom
    // both go through here.
    const slide = function (from, to) {
      if (from < options.from) {
        to += options.from - from;
        from = options.from;
      }
      if (to > options.to) {
        from -= to - options.to;
        to = options.to;
      }
      spread(from, to);
    };

    for (const chart of charts) {
      chart.papvaultSpread = spread;
      // Which of the page and the plot a wheel gesture belongs to, and when the last
      // event of it arrived. A gesture is latched to whatever scrolled first, so the
      // answer is settled once, on the first event carrying movement, and held until
      // a gap in the events ends the gesture.
      let takes = null;
      let lastWheel = 0;
      // What the gesture has asked for and not yet been given, and whether a frame is
      // already on its way. Wheel events arrive several times faster than a stack of
      // charts is redrawn and nothing throttles them, so they are added up here and
      // spent once a frame. The first event of a gesture is spent where it lands, so
      // a swipe answers the moment it starts.
      let owed = 0;
      let framed = false;
      // Seconds per pixel at the width the gesture began with. Reading it once keeps
      // a layout measurement out of the path every event takes.
      let perPixel = 0;
      const spend = function () {
        const by = owed;
        owed = 0;
        if (by) {
          slide(chart.scales.x.min + by, chart.scales.x.max + by);
        }
      };
      // The same for zooming, which a pinch drives at the same rate. Factors multiply,
      // so adding the distances up and raising two to the total once is the same
      // answer as taking each event in turn, and it costs one redraw instead of many.
      let owedZoom = 0;
      let zoomedAt = 0;
      let zoomFramed = false;
      let zoomTravel = 0;
      const spendZoom = function () {
        const by = owedZoom;
        owedZoom = 0;
        if (!by) {
          return;
        }
        const box = chart.over.getBoundingClientRect();
        const at = chart.posToVal(zoomedAt - box.left, "x");
        const min = chart.scales.x.min;
        const max = chart.scales.x.max;
        const factor = Math.pow(2, by / (zoomTravel || WHEEL_TRAVEL));
        const from = at - (at - min) * factor;
        const to = at + (max - at) * factor;
        if (to - from >= options.to - options.from) {
          spread(options.from, options.to);
        } else {
          slide(from, to);
        }
      };
      chart.over.addEventListener("wheel", function (event) {
        // Zooming is the wheel with Ctrl held, which is also what a trackpad pinch
        // sends.
        if (event.timeStamp - lastWheel > GESTURE_GAP) {
          takes = null;
          framed = false;
          owed = 0;
          zoomTravel = 0;
        }
        lastWheel = event.timeStamp;
        if (event.ctrlKey) {
          event.preventDefault();
          if (!zoomTravel && Math.abs(event.deltaY) >= ZOOM_TRACE) {
            zoomTravel = Math.abs(event.deltaY) < PINCH_STEP ? PINCH_TRAVEL : WHEEL_TRAVEL;
          }
          zoomedAt = event.clientX;
          owedZoom += event.deltaY;
          if (zoomFramed) {
            return;
          }
          spendZoom();
          zoomFramed = true;
          requestAnimationFrame(function () {
            zoomFramed = false;
            spendZoom();
          });
          return;
        }
        if (takes === null) {
          if (!event.deltaX && !event.deltaY) {
            return;
          }
          // Sideways, and with somewhere left to slide to. Anything else is the
          // page's, which is what scrolls a plot out of the way to read the next one.
          takes = Math.abs(event.deltaX) > Math.abs(event.deltaY)
            && (chart.scales.x.min > options.from || chart.scales.x.max < options.to);
          perPixel = (chart.scales.x.max - chart.scales.x.min)
            / chart.over.getBoundingClientRect().width;
        }
        if (!takes) {
          return;
        }
        event.preventDefault();
        owed += event.deltaX * perPixel;
        if (framed) {
          return;
        }
        spend();
        framed = true;
        requestAnimationFrame(function () {
          framed = false;
          spend();
        });
      }, { passive: false });

      // Ctrl and drag slides the window instead of zooming it: the span is kept, and
      // the window is clamped to the period the stack was given.
      chart.over.addEventListener("mousedown", function (event) {
        if (!isPan(event)) {
          return;
        }
        event.preventDefault();
        const min = chart.scales.x.min;
        const max = chart.scales.x.max;
        const perPixel = (max - min) / chart.over.getBoundingClientRect().width;
        const grabbed = event.clientX;
        chart.over.classList.add("panning");
        const move = function (moved) {
          // The button was let go where this could not hear it, outside the window.
          if (moved.buttons === 0) {
            stop();
            return;
          }
          const by = (grabbed - moved.clientX) * perPixel;
          slide(min + by, max + by);
        };
        const stop = function () {
          window.removeEventListener("mousemove", move);
          window.removeEventListener("mouseup", stop);
          chart.over.classList.remove("panning");
        };
        window.addEventListener("mousemove", move);
        window.addEventListener("mouseup", stop);
      });

      chart.over.addEventListener("dblclick", function () {
        spread(options.from, options.to);
      });

      // A touch screen has no wheel, no Ctrl and no hover, so the same three things
      // are done with fingers: one finger slides the window and takes the cursor with
      // it, two fingers zoom about the point between them, and two taps in quick
      // succession put the whole period back. Up and down is left to the page, which
      // is what touch-action asks the browser for.
      let began = null;
      let tapped = 0;

      const spanOf = function (touches) {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
      };

      const middleOf = function (touches) {
        if (touches.length < 2) {
          return touches[0].clientX;
        }
        return (touches[0].clientX + touches[1].clientX) / 2;
      };

      const cursorAt = function (x) {
        const box = chart.over.getBoundingClientRect();
        chart.setCursor({ left: x - box.left, top: chart.over.clientHeight / 2 }, true);
      };

      // Where the window and the fingers are as of now. Taken again whenever a finger
      // lands or leaves, so the gesture carries on from where it was rather than
      // jumping by however far the fingers that remain are from the ones that went.
      const beginFrom = function (touches, fingers) {
        const box = chart.over.getBoundingClientRect();
        began = {
          at: middleOf(touches),
          min: chart.scales.x.min,
          max: chart.scales.x.max,
          perPixel: (chart.scales.x.max - chart.scales.x.min) / box.width,
          apart: touches.length > 1 ? spanOf(touches) : 0,
          anchor: chart.posToVal(middleOf(touches) - box.left, "x"),
          moved: 0,
          fingers: fingers,
        };
      };

      chart.root.addEventListener("touchstart", function (event) {
        beginFrom(event.touches,
          Math.max(event.touches.length, began ? began.fingers : 0));
      }, { passive: true });

      chart.root.addEventListener("touchmove", function (event) {
        if (!began) {
          return;
        }
        const now = middleOf(event.touches);
        began.moved = Math.max(began.moved, Math.abs(now - began.at));
        // Two fingers that have moved apart or together zoom by how far they did,
        // and where their middle went slides the window under them.
        if (event.touches.length > 1 && began.apart) {
          event.preventDefault();
          const factor = began.apart / Math.max(spanOf(event.touches), 1);
          const by = (began.at - now) * began.perPixel * factor;
          const from = began.anchor - (began.anchor - began.min) * factor + by;
          const to = began.anchor + (began.max - began.anchor) * factor + by;
          if (to - from >= options.to - options.from) {
            spread(options.from, options.to);
          } else {
            slide(from, to);
          }
          return;
        }
        if (began.moved < TAP_SLOP) {
          return;
        }
        event.preventDefault();
        const by = (began.at - now) * began.perPixel;
        slide(began.min + by, began.max + by);
        cursorAt(now);
      }, { passive: false });

      chart.root.addEventListener("touchend", function (event) {
        if (!began) {
          return;
        }
        // A single finger that went nowhere is a tap: the first puts the cursor where
        // it landed, and a second one soon after puts the whole period back. A pinch
        // is never a tap, however still its middle stayed.
        if (began.fingers === 1 && began.moved < TAP_SLOP && !event.touches.length) {
          if (event.timeStamp - tapped < DOUBLE_TAP) {
            spread(options.from, options.to);
            tapped = 0;
          } else {
            cursorAt(began.at);
            tapped = event.timeStamp;
          }
        }
        if (event.touches.length) {
          beginFrom(event.touches, began.fingers);
          return;
        }
        tapped = began.fingers === 1 ? tapped : 0;
        began = null;
      }, { passive: true });
    }
  }

  // Draws the stack into an empty container and hands back what it could not draw.
  function show(container, given) {
    const width = Math.max(container.clientWidth, PLOT_LEAST);
    const names = [];
    for (const event of given.events) {
      if (names.indexOf(event.text) === -1) {
        names.push(event.text);
      }
    }
    const axis = axisWidthFor(names, AXIS_WIDTH);
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
      eventColors: given.eventColors || eventColorsFor(given.eventLabels || names, given.colorOf),
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
        const now = Math.max(container.clientWidth, PLOT_LEAST);
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

  // One entry per summary chart, in the order they are stacked. Each reads its columns
  // off the per-day figures it is handed, one line per figure a night carries.
  const SUMMARIES = [
    {
      key: "usage", title: "Hours Used/day", bars: true,
      series: [{ name: "Hours", groupedName: "Hours/day", color: "--plot-usage",
        of: function (day) { return day.hours; } }],
    },
    {
      key: "sessions", title: "Sessions", bars: true,
      series: [{ name: "Sessions", color: "--plot-sessions", of: function (day) { return day.sessions; } }],
    },
    { key: "events", title: "Events per Hour", perLabel: true, series: [] },
    {
      key: "pressure", title: "Pressure",
      series: [
        { name: "Mean", color: "--plot-mask-pressure", of: function (day) { return day.pressure.mean; } },
        { name: "95th percentile", color: "--plot-mask-pressure", dash: [6, 4], of: function (day) { return day.pressure.p95; } },
      ],
    },
    {
      key: "leak", title: "Leak",
      series: [
        { name: "Mean", color: "--plot-leak", of: function (day) { return day.leak.mean; } },
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
        splits: function (u) {
          // As many days as fit at the width the labels measure, so a long period
          // thins out instead of writing one date over the next.
          const room = u.over.clientWidth
            ? Math.max(1, Math.floor(u.over.clientWidth / options.dateSpace))
            : 8;
          const step = Math.max(1, Math.ceil(options.days.length / room));
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
      ? (options.eventsShown || options.eventLabels).map(function (text, index) {
        return {
          name: nameOf(options, text),
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

    const spellOut = options.formatPoint || options.formatDate;
    const series = [{ label: options.dateLabel || "Day", value: function (u, raw) {
      return raw === null ? "" : spellOut(raw);
    } }];
    specs.forEach(function (spec) {
      const drawn = {
        // A grouped point is a mean per day where a daily one is the day itself, and
        // a figure whose name says so carries the second name.
        label: options.grouped && spec.groupedName ? spec.groupedName : spec.name,
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
      padding: options.padding,
      title: summary.title + (unit ? " (" + unit + ")" : ""),
      cursor: { sync: { key: SUMMARY_SYNC.key, scales: ["x", null] }, drag: { x: true, y: false },
        bind: PAN_BIND },
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
    // The width the card gives it.
    function widthOf() {
      return Math.max(container.clientWidth, PLOT_LEAST);
    }

    const width = widthOf();
    // In a narrow card the names may not take more than half of it, or there is
    // no room left for the bars they label.
    // Measured against what is drawn, not against the word the file carried, or a
    // short form would reserve room for a name nobody sees.
    const drawn = names.map(function (text) {
      return nameOf(given, text);
    });
    const axis = axisWidthFor(drawn, width * 0.5);
    const colors = given.eventColors || eventColorsFor(names, given.colorOf);
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
            return drawn.slice().reverse().map(axis.fit);
          },
        },
      ],
      series: [{}, { show: false }],
      hooks: {
        draw: [function (u) {
          nameHovers(u, names, given);
          const ctx = u.ctx;
          ctx.save();
          const row = u.bbox.height / names.length;
          const zero = u.valToPos(0, "x", true);
          ctx.font = Math.round(11 * devicePixelRatio) + "px " + LABEL_FONT.slice(5);
          // The context arrives from uPlot's own axis drawing, which leaves the count
          // centered on the end of its bar, so both are set again here.
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
        chart.setSize({ width: widthOf(), height: chart.height });
      },
      destroy: function () {
        chart.destroy();
        container.replaceChildren();
      },
    };
  }

  // The closest two of these points come, in seconds, or zero for a single point.
  // Months are of different lengths, so this is the shortest gap and not the mean one.
  function shortestStep(days) {
    let step = 0;
    for (let index = 1; index < days.length; index++) {
      const gap = days[index].seconds - days[index - 1].seconds;
      if (!step || gap < step) {
        step = gap;
      }
    }
    return step;
  }

  // The summary stack: one point or bar per CPAP day, or per group of them, in the
  // chosen period.
  function showSummary(container, given) {
    const width = Math.max(container.clientWidth, PLOT_LEAST);
    // The scale reaches half a step past the first and last point, which is what a
    // bar centered on either of them needs to be drawn whole. A single point has no
    // step and stands for a day.
    const HALF_DAY = 43200;
    const half = shortestStep(given.days) / 2 || HALF_DAY;
    const from = given.from - half;
    const to = given.to + half;
    const dateWidth = widestDateLabel(given);
    const options = Object.assign({}, given, {
      axisWidth: AXIS_WIDTH,
      from: from,
      to: to,
      dateSpace: dateWidth + AXIS_LABEL_GAP,
      // Wide enough on the right for half of the last date, which sits at the end of
      // the scale once a period is long enough for half a step to be nothing.
      padding: [PLOT_PADDING[0], Math.max(PLOT_PADDING[1], Math.ceil(dateWidth / 2) + 6),
        PLOT_PADDING[2], PLOT_PADDING[3]],
      eventColors: given.eventColors || eventColorsFor(given.eventLabels || [], given.colorOf),
    });
    container.style.setProperty("--plot-axis", AXIS_WIDTH + "px");
    const built = [];
    const drawn = [];
    const chosen = SUMMARIES.filter(function (summary) {
      return !options.charts || options.charts.indexOf(summary.key) !== -1;
    });
    chosen.forEach(function (summary, index) {
      const made = buildSummary(container, summary, options, width, index === chosen.length - 1);
      if (made) {
        built.push(made);
        drawn.push(summary.key);
      }
    });
    link(built, options);
    return {
      drawn: drawn,
      resize: function () {
        const now = Math.max(container.clientWidth, PLOT_LEAST);
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
