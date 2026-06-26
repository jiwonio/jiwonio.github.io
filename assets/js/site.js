(function () {
  var ICONS = {
    adjust:
      '<svg class="icon" aria-hidden="true" width="1em" height="1em" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8V20z"/></svg>',
    sun:
      '<svg class="icon icon--stroke icon--theme" aria-hidden="true" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"><circle cx="12" cy="12" r="3.5"/><line x1="12" y1="2" x2="12" y2="5.5"/><line x1="12" y1="18.5" x2="12" y2="22"/><line x1="2" y1="12" x2="5.5" y2="12"/><line x1="18.5" y1="12" x2="22" y2="12"/></svg>',
    moon:
      '<svg class="icon icon--theme" aria-hidden="true" width="1em" height="1em" viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
  };

  function setIcon(element, name) {
    if (!element || !ICONS[name]) {
      return;
    }
    element.innerHTML = ICONS[name];
  }

  window.SiteIcons = {
    set: setIcon,
    names: Object.keys(ICONS),
  };
})();

(function () {
  var STORAGE_KEY = "theme-preference";
  var CYCLE = ["system", "light", "dark"];

  var LABELS = {
    system: "시스템 설정",
    light: "라이트 모드",
    dark: "다크 모드",
  };

  var ICONS = {
    system: "adjust",
    light: "sun",
    dark: "moon",
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

  function clickToChangeSuffix(labels) {
    return labels.click_to_change ? " (" + labels.click_to_change + ")" : "";
  }

  function updateToggle(button, preference) {
    var labels = resolveLabels();
    var icon = button.querySelector("[data-icon]");
    if (icon && window.SiteIcons) {
      window.SiteIcons.set(icon, ICONS[preference]);
    }
    button.dataset.themePreference = preference;
    button.setAttribute("aria-label", labels[preference] + clickToChangeSuffix(labels));
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

(function () {
  function init() {
    var details = document.querySelector(".lang-switcher__details");
    if (!details) {
      return;
    }

    document.addEventListener("click", function (event) {
      if (!details.open) {
        return;
      }
      if (!details.contains(event.target)) {
        details.open = false;
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && details.open) {
        details.open = false;
        details.querySelector(".lang-switcher__trigger").focus();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

(function () {
  var STORAGE_KEY = "blog-consent-v1";
  var banner = document.getElementById("cookie-consent");
  if (!banner) {
    return;
  }

  var focusableSelector =
    'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])';
  var lastFocusedElement = null;

  function getFocusableElements() {
    return Array.prototype.slice.call(banner.querySelectorAll(focusableSelector)).filter(function (el) {
      return !el.hasAttribute("disabled") && el.offsetParent !== null;
    });
  }

  function trapFocus(event) {
    if (banner.hidden || event.key !== "Tab") {
      return;
    }

    var focusable = getFocusableElements();
    if (!focusable.length) {
      return;
    }

    var first = focusable[0];
    var last = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function updateConsent(granted) {
    if (typeof gtag !== "function") {
      return;
    }
    gtag("consent", "update", {
      ad_storage: granted ? "granted" : "denied",
      ad_user_data: granted ? "granted" : "denied",
      ad_personalization: granted ? "granted" : "denied",
      analytics_storage: granted ? "granted" : "denied",
    });
  }

  function scheduleIdle(fn) {
    if (typeof requestIdleCallback === "function") {
      requestIdleCallback(function () {
        fn();
      }, { timeout: 3000 });
      return;
    }
    setTimeout(fn, 1);
  }

  function loadScript(src, options) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement("script");
      script.async = true;
      script.src = src;
      if (options && options.crossOrigin) {
        script.crossOrigin = options.crossOrigin;
      }
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  function loadAdsRuntime() {
    var config = window.SITE_I18N && window.SITE_I18N.ads;
    if (!config || !config.adsenseClient) {
      return Promise.resolve();
    }

    return loadScript(
      "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + config.adsenseClient,
      { crossOrigin: "anonymous" }
    ).then(function () {
      if (!document.querySelector('script[src="/assets/js/ads.js"]')) {
        return loadScript("/assets/js/ads.js");
      }
    }).catch(function () {
      /* ignore ad load failures */
    });
  }

  function loadGoogleAnalytics() {
    var config = window.SITE_I18N && window.SITE_I18N.analytics;
    if (!config || !config.googleId) {
      return Promise.resolve();
    }

    return loadScript(
      "https://www.googletagmanager.com/gtag/js?id=" + config.googleId
    ).then(function () {
      window.dataLayer = window.dataLayer || [];
      window.gtag = function () {
        window.dataLayer.push(arguments);
      };
      gtag("consent", "default", {
        ad_storage: "denied",
        ad_user_data: "denied",
        ad_personalization: "denied",
        analytics_storage: "denied",
        wait_for_update: 500,
      });
      gtag("js", new Date());
      gtag("config", config.googleId);
      gtag("consent", "update", {
        ad_storage: "granted",
        ad_user_data: "granted",
        ad_personalization: "granted",
        analytics_storage: "granted",
      });
    }).catch(function () {
      /* ignore analytics load failures */
    });
  }

  function loadNaverAnalytics() {
    var config = window.SITE_I18N && window.SITE_I18N.analytics;
    if (!config || !config.naverId) {
      return Promise.resolve();
    }

    return loadScript("https://wcs.pstatic.net/wcslog.js").then(function () {
      if (!window.wcs_add) {
        window.wcs_add = {};
      }
      window.wcs_add.wa = config.naverId;
      if (window.wcs) {
        window.wcs_do();
      }
    }).catch(function () {
      /* ignore analytics load failures */
    });
  }

  function activateTracking() {
    scheduleIdle(function () {
      loadGoogleAnalytics();
      loadAdsRuntime();
      loadNaverAnalytics();
    });
  }

  function hideBanner() {
    banner.hidden = true;
    document.removeEventListener("keydown", trapFocus);
    if (lastFocusedElement && typeof lastFocusedElement.focus === "function") {
      lastFocusedElement.focus();
    }
  }

  function showBanner() {
    lastFocusedElement = document.activeElement;
    banner.hidden = false;
    document.addEventListener("keydown", trapFocus);

    var focusable = getFocusableElements();
    if (focusable.length) {
      focusable[0].focus();
    }
  }

  function saveChoice(value) {
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch (error) {
      /* ignore storage failures */
    }
  }

  function readChoice() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      return null;
    }
  }

  function reopenConsent() {
    showBanner();
  }

  window.reopenCookieConsent = reopenConsent;

  function handleHashOpen() {
    if (window.location.hash === "#cookie-settings") {
      reopenConsent();
    }
  }

  document.addEventListener("cookie-consent:reopen", reopenConsent);
  window.addEventListener("hashchange", handleHashOpen);

  var saved = readChoice();
  if (saved === "accepted") {
    activateTracking();
    hideBanner();
  } else if (saved === "rejected") {
    updateConsent(false);
    hideBanner();
  } else {
    showBanner();
  }

  handleHashOpen();

  var acceptButton = document.getElementById("cookie-consent-accept");
  var rejectButton = document.getElementById("cookie-consent-reject");

  if (acceptButton) {
    acceptButton.addEventListener("click", function () {
      saveChoice("accepted");
      activateTracking();
      hideBanner();
    });
  }

  if (rejectButton) {
    rejectButton.addEventListener("click", function () {
      saveChoice("rejected");
      updateConsent(false);
      hideBanner();
    });
  }
})();
