from odoo import models, fields, api, _


class ProductCategoryExt(models.Model):
    _inherit = 'product.category'

    print_profile = fields.Char('Print Profile')
    pallet_type = fields.Char('Pallet Type')
