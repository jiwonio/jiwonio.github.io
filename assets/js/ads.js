(function () {
  var FALLBACK_MS = 5000;

  function syncSlot(slot) {
    var ins = slot.querySelector("ins.adsbygoogle");
    if (!ins) {
      return;
    }

    var status = ins.getAttribute("data-ad-status");
    if (status === "filled") {
      slot.classList.add("ad-slot--filled");
      slot.classList.remove("ad-slot--hidden");
    } else {
      slot.classList.remove("ad-slot--filled");
      slot.classList.add("ad-slot--hidden");
    }
  }

  function observeSlot(slot) {
    var ins = slot.querySelector("ins.adsbygoogle");
    if (!ins) {
      return;
    }

    slot.classList.add("ad-slot--hidden");

    syncSlot(slot);

    if (typeof MutationObserver !== "function") {
      return;
    }

    new MutationObserver(function () {
      syncSlot(slot);
    }).observe(ins, {
      attributes: true,
      attributeFilter: ["data-ad-status"],
    });

    window.setTimeout(function () {
      syncSlot(slot);
    }, FALLBACK_MS);
  }

  function init() {
    var slots = document.querySelectorAll(".ad-slot");
    if (!slots.length) {
      return;
    }

    slots.forEach(observeSlot);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();