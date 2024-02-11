# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMoveExt(models.Model):
    _inherit = 'account.move'

    client_company_id = fields.Many2one('res.partner', domain="[('is_client','=',True)]", store=True)

    # @api.onchange('partner_id')
    # def update_client_company(self):
    #     for rec in self:
    #         if rec.partner_id.is_client:
    #             self.client_company_id = rec.partner_id.id


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        res.get('context')['default_client_company_id'] = res.get('context')['default_partner_id']
        return res
