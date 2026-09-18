(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    if (!window.fetch) return;
    document.querySelectorAll('.finance-sync-form[data-result]').forEach(function (form) {
      var button = form.querySelector('button[type="submit"]');
      var scope = form.querySelector('select');
      var result = document.getElementById(form.dataset.result);
      var history = '#' + form.dataset.history;
      var caption = button.querySelector('span');
      var originalCaption = caption.textContent;
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
        button.disabled = true;
        if (scope) scope.disabled = true;
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
          button.disabled = false;
          if (scope) scope.disabled = false;
          form.removeAttribute('aria-busy');
          caption.textContent = originalCaption;
          if (window.jQuery && jQuery.fn.DataTable && jQuery.fn.DataTable.isDataTable(history)) {
            jQuery(history).DataTable().ajax.reload(null, false);
          }
        }
      });
    });
  });
}());
