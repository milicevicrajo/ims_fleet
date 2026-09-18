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
  $(function () {
    var language = {search:'Pretraga:',lengthMenu:'Prikaži _MENU_ redova',info:'_START_–_END_ od _TOTAL_',infoEmpty:'Nema redova',zeroRecords:'Nema odgovarajućih podataka',emptyTable:'Nema podataka za ovaj obuhvat',processing:'Učitavanje…',paginate:{first:'Prva',last:'Poslednja',next:'Sledeća',previous:'Prethodna'}};
    $('.collections-table').each(function () {
      var table = $(this), columns = table.find('thead th').map(function (i) {return {data:i,render:renderCell};}).get();
      var orders={contacts:[1,'asc'],activities:[2,'desc'],notices:[4,'desc'],legal:[2,'asc'],directory:[0,'asc']};
      ['calls','notes'].forEach(function(k){orders[k]=orders.activities;});
      ['reminders','letters','claims'].forEach(function(k){orders[k]=orders.notices;});
      if (['contacts','activities','notices','legal','calls','notes','reminders','letters','claims'].indexOf(table.data('kind'))>=0) columns[columns.length-1].orderable=false;
      table.DataTable({serverSide:true,processing:true,pageLength:100,lengthMenu:[25,50,100,250,500],scrollX:true,autoWidth:false,
        order:[orders[table.data('kind')] || [columns.length-1,'desc']],language:language,columns:columns,
        ajax:{url:table.data('url'),data:function (d) {
          d.kind=table.data('kind');d.snapshot=table.data('snapshot');d.partner=table.data('partner');d.center=table.data('center');
          var params=new URLSearchParams(window.location.search);
          ['job','type','year','archived','review'].forEach(function(key){if(params.has(key)) d[key]=params.get(key);});
        },error:function () {table.closest('.table-responsive').find('.collections-error').remove();table.closest('.table-responsive').prepend('<p class="collections-error text-danger" role="alert">Podaci nisu učitani. Osvežite stranicu i proverite pristup.</p>');}}
      });
    });
    $('.collections-static').each(function () {$(this).DataTable({pageLength:100,lengthMenu:[25,50,100,250],language:language,order:[]});});
    $('button[data-bs-toggle="tab"]').on('shown.bs.tab',function () {$.fn.dataTable.tables({visible:true,api:true}).columns.adjust();});
    $('.collections-sync-form').on('submit',function () {$(this).find('button').prop('disabled',true).text('Sinhronizacija je u toku…');});
    $(document).on('change','.collections-review',function(){
      var input=$(this);input.prop('disabled',true);
      $.ajax({url:input.data('url'),method:'POST',data:{csrfmiddlewaretoken:$('.collections-csrf input').val(),value:input.prop('checked')?'1':'0',version:input.attr('data-version')}})
        .fail(function(xhr){$('.collections-feedback').removeClass('d-none').text((xhr.responseJSON||{}).error||'Oznaka nije sačuvana. Proverite pristup.');})
        .always(function(){ $('.collections-table').each(function(){$(this).DataTable().ajax.reload(null,false);}); });
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
    $('.collections-export').on('click',function(){var table=$('.collections-table').first();if(table.length){var url=new URL(this.href,window.location.origin);url.searchParams.set('q',table.DataTable().search());this.href=url.toString();}});
  });
})();
