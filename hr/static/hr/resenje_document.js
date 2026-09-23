(function () {
  'use strict';

  // Puna visina poslednje A4 strane ostavlja potpis i dostavljanje pri dnu.
  function alignFooters() {
    document.querySelectorAll('.resenje').forEach(function (documentElement) {
      documentElement.style.minHeight = '';
      var pageHeight = parseFloat(getComputedStyle(documentElement).minHeight);
      if (!pageHeight) return;
      var pages = Math.max(1, Math.ceil((documentElement.getBoundingClientRect().height - 1) / pageHeight));
      // Mala rezerva po prelomu izbegava prenos celog potpisa zbog zaokruživanja
      // milimetara i pravila za udovice/siročiće u štampi pregledača.
      documentElement.style.minHeight = (pages * pageHeight - (pages - 1) * 12) + 'px';
    });
  }

  window.addEventListener('load', alignFooters);
  window.addEventListener('beforeprint', alignFooters);
  if (document.fonts) document.fonts.ready.then(alignFooters);
}());
