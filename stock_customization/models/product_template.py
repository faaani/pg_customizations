from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    binning_category = fields.Many2one('binning.category')

    @api.model
    def _get_volume_uom_id_from_ir_config_parameter(self):
        """ Get the unit of measure to interpret the `volume` field. By default, we consider
        that volumes are expressed in cubic meters. Users can configure to express them in cubic feet
        by adding an ir.config_parameter record with "product.volume_in_cubic_feet" as key
        and "1" as value.
        """
        product_length_in_feet_param = self.env['ir.config_parameter'].sudo().get_param('product.volume_in_cubic_feet')
        if product_length_in_feet_param == '1':
            return self.env.ref('uom.product_uom_cubic_foot')
        if product_length_in_feet_param == '2':
            return self.env.ref('stock_customization.product_uom_cubic_centimeter')
        else:
            return self.env.ref('uom.product_uom_cubic_meter')
