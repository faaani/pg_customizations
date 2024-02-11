# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Productlist(models.Model):
    _name = "product.list"
    _description = "Productlist"
    _rec_names = 'name'  # TODO check if should be removed
    # _order = "sequence asc, id desc"

    client_id = fields.Many2one('res.partner', domain="[('is_client', '=', True)]")
    name = fields.Char(related='client_id.name', store=True)
    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, it will allow you to hide the product list without removing it.")
    client_company_id = fields.Many2one('res.partner')
    product_list_item_ids = fields.One2many('product.list.item', 'product_list_id')


class ProductlistItem(models.Model):
    _name = "product.list.item"
    _description = "Product list Item"

    product_list_id = fields.Many2one('product.list', ondelete='cascade')
    product_id = fields.Many2one('product.product')
    product_tmpl_id = fields.Many2one('product.template')
    location_id = fields.Many2one('printing.location')
    offset_x = fields.Integer('OffSet X')
    offset_y = fields.Integer('OffSet Y')
    resize_width = fields.Integer(string="Resize Width (mm)")
    resize_height = fields.Integer(string="Resize Height (mm)")
    uom_id = fields.Many2one('uom.uom')
