(function (window, document) {
  'use strict';

  if (window.initFleetReportTable) {
    return;
  }

  const DEFAULT_LANGUAGE = {
    decimal: ',',
    thousands: '.',
    search: 'Pretraga:',
    lengthMenu: 'Prikazi _MENU_ stavki po strani',
    info: 'Prikazano _START_ do _END_ od _TOTAL_ stavki',
    infoEmpty: 'Prikazano 0 do 0 od 0 stavki',
    infoFiltered: '(filtrirano od ukupno _MAX_ stavki)',
    loadingRecords: 'Ucitavanje...',
    zeroRecords: 'Nema pronadjenih podataka',
    emptyTable: 'Nema podataka u tabeli',
    paginate: {
      first: 'Prva',
      previous: 'Prethodna',
      next: 'Sledeca',
      last: 'Poslednja'
    },
    aria: {
      sortAscending: ': aktiviraj za sortiranje uzlazno',
      sortDescending: ': aktiviraj za sortiranje silazno'
    }
  };

  const DEFAULT_OPTIONS = {
    pageLength: 50,
    exportTitle: document.title || 'Izveštaj',
    autoSelectThreshold: 25,
    language: DEFAULT_LANGUAGE,
    scrollX: true
  };

  function mergeOptions(base, extra) {
    const out = Object.assign({}, base);
    if (!extra) {
      return out;
    }
    Object.keys(extra).forEach(function (key) {
      if (extra[key] && typeof extra[key] === 'object' && !Array.isArray(extra[key])) {
        out[key] = mergeOptions(out[key] || {}, extra[key]);
      } else {
        out[key] = extra[key];
      }
    });
    return out;
  }

  function parseSrNumber(val) {
    if (val == null || val === '') {
      return NaN;
    }
    const normalized = String(val)
      .replace(/\u00a0/g, ' ')
      .replace(/\s+/g, '')
      .replace(/\./g, '')
      .replace(',', '.')
      .trim();
    if (normalized === '') {
      return NaN;
    }
    const num = Number(normalized);
    return Number.isFinite(num) ? num : NaN;
  }

  function stripHtml(value) {
    if (value == null) {
      return '';
    }
    return String(value)
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<[^>]*>/g, '')
      .replace(/\u00a0/g, ' ')
      .replace(/&nbsp;/gi, ' ')
      .trim();
  }

  function isLikelyNumeric(text) {
    if (text == null) {
      return false;
    }
    const value = stripHtml(text).replace(/\s+/g, '');
    if (value === '') {
      return false;
    }
    return /^-?\d+(?:[.,]\d+)?$/.test(value) || /^-?\d{1,3}(?:\.\d{3})*(?:,\d+)?$/.test(value);
  }

  function ensureFilterRow(table) {
    const thead = table.querySelector('thead');
    if (!thead) {
      return null;
    }
    let filterRow = thead.querySelector('tr.filters');
    const headerRow = thead.querySelector('tr');
    if (!headerRow) {
      return null;
    }
    const columnCount = headerRow.children.length;

    if (!filterRow) {
      filterRow = document.createElement('tr');
      filterRow.className = 'filters';
      for (let i = 0; i < columnCount; i += 1) {
        filterRow.appendChild(document.createElement('th'));
      }
      thead.appendChild(filterRow);
    } else {
      // ensure correct number of cells
      while (filterRow.children.length < columnCount) {
        filterRow.appendChild(document.createElement('th'));
      }
      while (filterRow.children.length > columnCount) {
        filterRow.removeChild(filterRow.lastElementChild);
      }
    }
    return filterRow;
  }

  function createTextInput(placeholder) {
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control form-control-sm';
    input.placeholder = placeholder || '';
    return input;
  }

  function createSelectInput(options, placeholder) {
    const select = document.createElement('select');
    select.className = 'form-select form-select-sm';
    const emptyOption = document.createElement('option');
    emptyOption.value = '';
    emptyOption.textContent = placeholder || 'Sve';
    select.appendChild(emptyOption);
    options.forEach(function (opt) {
      const option = document.createElement('option');
      option.value = opt;
      option.textContent = opt;
      select.appendChild(option);
    });
    return select;
  }

  function applyFilters(dt, filterRow, options) {
    const escRe =
      (window.DataTable && DataTable.util && DataTable.util.escapeRegex) ||
      function (value) {
        return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      };

    const headerCells = [];
    const header = dt.table().header();
    if (header) {
      const firstRow = header.querySelector('tr');
      if (firstRow) {
        firstRow.querySelectorAll('th').forEach(function (th) {
          headerCells.push(th);
        });
      }
    }

    dt.columns().every(function (index) {
      const column = this;
      const cell = filterRow.children[index];
      if (!cell) {
        return;
      }
      cell.innerHTML = '';

      const headerCell = headerCells[index] || null;
      const filterAttr = headerCell ? headerCell.getAttribute('data-filter') : null;
      if (filterAttr === 'none') {
        return;
      }

      const colData = column.data().toArray().map(stripHtml).filter(Boolean);
      const uniqueValues = Array.from(new Set(colData)).sort(function (a, b) {
        return a.localeCompare(b, 'sr', { sensitivity: 'base' });
      });
      const forceSelect = filterAttr === 'select';
      const forceText = filterAttr === 'text';
      const shouldUseSelect =
        !forceText &&
        (forceSelect ||
          (uniqueValues.length > 1 &&
            uniqueValues.length <= (options.autoSelectThreshold || DEFAULT_OPTIONS.autoSelectThreshold)));

      if (shouldUseSelect) {
        const select = createSelectInput(uniqueValues, 'Sve');
        cell.appendChild(select);
        select.addEventListener('change', function () {
          const value = this.value;
          column.search(value ? '^' + escRe(value) + '$' : '', true, false).draw();
        });
      } else {
        const placeholder =
          (cell.getAttribute('data-placeholder') ||
            (headerCell && headerCell.getAttribute('data-placeholder'))) ||
          (headerCell ? headerCell.textContent.trim() : '');
        const input = createTextInput(placeholder);
        cell.appendChild(input);
        ['keyup', 'change', 'input'].forEach(function (eventName) {
          input.addEventListener(eventName, function () {
            column.search(this.value).draw();
          });
        });
      }
    });
  }

  function createButtonsConfig(options) {
    if (!window.DataTable || !DataTable.Buttons) {
      return undefined;
    }

    const exportFileName =
      (options.exportFileName ||
        (options.exportTitle ? options.exportTitle.replace(/\s+/g, '_').toLowerCase() : 'izvestaj')) +
      '_' +
      new Date().toISOString().slice(0, 10);

    function formatExportCell(data) {
      if (data == null) {
        return '';
      }
      if (typeof data === 'number') {
        return data;
      }
      const text = stripHtml(data);
      if (text === '') {
        return '';
      }
      if (isLikelyNumeric(text)) {
        const num = parseSrNumber(text);
        if (!Number.isNaN(num)) {
          return num;
        }
      }
      return text;
    }

    return {
      topStart: {
        buttons: [
          {
            extend: 'csvHtml5',
            text: 'CSV',
            title: options.exportTitle || DEFAULT_OPTIONS.exportTitle,
            filename: exportFileName,
            exportOptions: {
              columns: ':visible',
              format: {
                body: formatExportCell
              }
            }
          },
          {
            extend: 'excelHtml5',
            text: 'Excel',
            title: options.exportTitle || DEFAULT_OPTIONS.exportTitle,
            filename: exportFileName,
            exportOptions: {
              columns: ':visible',
              format: {
                body: formatExportCell
              }
            }
          },
          'print',
          'colvis'
        ]
      }
    };
  }

  function buildColumnDefs(table, filterRow, options) {
    if (!filterRow) {
      return [];
    }
    const defs = [];
    const numericSet = new Set();

    if (options.numericColumns && Array.isArray(options.numericColumns)) {
      options.numericColumns.forEach(function (idx) {
        if (Number.isInteger(idx)) {
          numericSet.add(idx);
        }
      });
    }

    const headerRow = table.querySelector('thead tr');
    if (headerRow) {
      headerRow.querySelectorAll('th').forEach(function (th, idx) {
        const typeAttr = th.getAttribute('data-type');
        if (typeAttr === 'numeric' || typeAttr === 'number') {
          numericSet.add(idx);
        }
      });
    }

    numericSet.forEach(function (idx) {
      defs.push({
        targets: idx,
        className: 'text-end',
        render: function (data, type) {
          const num = parseSrNumber(data);
          if (type === 'display') {
            if (Number.isNaN(num)) {
              return data == null ? '' : stripHtml(data);
            }
            return new Intl.NumberFormat('sr-RS').format(num);
          }
          return Number.isNaN(num) ? (data == null ? '' : stripHtml(data)) : num;
        }
      });
    });
    return defs;
  }

  function initFleetReportTable(selector, userOptions) {
    const table =
      typeof selector === 'string'
        ? document.querySelector(selector)
        : selector instanceof HTMLElement
          ? selector
          : null;
    if (!table) {
      return;
    }

    const start = function () {
      if (typeof DataTable === 'undefined') {
        setTimeout(start, 50);
        return;
      }
      if (DataTable.isDataTable && DataTable.isDataTable(table)) {
        return;
      }

      const options = mergeOptions(DEFAULT_OPTIONS, userOptions || {});
      const filterRow = ensureFilterRow(table);
      const layout = createButtonsConfig(options);
      const columnDefs = buildColumnDefs(table, filterRow, options);

      const dt = new DataTable(table, {
        language: options.language,
        pageLength: options.pageLength,
        order: options.order || [],
        autoWidth: false,
        scrollX: options.scrollX,
        layout: layout,
        orderCellsTop: true,
        columnDefs: columnDefs,
        retrieve: false,
        deferRender: true
      });

      applyFilters(dt, filterRow, options);
    };

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', start);
    } else {
      start();
    }
  }

  window.initFleetReportTable = initFleetReportTable;
  window.ReportsDT = initFleetReportTable;
})(window, document);
