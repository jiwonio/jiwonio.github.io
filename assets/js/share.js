(function () {
  function showCopied(button) {
    button.classList.add("post-share__btn--copied");
    var copiedLabel = button.getAttribute("data-share-copied");
    if (copiedLabel) {
      button.setAttribute("aria-label", copiedLabel);
    }

    window.setTimeout(function () {
      button.classList.remove("post-share__btn--copied");
      button.setAttribute("aria-label", button.getAttribute("data-share-label") || "");
    }, 2000);
  }

  function copyUrl(button) {
    var url = button.getAttribute("data-share-url");
    if (!url) {
      return;
    }

    if (!button.getAttribute("data-share-label")) {
      button.setAttribute("data-share-label", button.getAttribute("aria-label") || "");
    }

    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      navigator.clipboard.writeText(url).then(function () {
        showCopied(button);
      });
      return;
    }

    var input = document.createElement("textarea");
    input.value = url;
    input.setAttribute("readonly", "");
    input.style.position = "absolute";
    input.style.left = "-9999px";
    document.body.appendChild(input);
    input.select();

    try {
      if (document.execCommand("copy")) {
        showCopied(button);
      }
    } finally {
      document.body.removeChild(input);
    }
  }

  function init() {
    var buttons = document.querySelectorAll("[data-share-copy]");
    if (!buttons.length) {
      return;
    }

    buttons.forEach(function (button) {
      button.addEventListener("click", function () {
        copyUrl(button);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();