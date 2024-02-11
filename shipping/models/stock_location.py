from odoo import _, api, fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    is_shipping_station = fields.Boolean(string="Is Shipping Station")
