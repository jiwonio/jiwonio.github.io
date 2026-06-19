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