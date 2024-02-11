# import calendar

# from collections import defaultdict, OrderedDict
# from datetime import timedelta

from odoo import _, api, fields, models


# from odoo.exceptions import UserError, ValidationError
# from odoo.osv import expression
# from odoo.tools.float_utils import float_compare

class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = "priority desc, scheduled_date asc, id desc, partner_id asc"


class Location(models.Model):
    _inherit = "stock.location"

    is_bin = fields.Boolean(default=False, string="Is Bin?")
    bin_size = fields.Integer('Bin Volume Max')
    is_occupied = fields.Boolean(default=False, string='Is Occupied')
    volume_uom = fields.Char(string='Volume unit of measure label', compute='_compute_volume_uom_name')
    single_order_bin = fields.Boolean(default=False, string="Single Order Bin?")
    binning_category = fields.Many2one('binning.category')
    available_space = fields.Integer('Available Space')
    occupied_space = fields.Integer('Occupied Space')

    @api.model
    def _compute_volume_uom_name(self):
        product_length_in_feet_param = self.env['ir.config_parameter'].sudo().get_param('product.volume_in_cubic_feet')
        if product_length_in_feet_param == '1':
            self.update({
                'volume_uom': self.env.ref('uom.product_uom_cubic_foot').name
            })
        if product_length_in_feet_param == '2':
            self.update({
                'volume_uom': self.env.ref('stock_customization.product_uom_cubic_centimeter').name
            })
        else:
            self.update({
                'volume_uom': self.env.ref('uom.product_uom_cubic_meter').name
            })

    @api.onchange('usage')
    def change_bin_size_value(self):
        for rec in self:
            if rec.usage and rec.usage != 'internal':
                rec.is_bin = False
                rec.is_occupied = False
                rec.bin_size = 0

    @api.onchange('is_bin')
    def change_bin_size(self):
        for rec in self:
            if not rec.is_bin:
                rec.bin_size = 0

    # @api.onchange('bin_size')
    # def set_available_size(self):
    #     for rec in self:
    #         if not rec.occupied_space:
    #             rec.available_space = rec.bin_size
    #         else:
    #             old_bin_size = rec.available_space + rec.occupied_space
    #             new_bin_size = rec.bin_size
    #             difference = new_bin_size - old_bin_size
    #             rec.available_space = rec.available_space + difference



    # @api.model
    # def create(self, vals):
    #     vals['available_space'] = vals['bin_size']
    #     res = super(Location, self).create(vals)
    #     return res
