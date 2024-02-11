from odoo import api, fields, models


class Product(models.Model):
    _inherit = "product.product"
    #
    setup = fields.Char('Print Profile')
    pallet = fields.Char('Pallet Type')
    customization_code = fields.Char('customization_code', readonly=False)
    product_variant_code = fields.Char('Product Variant Code')
    height = fields.Float()
    width = fields.Float()
    length = fields.Float()

    def create(self, vals_list):
        res = super(Product, self).create(vals_list)
        res.write({
            'setup': res.categ_id.print_profile,
            'pallet': res.categ_id.pallet_type
        })
        return res
