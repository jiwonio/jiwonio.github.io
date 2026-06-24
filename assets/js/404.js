(function () {
  var LANG_CODES = ["ko", "en", "ja", "zh"];
  var DEFAULT_LANG = "ko";

  function detectLang() {
    var path = window.location.pathname || "/";
    var match = path.match(/^\/(en|ja|zh)(?:\/|$)/);
    if (match) {
      return match[1];
    }
    return DEFAULT_LANG;
  }

  function getStrings(lang) {
    var all = window.SITE_I18N && window.SITE_I18N.page_404_all;
    if (all && all[lang]) {
      return all[lang];
    }
    if (all && all[DEFAULT_LANG]) {
      return all[DEFAULT_LANG];
    }
    return null;
  }

  function init() {
    var root = document.getElementById("page-404");
    if (!root) {
      return;
    }

    var strings = getStrings(detectLang());
    if (!strings) {
      return;
    }

    var title = root.querySelector("[data-404-title]");
    var message = root.querySelector("[data-404-message]");
    var home = root.querySelector("[data-404-home]");

    if (title && strings.title) {
      title.textContent = strings.title;
    }
    if (message && strings.message) {
      message.textContent = strings.message;
    }
    if (home && strings.home) {
      home.textContent = strings.home;
    }

    var lang = detectLang();
    if (home) {
      home.href = lang === DEFAULT_LANG ? "/" : "/" + lang + "/";
    }

    if (strings.title) {
      document.title = strings.title;
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();