(function () {
  var copiedClass = "post-share__btn--copied-state";

  function getToast(button) {
    return button.querySelector(".post-share__toast");
  }

  function isCopied(button) {
    return button.classList.contains(copiedClass);
  }

  function showToast(button, text) {
    var toast = getToast(button);
    if (!toast) {
      return;
    }
    toast.textContent = text;
    toast.classList.add("post-share__toast--visible");
  }

  function hideToast(button) {
    var toast = getToast(button);
    if (!toast) {
      return;
    }
    toast.textContent = "";
    toast.classList.remove("post-share__toast--visible");
  }

  function showHoverToast(button) {
    if (isCopied(button)) {
      return;
    }
    showToast(button, button.getAttribute("data-share-toast") || "Copy");
  }

  function showCopied(button) {
    var copiedLabel = button.getAttribute("data-share-toast-copied") || "Copied!";
    var resetMs = 2000;

    button.classList.add("post-share__btn--copied");
    button.classList.add(copiedClass);
    button.setAttribute("aria-label", button.getAttribute("data-share-copied") || copiedLabel);
    showToast(button, copiedLabel);

    window.clearTimeout(button._shareCopiedTimer);
    button._shareCopiedTimer = window.setTimeout(function () {
      button.classList.remove("post-share__btn--copied");
      button.classList.remove(copiedClass);
      button.setAttribute("aria-label", button.getAttribute("data-share-label") || "");

      if (button.matches(":hover") || button.matches(":focus-visible")) {
        showHoverToast(button);
      } else {
        hideToast(button);
      }
    }, resetMs);
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
      button.addEventListener("mouseenter", function () {
        showHoverToast(button);
      });

      button.addEventListener("mouseleave", function () {
        if (!isCopied(button)) {
          hideToast(button);
        }
      });

      button.addEventListener("focus", function () {
        showHoverToast(button);
      });

      button.addEventListener("blur", function () {
        if (!isCopied(button)) {
          hideToast(button);
        }
      });

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