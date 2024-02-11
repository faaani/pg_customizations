from odoo import _, api, fields, models
import json
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    shipping_station_id = fields.Many2one('stock.location', domain=[('is_shipping_station', '=', True)])

    # def button_validate(self):
    #     if self.picking_type_id.code == 'outgoing':
    #         if not self.carrier_id:
    #             carrier = self.env['delivery.carrier'].search(
    #                 [('client_company_id', '=', self.sale_id.partner_invoice_id.id)])
    #             if not carrier:
    #                 raise UserError('No Carrier associated with this client please create carrier for this client')
    #             elif carrier and len(carrier) > 1:
    #                 raise UserError(
    #                     'There are multiple carriers associated with this client please select one manually')
    #             else:
    #                 self.carrier_id = carrier.id
    #
    #     result = super(StockPicking, self).button_validate()
    #     return result

    def validate_transfer(self, args):
        reserved_moves = self.move_ids_without_package.filtered(lambda m: m.move_line_ids.reserved_qty)
        for move in reserved_moves:
            move.update({
                'quantity_done': move.product_uom_qty or 0.0,
            })
        if args:
            location_id = int(args)
            shipping_station_id = self.env['stock.location'].browse(location_id)
            self.update({
                'shipping_station_id': shipping_station_id.id or False,
            })
        self.update({
            'user_id': self.env.user.id or False,
        })
        # if not self.carrier_id:
        #     carrier = self.env['delivery.carrier'].search(
        #         [('client_company_id', '=', self.sale_id.partner_invoice_id.id),
        #          ('country_ids', '=', self.sale_id.partner_id.country_id.id),
        #          ('zip_prefix_ids', '=', self.sale_id.partner_id.zip[0])])
        #     if carrier:
        #         self.write({
        #             'carrier_id': carrier.id,
        #         })
        # self.action_put_in_pack()
        # self.create_package_to_ship()

        self.with_context(create_backorder=True).button_validate()
        locations = self.move_line_ids.mapped('location_id')
        for location in locations:
            location.update({
                'is_occupied': False,
            })
        return self.env['ir.attachment'].search([('res_model', '=', 'stock.picking'), ('res_id', '=', self.id)])

    def _pre_action_done_hook(self):
        vals = super(StockPicking, self)._pre_action_done_hook()
        if isinstance(vals, dict):
            if self._context.get('create_backorder'):
                if (
                        vals.get('type') == 'ir.actions.act_window' and
                        vals.get('res_model') == 'stock.backorder.confirmation'
                ):
                    pickings_to_validate = self.env.context.get(
                        'button_validate_picking_ids')
                    if pickings_to_validate:
                        pickings_to_validate = self.env['stock.picking'].browse(
                            pickings_to_validate).with_context(skip_backorder=True)
                        return pickings_to_validate.button_validate()
        return vals

    def attach_carrier_id(self):
        lines = []
        days = 0
        hours = 0
        image_1 = False
        image_2 = False
        operations_1 = ''
        operations_2 = ''
        rec = self
        if not self.carrier_id:
            carrier = self.env['delivery.carrier'].search(
                [('client_company_id', '=', self.sale_id.partner_invoice_id.id),
                 ('country_ids', '=', self.sale_id.partner_id.country_id.id),
                 ('zip_prefix_ids', '=', self.sale_id.partner_id.zip[0])])
            if carrier:
                self.write({
                    'carrier_id': carrier.id,
                })
                try:
                    self.create_package_to_ship()
                except Exception as e:
                    self.write({
                        'carrier_id': False,
                    })
                    return json.dumps({'code': 20, 'message': f'{e}'})
                if self.package_ids:
                    move_ids = self.move_ids_without_package
                    for pkg in self.package_ids:
                        package_details = []
                        moves_lines = self.env['stock.move.line'].search([('result_package_id', '=', pkg.id)])
                        for move_line in moves_lines:
                            images = []
                            operations = []
                            diff = datetime.now() - move_line.picking_id.scheduled_date
                            if diff.days:
                                days = diff.days
                                if diff.seconds >= 3600:
                                    hours = int(diff.seconds / 3600)
                                    if hours < 9:
                                        hours = str(0) + str(hours)
                            else:
                                days = '00'
                                if diff.seconds > 3600:
                                    hours = int(diff.seconds / 3600)
                                else:
                                    hours = '00'
                            for printing_line in move_line.move_id.sale_line_id.printing_details_id.printing_details_ids:
                                images.append((printing_line.mockup_img))
                                operations.append(printing_line.location.location)
                            try:
                                image_1 = images[1].decode()
                                operations_1 = operations[1]
                            except Exception as e:
                                pass
                            try:
                                image_2 = images[2].decode()
                                operations_2 = operations[2]
                            except Exception as e:
                                pass
                            mo_state = move_line.move_id.sale_line_id.manufacturing_order_id.barcode_status
                            status = ''
                            if mo_state == 'added_in_batch':
                                status = 'Added In Batch And Waiting for Label Printing'
                            if mo_state == 'waiting_components':
                                status = 'To Be Picked'
                            if mo_state == 'components_picked':
                                status = 'To Be Printed'
                            if mo_state == 'waiting_binning':
                                status = 'To Be Binned'
                            if mo_state == 'mrp_done':
                                status = 'To Be Shipped'

                            package_details.append({
                                'name': pkg.name,
                                'sale_order_id': move_line.picking_id.origin,
                                'sale_order_name': move_line.picking_id.origin,
                                'transfer_id': move_line.picking_id.id or False,
                                'customer_name': move_line.move_id.sale_line_id.order_id.partner_id.name or ' ',
                                'client_name': move_line.move_id.sale_line_id.order_id.partner_invoice_id.name or False,
                                'image_0': (images[0].decode() if images and images[0] else False),
                                'image_1': image_1,
                                'image_2': image_2,
                                'operations_0': (operations[0] if operations and operations[0] else ''),
                                'operations_1': operations_1,
                                'operations_2': operations_2,
                                'product_name': move_line.move_id.product_id.name,
                                'number': move_line.move_id.sale_line_id.number,
                                'manufacturing_order_name': move_line.move_id.sale_line_id.manufacturing_order_id.name,
                                'size': [attribute.name for attribute in
                                         move_line.move_id.product_id.product_template_attribute_value_ids if
                                         'size' in attribute.attribute_id.name.lower()][0] if [attribute.name for
                                                                                               attribute
                                                                                               in
                                                                                               move_line.move_id.product_id.product_template_attribute_value_ids
                                                                                               if
                                                                                               'size' in attribute.attribute_id.name.lower()] else " ",
                                'color': [attribute.name for attribute in
                                          move_line.move_id.product_id.product_template_attribute_value_ids
                                          if
                                          'color' in attribute.attribute_id.name.lower()][0] if [attribute.name for
                                                                                                 attribute in
                                                                                                 move_line.move_id.product_id.product_template_attribute_value_ids
                                                                                                 if
                                                                                                 'color' in attribute.attribute_id.name.lower()] else " ",
                                'operations': ' + '.join(
                                    move_line.move_id.sale_line_id.printing_details_id.printing_details_ids.location.mapped(
                                        'location')) or 'No Printing Details Provided',
                                'status': status,
                                'allocated_bin': move_line.move_id.sale_line_id.manufacturing_order_id.location_dest_id.display_name or False,
                                'full_order_ready': all([move.state == 'assigned' for move in move_ids]),
                                'carrier_id': self.carrier_id.id if self.carrier_id else 0,
                                'order_hours': hours,
                                'order_days': days,
                                'ordered_quantity': sum(
                                    move_line.move_id.sale_line_id.order_id.order_line.mapped(
                                        'product_uom_qty')) or False,
                                'package_image': self.package_ids[
                                    0].package_type_id.package_image.decode() if self.package_ids and self.package_ids.package_type_id.package_image else '',
                            })
                        lines.append(package_details)
                    return json.dumps(lines)
                else:
                    return False
        else:
            if self.package_ids:
                move_ids = self.move_ids_without_package
                for pkg in self.package_ids:
                    package_details = []
                    moves_lines = self.env['stock.move.line'].search([('result_package_id', '=', pkg.id)])
                    for move_line in moves_lines:
                        images = []
                        operations = []
                        diff = datetime.now() - move_line.picking_id.scheduled_date
                        if diff.days:
                            days = diff.days
                            if diff.seconds >= 3600:
                                hours = int(diff.seconds / 3600)
                                if hours < 9:
                                    hours = str(0) + str(hours)
                        else:
                            days = '00'
                            if diff.seconds > 3600:
                                hours = int(diff.seconds / 3600)
                            else:
                                hours = '00'
                        for printing_line in move_line.move_id.sale_line_id.printing_details_id.printing_details_ids:
                            images.append((printing_line.mockup_img))
                            operations.append(printing_line.location.location)
                        try:
                            image_1 = images[1].decode()
                            operations_1 = operations[1]
                        except Exception as e:
                            pass
                        try:
                            image_2 = images[2].decode()
                            operations_2 = operations[2]
                        except Exception as e:
                            pass
                        mo_state = move_line.move_id.sale_line_id.manufacturing_order_id.barcode_status
                        status = ''
                        if mo_state == 'added_in_batch':
                            status = 'Added In Batch And Waiting for Label Printing'
                        if mo_state == 'waiting_components':
                            status = 'To Be Picked'
                        if mo_state == 'components_picked':
                            status = 'To Be Printed'
                        if mo_state == 'waiting_binning':
                            status = 'To Be Binned'
                        if mo_state == 'mrp_done':
                            status = 'To Be Shipped'

                        package_details.append({
                            'name': pkg.name,
                            'sale_order_id': move_line.picking_id.origin,
                            'sale_order_name': move_line.picking_id.origin,
                            'transfer_id': move_line.picking_id.id or False,
                            'customer_name': move_line.move_id.sale_line_id.order_id.partner_id.name or ' ',
                            'client_name': move_line.move_id.sale_line_id.order_id.partner_invoice_id.name or False,
                            'image_0': (images[0].decode() if images and images[0] else False),
                            'image_1': image_1,
                            'image_2': image_2,
                            'operations_0': (operations[0] if operations and operations[0] else ''),
                            'operations_1': operations_1,
                            'operations_2': operations_2,
                            'product_name': move_line.move_id.product_id.name,
                            'number': move_line.move_id.sale_line_id.number,
                            'manufacturing_order_name': move_line.move_id.sale_line_id.manufacturing_order_id.name,
                            'size': [attribute.name for attribute in
                                     move_line.move_id.product_id.product_template_attribute_value_ids if
                                     'size' in attribute.attribute_id.name.lower()][0] if [attribute.name for
                                                                                           attribute
                                                                                           in
                                                                                           move_line.move_id.product_id.product_template_attribute_value_ids
                                                                                           if
                                                                                           'size' in attribute.attribute_id.name.lower()] else " ",
                            'color': [attribute.name for attribute in
                                      move_line.move_id.product_id.product_template_attribute_value_ids
                                      if
                                      'color' in attribute.attribute_id.name.lower()][0] if [attribute.name for
                                                                                             attribute in
                                                                                             move_line.move_id.product_id.product_template_attribute_value_ids
                                                                                             if
                                                                                             'color' in attribute.attribute_id.name.lower()] else " ",
                            'operations': ' + '.join(
                                move_line.move_id.sale_line_id.printing_details_id.printing_details_ids.location.mapped(
                                    'location')) or 'No Printing Details Provided',
                            'status': status,
                            'allocated_bin': move_line.move_id.sale_line_id.manufacturing_order_id.location_dest_id.display_name or False,
                            'full_order_ready': all([move.state == 'assigned' for move in move_ids]),
                            'carrier_id': self.carrier_id.id if self.carrier_id else 0,
                            'order_hours': hours,
                            'order_days': days,
                            'ordered_quantity': sum(
                                move_line.move_id.sale_line_id.order_id.order_line.mapped('product_uom_qty')) or False,
                            'package_image': self.package_ids[
                                0].package_type_id.package_image.decode() if self.package_ids and self.package_ids.package_type_id.package_image else '',
                        })
                    lines.append(package_details)
                return json.dumps(lines)
            else:
                return False


class StockPackageType(models.Model):
    _inherit = 'stock.package.type'

    def find_package(self):
        package_id = self.env['stock.package.type'].search([('id', '=', self.id)])
        if package_id:
            return json.dumps(package_id.package_image.decode())


class StockMoveExt(models.Model):
    _inherit = 'stock.move'

    confirmed = fields.Boolean(default=False)
