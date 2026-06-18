(function () {
  var STORAGE_KEY = "theme-preference";
  var CYCLE = ["system", "light", "dark"];

  // i18n: replace via window.SITE_I18N.theme when multilingual support ships
  var LABELS = {
    system: "시스템 설정",
    light: "라이트 모드",
    dark: "다크 모드",
  };

  var ICONS = {
    system: "fa-adjust",
    light: "fa-sun-o",
    dark: "fa-moon-o",
  };

  function getStored() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      return null;
    }
  }

  function applyTheme(preference) {
    var root = document.documentElement;
    if (preference === "light" || preference === "dark") {
      root.setAttribute("data-theme", preference);
      return;
    }
    root.removeAttribute("data-theme");
  }

  function resolveLabels() {
    if (window.SITE_I18N && window.SITE_I18N.theme) {
      return Object.assign({}, LABELS, window.SITE_I18N.theme);
    }
    return LABELS;
  }

  function updateToggle(button, preference) {
    var labels = resolveLabels();
    var icon = button.querySelector("i");
    if (icon) {
      icon.className = "fa " + ICONS[preference];
    }
    button.dataset.themePreference = preference;
    button.setAttribute("aria-label", labels[preference] + " (클릭하여 변경)");
    button.setAttribute("title", labels[preference]);
  }

  function nextPreference(current) {
    var index = CYCLE.indexOf(current);
    return CYCLE[(index + 1) % CYCLE.length];
  }

  function init() {
    var button = document.getElementById("theme-toggle");
    if (!button) {
      return;
    }

    var preference = getStored() || "system";
    applyTheme(preference);
    updateToggle(button, preference);

    button.addEventListener("click", function () {
      preference = nextPreference(preference);
      try {
        localStorage.setItem(STORAGE_KEY, preference);
      } catch (error) {
        // ignore private browsing quota errors
      }
      applyTheme(preference);
      updateToggle(button, preference);
    });

    var media = window.matchMedia("(prefers-color-scheme: dark)");
    if (typeof media.addEventListener === "function") {
      media.addEventListener("change", function () {
        if ((getStored() || "system") === "system") {
          applyTheme("system");
        }
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();