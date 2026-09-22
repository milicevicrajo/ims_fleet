(function () {
  'use strict';
  function escape(value) { return $('<div>').text(value == null ? '' : String(value)).html(); }
  function renderCell(cell, type) {
    if (type !== 'display') return cell.sort;
    var value = escape(cell.display);
    if (cell.actions) return cell.actions.map(function(a){return '<a class="btn btn-sm btn-outline-primary me-1" href="'+escape(a.url)+'">'+escape(a.label)+'</a>';}).join('');
    if (cell.review) return value+'<label class="form-check form-switch mt-1"><input type="checkbox" class="form-check-input collections-review" data-url="'+escape(cell.review.url)+'" data-version="'+escape(cell.review.version)+'" '+(cell.review.checked?'checked':'')+'> Za proveru</label>';
    if (cell.kind === 'money') {
      var tone = [1,2,3,4,5].indexOf(cell.tone) >= 0 ? cell.tone : 3;
      var cls = Number(cell.sort) === 0 ? 'receivable-zero' : 'receivable-tone-' + tone;
      return '<span class="receivable-amount ' + cls + '">' + value + '</span>';
    }
    if (cell.url) return '<a class="btn btn-sm btn-outline-primary collections-link" href="' + escape(cell.url) + '">' + value + ' <i class="mdi mdi-arrow-right" aria-hidden="true"></i></a>';
    return value;
  }
  var simpleMoney = new Intl.NumberFormat('sr-RS');
  function renderSimpleCell(cell, type) {
    if (type !== 'display') return cell.sort;
    if (cell.actions) return cell.actions.map(function(action) {
      return '<a class="me-2" href="' + escape(action.url) + '">' + escape(action.label) + '</a>';
    }).join(' ');
    var value = escape(cell.display);
    if (cell.review) return '<span class="collections-cell-text">' + value + '</span><label class="collections-simple-review"><input type="checkbox" class="collections-review" data-url="' + escape(cell.review.url) + '" data-version="' + escape(cell.review.version) + '" ' + (cell.review.checked ? 'checked' : '') + '> Za proveru</label>';
    if (cell.kind === 'money' && cell.sort !== '') return simpleMoney.format(Number(cell.sort));
    if (cell.url) return '<a class="collections-cell-text" href="' + escape(cell.url) + '">' + value + '</a>';
    return '<span class="collections-cell-text">' + value + '</span>';
  }
  $(function () {
    var partnerPage = $('.collections-partners');
    function setPresentation(mode) {
      mode = mode === 'pretty' ? 'pretty' : 'basic';
      partnerPage.toggleClass('collections-basic', mode === 'basic');
      partnerPage.find('[data-collections-presentation]').each(function () {
        var selected = this.getAttribute('data-collections-presentation') === mode;
        $(this).toggleClass('btn-primary', selected).toggleClass('btn-outline-primary', !selected).attr('aria-pressed', String(selected));
      });
      partnerPage.find('.collections-table, #DugovanjaBuketi').each(function () {
        if ($.fn.dataTable.isDataTable(this)) $(this).DataTable().columns.adjust();
      });
    }
    if (partnerPage.length) {
      var savedPresentation = 'basic';
      try { savedPresentation = localStorage.getItem('ims.collections.partners.presentation') || 'basic'; } catch (_) {}
      setPresentation(savedPresentation);
      partnerPage.find('[data-collections-presentation]').on('click', function () {
        var mode = this.getAttribute('data-collections-presentation');
        setPresentation(mode);
        try { localStorage.setItem('ims.collections.partners.presentation', mode); } catch (_) {}
      });
    }
    var language = {search:'Pretraga:',lengthMenu:'Prikaži _MENU_ redova',info:'_START_–_END_ od _TOTAL_',infoEmpty:'Nema redova',zeroRecords:'Nema odgovarajućih podataka',emptyTable:'Nema podataka za ovaj obuhvat',processing:'Učitavanje…',paginate:{first:'Prva',last:'Poslednja',next:'Sledeća',previous:'Prethodna'}};
    $('.collections-table').each(function () {
      var table = $(this), simple = table.hasClass('collections-simple-table');
      var columns = table.find('thead th').map(function () {return {data:Number(this.getAttribute('data-column')),render:simple ? renderSimpleCell : renderCell,
        createdCell:function(td, cell){
          if(cell.kind === 'money') $(td).addClass('collections-money');
          td.title = cell.actions ? cell.actions.map(function(action){return action.label;}).join(' · ') : String(cell.display == null ? '' : cell.display);
        }};}).get();
      var orders={contacts:[1,'asc'],activities:[2,'desc'],notices:[4,'desc'],legal:[2,'asc'],directory:[0,'asc'],debts:[4,'asc'],buckets:[1,'asc']};
      ['calls','notes'].forEach(function(k){orders[k]=orders.activities;});
      ['reminders','letters','claims'].forEach(function(k){orders[k]=orders.notices;});
      if (['contacts','activities','notices','legal','calls','notes','reminders','letters','claims'].indexOf(table.data('kind'))>=0) columns[columns.length-1].orderable=false;
      var sourceOrder = orders[table.data('kind')] || [Math.max.apply(null, columns.map(function(column){return column.data;})), 'desc'];
      var order = [columns.findIndex(function(column){return column.data === sourceOrder[0];}), sourceOrder[1]];
      if (order[0] < 0) order = [0,'asc'];
      var defaults = simple ? window.imsDebtTableDefaults() : {pageLength:100,lengthMenu:[25,50,100,250,500],autoWidth:false,language:language};
      table.DataTable($.extend(true, defaults, {serverSide:true,processing:true,scrollX:!simple,
        order:simple ? [[0,'asc']] : [order],columns:columns,
        ajax:{url:table.data('url'),data:function (d) {
          d.kind=table.data('kind');d.snapshot=table.data('snapshot');d.partner=table.data('partner');d.center=table.data('center');
          // The endpoint sorts the original row; detail tables omit partner columns.
          d.order.forEach(function(order){order.column=columns[order.column].data;});
          var params=new URLSearchParams(window.location.search);
          ['job','type','year','archived','review'].forEach(function(key){if(params.has(key)) d[key]=params.get(key);});
        },error:function () {table.closest('.table-responsive').find('.collections-error').remove();table.closest('.table-responsive').prepend('<p class="collections-error text-danger" role="alert">Podaci nisu učitani. Osvežite stranicu i proverite pristup.</p>');}}
      }));
    });
    $('.collections-static').each(function () {$(this).DataTable(window.imsDebtTableDefaults());});
    function textHints(root) {
      $(root).find('th, td').each(function(){
        if (!this.hasAttribute('title')) this.title = this.textContent.trim();
        $(this).find('a, button, label').each(function(){if (!this.hasAttribute('title')) this.title = this.textContent.trim();});
      });
    }
    textHints($('.collections-page'));
    $('.collections-page table').on('draw.dt', function(){textHints(this);});
    $('button[data-bs-toggle="tab"]').on('shown.bs.tab',function () {$.fn.dataTable.tables({visible:true,api:true}).columns.adjust();});
    $('.collections-sync-form').on('submit',function () {$(this).find('button').prop('disabled',true).text('Sinhronizacija je u toku…');});
    $(document).on('change','.collections-review',function(){
      var input=$(this);input.prop('disabled',true);
      $.ajax({url:input.data('url'),method:'POST',data:{csrfmiddlewaretoken:$('.collections-csrf input').val(),value:input.prop('checked')?'1':'0',version:input.attr('data-version')}})
        .done(function(result){
          var checks=$('.collections-review');
          if ($.fn.dataTable.isDataTable('#DugovanjaBuketi')) checks=checks.add($('#DugovanjaBuketi').DataTable().$('.collections-review'));
          checks.filter(function(){return this.getAttribute('data-url')===input.attr('data-url');})
            .attr('data-version',result.version).prop('checked',input.prop('checked')).prop('defaultChecked',input.prop('checked'));
        })
        .fail(function(xhr){input.prop('checked',input.prop('defaultChecked'));$('.collections-feedback').removeClass('d-none').text((xhr.responseJSON||{}).error||'Oznaka nije sačuvana. Proverite pristup.');if(xhr.status===409 && input.closest('#DugovanjaBuketi').length) window.location.reload();})
        .always(function(){input.prop('disabled',false);$('.collections-table').each(function(){$(this).DataTable().ajax.reload(null,false);});});
    });
    var form=$('.collections-record-form'),partner=form.find('.collection-partner-select');
    if (partner.length && $.fn.select2) partner.select2({width:'100%',placeholder:'Pretraži naziv, šifru ili PIB',minimumInputLength:1,
      ajax:{url:form.data('partners-url'),dataType:'json',delay:250,data:function(p){return {q:p.term};},processResults:function(data){return data;}}});
    partner.on('change',function(){
      var contact=form.find('#id_contact');if(!contact.length)return;
      contact.empty().append(new Option('---------',''));
      $.getJSON(form.data('contacts-url'),{partner:partner.val()},function(data){data.results.forEach(function(row){contact.append(new Option(row.text,row.id));});});
    });
    $('.collections-add-row').on('click',function(){
      var total=$('#id_items-TOTAL_FORMS'),index=Number(total.val()),max=Number($('#id_items-MAX_NUM_FORMS').val());
      if(index>=max)return;
      $('.collections-formset').append($('#collection-empty-form').html().replace(/__prefix__/g,index));total.val(index+1);
    });
    $('.collections-export').on('click',function(){var table=$('#DugovanjaBuketi:visible');if(!table.length)table=$('.collections-table').first();if(table.length){var url=new URL(this.href,window.location.origin);url.searchParams.set('q',table.DataTable().search());this.href=url.toString();}});
  });
})();
