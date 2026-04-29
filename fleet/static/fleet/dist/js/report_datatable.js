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
    pageLength: 25,
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
    let normalized = stripHtml(val)
      .replace(/\u00a0/g, ' ')
      .replace(/\s+/g, '')
      .replace(/[^\d,.-]/g, '')
      .trim();
    if (normalized === '' || normalized === '-') {
      return NaN;
    }

    const lastComma = normalized.lastIndexOf(',');
    const lastDot = normalized.lastIndexOf('.');

    if (lastComma !== -1 && lastDot !== -1) {
      const decimalSeparator = lastComma > lastDot ? ',' : '.';
      const thousandsSeparator = decimalSeparator === ',' ? '.' : ',';
      normalized = normalized
        .replace(new RegExp('\\' + thousandsSeparator, 'g'), '')
        .replace(decimalSeparator, '.');
    } else if (lastComma !== -1) {
      normalized = normalized.replace(/\./g, '').replace(',', '.');
    } else if (lastDot !== -1 && /^-?\d{1,3}(?:\.\d{3})+$/.test(normalized)) {
      normalized = normalized.replace(/\./g, '');
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

  function getColumnDecimals(headerCell) {
    if (!headerCell) {
      return null;
    }
    const value = headerCell.getAttribute('data-decimals');
    if (value == null || value === '') {
      return null;
    }
    const decimals = Number(value);
    return Number.isInteger(decimals) && decimals >= 0 ? decimals : null;
  }

  function formatSrNumber(num, decimals) {
    const formatOptions =
      Number.isInteger(decimals)
        ? {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
          }
        : {};
    return new Intl.NumberFormat('sr-RS', formatOptions).format(num);
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
    const decimalMap = new Map();

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
        const decimals = getColumnDecimals(th);
        if (decimals !== null) {
          decimalMap.set(idx, decimals);
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
            return formatSrNumber(num, decimalMap.get(idx));
          }
          return Number.isNaN(num) ? (data == null ? '' : stripHtml(data)) : num;
        }
      });
    });
    return defs;
  }

  function getHeaderCells(table) {
    const headerRow = table.querySelector('thead tr');
    return headerRow ? Array.from(headerRow.querySelectorAll('th')) : [];
  }

  function ensureSummaryFooter(table, options) {
    const hasSums = Array.isArray(options.sumColumns) && options.sumColumns.length;
    const hasAverages = Array.isArray(options.avgColumns) && options.avgColumns.length;
    if (!hasSums && !hasAverages) {
      return null;
    }

    const headerCells = getHeaderCells(table);
    if (!headerCells.length) {
      return null;
    }

    let footer = table.querySelector('tfoot[data-summary-footer="true"]');
    if (!footer) {
      footer = table.querySelector('tfoot') || document.createElement('tfoot');
      footer.innerHTML = '';
      footer.setAttribute('data-summary-footer', 'true');
      table.appendChild(footer);
    }

    function createRow(label) {
      const row = document.createElement('tr');
      for (let idx = 0; idx < headerCells.length; idx += 1) {
        const cell = document.createElement(idx === 0 ? 'th' : 'td');
        cell.textContent = idx === 0 ? label : '';
        if (idx > 0) {
          cell.className = 'text-end';
        }
        row.appendChild(cell);
      }
      footer.appendChild(row);
      return row;
    }

    if (hasSums && hasAverages) {
      createRow(options.summaryLabel || 'Sumarno / prosek');
    } else if (hasSums) {
      createRow(options.sumLabel || 'Sumarno');
    } else if (hasAverages) {
      createRow(options.avgLabel || 'Prosek');
    }
    return footer;
  }

  function updateSummaryFooter(dt, table, options) {
    const footer = table.querySelector('tfoot[data-summary-footer="true"]');
    if (!footer) {
      return;
    }

    const headerCells = getHeaderCells(table);
    const sumColumns = Array.isArray(options.sumColumns) ? options.sumColumns : [];
    const avgColumns = Array.isArray(options.avgColumns) ? options.avgColumns : [];
    const rows = dt.rows({ search: 'applied' }).data().toArray();
    const combinedSummary = sumColumns.length && avgColumns.length;

    function getStats(columnIndex) {
      let sum = 0;
      let count = 0;
      rows.forEach(function (row) {
        const value = Array.isArray(row) ? row[columnIndex] : row[columnIndex];
        const num = parseSrNumber(value);
        if (!Number.isNaN(num)) {
          sum += num;
          count += 1;
        }
      });
      return { sum: sum, count: count };
    }

    function decimalsFor(columnIndex) {
      return getColumnDecimals(headerCells[columnIndex]);
    }

    const footerRows = Array.from(footer.querySelectorAll('tr'));
    let rowIndex = 0;
    if (sumColumns.length && footerRows[rowIndex]) {
      sumColumns.forEach(function (columnIndex) {
        const cell = footerRows[rowIndex].children[columnIndex];
        if (!cell) {
          return;
        }
        cell.textContent = formatSrNumber(getStats(columnIndex).sum, decimalsFor(columnIndex));
      });
      if (!combinedSummary) {
        rowIndex += 1;
      }
    }
    if (avgColumns.length && footerRows[rowIndex]) {
      avgColumns.forEach(function (columnIndex) {
        const cell = footerRows[rowIndex].children[columnIndex];
        if (!cell) {
          return;
        }
        const stats = getStats(columnIndex);
        const avg = stats.count ? stats.sum / stats.count : 0;
        const formattedAvg = formatSrNumber(avg, decimalsFor(columnIndex));
        cell.textContent = combinedSummary && sumColumns.indexOf(columnIndex) !== -1
          ? cell.textContent + ' / ' + formattedAvg
          : formattedAvg;
      });
    }
  }

  function captureColumnWidths(dt) {
    const widths = [];
    dt.columns().every(function (idx) {
      const header = dt.column(idx).header();
      if (header && header.getBoundingClientRect) {
        widths[idx] = header.getBoundingClientRect().width;
      }
    });
    return widths;
  }

  function applyColumnWidths(dt, widths) {
    if (!widths || !widths.length) {
      return;
    }
    dt.columns().every(function (idx) {
      const w = widths[idx];
      if (!w) {
        return;
      }
      const header = dt.column(idx).header();
      if (header) {
        header.style.width = w + 'px';
      }
      const nodes = dt.column(idx).nodes().toArray();
      nodes.forEach(function (node) {
        if (node && node.style) {
          node.style.width = w + 'px';
        }
      });
    });
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
      ensureSummaryFooter(table, options);
      const layout = createButtonsConfig(options);
      let columnDefs = buildColumnDefs(table, filterRow, options);
      if (Array.isArray(options.columnDefs) && options.columnDefs.length) {
        columnDefs = columnDefs.concat(options.columnDefs);
      }

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
      updateSummaryFooter(dt, table, options);
      let fixedWidths = null;
      const refreshWidths = function (capture) {
        if (dt.columns && dt.columns.adjust) {
          dt.columns.adjust();
        }
        setTimeout(function () {
          if (!fixedWidths || capture) {
            fixedWidths = captureColumnWidths(dt);
          }
          applyColumnWidths(dt, fixedWidths);
        }, 0);
      };

      dt.on('draw', function () {
        updateSummaryFooter(dt, table, options);
        refreshWidths(false);
      });
      dt.on('page', function () {
        refreshWidths(false);
      });
      dt.on('column-visibility', function () {
        fixedWidths = null;
        refreshWidths(true);
      });
      dt.on('responsive-resize', function () {
        fixedWidths = null;
        refreshWidths(true);
      });
      dt.on('columns-reorder', function () {
        fixedWidths = null;
        refreshWidths(true);
      });
      window.addEventListener('resize', function () {
        fixedWidths = null;
        refreshWidths(true);
      });
      refreshWidths(true);
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
