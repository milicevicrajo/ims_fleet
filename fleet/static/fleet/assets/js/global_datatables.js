        $(document).ready(function() {
            // Postavljanje lokalizacije na srpski


            // Ručna implementacija sortiranja datuma
            // Ako koristiš datetime-moment plugin, registruj format:
            if ($.fn.dataTable.moment) {
            $.fn.dataTable.moment('DD.MM.YYYY');
            $.fn.dataTable.moment('DD.MM.YYYY HH:mm:ss');
            }

            // Fallback custom tip (ako želiš eksplicitno da ga koristiš kroz "type":"date-custom")
            $.fn.dataTable.ext.type.order['date-custom-pre'] = function(date) {
            const m = moment(date, 'DD.MM.YYYY', true);
            return m.isValid() ? +m.toDate() : 0;
            };

    
            var languageSettings = {
                "decimal": ",",
                "thousands": ".",
                "search": "Pretraga:",
                "lengthMenu": "Prikaži _MENU_ stavki po strani",
                "info": "Prikazano _START_ do _END_ od _TOTAL_ stavki",
                "infoEmpty": "Prikazano 0 do 0 od 0 stavki",
                "infoFiltered": "(filtrirano od ukupno _MAX_ stavki)",
                "loadingRecords": "Učitavanje...",
                "zeroRecords": "Nema pronađenih podataka",
                "emptyTable": "Nema podataka u tabeli",
                "paginate": {
                    "first": "Prva",
                    "previous": "Prethodna",
                    "next": "Sledeća",
                    "last": "Poslednja"
                },
                "aria": {
                    "sortAscending": ": aktiviraj za sortiranje kolone uzlazno",
                    "sortDescending": ": aktiviraj za sortiranje kolone silazno"
                }
            };
    
            // Inicijalizacija DataTables sa prilagođenim formatom datuma
            var $defaultDatatable = $('#Datatable');
            if ($defaultDatatable.length && !$defaultDatatable.is('[data-reports-dt]')) {
                $defaultDatatable.DataTable({
                    "language": languageSettings,
                });
            }
            
            var $vozilaTable = $('#DatatableVozila');
            if ($vozilaTable.length && !$vozilaTable.is('[data-server-side-dt]') && !$.fn.DataTable.isDataTable($vozilaTable[0])) {
                $vozilaTable.DataTable({
                    "language": languageSettings,
                    "pageLength": 50,  // Postavlja podrazumevani broj redova
                });
            }
            var table = $('#DatatableSaobracajne').DataTable({
                "language": languageSettings,
                "columnDefs": [
                { "type": "date-custom", "targets": [2,3] }
                ]
            });
            var $leaseTable = $('#DatatableLease');
            if ($leaseTable.length && !$leaseTable.is('[data-server-side-dt]') && !$.fn.DataTable.isDataTable($leaseTable[0])) {
                $leaseTable.DataTable({
                    "language": languageSettings,
                    "columnDefs": [
                    { "type": "date-custom", "targets": [6,7] }
                    ]
                });
            }

            var table = $('#DatatablePolicy').DataTable({
                "language": languageSettings,
                "pageLength": 100, 
                autoWidth: false,     // DataTables da ne postavlja inline širine
                responsive: true,     // automatski prelama kolone ako je usko
                "columnDefs": [
                { "type": "date-custom", "targets": [] },
                ]
            });

            var table = $('#DatatablePolicyAgregat').DataTable({
                "language": languageSettings,
                "pageLength": 25, 
                autoWidth: false,     // DataTables da ne postavlja inline širine
                responsive: true,
                "order": [[0, "desc"]], 
            });

            var table = $('#DatatableFuel').DataTable({
                "language": languageSettings,
                "scrollX": true,  // Enable horizontal scrolling
                "autoWidth": false,  // Disable automatic column width calculation
                "columnDefs": [
                { "type": "date-custom", "targets": [1] }
                        ],
                "pageLength": 100,  // Postavlja podrazumevani broj redova
                "order": [[1, "desc"]],  // Sort by column 1 in descending order
                layout: {
                    topStart: {
                        buttons: [
                            'copy', 'excel', 'pdf'
                        ]
                    }
                },

            });
            var table = $('#DatatableEmployee').DataTable({
                "language": languageSettings,
                "scrollX": true,  // Enable horizontal scrolling
                "autoWidth": false,  // Disable automatic column width calculation
                "pageLength": 100,
                "columnDefs": [
                { "type": "date-custom", "targets": [5,6] }
                        ],

            });
            var table = $('#DatatableIncident').DataTable({
                "language": languageSettings,
                "scrollX": true,  // Enable horizontal scrolling
                "autoWidth": false,  // Disable automatic column width calculation
                "columnDefs": [
                { "type": "date-custom", "targets": [3] }
                        ],


            });
            var table = $('#DatatableNalozi').DataTable({
                "language": languageSettings,
                "scrollX": true,  // Enable horizontal scrolling
                "autoWidth": false,  // Disable automatic column width calculation
                "columnDefs": [
                { "type": "date-custom", "targets": [5] }
                        ],
                "order": [[5, "desc"]],  // Sort by column 1 in descending order
            });
            var table = $('#DatatableServisi').DataTable({
                "language": languageSettings,
                "scrollX": true,  // Enable horizontal scrolling
                "autoWidth": false,  // Disable automatic column width calculation
                "columnDefs": [
                { "type": "date-custom", "targets": [2] }
                        ],
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
                "pageLength": 50,  // Postavlja podrazumevani broj redova
                layout: {
                    topStart: {
                        buttons: [
                            'copy', 'excel', 'pdf'
                        ]
                    }
                },
            });
            var table = $('#DatatableTrebovanja').DataTable({
                "language": languageSettings,
                "scrollX": true,  // Enable horizontal scrolling
                "autoWidth": false,  // Disable automatic column width calculation
                "columnDefs": [
                { "type": "date-custom", "targets": [3] }
                        ],
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
                "pageLength": 50,  // Postavlja podrazumevani broj redova

            });
            var table = $('#DatatableFuelDetail').DataTable({
                "language": languageSettings,
                "scrollX": true,  // Enable horizontal scrolling
                "autoWidth": false,  // Disable automatic column width calculation
                "columnDefs": [
                { "type": "date-custom", "targets": [0] }
                        ],
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
                "pageLength": 10,  // Postavlja podrazumevani broj redova
                "order": [[0, "desc"]],
                layout: {
                    topStart: {
                        buttons: [
                            'copy', 'excel', 'pdf'
                        ]
                    }
                },
            });

            var table = $('#DatatableFuelMonth').DataTable({
                "language": languageSettings,

                "autoWidth": false,  // Disable automatic column width calculation
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
                "pageLength": 10,  // Postavlja podrazumevani broj redova
                "order": [[0, "desc"]],  // Sort by column 1 in descending order
                layout: {
                    topStart: {
                        buttons: [
                            'copy', 'excel', 'pdf'
                        ]
                    }
                },
            });
            var table = $('#DatatableFuelMonth2').DataTable({
                "language": languageSettings,

                "autoWidth": false,  // Disable automatic column width calculation
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
                "pageLength": 10,  // Postavlja podrazumevani broj redova
                layout: {
                    topStart: {
                        buttons: [
                            'copy', 'excel', 'pdf'
                        ]
                    }
                },
            });
            var table = $('#DatatableServiceDetail').DataTable({
                "language": languageSettings,

                "autoWidth": false,  // Disable automatic column width calculation
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
                "pageLength": 10,  // Postavlja podrazumevani broj redova
                "columnDefs": [
                { "type": "date-custom", "targets": [0] }
                        ],
                layout: {
                    topStart: {
                        buttons: [
                            'copy', 'excel', 'pdf'
                        ]
                    }
                },
            });
            var table = $('#DatatableRequisitionDetail').DataTable({
                "language": languageSettings,

                "autoWidth": false,  // Disable automatic column width calculation
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
                "pageLength": 10,  // Postavlja podrazumevani broj redova
                "columnDefs": [
                { "type": "date-custom", "targets": [0] }
                        ],
                layout: {
                    topStart: {
                        buttons: [
                            'copy', 'excel', 'pdf'
                        ]
                    }
                },
            });

            var table = $('#DatatablePolicyExpiring').DataTable({
                "language": languageSettings,

                "autoWidth": false,  // Disable automatic column width calculation
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
                "pageLength": 25,  // Postavlja podrazumevani broj redova
                "columnDefs": [
                { "type": "date-custom", "targets": [2,6,7] }
                        ],
                layout: {
                    topStart: {
                        buttons: [
                            'copy', 'excel', 'pdf'
                        ]
                    }
                },
            });

            var table = $('#DatatablePolicyExpired').DataTable({
                "language": languageSettings,

                "autoWidth": false,  // Disable automatic column width calculation
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
                "pageLength": 25,  // Postavlja podrazumevani broj redova
                "columnDefs": [
                { "type": "date-custom", "targets": [0] }
                        ],
                layout: {
                    topStart: {
                        buttons: [
                            'copy', 'excel', 'pdf'
                        ]
                    }
                },
            });
            var table = $('#DatatableCenterStat').DataTable({
                "language": languageSettings,

                "autoWidth": false,  // Disable automatic column width calculation
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
                "pageLength": 10,  // Postavlja podrazumevani broj redova
                layout: {
                    topStart: {
                        buttons: [
                            'copy', 'excel', 'pdf'
                        ]
                    }
                },
            });
        var table = $('#DatatableDraftInsurance').DataTable({
            "language": languageSettings,

            "autoWidth": false,  // Disable automatic column width calculation
            "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
            "pageLength": 25,  // Postavlja podrazumevani broj redova
            "columnDefs": [
            { "type": "date-custom", "targets": [0] }
                    ],
            layout: {
                topStart: {
                    buttons: [
                        'copy', 'excel', 'pdf'
                    ]
                }
            },
        });
            var table = $('#DatatableOrgUnits').DataTable({
                "language": languageSettings,
                "autoWidth": false,  // Disable automatic column width calculation
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],  // Definiše opcije za broj redova po stranici
                "pageLength": 25,  // Postavlja podrazumevani broj redova
            });



            


            //**************************************************************************************
            // Tabele za izvestaje NAPLATE sa servera sa sumama u footer-u
            //**************************************************************************************
            var table = $('#DugovanjaBuketi').DataTable({
                "language": languageSettings,
                "autoWidth": false,
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],
                "pageLength": 100,
                "columnDefs": [
                        { 
                            targets: 1,  // Kolona broj 2
                            width: "400px" // Postavi širinu kolone (možeš promeniti vrednost)
                        },
                        {
                            targets: [2, 3, 4, 5, 6, 7, 8, 9,10], // Indeksi kolona koje formatiramo
                            render: function (data, type, row) {
                                if (type === 'display') {
                                    return new Intl.NumberFormat('sr-RS').format(data);
                                }
                                return data;
                            }
                        }
                    ],
                "footerCallback": function(row, data, start, end, display) {
                    var api = this.api();

                    // Funkcija za sumiranje
                    var sumColumn = function(index) {
                        return api.column(index, { page: 'all' }).data().reduce(function(a, b) {
                            return (parseFloat(a) || 0) + (parseFloat(b) || 0);
                        }, 0).toLocaleString('sr-RS');
                    };

                    // Upisivanje suma u tfoot
                    $('#total_nedospelo').html(sumColumn(2));
                    $('#total_30').html(sumColumn(3));
                    $('#total_45').html(sumColumn(4));
                    $('#total_60').html(sumColumn(5));
                    $('#total_90').html(sumColumn(6));
                    $('#total_180').html(sumColumn(7));
                    $('#total_181').html(sumColumn(8));
                    $('#total_dospelo').html(sumColumn(9));   // Novo: DOSPELO
                    $('#total_ukupno').html(sumColumn(10));   // Pomerena kolona UKUPNO
                }
            });

            var table = $('#DugovanjaDetalj').DataTable({
                "language": languageSettings,
                "autoWidth": false,
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],
                "pageLength": 10,
                "columnDefs": [
                        {
                            targets: [8,9], // Indeksi kolona koje formatiramo
                            render: function (data, type, row) {
                                if (type === 'display') {
                                    return new Intl.NumberFormat('sr-RS').format(data);
                                }
                                return data;
                            }
                        }
                    ],
                "footerCallback": function(row, data, start, end, display) {
                    var api = this.api();
                    
                    // Funkcija za sumiranje
                    var sumColumn = function(index) {
                        return api.column(index, { page: 'all' }).data().reduce(function(a, b) {
                            return (parseFloat(a) || 0) + (parseFloat(b) || 0);
                        }, 0).toLocaleString('sr-RS'); // Formatiranje broja
                    };        
                }
            });

            var table = $('#DugovanjaBaketiDetalj').DataTable({
                "language": languageSettings,
                "autoWidth": false,
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],
                "pageLength": 10,
                "columnDefs": [
                    {
                        targets: [5, 6, 7], // Indeksi kolona: duguje, potražuje, saldo
                        render: function (data, type, row) {
                            if (type === 'display' && data !== null) {
                                return new Intl.NumberFormat('sr-RS').format(data);
                            }
                            return data;
                        }
                    },
                    { "type": "date-custom", "targets": [4] }  // Ako je dpo u 5. koloni
                ],

                "footerCallback": function (row, data, start, end, display) {
                    var api = this.api();
            
                    // Funkcija za sumu i zaobljavanje
                    var sumColumn = function(index) {
                        return api.column(index, { page: 'all' }).data().reduce(function (a, b) {
                            return (parseFloat(a) || 0) + (parseFloat(b) || 0);
                        }, 0);
                    };
            
                    // Postavi sume u footer
                    $(api.column(5).footer()).html(new Intl.NumberFormat('sr-RS').format(sumColumn(5))); // Duguje
                    $(api.column(6).footer()).html(new Intl.NumberFormat('sr-RS').format(sumColumn(6))); // Potražuje
                    $(api.column(7).footer()).html(new Intl.NumberFormat('sr-RS').format(sumColumn(7))); // Saldo
                }
            });
            

            var table = $('#DugovanjaDetaljFaktureTuzbe').DataTable({
                "language": languageSettings,
                "autoWidth": false,
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],
                "pageLength": 10,
                "columnDefs": [
                        {
                            targets: [3,4,5,6], // Indeksi kolona koje formatiramo
                            render: function (data, type, row) {
                                if (type === 'display') {
                                    return new Intl.NumberFormat('sr-RS').format(data);
                                }
                                return data;
                            }
                        }
                    ],
                "footerCallback": function(row, data, start, end, display) {
                    var api = this.api();
                    
                    // Funkcija za sumiranje
                    var sumColumn = function(index) {
                        return api.column(index, { page: 'all' }).data().reduce(function(a, b) {
                            return (parseFloat(a) || 0) + (parseFloat(b) || 0);
                        }, 0).toLocaleString('sr-RS'); // Formatiranje broja
                    };        
                }
            });
            var table = $('#DugovanjaDetaljFaktureOpomene').DataTable({
                "language": languageSettings,
                "autoWidth": false,
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],
                "pageLength": 10,
                "columnDefs": [
                        {
                            targets: [3,4,5,6], // Indeksi kolona koje formatiramo
                            render: function (data, type, row) {
                                if (type === 'display') {
                                    return new Intl.NumberFormat('sr-RS').format(data);
                                }
                                return data;
                            }
                        }
                    ],
                "footerCallback": function(row, data, start, end, display) {
                    var api = this.api();
                    
                    // Funkcija za sumiranje
                    var sumColumn = function(index) {
                        return api.column(index, { page: 'all' }).data().reduce(function(a, b) {
                            return (parseFloat(a) || 0) + (parseFloat(b) || 0);
                        }, 0).toLocaleString('sr-RS'); // Formatiranje broja
                    };        
                }
            });

            var table = $('#DugovanjaDetaljFaktureBaket90').DataTable({
                "language": languageSettings,
                "autoWidth": false,
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],
                "pageLength": 10,
                "columnDefs": [
                        {
                            targets: [3,4,5,6], // Indeksi kolona koje formatiramo
                            render: function (data, type, row) {
                                if (type === 'display') {
                                    return new Intl.NumberFormat('sr-RS').format(data);
                                }
                                return data;
                            }
                        }
                    ],
                "footerCallback": function(row, data, start, end, display) {
                    var api = this.api();
                    
                    // Funkcija za sumiranje
                    var sumColumn = function(index) {
                        return api.column(index, { page: 'all' }).data().reduce(function(a, b) {
                            return (parseFloat(a) || 0) + (parseFloat(b) || 0);
                        }, 0).toLocaleString('sr-RS'); // Formatiranje broja
                    };        
                }
            });

            var table = $('#DugovanjaDetaljFaktureBaket60').DataTable({
                "language": languageSettings,
                "autoWidth": false,
                "lengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],
                "pageLength": 10,
                "columnDefs": [
                        {
                            targets: [3,4,5,6], // Indeksi kolona koje formatiramo
                            render: function (data, type, row) {
                                if (type === 'display') {
                                    return new Intl.NumberFormat('sr-RS').format(data);
                                }
                                return data;
                            }
                        }
                    ],
                "footerCallback": function(row, data, start, end, display) {
                    var api = this.api();
                    
                    // Funkcija za sumiranje
                    var sumColumn = function(index) {
                        return api.column(index, { page: 'all' }).data().reduce(function(a, b) {
                            return (parseFloat(a) || 0) + (parseFloat(b) || 0);
                        }, 0).toLocaleString('sr-RS'); // Formatiranje broja
                    };        
                }
            });

        });           
