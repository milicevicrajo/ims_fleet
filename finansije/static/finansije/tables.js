(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    if (!window.jQuery || !jQuery.fn.DataTable) return;
    // Only raw numeric values (JSON sort / data-order), never formatted badge text.
    // Missing amounts stay after known amounts in both ordering directions.
    function signedNumber(value) {
      if (value && typeof value === 'object') value = value.sort;
      if (value == null || String(value).trim() === '') return null;
      var number = Number(value);
      return Number.isFinite(number) ? number : null;
    }
    function compareSigned(left, right, direction) {
      var a = signedNumber(left), b = signedNumber(right);
      if (a === null) return b === null ? 0 : 1;
      if (b === null) return -1;
      return direction * (a < b ? -1 : a > b ? 1 : 0);
    }
    jQuery.fn.dataTable.ext.type.order['finance-signed-asc'] = function (a, b) { return compareSigned(a, b, 1); };
    jQuery.fn.dataTable.ext.type.order['finance-signed-desc'] = function (a, b) { return compareSigned(a, b, -1); };
    function initialize() {
      var table = jQuery(this);
      if (jQuery.fn.DataTable.isDataTable(this)) return;
      var source = table.attr('data-source');
      var ajaxSource = table.attr('data-ajax-source');
      var options = {
        pageLength: table.attr('data-page-length') === '100' ? 100 : 50,
        lengthMenu: source ? [25, 50, 100, 200] : [[25, 50, 100, -1], [25, 50, 100, 'Sve']],
        autoWidth: false,
        deferRender: true,
        scrollX: true,
        order: [[0, table.attr('data-order-direction') || 'asc']],
        columnDefs: [
          { targets: 'no-sort', orderable: false, searchable: false },
          { targets: 'finance-number', type: 'finance-signed', className: 'text-end text-nowrap' },
          { targets: 'finance-date', className: 'text-nowrap' }
        ],
        language: {
          processing: 'Učitavanje…', search: 'Pretraga:',
          lengthMenu: 'Prikaži _MENU_ redova', info: 'Prikaz _START_–_END_ od _TOTAL_ redova',
          infoEmpty: 'Nema redova', infoFiltered: '(od ukupno _MAX_)',
          emptyTable: 'Nema podataka za izabrane filtere.', zeroRecords: 'Nema rezultata pretrage.',
          paginate: { first: 'Prva', last: 'Poslednja', next: 'Sledeća', previous: 'Prethodna' }
        }
      };
      if (ajaxSource) {
        options.processing = true;
        options.columnDefs.push({
          targets: '_all',
          render: function (data, type) {
            if (!data || typeof data !== 'object') return data;
            if (type === 'display') return data.display;
            if (type === 'filter') return data.filter;
            return data.sort;
          }
        });
        options.ajax = function (_data, callback) {
          var card = table.closest('.card-body');
          var errorBox = card.find('.finance-table-error');
          errorBox.addClass('d-none');
          jQuery.ajax({ url: ajaxSource, dataType: 'json', timeout: 60000 })
            .done(function (result) {
              if (!result || !Array.isArray(result.data)) {
                showError();
                return;
              }
              Object.keys(result.footer || {}).forEach(function (key) {
                card.find('[data-footer]').filter(function () {
                  return jQuery(this).attr('data-footer') === key;
                }).html(result.footer[key]);
              });
              callback(result);
            })
            .fail(showError);
          function showError() {
            errorBox.removeClass('d-none').find('.finance-table-error-text')
              .text('Tabela nije učitana. Pokušajte ponovo.');
            card.find('[data-footer]').text('—');
            callback({ data: [] });
          }
        };
      }
      if (source) {
        options.serverSide = true;
        options.processing = true;
        options.searchDelay = 350;
        options.ajax = function (data, callback) {
          var errorBox = table.closest('.card-body').find('.finance-table-error');
          errorBox.addClass('d-none');
          jQuery.ajax({ url: source, data: data, dataType: 'json' })
            .done(callback)
            .fail(function () {
              errorBox.removeClass('d-none').text('Tabela nije učitana. Osvežite stranicu i pokušajte ponovo.');
              callback({ draw: data.draw, recordsTotal: 0, recordsFiltered: 0, data: [] });
            });
        };
      }
      var dataTable = table.DataTable(options);
      table.closest('.card-body').find('.finance-table-retry').on('click', function () {
        dataTable.ajax.reload(null, false);
      });
      jQuery(window).on('resize.financeTables', function () { dataTable.columns.adjust(); });
    }
    var observer = 'IntersectionObserver' in window ? new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        initialize.call(entry.target);
      });
    }, { rootMargin: '250px' }) : null;
    var tabs = Array.from(document.querySelectorAll('.finance-job-nav [role="tab"]'));
    tabs.forEach(function (button, index) {
      button.addEventListener('shown.bs.tab', function () {
        tabs.forEach(function (tab) { tab.tabIndex = tab === button ? 0 : -1; });
        var panel = document.getElementById(button.getAttribute('aria-controls'));
        if (!panel) return;
        if (button.closest('[data-job-analysis-tabs]')) {
          var analysis = panel.id === 'jobs-additional' ? 'additional' : 'standard';
          document.getElementById('finance-analysis').value = analysis;
          document.querySelectorAll('[data-finance-section]').forEach(function (link) {
            var active = link.dataset.financeSection === (analysis === 'additional' ? 'additional' : 'jobs');
            link.classList.toggle('active', active);
            link.closest('li').classList.toggle('selected', active);
            if (active) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
          });
          document.querySelectorAll('[data-finance-jobs-export]').forEach(function (link) {
            var url = new URL(link.href);
            url.searchParams.set('analysis', analysis);
            link.href = url.toString();
          });
        }
        jQuery(panel).find('.finance-datatable').each(function () {
          initialize.call(this);
          jQuery(this).DataTable().columns.adjust();
        });
      });
      button.addEventListener('keydown', function (event) {
        var next;
        if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
        if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = tabs.length - 1;
        if (next !== undefined && window.bootstrap) {
          event.preventDefault();
          tabs[next].focus();
          (bootstrap.Tab.getInstance(tabs[next]) || new bootstrap.Tab(tabs[next])).show();
        }
      });
    });
    jQuery('.finance-datatable').each(function () {
      var panel = this.closest('.finance-job-panels > .tab-pane');
      if (panel) {
        if (this.dataset.lazyTab !== 'true' || panel.classList.contains('active')) initialize.call(this);
      }
      else if (observer && this.getAttribute('data-lazy') === 'true') observer.observe(this);
      else initialize.call(this);
    });
    var linkedTab = tabs.find(function (tab) { return '#' + tab.getAttribute('aria-controls') === window.location.hash; });
    if (linkedTab && window.bootstrap) (bootstrap.Tab.getInstance(linkedTab) || new bootstrap.Tab(linkedTab)).show();
    jQuery('.finance-shared-block[data-metrics-source]').each(function () {
      var block = jQuery(this);
      function connectMetrics(sourceAttr, metricAttr, noteAttr, errorSelector, errorMessage) {
        if (!block.attr(sourceAttr)) return;
        var errorBox = block.find(errorSelector);
        function loadMetrics() {
          errorBox.find('.finance-table-error').addClass('d-none');
          block.find('[' + metricAttr + ']').text('Učitavanje…');
          jQuery.ajax({ url: block.attr(sourceAttr), dataType: 'json', timeout: 60000 })
            .done(function (result) {
              if (!result || !result.metrics) { failed(); return; }
              block.find('[' + metricAttr + ']').each(function () {
                jQuery(this).html(result.metrics[jQuery(this).attr(metricAttr)] || 'Nema podataka');
              });
              block.find('[' + noteAttr + ']').text(result.note || '').toggleClass('alert alert-warning', result.complete === false);
            }).fail(failed);
        }
        function failed() {
          block.find('[' + metricAttr + ']').text('Nema podataka');
          block.find('[' + noteAttr + ']').text('').removeClass('alert alert-warning');
          errorBox.find('.finance-table-error').removeClass('d-none')
            .find('.finance-table-error-text').text(errorMessage);
        }
        errorBox.find('.finance-table-retry').on('click', loadMetrics);
        loadMetrics();
      }
      connectMetrics('data-metrics-source', 'data-metric', 'data-shared-note', '.finance-shared-error', 'Zajednički troškovi nisu učitani. Pokušajte ponovo.');
      connectMetrics('data-cash-source', 'data-cash-metric', 'data-cash-note', '.finance-cash-error', 'Novčani tokovi nisu učitani. Pokušajte ponovo.');
    });
  });
}());
