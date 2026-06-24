(function () {
  var STORAGE_KEY = "blog-consent-v1";
  var banner = document.getElementById("cookie-consent");
  if (!banner) {
    return;
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

  function hideBanner() {
    banner.hidden = true;
  }

  function showBanner() {
    banner.hidden = false;
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

  var saved = readChoice();
  if (saved === "accepted") {
    updateConsent(true);
    hideBanner();
    return;
  }
  if (saved === "rejected") {
    updateConsent(false);
    hideBanner();
    return;
  }

  showBanner();

  var acceptButton = document.getElementById("cookie-consent-accept");
  var rejectButton = document.getElementById("cookie-consent-reject");
  if (acceptButton) {
    acceptButton.addEventListener("click", function () {
      saveChoice("accepted");
      updateConsent(true);
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