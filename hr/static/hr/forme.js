/* Forme Kadrova u sekcijama (hr/templates/hr/forms/base.html).
 *
 * - desna kartica se pravi iz sekcija na stranici ([data-ef-section], data-ef-title, data-ef-icon);
 *   skrivena sekcija (npr. polja koja izabrana vrsta ne traži) nestaje i iz kartice;
 * - kartica ostaje na ekranu pri pomeranju (position:fixed, jer tema isključuje sticky);
 * - istaknuta je sekcija koja se gleda; sekcije sa greškom nose broj grešaka;
 * - prozor „Uputstvo" se puni uputstvima sekcija; dugme se sakriva ako uputstva nema.
 */
(function () {
  'use strict';

  function init() {
    var layout = document.getElementById('ef-layout');
    var aside = document.getElementById('ef-aside');
    var nav = document.getElementById('ef-nav');
    var navLinks = document.getElementById('ef-nav-links');
    if (!layout || !nav || !navLinks) return;
    var sections = Array.prototype.slice.call(document.querySelectorAll('[data-ef-section]'));

    function brojGresaka(section) {
      return section.querySelectorAll('.invalid-feedback, .errorlist li').length;
    }
    var links = sections.map(function (section) {
      var key = section.getAttribute('data-ef-section');
      var link = document.createElement('a');
      link.href = '#' + section.id;
      link.setAttribute('data-ef-nav', key);
      var icon = document.createElement('i');
      icon.className = 'mdi ' + (section.getAttribute('data-ef-icon') || 'mdi-form-select');
      link.appendChild(icon);
      link.appendChild(document.createTextNode(section.getAttribute('data-ef-title') || key));
      var greske = brojGresaka(section);
      if (greske) {
        section.classList.add('has-errors');
        var badge = document.createElement('span');
        badge.className = 'ef-nav-err';
        badge.title = 'Greške u sekciji';
        badge.textContent = greske;
        link.appendChild(badge);
      }
      link.addEventListener('click', function (event) {
        event.preventDefault();
        section.scrollIntoView({behavior: 'smooth', block: 'start'});
        oznaci(key);
      });
      navLinks.appendChild(link);
      return link;
    });

    function vidljiva(section) { return section.offsetParent !== null; }
    function osveziVidljivost() {
      var broj = 0;
      sections.forEach(function (section, index) {
        var vid = vidljiva(section);
        links[index].hidden = !vid;
        if (vid) broj += 1;
      });
      layout.classList.toggle('is-single', broj < 2);
    }
    function oznaci(key) {
      links.forEach(function (link) { link.classList.toggle('is-active', link.getAttribute('data-ef-nav') === key); });
    }
    function aktivnaSekcija() {
      var vidljive = sections.filter(vidljiva);
      if (!vidljive.length) return;
      var naDnu = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
      var aktivna = vidljive[0];
      vidljive.forEach(function (s) { if (s.getBoundingClientRect().top <= 140) aktivna = s; });
      if (naDnu) aktivna = vidljive[vidljive.length - 1];
      oznaci(aktivna.getAttribute('data-ef-section'));
    }

    var RAZMAK = 16, DONJA_TRAKA = 76;
    function postaviKarticu() {
      if (window.innerWidth < 992 || layout.classList.contains('is-single')) {
        nav.classList.remove('is-fixed');
        nav.style.left = nav.style.top = nav.style.width = nav.style.maxHeight = '';
        return;
      }
      var okvir = aside.getBoundingClientRect();
      var vrh = Math.max(RAZMAK, okvir.top);
      nav.classList.add('is-fixed');
      nav.style.left = okvir.left + 'px';
      nav.style.width = okvir.width + 'px';
      nav.style.top = vrh + 'px';
      nav.style.maxHeight = (window.innerHeight - vrh - DONJA_TRAKA) + 'px';
    }
    var zakazano = false;
    function osvezi() {
      if (zakazano) return;
      zakazano = true;
      window.requestAnimationFrame(function () {
        zakazano = false;
        osveziVidljivost();
        postaviKarticu();
        aktivnaSekcija();
      });
    }
    window.addEventListener('scroll', osvezi, {passive: true});
    window.addEventListener('resize', osvezi);
    // Promena vrste u formi može da sakrije ili prikaže sekcije.
    document.addEventListener('change', function () { setTimeout(osvezi, 0); });
    osvezi();
    setTimeout(osvezi, 300);
    window.addEventListener('load', osvezi);

    // Uputstvo: uputstva sekcija u prozor; bez ijednog uputstva dugme se ne prikazuje.
    var manualBody = document.getElementById('ef-manual-body');
    var manualButton = document.getElementById('ef-manual-button');
    if (manualBody) {
      Array.prototype.forEach.call(document.querySelectorAll('.ef-help[data-ef-help-title]'), function (help) {
        var naslov = document.createElement('h6');
        naslov.className = 'mt-3';
        naslov.textContent = help.getAttribute('data-ef-help-title');
        var tekst = document.createElement('p');
        tekst.className = 'mb-0';
        tekst.textContent = help.textContent.trim();
        manualBody.appendChild(naslov);
        manualBody.appendChild(tekst);
      });
      if (manualButton && !manualBody.textContent.trim()) manualButton.hidden = true;
    }

    var greska = document.querySelector('.ef-section.has-errors');
    if (greska) greska.scrollIntoView({block: 'start'});
    Array.prototype.forEach.call(document.querySelectorAll('.ef-predlog'), function (polje) {
      polje.addEventListener('input', function () { polje.classList.remove('ef-predlog'); });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
}());
