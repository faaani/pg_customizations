# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductTemplateAttributeExt(models.Model):
    _inherit = 'product.attribute.value'

    size = fields.Float()
    height = fields.Float()
    width = fields.Float()
    length = fields.Float()
    uom_id = fields.Many2one('uom.uom')