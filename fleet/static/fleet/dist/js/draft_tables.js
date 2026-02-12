(function (window, document) {
  'use strict';

  function hasElement(selector) {
    return !!document.querySelector(selector);
  }

  function applyHoverTitles(tableSelector) {
    const table = document.querySelector(tableSelector);
    if (!table) {
      return;
    }

    const bodyRows = table.querySelectorAll('tbody tr');
    bodyRows.forEach(function (row) {
      const cells = row.querySelectorAll('td');
      cells.forEach(function (cell, idx) {
        if (idx === cells.length - 1) {
          return;
        }
        const text = (cell.textContent || '').trim();
        if (!text) {
          cell.removeAttribute('title');
          return;
        }
        cell.setAttribute('title', text);
      });
    });
  }

  function injectDraftTableStyles() {
    if (document.getElementById('draft-fixed-table-style')) {
      return;
    }

    const style = document.createElement('style');
    style.id = 'draft-fixed-table-style';
    style.textContent = [
      '.draft-fixed-table { table-layout: fixed; }',
      '.draft-fixed-table tbody td { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }',
      '.draft-fixed-table tbody td:last-child { white-space: nowrap; overflow: visible; text-overflow: initial; }'
    ].join('\n');

    document.head.appendChild(style);
  }

  function initOne(selector, options) {
    if (!hasElement(selector) || !window.ReportsDT) {
      return;
    }

    window.ReportsDT(selector, options);

    const tableEl = document.querySelector(selector);
    if (tableEl) {
      tableEl.classList.add('draft-fixed-table');
    }

    applyHoverTitles(selector);

    if (window.DataTable && DataTable.isDataTable && DataTable.isDataTable(selector)) {
      const dt = new DataTable(selector);
      dt.on('draw', function () {
        applyHoverTitles(selector);
      });
    }
  }

  function initDraftTables() {
    injectDraftTableStyles();

    initOne('#DraftServiceTransactionsTable', {
      exportTitle: 'Nedovršeni servisi',
      order: [[6, 'asc']],
      autoSelectThreshold: 20,
      scrollX: false,
      fixedColumnWidths: true,
      columnWidths: [500, 130, 120, 110, 300, 80, 120, 100, 100]
    });

    initOne('#DatatableTrebovanjaDraft', {
      exportTitle: 'Nedovrsena trebovanja',
      order: [[3, 'desc']],
      numericColumns: [5],
      autoSelectThreshold: 20,
      scrollX: false,
      fixedColumnWidths: true,
      columnWidths: [170, 90, 140, 120, 500, 100, 90]
    });

    initOne('#DraftPolicyTable', {
      exportTitle: 'Nedovrsene polise',
      order: [[5, 'desc']],
      autoSelectThreshold: 20,
      scrollX: false,
      fixedColumnWidths: true,
      columnWidths: [170, 120, 170, 120, 120, 120, 130, 130, 110, 120, 120, 120, 120, 90, 90]
    });

    initOne('#DraftInsuranceTable', {
      exportTitle: 'Nedovrsena osiguranja',
      order: [[1, 'asc']],
      autoSelectThreshold: 20,
      scrollX: false,
      fixedColumnWidths: true,
      columnWidths: [170, 90, 110, 130, 100, 100, 120, 160, 110, 200, 90]
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDraftTables);
  } else {
    initDraftTables();
  }
})(window, document);
