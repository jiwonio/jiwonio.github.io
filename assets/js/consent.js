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
    updateConsent(true);
    scheduleIdle(function () {
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