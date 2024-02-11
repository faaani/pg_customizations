# -*- coding: utf-8 -*-
import csv
import io

from odoo import models, fields, api, _
import base64
from io import BytesIO
from odoo.tools.misc import xlwt


class ProductLabelLayoutExt(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection(selection_add=[
        ('cfb', ' CSV for Bartender')
    ], ondelete={'cfb': 'set default'}, default='cfb')
    report = fields.Binary('Report')
    file_name = fields.Char('File Name')

    def process(self):
        """
        overwrite this function for adding new
        report
        """
        if self.print_format == 'cfb':

            # This portion of code would be executed when we try to print labels from batch transfers
            if self._context.get('active_model') == 'stock.picking.batch':
                sale_order = self.env['sale.order'].search([('name', 'in', self.env['stock.picking.batch'].search(
                    [('id', '=', self._context.get('active_id'))]).move_ids.mapped('origin'))])
                if sale_order:
                    return self.printing_labels(sale_order)
                else:
                    sale_order = self.env['mrp.production'].search(
                        [('name', 'in', self.env['stock.picking.batch'].search(
                            [('id', '=', self._context.get('active_id'))]).move_ids.mapped('picking_id').mapped(
                            'origin'))]).sale_order_line_id.order_id
                    return self.printing_labels(sale_order)
            # This portion of code would be executed when we try to print labels from transfers
            if self._context.get('active_model') == 'stock.picking':
                sale_order = self.env['sale.order'].search([('name', 'in', self.env['stock.picking'].search(
                    [('id', '=', self._context.get('active_id'))]).move_ids.mapped('origin'))])
                return self.printing_labels(sale_order)
        else:
            res = super(ProductLabelLayoutExt, self).process()
            return res

    def printing_labels(self, sale_order):
        """
        used for getting excel report values
        """
        output = io.StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerow(['Order Creation Date',
                             'Print Location',
                             'Sequence',
                             'Product',
                             'Size',
                             'Color',
                             'Barcode',
                             'Create time',
                             'Mo Name',
                             'So Name',
                             'Client',
                             'Raw Material Barcode',
                             'Pick ID',
                             'Component Location',
                             'Batch ID',
                             'Manufacturing Quantity'
                             ])

        # Write the rows to the CSV writer (replace with your own code)
        for order in sale_order:
            for rec in order.order_line.filtered(lambda l: l.manufacturing_order_id.picking_ids.filtered(
                    lambda x: x.batch_id.id == self._context.get('active_id'))).printing_details_id:

                csv_writer.writerow(
                    [str(rec.sale_order_line_id.order_id.create_date.date()),
                     ' + '.join(rec.printing_details_ids.location.mapped('location')),
                     str(rec.sale_order_line_id.number) + " of " + str(
                         len(rec.sale_order_line_id.order_id.order_line)), rec.product_id.name,
                     rec.size if rec.size else
                     [attribute.name for attribute in rec.product_id.product_template_attribute_value_ids if
                      'size' in attribute.attribute_id.name.lower()][0] if [attribute.name for attribute in
                                                                            rec.product_id.product_template_attribute_value_ids
                                                                            if
                                                                            'size' in attribute.attribute_id.name.lower()] else " ",
                     rec.color_type if rec.color_type else
                     [attribute.name for attribute in rec.product_id.product_template_attribute_value_ids if
                      'color' in attribute.attribute_id.name.lower()][0] if [attribute.name for attribute in
                                                                             rec.product_id.product_template_attribute_value_ids
                                                                             if
                                                                             'color' in attribute.attribute_id.name.lower()] else " ",
                     rec.product_id.barcode if rec.product_id.barcode else '',
                     rec.sale_order_line_id.order_id.create_date.strftime("%I:%M %p"),
                     rec.manufacturing_order_id.name, rec.sale_order_line_id.order_id.name,
                     rec.sale_order_line_id.order_id.partner_invoice_id.name,
                     rec.manufacturing_order_id.bom_id.bom_line_ids[0].product_id.barcode,
                     rec.sale_order_line_id.manufacturing_order_id.picking_ids.filtered(lambda
                                                                                            l: l.picking_type_id.name == 'Pick Components').name if rec.sale_order_line_id.manufacturing_order_id.picking_ids.filtered(
                         lambda l: l.picking_type_id.name == 'Pick Components') else '',
                     rec.sale_order_line_id.manufacturing_order_id.picking_ids.filtered(lambda
                                                                                            l: l.picking_type_id.name == 'Pick Components').move_line_ids.picking_id.move_line_ids_without_package.location_id.display_name if rec.sale_order_line_id.manufacturing_order_id.picking_ids.filtered(
                         lambda l: l.picking_type_id.name == 'Pick Components') else '',
                     rec.sale_order_line_id.manufacturing_order_id.picking_ids.filtered(lambda
                                                                                            l: l.picking_type_id.name == 'Pick Components').batch_id.name if rec.sale_order_line_id.manufacturing_order_id.picking_ids.filtered(
                         lambda l: l.picking_type_id.name == 'Pick Components') else '',
                     rec.sale_order_line_id.product_uom_qty],
                )

        # Convert the CSV data to base64
        csv_data = output.getvalue().encode('utf-8')
        base64_data = base64.b64encode(csv_data).decode('utf-8')

        # Set the report and file name fields (replace with your own code)
        self.report = base64_data
        self.file_name = 'CSV for Bartender.csv'
        if self._context.get('active_model') == 'stock.picking':
            name = self.env['stock.picking'].search([('id', '=', self._context.get('active_id'))]).name
            fine_name = name + '.' + 'csv'
        if self._context.get('active_model') == 'stock.picking.batch':
            name = self.env['stock.picking.batch'].search([('id', '=', self._context.get('active_id'))]).name
            fine_name = name + '.' + 'csv'
        # Return the download action
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=product.label.layout&field=report&download=true&id=%s&filename=%s' % (
                self.id, fine_name),
        }
