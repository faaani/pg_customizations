import json
import re
from datetime import date
from odoo import http
from odoo.http import request
from datetime import date, datetime, timedelta


class ShippingController(http.Controller):

    @http.route('/ready/transfers/', type='http', auth='public')
    def get_ready_transfers(self, user_id=None):
        """
        fetch records from transfers
        """
        # transfer_ids = request.env['stock.picking'].search(
        #     [('state', '=', 'assigned'), ('origin', 'like', "S%")])
        stock_moves = request.env['stock.move'].search(
            [('state', '=', 'assigned'), ('origin', 'like', "S%"), ('picking_id', '!=', False),
             ('sale_line_id', '!=', False)])
        lines = []
        days = 0
        hours = 00
        for rec in stock_moves:
            # if all(trans.state == 'assigned' for trans in rec.move_ids_without_package):
            if rec.picking_id.scheduled_date:
                diff = datetime.now() - rec.picking_id.scheduled_date
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
            mo_state = rec.sale_line_id.manufacturing_order_id.barcode_status
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
            lines.append({
                'order_days': days,
                'order_hours': hours,
                'name': rec.picking_id.name,
                'manufacturing_name': rec.sale_line_id.manufacturing_order_id.name if rec.sale_line_id.manufacturing_order_id else 'false',
                'state': status,
                'origin': rec.origin if rec.origin else 'No Origin Defined',
                'scheduled_date': str(rec.date_deadline.date() if rec.date_deadline else 'Not Selected')
            })
        return json.dumps(lines)

    @http.route('/get/transfer/orders/', type='http', auth='public', csrf=False)
    def get_transfer_orders(self, **kwargs):
        """
        fetch a specific record from transfer orders
        """
        days = 0
        hours = 0
        searched_value = kwargs.get('value')[-5:] if kwargs.get('value') and len(
            kwargs.get('value')) >= 5 else kwargs.get('value')
        # searched_value = kwargs.get('value')[-7:] if kwargs.get('value') and len(
        #     kwargs.get('value')) >= 7 else kwargs.get('value')
        barcode = kwargs.get('barcode')
        if searched_value and len(searched_value) != 5:
            kwargs['barcode'] = ''
        if barcode:
            match = re.search(r'M.*', barcode)
            if match:
                barcode = match.group(0)
            barcode = ''.join(barcode.splitlines())

        lines = []
        image_1 = False
        image_2 = False
        operations_1 = ''
        operations_2 = ''
        no_carrier = False
        multi_carrier = False
        if searched_value:
            searched_picking = request.env['mrp.production'].search(
                [('name', 'like', f"%{searched_value}"),
                 ('state', 'in', ('to_close', 'done'))]).sale_order_line_id.order_id.picking_ids.filtered(
                lambda l: l.state == 'assigned' and l.picking_type_id.sequence_code == 'OUT')
            if searched_picking:
                mo_name = request.env['mrp.production'].search(
                    [('name', 'like', f"%{searched_value}")]).name
                searched_picking = searched_picking[0]
                if not searched_picking.carrier_id:
                    carrier = request.env['delivery.carrier'].search(
                        [('client_company_id', '=', searched_picking.sale_id.partner_invoice_id.id),
                         ('country_ids', '=', searched_picking.sale_id.partner_id.country_id.id),
                         ('zip_prefix_ids', '=', searched_picking.sale_id.partner_id.zip[0])])
                    if not carrier:
                        no_carrier = True
                    elif carrier and len(carrier) > 1:
                        multi_carrier = True
                    else:
                        if searched_picking.sale_id.service_level:
                            service_level_id = request.env['canpost.service.type'].search(
                                [('look_up', '=', searched_picking.sale_id.service_level)])
                            if service_level_id:
                                searched_picking.write({
                                    'service_level_id': service_level_id.id
                                })
                            else:
                                return json.dumps({'reason': 'service level not found',
                                                   'message': f'No Service Level Matched to the Provided service level ({searched_picking.sale_id.service_level})'})
                        else:
                            searched_picking.write({
                                'service_level_id': carrier.canpost_service_type.id
                            })

                # if searched_picking and all(trans.state in ('assigned', 'done') for trans in searched_picking.move_ids_without_package):
                move_ids = searched_picking.move_ids_without_package.filtered(lambda l:l.sale_line_id.manufacturing_order_id)

                if searched_picking.scheduled_date:
                    diff = datetime.now() - searched_picking.scheduled_date
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
                sale_order_id = searched_picking.move_ids_without_package[0].sale_line_id.order_id.id
                sale_order_name = searched_picking.move_ids_without_package[0].sale_line_id.order_id.display_name
                for move in move_ids:
                    images = []
                    operations = []
                    for printing_line in move.sale_line_id.printing_details_id.printing_details_ids:
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
                    mo_state = move.sale_line_id.manufacturing_order_id.barcode_status
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
                    if mo_name == move.sale_line_id.manufacturing_order_id.name:
                        move.update({
                            'confirmed': True
                        })
                    lines.append({
                        'sale_order_id': sale_order_id,
                        'sale_order_name': sale_order_name,
                        'transfer_id': searched_picking.id or False,
                        'customer_name': move.sale_line_id.order_id.partner_id.name or ' ',
                        'client_name': move.sale_line_id.order_id.partner_invoice_id.name or False,
                        'order_hours': hours,
                        'order_days': days,
                        'ordered_quantity': sum(
                            move.sale_line_id.order_id.order_line.mapped('product_uom_qty')) or False,
                        'allocated_bin': move.sale_line_id.manufacturing_order_id.location_dest_id.display_name or False,
                        'product_name': move.product_id.name,
                        'number': move.sale_line_id.number,
                        'manufacturing_order_name': move.sale_line_id.manufacturing_order_id.name,
                        'size': [attribute.name for attribute in
                                 move.product_id.product_template_attribute_value_ids if
                                 'size' in attribute.attribute_id.name.lower()][0] if [attribute.name for attribute
                                                                                       in
                                                                                       move.product_id.product_template_attribute_value_ids
                                                                                       if
                                                                                       'size' in attribute.attribute_id.name.lower()] else " ",
                        'color': [attribute.name for attribute in
                                  move.product_id.product_template_attribute_value_ids
                                  if
                                  'color' in attribute.attribute_id.name.lower()][0] if [attribute.name for
                                                                                         attribute in
                                                                                         move.product_id.product_template_attribute_value_ids
                                                                                         if
                                                                                         'color' in attribute.attribute_id.name.lower()] else " ",
                        'operations': ' + '.join(
                            move.sale_line_id.printing_details_id.printing_details_ids.location.mapped(
                                'location')) or 'No Printing Details Provided',
                        'image_0': (images[0].decode() if images and images[0] else False),
                        'image_1': image_1,
                        'image_2': image_2,
                        'operations_0': (operations[0] if operations and operations[0] else ''),
                        'operations_1': operations_1,
                        'operations_2': operations_2,
                        'status': status,
                        'full_order_ready': all([move.state == 'assigned' for move in move_ids]),
                        'carrier_id': searched_picking.carrier_id.id if searched_picking.carrier_id else 0,
                        'package_ids': move.picking_id.package_ids.ids if move.picking_id.package_ids else False,
                        'no_carrier': no_carrier,
                        'multi_carrier': multi_carrier,
                        'confirm_order': move.confirmed,
                    })
            else:
                return json.dumps({'error': 'not found',
                                   'message': 'Delivery Order Not Ready!'})
        else:
            searched_picking = request.env['mrp.production'].search(
                [('name', 'like', f"%{barcode}"),
                 ('state', 'in', ('to_close', 'done'))]).sale_order_line_id.order_id.picking_ids.filtered(
                lambda l: l.picking_type_id.sequence_code == 'OUT')
            if searched_picking:
                searched_picking = searched_picking[0]
                if not searched_picking.carrier_id:
                    carrier = request.env['delivery.carrier'].search(
                        [('client_company_id', '=', searched_picking.sale_id.partner_invoice_id.id),
                         ('country_ids', '=', searched_picking.sale_id.partner_id.country_id.id),
                         ('zip_prefix_ids', '=', searched_picking.sale_id.partner_id.zip[0])])
                    if not carrier:
                        no_carrier = True
                    elif carrier and len(carrier) > 1:
                        multi_carrier = True
                    else:
                        if searched_picking.sale_id.service_level:
                            service_level_id = request.env['canpost.service.type'].search(
                                [('look_up', '=', searched_picking.sale_id.service_level)])
                            if service_level_id:
                                searched_picking.write({
                                    'service_level_id': service_level_id.id
                                })
                            else:
                                return json.dumps({'reason': 'service level not found',
                                                   'message': f'No Service Level Matched to the Provided service level ({searched_picking.sale_id.service_level})'})
                        else:
                            searched_picking.write({
                                'service_level_id': carrier.canpost_service_type.id
                            })

                move_ids = searched_picking.move_ids_without_package.filtered(lambda l:l.sale_line_id.manufacturing_order_id != False)

                if searched_picking.scheduled_date:
                    diff = datetime.now() - searched_picking.scheduled_date
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
                sale_order_id = searched_picking.move_ids_without_package[0].sale_line_id.order_id.id
                sale_order_name = searched_picking.move_ids_without_package[0].sale_line_id.order_id.display_name
                for move in move_ids:
                    images = []
                    operations = []
                    for printing_line in move.sale_line_id.printing_details_id.printing_details_ids:
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
                    mo_state = move.sale_line_id.manufacturing_order_id.barcode_status
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
                    if barcode == move.sale_line_id.manufacturing_order_id.name:
                        move.update({
                            'confirmed': True
                        })
                    lines.append({
                        'sale_order_id': sale_order_id,
                        'sale_order_name': sale_order_name,
                        'transfer_id': searched_picking.id or False,
                        'customer_name': move.sale_line_id.order_id.partner_id.name or ' ',
                        'client_name': move.sale_line_id.order_id.partner_invoice_id.name or False,
                        'order_hours': hours,
                        'order_days': days,
                        'ordered_quantity': sum(
                            move.sale_line_id.order_id.order_line.mapped('product_uom_qty')) or False,
                        'allocated_bin': move.sale_line_id.manufacturing_order_id.location_dest_id.display_name or False,
                        'product_name': move.product_id.name,
                        'number': move.sale_line_id.number,
                        'manufacturing_order_name': move.sale_line_id.manufacturing_order_id.name,
                        'size': [attribute.name for attribute in
                                 move.product_id.product_template_attribute_value_ids if
                                 'size' in attribute.attribute_id.name.lower()][0] if [attribute.name for attribute
                                                                                       in
                                                                                       move.product_id.product_template_attribute_value_ids
                                                                                       if
                                                                                       'size' in attribute.attribute_id.name.lower()] else " ",
                        'color': [attribute.name for attribute in
                                  move.product_id.product_template_attribute_value_ids
                                  if
                                  'color' in attribute.attribute_id.name.lower()][0] if [attribute.name for
                                                                                         attribute in
                                                                                         move.product_id.product_template_attribute_value_ids
                                                                                         if
                                                                                         'color' in attribute.attribute_id.name.lower()] else " ",
                        'operations': ' + '.join(
                            move.sale_line_id.printing_details_id.printing_details_ids.location.mapped(
                                'location')) or 'No Printing Details Provided',
                        'image_0': (images[0].decode() if images and images[0] else False),
                        'image_1': image_1,
                        'image_2': image_2,
                        'operations_0': (operations[0] if operations and operations[0] else ''),
                        'operations_1': operations_1,
                        'operations_2': operations_2,
                        'status': status,
                        'full_order_ready': all([move.state == 'assigned' for move in move_ids]),
                        'carrier_id': searched_picking.carrier_id.id if searched_picking.carrier_id else 0,
                        'package_ids': move.picking_id.package_ids.ids if move.picking_id.package_ids else False,
                        'no_carrier': no_carrier,
                        'multi_carrier': multi_carrier,
                        'confirm_order': move.confirmed,
                    })
            else:
                return json.dumps({'error': 'not found',
                                   'message': 'Delivery Order Not Ready'})

        return json.dumps(lines)
