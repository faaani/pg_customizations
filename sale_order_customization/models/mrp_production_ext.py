from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import OrderedSet, format_date, groupby as tools_groupby


class MrpProductionExt(models.Model):
    _inherit = 'mrp.production'
    _order = 'partner_id asc'

    @api.depends('workorder_ids')
    def _compute_printing_locations(self):
        for order in self:
            print_locations = ''
            for line in order.workorder_ids:
                if print_locations:
                    print_locations += ','
                print_locations += line.name
            order.print_location = print_locations

    availability_status = fields.Char("Component's availability Status", compute='_availability_status', store=True)
    sale_order_line_id = fields.Many2one('sale.order.line')
    partner_id = fields.Many2one('res.partner', 'Client Name')
    print_location = fields.Char(string='Print Locations', compute='_compute_printing_locations', store=True)
    scrapped = fields.Boolean()
    added_to_batch = fields.Boolean(default=False)
    item_id = fields.Char('Item ID')
    product_categ_id = fields.Many2one('product.category')
    receipt_id = fields.Char('Receipt ID')
    client_order_date = fields.Datetime()
    date_order = fields.Datetime(
        string="Order Date")
    barcode_status = fields.Selection([
        ('waiting_to_add_in_batch', 'To Be Batched'),
        ('added_in_batch', 'Added In Batch And Waiting for Label Printing'),
        ('waiting_components', 'To Be Picked'),
        ('components_picked', 'To Be Printed'),
        ('printing', 'Partially Printed'),
        ('waiting_binning', 'To Be Binned'),
        ('mrp_done', 'To Be Shipped'),
        ('scrapped', 'Scrapped')
    ], tracking=True, default='waiting_to_add_in_batch', string="MO Status")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('progress', 'In Progress'),
        ('to_close', 'To Close'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('scrapped', 'Scrapped')], string='State',
        compute='_compute_state', copy=False, index=True, readonly=True,
        store=True, tracking=False,
        help=" * Draft: The MO is not confirmed yet.\n"
             " * Confirmed: The MO is confirmed, the stock rules and the reordering of the components are trigerred.\n"
             " * In Progress: The production has started (on the MO or on the WO).\n"
             " * To Close: The production is done, the MO has to be closed.\n"
             " * Done: The MO is closed, the stock moves are posted. \n"
             " * Cancelled: The MO has been cancelled, can't be confirmed anymore.")

    reservation_state = fields.Selection([
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('waiting', 'Waiting Another Operation')],
        string='MO Readiness',
        compute='_compute_reservation_state', copy=False, index=True, readonly=True,
        store=True, tracking=False,
        help="Manufacturing readiness for this MO, as per bill of material configuration:\n\
                * Ready: The material is available to start the production.\n\
                * Waiting: The material is not available to start the production.\n")

    @api.depends('state', 'reservation_state', 'date_planned_start', 'move_raw_ids',
                 'move_raw_ids.forecast_availability', 'move_raw_ids.forecast_expected_date')
    def _availability_status(self):
        productions = self.filtered(lambda mo: mo.state not in ('cancel', 'done', 'draft'))
        productions.availability_status = _('Available')

        other_productions = self - productions
        other_productions.availability_status = False

        all_raw_moves = productions.move_raw_ids
        # Force to prefetch more than 1000 by 1000
        all_raw_moves._fields['forecast_availability'].compute_value(all_raw_moves)
        for production in productions:
            if any(float_compare(move.forecast_availability, 0 if move.state == 'draft' else move.product_qty,
                                 precision_rounding=move.product_id.uom_id.rounding) == -1 for move in
                   production.move_raw_ids):
                production.availability_status = _('Not Available')
            else:
                forecast_date = max(
                    production.move_raw_ids.filtered('forecast_expected_date').mapped('forecast_expected_date'),
                    default=False)
                if forecast_date:
                    production.availability_status = _('Exp %s', format_date(self.env, forecast_date))

    def button_scrap(self):
        result = super(MrpProductionExt, self).button_scrap()
        result['context']['default_product_id'] = self.product_id.id
        result['context']['default_scrap_qty'] = self.product_qty
        return result

    _sql_constraints = [
        # ('name_uniq', 'unique(company_id)', 'Reference must be unique per Company!'),
        ('qty_positive', 'check (product_qty > 0)', 'The quantity to produce must be positive!'),
    ]

    def action_confirm(self):
        res = super(MrpProductionExt, self).action_confirm()
        return res

    def add_to_batch(self):
        pickings = []
        for order in self:
            if order.picking_ids:
                if order.state == 'confirmed' and order.added_to_batch == False:
                    for val in order.picking_ids:
                        if val.picking_type_id.name == 'Pick Components':
                            val.write({
                                'client_company_id': order.partner_id.id,
                                'print_locations': order.print_location
                            })
                            pickings.append(val.id)
        if not pickings:
            raise UserError(
                _("You don't have anything to put in the batch please select other manufacturing orders to proceed with!"))

        batch_obj = self.env['stock.picking.batch']

        vals = {
            "picking_type_id": self.env['stock.picking.type'].search([('name', '=', 'Pick Components')]).id,
            "user_id": self.env.user.id,
            "company_id": self.env.company.id,
            "scheduled_date": fields.Datetime.now(),
            "picking_ids": [(6, 0, [rec for rec in pickings])]
        }

        batch = batch_obj.create(vals)

        res = {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking.batch',
            'target': 'current',
            'view_mode': 'form',
            'res_id': batch.id
            # 'context': {
            #     'active_model': 'mrp.production',
            #     'active_ids': pickings,
            # },
        }
        return res

    def button_mark_done(self):
        result = super(MrpProductionExt, self).button_mark_done()
        self.write({
            'barcode_status': 'mrp_done'
        })
        return result

    @api.depends(
        'move_raw_ids.state', 'move_raw_ids.quantity_done', 'move_finished_ids.state',
        'workorder_ids.state', 'product_qty', 'qty_producing', 'scrapped')
    def _compute_state(self):
        """ Compute the production state. This uses a similar process to stock
        picking, but has been adapted to support having no moves. This adaption
        includes some state changes outside of this compute.

        There exist 3 extra steps for production:
        - progress: At least one item is produced or consumed.
        - to_close: The quantity produced is greater than the quantity to
        produce and all work orders has been finished.
        """
        for production in self:
            if not production.state or not production.product_uom_id:
                production.state = 'draft'
            elif production.state == 'cancel' or (production.move_finished_ids and all(
                    move.state == 'cancel' for move in production.move_finished_ids)):
                production.state = 'cancel'
            elif (
                    production.state == 'done'
                    or (production.move_raw_ids and all(
                move.state in ('cancel', 'done') for move in production.move_raw_ids))
                    and all(move.state in ('cancel', 'done') for move in production.move_finished_ids)
            ):
                production.state = 'done'
            elif production.workorder_ids and all(
                    wo_state in ('done', 'cancel') for wo_state in production.workorder_ids.mapped('state')):
                production.state = 'to_close'
            elif not production.workorder_ids and float_compare(production.qty_producing, production.product_qty,
                                                                precision_rounding=production.product_uom_id.rounding) >= 0:
                production.state = 'to_close'
            elif any(wo_state in ('progress', 'done') for wo_state in production.workorder_ids.mapped('state')):
                production.state = 'progress'
            elif production.product_uom_id and not float_is_zero(production.qty_producing,
                                                                 precision_rounding=production.product_uom_id.rounding):
                production.state = 'progress'
            elif any(not float_is_zero(move.quantity_done,
                                       precision_rounding=move.product_uom.rounding or move.product_id.uom_id.rounding)
                     for move in production.move_raw_ids):
                production.state = 'progress'
            if production.scrapped == True:
                production.state = 'scrapped'
