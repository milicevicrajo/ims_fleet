/* Ugovor u stranoj valuti: ispod polja iznosa napomena da se iznos unosi u dinarima (fleet/forms/ugovor.py).
   Polje izbora ugovora nosi data-ugovor-valuta="<id polja iznosa>", a opcije data-currency. */
(function () {
  function osvezi(select) {
    var iznos = document.getElementById(select.getAttribute('data-ugovor-valuta'));
    if (!iznos) return;
    var opcija = select.options[select.selectedIndex];
    var valuta = opcija ? (opcija.getAttribute('data-currency') || 'RSD').toUpperCase() : 'RSD';
    var napomena = iznos.parentNode.querySelector('.ugovor-valuta-napomena');
    if (valuta === 'RSD') {
      if (napomena) napomena.remove();
      iznos.removeAttribute('placeholder');
      return;
    }
    if (!napomena) {
      napomena = document.createElement('div');
      napomena.className = 'alert alert-warning py-2 px-3 mt-2 mb-0 small ugovor-valuta-napomena';
      napomena.setAttribute('role', 'status');
      iznos.insertAdjacentElement('afterend', napomena);
    }
    napomena.textContent = 'Ugovor je u ' + valuta + '. Iznos unesite u dinarima (RSD), preračunat po kursu — obračun flote vodi iznose u dinarima.';
    iznos.setAttribute('placeholder', 'Iznos u RSD');
  }

  document.addEventListener('DOMContentLoaded', function () {
    var polja = document.querySelectorAll('select[data-ugovor-valuta]');
    polja.forEach(function (select) {
      select.addEventListener('change', function () { osvezi(select); });
      // Select2 javlja promenu kroz jQuery, koji ne okida obične osluškivače.
      if (window.jQuery) window.jQuery(select).on('change.ugovorValuta select2:select select2:clear', function () { osvezi(select); });
      osvezi(select);
    });
  });
})();
