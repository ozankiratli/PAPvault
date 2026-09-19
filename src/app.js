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
  const selectionLabel = document.getElementById("selection-label");

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function isoDate(d) {
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
  }

  function clockTime(d) {
    const minutes = pad(d.getMinutes());
    if (timeFormat === "24") {
      return pad(d.getHours()) + ":" + minutes;
    }
    const hour = d.getHours() % 12 === 0 ? 12 : d.getHours() % 12;
    return hour + ":" + minutes + " " + (d.getHours() < 12 ? "AM" : "PM");
  }

  function dateTime(d) {
    return isoDate(d) + " " + clockTime(d);
  }

  function nextDay(d) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1);
  }

  // A CPAP day runs from 12:00 on its date to 12:00 on the next calendar day.
  // The calendar's days are CPAP days, each held as local midnight of its date.
  function cpapDayOf(instant) {
    const date = new Date(instant.getFullYear(), instant.getMonth(), instant.getDate());
    return instant.getHours() < 12 ? new Date(date.getFullYear(), date.getMonth(), date.getDate() - 1) : date;
  }

  function cpapDayStart(day) {
    return new Date(day.getFullYear(), day.getMonth(), day.getDate(), 12);
  }

  const currentDay = cpapDayOf(new Date());
  let shown = new Date(currentDay.getFullYear(), currentDay.getMonth(), 1);
  let start = currentDay;
  let end = currentDay;
  let pending = false;

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

  function renderSelection() {
    let text = dateTime(cpapDayStart(start)) + " to " + dateTime(cpapDayStart(nextDay(end)));
    if (end > start) {
      text += " (" + dayCount(start, end) + " days)";
    }
    selectionLabel.textContent = text;
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
      button.setAttribute("aria-label", isoDate(day));
      if (t === currentDay.getTime()) {
        button.classList.add("current");
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
    if (focused !== null) {
      const again = Array.prototype.find.call(grid.children, function (cell) {
        return cell.getAttribute("aria-label") === focused;
      });
      if (again) {
        again.focus();
      }
    }
    renderSelection();
  }

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

  document.querySelectorAll("[data-dialog]").forEach(function (button) {
    button.addEventListener("click", function () {
      document.getElementById(button.dataset.dialog).showModal();
    });
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
      renderSelection();
    });
  });

  const calendar = document.getElementById("calendar");
  const cardSlot = document.getElementById("calendar-card-slot");
  const dialogSlot = document.getElementById("calendar-dialog-slot");
  const calendarDialog = document.getElementById("calendar-dialog");
  const calendarButton = document.getElementById("open-calendar");
  const narrow = window.matchMedia("(max-width: 649.98px)");

  function placeCalendar() {
    root.classList.toggle("narrow", narrow.matches);
    calendarButton.hidden = !narrow.matches;
    cardSlot.hidden = narrow.matches;
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
  placeCalendar();
  render();
  app.hidden = false;
})();
