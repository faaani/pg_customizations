from odoo import models, fields, api, _


class BinningCategories(models.Model):
    _name = 'binning.category'
    _description = "Binning Category"

    name = fields.Char('Category Name')
