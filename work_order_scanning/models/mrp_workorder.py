from odoo import models, fields, api, _


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def button_start(self):
        res = super(MrpWorkorder, self).button_start()
        return res

    def button_finish(self):
        if any(value == "progress" for value in self.production_id.workorder_ids.mapped('state')):
            self.production_id.barcode_status = 'printing'
        res = super(MrpWorkorder, self).button_finish()
        if all(value == "done" for value in self.production_id.workorder_ids.mapped('state')):
            self.production_id.barcode_status = 'waiting_binning'
        return res

    # @api.depends('production_availability', 'blocked_by_workorder_ids', 'blocked_by_workorder_ids.state')
    # def _compute_state(self):
    #     # Force the flush of the production_availability, the wo state is modify in the _compute_reservation_state
    #     # It is a trick to force that the state of workorder is computed as the end of the
    #     # cyclic depends with the mo.state, mo.reservation_state and wo.state
    #     for workorder in self:
    #         if workorder.state == 'pending':
    #             if all([wo.state in ('done', 'cancel') for wo in workorder.blocked_by_workorder_ids]):
    #                 workorder.state = 'ready' if workorder.production_id.reservation_state == 'assigned' else 'waiting'
    #                 continue
    #         if workorder.state not in ('waiting', 'ready'):
    #             continue
    #         if not all([wo.state in ('done', 'cancel') for wo in workorder.blocked_by_workorder_ids]):
    #             workorder.state = 'ready'
    #             continue
    #         if workorder.production_id.reservation_state not in ('waiting', 'confirmed', 'assigned'):
    #             continue
    #         if workorder.production_id.reservation_state == 'assigned' and workorder.state == 'waiting':
    #             workorder.state = 'ready'
    #         elif workorder.production_id.reservation_state != 'assigned' and workorder.state == 'ready':
    #             workorder.state = 'ready'
