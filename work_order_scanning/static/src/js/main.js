odoo.define('work_order_scanning.MyCustomAction', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var scannerInput = '';
    var ajax = require('web.ajax');
    var barcode_out = ''

//    function action_print_label() {
//        $.ajax({
//            url: '/print/label',
//            type: "POST",
//            data: {print_details_id: $('#print_detail_id').text()},
//            success: function (data) {
//                let json_values;
//                json_values = JSON.parse(data)
//                $('#dowlaod_file').attr('href', json_values.url)
//            },
//            error: function (err) {
//                console.log(err)
//            }
//        });
//    }

    document.addEventListener('keydown', function (event) {
        var self = this;
        const keyCode = event.keyCode || event.which;
        scannerInput += String.fromCharCode(keyCode);

        // Detect if the input came from a scanner
        if (keyCode === 13) {
            // Handle the full scanner input
            scannerInput = scannerInput.replace(/¿/g, '/');
            scannerInput = scannerInput.replace(//g, '/');
            scannerInput = scannerInput.replace(/[\x00-\x1F]|V/g, '');
            scannerInput = scannerInput.substring(1).replace("//", "/")
             if (scannerInput)
            {
                scannerInput = scannerInput.replace(/[^a-zA-Z0-9]/g, '');
            }
            let selected_work_center = $('#selected_printer').text();
            var search_value = $("#filter_search").val()
            if (search_value) {
                search_value = search_value.toLowerCase();
                if (scannerInput.length > 6) {
                    $('#filter_search').val('');
                    search_value = ''
                }
            }
            if (selected_work_center != 'No Printer Allocated') {
                if (scannerInput) {
                    let selected_option = $('#filter').val();
                    $.ajax({
                        url: '/scan/work/order/',
                        type: "POST",
                        data: {
                            barcode: scannerInput,
                            value: search_value,
                            filter_value: selected_option,
                            work_center: localStorage.getItem('work_center_id')
                        },
                        success: function (data) {
                            $("#right_scan_value").children().remove();
                            let json_values;
                            json_values = JSON.parse(data)
                            if (json_values.error) {
                                if (json_values.error == "not found ready") {
                                    $('#scan_again_work_order').modal('show');
                                    barcode_out = json_values.barcode
                                    $('.modal_body_scan_again').text('Are you wanted to scan this order ' + barcode_out + ' again?')
                                    //     $("#right_scan_value").append(`
                                    //         <div class="row  text-center">
                                    //             <div class="col-md-12">
                                    //                 <h1 style="margin-top:20px"><strong>${json_values['message']} </strong></h1>
                                    //             </div>
                                    //         </div>
                                    //         <div class="row  text-center">
                                    //             <div class="col-md-12">
                                    //                 <div class=" text-center">
                                    //                     <img src="/work_order_scanning/static/src/img/order_not_ready.jpg" alt="shirt" width="40%"/>
                                    //                 </div>
                                    //             </div>
                                    //         </div>
                                    // `);

                                } else if (json_values.error == 'not found') {
                                    $("#right_scan_value").append(`
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <h1 style="margin-top:20px"><strong>${json_values['message']} </strong></h1>
                                            </div>
                                        </div>
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <div class=" text-center">
                                                    <img src="/work_order_scanning/static/src/img/order_not_ready.jpg" alt="shirt" width="40%"/>
                                                </div>
                                            </div>
                                        </div>
                                `);
                                } else if (json_values.error == 'no filter') {
                                    $("#right_scan_value").append(`
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <h1 style="margin-top:20px"><strong>${json_values['message']} </strong></h1>
                                            </div>
                                        </div>
                                        <div class="row  text-center mt-5">
                                            <div class="col-md-12 mt-5">
                                                <div class=" text-center">
                                                    <img src="/work_order_scanning/static/src/img/clear-filter.png" alt="shirt" width="35%"/>
                                                </div>
                                            </div>
                                        </div>
                                `);
                                } else if (json_values.error == 'not found ready current operation') {
                                    $("#right_scan_value").append(`
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <h1 style="margin-top:20px"><strong>${json_values['message']} </strong></h1>
                                            </div>
                                        </div>
                                        <div class="row  text-center mt-5">
                                            <div class="col-md-12 mt-5">
                                                <div class=" text-center">
                                                     <img src="/work_order_scanning/static/src/img/order_not_ready.jpg" alt="shirt" width="40%"/>
                                                </div>
                                            </div>
                                        </div>
                                `);
                                }

                            } else {
                                json_values.forEach(function (res) {
                                    $("#right_scan_value").append(`
                                           <div class="hide_show">
                                                    <div class="row p-3 mt-5">
                                                        <div class="col-md-6">
                                                            <div class="row mt-5">
                                                                <div class="col-md-1">
                                                                </div>
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Age</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text" readonly="true" data="${res.order_days}" style="font-weight: bold;background: ${res.order_days <=2 ? 'orange' : 'red'};color: ${res.order_days <= 2 ? 'black' : 'White'}" value="${res.order_days +"D-"+ res.order_hours+"H"}"/>
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-1">
                                                                </div>
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Sale Order</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.sale_order_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-1">
                                                                </div>
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Manufacturing Order</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.manufacturing_order_name}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                            </div>

                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="row mt-5">

                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Customer Name</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.partner_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>
                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Total Order Quantity</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.quantity_order}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>
                                                            </div>
                                                        </div>


                                                    </div>
                                                    <div class="row p-3 mt-6">
                                                        <div class="col-md-1"></div>
                                                        <div class="col-md-4">
                                                            <div class="row">
                                                            <div class="col-md-6">
                                                             <img onerror="this.style.display='none'"  src="data:image/png;base64,${res.filter_img}"  width="115%" />
                                                            </div>
                                                            <div class="col-md-6">
                                                            <div class="col">
                                                            <img onerror="this.style.display='none'"  class="align-top" src="data:image/png;base64,${res.second_img}"
                                                                     width="54%"/>
                                                                <img onerror="this.style.display='none'" class="align-top mt-3" src="data:image/png;base64,${res.third_img}"
                                                                      width="54%"
                                                                     />
                                                                  
                                                            </div>
                                                            
                                                            </div> 
                                                            </div>

                                                            <div class="row mt-5 ">
                                                                <div class="col-md-3">
                                                                    <h5 class="mt-2">Operation</h5>
                                                                </div>
                                                                <div class="col-md-5">
                                                                    <input type="text"
                                                                           value="${res.operation}"
                                                                           readonly="True"
                                                                           class="input_field"
                                                                    />
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-7">
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Item</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.item}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Client</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.client_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Product</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.product_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Size</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.size}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Color/Type</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.color_type}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Operations</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.operations}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                        `);
                                    $("#" + res.work_order_id).remove()
                                    if (res.art_work_img) {
                                        const downloadLink = document.createElement('a');
                                        downloadLink.setAttribute('href', 'data:image/png;base64,' + res.art_work_img);
                                        downloadLink.setAttribute('download', res.art_work_img_name + '.png');
                                        downloadLink.click();
                                    }
                                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                                    model: 'mrp.workorder', method: 'button_start',
                                    args: [res.work_order_id],
                                    kwargs: {},
                                    });
                                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                                    model: 'mrp.workorder', method: 'button_finish',
                                    args: [res.work_order_id],
                                    kwargs: {},
                                    });

                                });
                            }


                        },
                        error: function (err) {
                            console.log(err)
                        }
                    });
                }
            } else {
                $("#right_scan_value").children().remove();
                $("#right_scan_value").append(`
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <h1 style="margin-top:20px"><strong>No Printer was Allocated.Please select a printer from the configuration menu.</strong></h1>
                                            </div>
                                        </div>
                                        <div class="row mt-5 text-center">
                                            <div class="col-md-12 mt-5">
                                                <div class=" text-center">
                                                    <img src="/work_order_scanning/static/src/img/no-print.png" alt="shirt" width="35%"/>
                                                </div>
                                            </div>
                                        </div>
                                `);
            }


            // Reset the scanner input
            scannerInput = '';
        }
    });


    var MyCustomAction = AbstractAction.extend({
        contentTemplate: 'PrintingScan',
        cssLibs: [],
        jsLibs: [],
        events: {
            'click .list-group-item': '_onListClick',
            'change #filter': 'action_option_filter',
            'click  #yes_rescan_button': 'action_scan_again',
        },

        init: function (parent, context) {
            this._super(parent, context);
            var self = this;
        },

        start: function () {
            var self = this;

            self.render_dashboards();
            return this._super();

        },

        render_dashboards: function (value) {
            var self = this;
            $.ajax({
                url: '/work/order/infos',
                type: "GET",
                success: function (data) {
                    let json_values;
                    json_values = JSON.parse(data)
                    let options = []
                    json_values.forEach(function (res) {
                        let operation_str = res.operation
                        operation_str = operation_str.replace(/\s/g, '')
                        if (operation_str) {
                            operation_str = operation_str.toLowerCase()
                            options.push(operation_str)
                        }
                        $("#print_scan_geek").append(`
                           <ul class="list-group" id="myList">
                            <li class="list-group-item">
                                    <div id="${res.word_order_id}" class="mt-3 card bg-white shadow appended_card rounded border  ${operation_str}">
                                        <div class="pt-3 ps-3 pe-3">
                                                <div class="row">
                                                    <div class="col-md-7 text-start">
                                                          <h4>${res.name}</h4>
                                                    </div>
                                                    <div class="col-md-5 text-end">
                                                        <button class="btn btn-success btn-state" >${res.state}</button>
                                                    </div>
                                                </div>
                                                <div class="row mt-4">
                                                    <div class="col-md-4 text-start">
                                                        <h6 class="text-danger operation">${res.operation}</h6>
                                                    </div>
                                                    <div class="col-md-4 text-end">
                                                          <p class="text-secondary">${res.date}</p>
                                                    </div>
                                                    <div class="col-md-4 text-end">
                                                          <button class="btn order_age" data="${res.order_days}" style="background: ${res.order_days <=2 ? 'orange' : 'red'};color: ${res.order_days <= 2 ? 'black' : 'White'}">${res.order_days +"D-"+ res.order_hours+"H"}</button>
                                                    </div>
                                                </div>
                                            </div>
                                    </div>
                            </li>
                            </ul>                
                            `);


                    });
                    self.printer_detect()
                    self._EnableFilters();

                    let unique_options = [...new Set(options)];
                    // unique_options.forEach(function (res) {
                    //     res = res.charAt(0).toUpperCase() + res.slice(1);
                    //     if (res == 'Front') {
                    //         $("#filter").append(`
                    //                     <option selected="" value="${res}">${res}</option>`);
                    //     } else if (res == 'Back') {
                    //         $("#filter").append(`
                    //                     <option selected=""  value="${res}">${res}</option>`);
                    //     } else if (res == 'Neck') {
                    //         $("#filter").append(`
                    //                     <option selected=""  value="${res}">${res}</option>`);
                    //     } else {
                    //           $("#filter").append(`
                    //                     <option value="${res}">${res}</option>`);
                    //     }
                    //
                    // });
                    self.action_option_filter()
                },
                error: function (err) {
                    console.log(err)
                }
            });
        },

        _EnableFilters() {
            $(document).ready(function () {
                $("#filter_search").on("keyup", function () {
                    var value = $(this).val().toLowerCase();
                    $("#myList li").filter(function () {
                        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
                    });
                });
            });
        },

        _onListClick: function (value) {
            const current_child_val = value.currentTarget.children[0].children[0].children[0].children[0].children[0].textContent
            $('#filter_search').val(current_child_val)
            let selected_work_center = $('#selected_printer').text();
            var search_value = $("#filter_search").val()
            if (search_value) {
                search_value = search_value.match(/\d+/)[0]
            }
            if (selected_work_center != 'No Printer Allocated') {
                if (search_value) {
                    let selected_option = $('#filter').val();
                    $.ajax({
                        url: '/scan/work/order/',
                        type: "POST",
                        data: {
                            value: search_value,
                            filter_value: selected_option,
                            work_center: localStorage.getItem('work_center_id')
                        },
                        success: function (data) {
                            $("#right_scan_value").children().remove();
                            let json_values;
                            json_values = JSON.parse(data)
                            if (json_values.error) {
                                if (json_values.error == "not found ready") {
                                    $('#scan_again_work_order').modal('show');
                                    barcode_out = json_values.barcode
                                    $('.modal_body_scan_again').text('Are you wanted to scan this order ' + barcode_out + ' again?')
                                    //     $("#right_scan_value").append(`
                                    //         <div class="row  text-center">
                                    //             <div class="col-md-12">
                                    //                 <h1 style="margin-top:20px"><strong>${json_values['message']} </strong></h1>
                                    //             </div>
                                    //         </div>
                                    //         <div class="row  text-center">
                                    //             <div class="col-md-12">
                                    //                 <div class=" text-center">
                                    //                     <img src="/work_order_scanning/static/src/img/order_not_ready.jpg" alt="shirt" width="40%"/>
                                    //                 </div>
                                    //             </div>
                                    //         </div>
                                    // `);

                                } else if (json_values.error == 'not found') {
                                    $("#right_scan_value").append(`
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <h1 style="margin-top:20px"><strong>${json_values['message']} </strong></h1>
                                            </div>
                                        </div>
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <div class=" text-center">
                                                    <img src="/work_order_scanning/static/src/img/order_not_ready.jpg" alt="shirt" width="40%"/>
                                                </div>
                                            </div>
                                        </div>
                                `);
                                } else if (json_values.error == 'no filter') {
                                    $("#right_scan_value").append(`
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <h1 style="margin-top:20px"><strong>${json_values['message']} </strong></h1>
                                            </div>
                                        </div>
                                        <div class="row  text-center mt-5">
                                            <div class="col-md-12 mt-5">
                                                <div class=" text-center">
                                                    <img src="/work_order_scanning/static/src/img/clear-filter.png" alt="shirt" width="35%"/>
                                                </div>
                                            </div>
                                        </div>
                                `);
                                }

                            } else {
                                json_values.forEach(function (res) {
                                    $("#right_scan_value").append(`
                                           <div class="hide_show">
                                                    <div class="row p-3 mt-5">
                                                        <div class="col-md-6">
                                                            <div class="row mt-5">
                                                                <div class="col-md-1">
                                                                </div>
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Age</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text" readonly="true" data="${res.order_days}" style="font-weight: bold;background: ${res.order_days <=2 ? 'orange' : 'red'};color: ${res.order_days <= 2 ? 'black' : 'White'}" value="${res.order_days +"D-"+ res.order_hours+"H"}"/>
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-1">
                                                                </div>
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Sale Order</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.sale_order_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                            </div>

                                                            <div class="row mt-2">
                                                                <div class="col-md-1">
                                                                </div>
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Manufacturing Order</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.manufacturing_order_name}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="row mt-5">

                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Customer Name</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.partner_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>
                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Total Order Quantity</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.quantity_order}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>
                                                            </div>
                                                        </div>


                                                    </div>
                                                    <div class="row p-3 mt-6">
                                                        <div class="col-md-1"></div>
                                                        <div class="col-md-4">
                                                            <div class="row">
                                                            <div class="col-md-6">
                                                             <img onerror="this.style.display='none'"  src="data:image/png;base64,${res.filter_img}"  width="115%" />
                                                            </div>
                                                            <div class="col-md-6">
                                                            <div class="col">
                                                            <img onerror="this.style.display='none'"  class="align-top" src="data:image/png;base64,${res.second_img}"
                                                                     width="54%"/>
                                                                <img onerror="this.style.display='none'" class="align-top mt-3" src="data:image/png;base64,${res.third_img}"
                                                                      width="54%"
                                                                     />

                                                            </div>

                                                            </div>
                                                            </div>

                                                            <div class="row mt-5 ">
                                                                <div class="col-md-3">
                                                                    <h5 class="mt-2">Operation</h5>
                                                                </div>
                                                                <div class="col-md-5">
                                                                    <input type="text"
                                                                           value="${res.operation}"
                                                                           readonly="True"
                                                                           class="input_field"
                                                                    />
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-7">
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Item</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.item}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Client</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.client_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Product</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.product_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Size</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.size}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Color/Type</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.color_type}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Operations</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.operations}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                        `);
                                    $("#" + res.work_order_id).remove()
                                    if (res.art_work_img) {
                                        const downloadLink = document.createElement('a');
                                        downloadLink.setAttribute('href', 'data:image/png;base64,' + res.art_work_img);
                                        downloadLink.setAttribute('download', res.art_work_img_name + '.png');
                                        downloadLink.click();
                                    }
                                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                                    model: 'mrp.workorder', method: 'button_start',
                                    args: [res.work_order_id],
                                    kwargs: {},
                                    });
                                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                                    model: 'mrp.workorder', method: 'button_finish',
                                    args: [res.work_order_id],
                                    kwargs: {},
                                    });



                                });
                            }

                        },
                        error: function (err) {
                            console.log(err)
                        }
                    });
                }
            } else {
                $("#right_scan_value").children().remove();
                $("#right_scan_value").append(`
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <h1 style="margin-top:20px"><strong>No Printer was Allocated.Please select a printer from the configuration menu.</strong></h1>
                                            </div>
                                        </div>
                                        <div class="row mt-5 text-center">
                                            <div class="col-md-12 mt-5">
                                                <div class=" text-center">
                                                    <img src="/work_order_scanning/static/src/img/no-print.png" alt="shirt" width="35%"/>
                                                </div>
                                            </div>
                                        </div>
                                `);
            }
        },

        printer_detect: function () {
            let selected_work_center = localStorage.getItem('work_center_name')
            if (selected_work_center && selected_work_center != 'Select Work center') {
                $('#selected_printer').text(selected_work_center);
            }
        },

        action_option_filter: function () {
            let selected_option = $('#filter').find(":selected").val().toLowerCase();
            if (selected_option == "select_filter") {
                $('.appended_card').removeClass('d-none')
            } else {
                $('.appended_card').addClass('d-none')
                $("." + selected_option).removeClass('d-none')
            }
        },

        action_scan_again: function () {
            $('#scan_again_work_order').modal('hide');
            let selected_work_center = $('#selected_printer').text();
            if (selected_work_center != 'No Printer Allocated') {
                let selected_option = $('#filter').val();
                var search_value = $("#filter_search").val()
                if (search_value) {
                    search_value = search_value.match(/\d+/)[0]
                    if (scannerInput.length > 6) {
                        search_value = ''
                    }
                }
                $.ajax({
                    url: '/scan/work/order/again',
                    type: "POST",
                    data: {
                        barcode: barcode_out,
                        value: search_value,
                        filter_value: selected_option,
                        work_center: localStorage.getItem('work_center_id')
                    },
                    success: function (data) {
                        $("#right_scan_value").children().remove();
                        let json_values;
                        json_values = JSON.parse(data)
                        if (json_values.error) {
                            if (json_values.error == 'not found') {
                                $("#right_scan_value").append(`
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <h1 style="margin-top:20px"><strong>${json_values['message']} </strong></h1>
                                            </div>
                                        </div>
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <div class=" text-center">
                                                    <img src="/work_order_scanning/static/src/img/order_not_ready.jpg" alt="shirt" width="40%"/>
                                                </div>
                                            </div>
                                        </div>
                                `);
                            } else if (json_values.error == 'no filter') {
                                $("#right_scan_value").append(`
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <h1 style="margin-top:20px"><strong>${json_values['message']} </strong></h1>
                                            </div>
                                        </div>
                                        <div class="row  text-center mt-5">
                                            <div class="col-md-12 mt-5">
                                                <div class=" text-center">
                                                    <img src="/work_order_scanning/static/src/img/clear-filter.png" alt="shirt" width="35%"/>
                                                </div>
                                            </div>
                                        </div>
                                `);
                            }

                        } else {
                            json_values.forEach(function (res) {
                                $("#right_scan_value").append(`
                                           <div class="hide_show">
                                                    <div class="row p-3 mt-5">
                                                        <div class="col-md-6">
                                                            <div class="row mt-5">
                                                                <div class="col-md-1">
                                                                </div>
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Age</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text" readonly="true" data="${res.order_days}" style="font-weight: bold;background: ${res.order_days <=2 ? 'orange' : 'red'};color: ${res.order_days <= 2 ? 'black' : 'White'}" value="${res.order_days +"D-"+ res.order_hours+"H"}"/>
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-1">
                                                                </div>
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Sale Order</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.sale_order_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                            </div>

                                                            <div class="row mt-2">
                                                                <div class="col-md-1">
                                                                </div>
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Manufacturing Order</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.manufacturing_order_name}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="row mt-5">

                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Customer Name</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.partner_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>
                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-4 ">
                                                                    <h5 class="mt-2">Total Order Quantity</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.quantity_order}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>
                                                            </div>
                                                        </div>


                                                    </div>
                                                    <div class="row p-3 mt-6">
                                                        <div class="col-md-1"></div>
                                                        <div class="col-md-4">
                                                            <div class="row">
                                                            <div class="col-md-6">
                                                             <img onerror="this.style.display='none'"  src="data:image/png;base64,${res.filter_img}"  width="115%" />
                                                            </div>
                                                            <div class="col-md-6">
                                                            <div class="col">
                                                            <img onerror="this.style.display='none'"  class="align-top" src="data:image/png;base64,${res.second_img}"
                                                                     width="54%"/>
                                                                <img onerror="this.style.display='none'" class="align-top mt-3" src="data:image/png;base64,${res.third_img}"
                                                                      width="54%"
                                                                     />
                                                            </div>
                                                            
                                                            </div> 
                                                            </div>

                                                            <div class="row mt-5 ">
                                                                <div class="col-md-3">
                                                                    <h5 class="mt-2">Operation</h5>
                                                                </div>
                                                                <div class="col-md-5">
                                                                    <input type="text"
                                                                           value="${res.operation}"
                                                                           readonly="True"
                                                                           class="input_field"
                                                                    />
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-7">
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Item</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.item}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Client</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.client_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Product</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.product_id}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Size</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.size}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Color/Type</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.color_type}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                            <div class="row mt-2">
                                                                <div class="col-md-2">
                                                                </div>
                                                                <div class="col-md-2 ">
                                                                    <h5 class="mt-2">Operations</h5>
                                                                </div>
                                                                <div class="col-md-7">
                                                                    <input type="text"
                                                                           value="${res.operations}"
                                                                           readonly="true"
                                                                    />
                                                                </div>
                                                                <div class="col-md-1">
                                                                </div>

                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                        `);
                                $("#" + res.work_order_id).remove()
                                    if (res.art_work_img) {
                                        const downloadLink = document.createElement('a');
                                        downloadLink.setAttribute('href', 'data:image/png;base64,' + res.art_work_img);
                                        downloadLink.setAttribute('download', res.art_work_img_name + '.png');
                                        downloadLink.click();
                                    }
                                $("#" + res.work_order_id).remove()


                            });
                        }


                    },
                    error: function (err) {
                        console.log(err)
                    }
                });
            } else {
                $("#right_scan_value").children().remove();
                $("#right_scan_value").append(`
                                        <div class="row  text-center">
                                            <div class="col-md-12">
                                                <h1 style="margin-top:20px"><strong>No Printer Allocated</strong></h1>
                                            </div>
                                        </div>
                                        <div class="row mt-5 text-center">
                                            <div class="col-md-12 mt-5">
                                                <div class=" text-center">
                                                    <img src="/work_order_scanning/static/src/img/no-print.png" alt="shirt" width="35%"/>
                                                </div>
                                            </div>
                                        </div>
                                `);
            }
        },

    });

    core.action_registry.add("bg-light-grey", MyCustomAction);
    return MyCustomAction
});
