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