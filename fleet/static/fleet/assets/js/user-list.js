document.addEventListener('DOMContentLoaded', function () {
  const $ = window.jQuery;
  if (!$ || !$.fn.DataTable) return;
  const language = {
    lengthMenu: '_MENU_ po strani', info: '_START_–_END_ od _TOTAL_ naloga',
    infoEmpty: 'Nema naloga za prikaz', infoFiltered: '(ukupno _MAX_)',
    zeroRecords: 'Nema korisnika koji odgovaraju izabranim filterima.', emptyTable: 'Nema korisnika.',
    paginate: {first:'Prva', last:'Poslednja', next:'Sledeća', previous:'Prethodna'}
  };
  const options = {
    autoWidth:false, pageLength:25, lengthMenu:[10,25,50,100], order:[[0,'asc']],
    dom:'t<"users-table-footer"lip>', language:language,
    columnDefs:[{targets:'users-actions-heading',orderable:false,searchable:false}]
  };
  const table = $('#UsersTable').DataTable(options);
  const search = document.getElementById('users-search');
  const role = document.getElementById('users-role');
  const status = document.getElementById('users-status');
  let quick = 'all';
  $.fn.dataTable.ext.search.push(function (settings, data, index) {
    if (settings.nTable.id !== 'UsersTable') return true;
    const row = settings.aoData[index].nTr.dataset;
    if (role.value && !row.roles.trim().split(/\s+/).includes(role.value)) return false;
    if (status.value && row.status !== status.value) return false;
    return quick === 'all' || row[quick] === '1';
  });
  function setQuick(value) {
    quick = value;
    document.querySelectorAll('[data-user-filter]').forEach(button => {
      const active = button.dataset.userFilter === quick;
      button.classList.toggle('is-selected',active); button.setAttribute('aria-pressed',String(active));
    });
  }
  search.addEventListener('input', () => table.search(search.value).draw());
  role.addEventListener('change', () => table.draw());
  status.addEventListener('change', () => table.draw());
  document.querySelectorAll('[data-user-filter]').forEach(button => button.addEventListener('click', () => {
    setQuick(button.dataset.userFilter); table.draw();
  }));
  document.getElementById('users-reset').addEventListener('click', () => {
    search.value=''; role.value=''; status.value=''; setQuick('all'); table.search('').draw();
  });
  let employees;
  if (document.getElementById('EmployeesWithoutProfileTable')) {
    employees = $('#EmployeesWithoutProfileTable').DataTable({
      ...options, columnDefs:[{targets:-1,orderable:false}],
      language:{...language,info:'_START_–_END_ od _TOTAL_ zaposlenih',infoEmpty:'Nema zaposlenih za prikaz',zeroRecords:'Nema zaposlenih koji odgovaraju pretrazi.'}
    });
    document.getElementById('employees-search').addEventListener('input', event => employees.search(event.target.value).draw());
  }
  document.querySelectorAll('[data-bs-toggle="tab"]').forEach(button => button.addEventListener('shown.bs.tab', () => {
    table.columns.adjust(); if (employees) employees.columns.adjust();
  }));
  const modal = document.getElementById('linkUserModal');
  if (modal) modal.addEventListener('show.bs.modal', event => {
    document.getElementById('link-user-id').value = event.relatedTarget.dataset.userId;
    document.getElementById('link-username').textContent = event.relatedTarget.dataset.username;
    $('#link-employee').val('').trigger('change');
  });
});
