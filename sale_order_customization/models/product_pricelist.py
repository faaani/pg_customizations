from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    client_company_id = fields.Many2one('res.partner', domain=[('is_client', '=', True)])
