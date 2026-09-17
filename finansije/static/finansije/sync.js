(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('FinanceSyncForm');
    if (!form || !window.fetch) return;
    var button = form.querySelector('button[type="submit"]');
    var scope = form.querySelector('select');
    var result = document.getElementById('FinanceSyncResult');
    var caption = button.querySelector('span');
    var running = false;

    function show(message, style) {
      result.textContent = message;
      result.className = 'alert alert-' + style + ' mt-3 mb-0';
    }
    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      if (running) return;
      var data = new FormData(form);
      running = true;
      button.disabled = scope.disabled = true;
      form.setAttribute('aria-busy', 'true');
      caption.textContent = 'Sinhronizacija je u toku…';
      show('Preuzimanje i provera podataka su u toku. Sačekajte završetak.', 'info');
      try {
        var response = await fetch(form.action, {
          method: 'POST', body: data, credentials: 'same-origin',
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (response.redirected || !(response.headers.get('content-type') || '').includes('application/json')) {
          throw new Error('Unexpected response');
        }
        var payload = await response.json();
        show(payload.message, payload.status === 'success' ? 'success' : payload.status === 'busy' ? 'warning' : 'danger');
      } catch (error) {
        show('Nije moguće potvrditi ishod zahteva. Proverite istoriju sinhronizacije pre ponovnog pokretanja.', 'warning');
      } finally {
        running = false;
        button.disabled = scope.disabled = false;
        form.removeAttribute('aria-busy');
        caption.textContent = 'Pokreni sinhronizaciju';
        if (window.jQuery && jQuery.fn.DataTable && jQuery.fn.DataTable.isDataTable('#FinanceSyncTable')) {
          jQuery('#FinanceSyncTable').DataTable().ajax.reload(null, false);
        }
      }
    });
  });
}());
