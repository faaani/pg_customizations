from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_volume_volume_in_cubic_feet = fields.Selection(selection_add=[('2', 'Cubic Centimeters')], default=None)
    order_span = fields.Float('Order Span')
    working_week_structure = fields.Selection([
        ('5_days', '5 Days Week'), ('6_days', '6 Days Week'), ('7_days', '7 Days Week'),
    ], default='5_days')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('stock_customization.order_span', self.order_span)
        self.env['ir.config_parameter'].set_param('stock_customization.working_week_structure',
                                                  self.working_week_structure)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            order_span=float(self.env['ir.config_parameter'].sudo().get_param('stock_customization.order_span', default=2)),
            working_week_structure = self.env['ir.config_parameter'].sudo().get_param('stock_customization.working_week_structure')
        )
        return res
