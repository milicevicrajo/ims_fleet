/* Ispod svakog polja kilometraže sa oznakom data-km-url ispisuje poslednju očitanu kilometražu
   vozila (do datuma unosa) i upozorava kada je uneta manja ili nerealno veća. Ne sprečava čuvanje.
   Oznake dodaje fleet/forms/kilometraza.py: oznaci_kilometrazu(). */
(function () {
  function hiljade(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }
  function polje(id) { return id ? document.getElementById(id) : null; }

  function pripremi(unos) {
    var voziloPolje = polje(unos.getAttribute('data-km-vozilo-polje'));
    var datumPolje = polje(unos.getAttribute('data-km-datum-polje'));
    var napomena = document.createElement('div');
    napomena.className = 'form-text km-napomena';
    var upozorenje = document.createElement('div');
    upozorenje.className = 'km-upozorenje';
    upozorenje.style.cssText = 'display:none;color:#7a4d00;background:#fff8e6;border:1px solid #f1d28d;border-radius:6px;padding:4px 8px;margin-top:4px;font-size:.85rem;';
    var sidro = unos.parentNode;
    sidro.insertBefore(upozorenje, unos.nextSibling);
    sidro.insertBefore(napomena, unos.nextSibling);
    var poslednja = null, pravilo = null, dan = null, zahtev = 0;

    function proveri() {
      var vrednost = parseInt(unos.value, 10), poruka = '';
      if (poslednja && pravilo && !isNaN(vrednost) && vrednost > 0) {
        var dana = Math.max(Math.round((new Date(dan) - new Date(poslednja.datum_iso)) / 86400000), 1);
        var dozvoljeno = Math.max(pravilo.najmanji_skok, dana * pravilo.km_dnevno);
        if (vrednost < poslednja.km) { poruka = 'Uneta kilometraža je manja od poslednje očitane (' + hiljade(poslednja.km) + ' km) — proverite.'; }
        else if (vrednost - poslednja.km > dozvoljeno) { poruka = 'Uneta kilometraža je za ' + hiljade(vrednost - poslednja.km) + ' km veća od poslednje očitane — proverite.'; }
      }
      upozorenje.textContent = poruka;
      upozorenje.style.display = poruka ? '' : 'none';
    }
    function ucitaj() {
      var vozilo = unos.getAttribute('data-km-vozilo') || (voziloPolje && voziloPolje.value);
      if (!vozilo) { napomena.textContent = ''; poslednja = null; proveri(); return; }
      var url = unos.getAttribute('data-km-url') + '?vozilo=' + encodeURIComponent(vozilo) +
                (datumPolje && datumPolje.value ? '&datum=' + encodeURIComponent(datumPolje.value) : '');
      var broj = ++zahtev;
      fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' })
        .then(function (r) { return r.ok ? r.json() : {}; })
        .then(function (d) {
          if (broj !== zahtev) return;
          poslednja = d.kilometraza || null; pravilo = d.pravilo || null; dan = d.dan || null;
          napomena.textContent = poslednja
            ? 'Poslednja očitana kilometraža: ' + hiljade(poslednja.km) + ' km (' + poslednja.datum + ', ' + poslednja.izvor + ').'
            : (d.dan ? 'Za ovo vozilo nema ranijih očitavanja brojila.' : '');
          proveri();
        })
        .catch(function () {});
    }
    unos.addEventListener('input', proveri);
    [voziloPolje, datumPolje].forEach(function (p) {
      if (!p) return;
      p.addEventListener('change', ucitaj);
      if (window.jQuery) { window.jQuery(p).on('change select2:select', ucitaj); }
    });
    ucitaj();
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('input[data-km-url]').forEach(pripremi);
  });
})();
