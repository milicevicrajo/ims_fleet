(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('table[data-legal-table]').forEach(function (table) {
      // DataTables needs an empty tbody, not a placeholder row with colspan.
      table.querySelectorAll('tbody td[colspan]').forEach(function (cell) {cell.parentElement.remove();});
      function hints() {
        table.querySelectorAll('th, td').forEach(function (cell) {
          if (!cell.hasAttribute('title')) cell.title = cell.textContent.trim();
        });
      }
      if (window.jQuery) window.jQuery(table).on('draw.dt', hints);
      var initialize = window.ReportsDT || window.initFleetReportTable;
      if (initialize) initialize(table, {
        exportTitle: table.dataset.exportTitle,
        order: [[Number(table.dataset.orderColumn || 0), table.dataset.orderDirection || 'asc']],
        autoSelectThreshold: 25,
        scrollX: false,
        columnDefs: [{targets: -1, orderable: false}],
        language: {emptyTable: 'Nema postupaka za izabrane filtere.'}
      });
      hints();
    });
  });
})();
