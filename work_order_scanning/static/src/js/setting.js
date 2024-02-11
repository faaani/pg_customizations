odoo.define('work_order_scanning.my_action', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');


    var MyAction = AbstractAction.extend({
        template: 'LocalStorage',
        cssLibs: [],
        jsLibs: [],
        events: {
            'click #save_center': 'action_save_option',
        },

        init: function (parent, context) {
            this._super(parent, context);
        },

        start: async function () {
            var self = this;
            self.render_dashboards();
            return this._super();
        },
        render_dashboards: async function (value) {
            var self = this;
            await this._rpc({
                model: 'mrp.workcenter',
                method: 'search_read',
                args: [[], ['id', 'name']],
            }).then(function (work_centers) {
                self.work_centers = work_centers;
                work_centers.forEach(function (res) {
                    let localstorage_work_center_id = localStorage.getItem('work_center_id')
                    if (localstorage_work_center_id) {
                        if (localstorage_work_center_id == res.id) {
                            $("#work_center_option").append(`
                            <option selected="" value="${res.id}">${res.name}</option>`);
                        } else {
                            if (res.name != 'unallocated') {
                                $("#work_center_option").append(`
                            <option value="${res.id}">${res.name}</option>`);
                            }

                        }
                    } else {
                        if (res.name != 'unallocated') {
                            $("#work_center_option").append(`
                            <option value="${res.id}">${res.name}</option>`);
                        }
                    }


                });
                $('.o_dialog .modal-footer').addClass('footer_custom')
            });

        },
        action_save_option: function (e) {
            $('.o_dialog').toggle();
            let selected_work_center = $('#work_center_option').find(":selected").val();
            localStorage.setItem('work_center_id', selected_work_center)
            localStorage.setItem('work_center_name', $('#work_center_option').find(":selected").text())
            let selected_work_center_name = $('#work_center_option').find(":selected").text()
            if (selected_work_center_name == 'Select Work center') {
                $('#selected_printer').text('No Printer Allocated');
            } else {
                $('#selected_printer').text(selected_work_center_name);
            }
        },
    });


    core.action_registry.add('work_order_scanning.work_center_list_view', MyAction);
    return MyAction
});
