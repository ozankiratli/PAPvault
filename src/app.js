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
  const THEME_KEY = "papvault-theme";

  function systemTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    root.dataset.theme = theme;
    toggle.textContent = theme === "dark" ? "Light mode" : "Dark mode";
  }

  let saved = null;
  try {
    saved = window.localStorage.getItem(THEME_KEY);
  } catch (e) {
    saved = null;
  }
  applyTheme(saved === "dark" || saved === "light" ? saved : systemTheme());

  toggle.addEventListener("click", function () {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(next);
    try {
      window.localStorage.setItem(THEME_KEY, next);
    } catch (e) {
      // Storage is unavailable in some private windows; the choice then lasts for this visit.
    }
  });

  app.hidden = false;
})();
