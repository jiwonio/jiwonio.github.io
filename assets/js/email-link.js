(function () {
  function activate(link) {
    var user = link.getAttribute("data-email-user");
    var domain = link.getAttribute("data-email-domain");
    if (!user || !domain) {
      return;
    }
    link.href = "mailto:" + user + "@" + domain;
  }

  document.querySelectorAll("[data-email-user][data-email-domain]").forEach(activate);
})();