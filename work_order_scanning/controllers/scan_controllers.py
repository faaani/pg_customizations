import json
from datetime import datetime, date
from odoo import http
from odoo.http import request
import re


class ScanController(http.Controller):

    @http.route('/work/order/infos', type='http', auth='public')
    def get_work_orders(self, user_id=None):
        """
        fetch records from work orders
        """
        work_orders = request.env['mrp.workorder'].search([('state', '=', 'ready')])
        lines = []
        days = 0
        hours = 00
        for rec in work_orders:
            if rec.production_id.date_planned_start:
                diff = datetime.now() - rec.production_id.date_planned_start
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
            lines.append({
                'word_order_id': rec.id,
                'name': rec.production_id.name,
                'state': 'Ready' if rec.state else False,
                'order_days': days,
                'order_hours': hours,
                'date': str(
                    rec.production_id.date_planned_start.date() if rec.production_id.date_planned_start else None),
                'operation': rec.name
            })
        return json.dumps(lines)

    @http.route('/scan/work/order/', type='http', auth='public', csrf=False)
    def get_manufacturing_order(self, *args, **params):
        """
        fetch records from work orders and doing operations
        """
        try:
            filter_value = params.get('filter_value')
            if filter_value == 'select_filter':
                return json.dumps({'error': 'no filter', 'message': 'No filter is selected.Please select a filter.'})
            searched_value = params.get('value')
            # This chunk of code developed to handle when we add oder number in search bar also scan the order
            if searched_value:
                barcode = searched_value
            else:
                barcode = params.get('barcode')
                match = re.search(r'M.*', barcode)
                if match:
                    barcode = match.group(0)
                barcode = ''.join(barcode.splitlines())
            manufacturing_order_id = request.env['mrp.production'].search([('name', 'like', f"%{barcode}")])
            if manufacturing_order_id:
                manufacturing_order_id = manufacturing_order_id.filtered(lambda l: l.scrapped == False)
            work_center = int(params.get('work_center'))
            work_center = request.env['mrp.workcenter'].search([('id', '=', work_center)])
            lines = []
            days = 0
            hours = 0
            image_1 = False
            image_2 = False
            if manufacturing_order_id:
                for rec in manufacturing_order_id.workorder_ids:
                    if rec.state == 'ready' and rec.name.lower() == filter_value:
                        "update work order state and pass start time"
                        rec.write(
                            {
                                'state': 'progress',
                                'date_planned_start': datetime.now(),
                                'workcenter_id': work_center.id or request.env.ref(
                                    'sale_order_customization.work_center_unallocated').id
                            }
                        )
                        if manufacturing_order_id.date_planned_start:
                            diff = datetime.now() - manufacturing_order_id.sale_order_line_id.order_id.date_order
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
                            images = []
                            if len(manufacturing_order_id.workorder_ids.printing_detail_line_id) > 1:
                                for img in manufacturing_order_id.workorder_ids.printing_detail_line_id:
                                    if img.id != rec.printing_detail_line_id.id:
                                        images.append(img.mockup_img)
                            try:
                                image_1 = images[0].decode()
                            except Exception as e:
                                pass
                            try:
                                image_2 = images[1].decode()
                            except Exception as e:
                                pass

                            lines.append({
                                'manufacturing_order_id': manufacturing_order_id.id,
                                'manufacturing_order_name': manufacturing_order_id.name,
                                'sale_order_id': manufacturing_order_id.sale_order_line_id.order_id.name or False,
                                'partner_id': manufacturing_order_id.sale_order_line_id.order_id.partner_id.name or False,
                                'client_id': manufacturing_order_id.sale_order_line_id.order_id.partner_invoice_id.name or False,
                                'quantity_order': manufacturing_order_id.product_qty or False,
                                'item': str(manufacturing_order_id.sale_order_line_id.number) + " of " + str(
                                    len(manufacturing_order_id.sale_order_line_id.order_id.order_line)) or False,
                                'operations': ' + '.join(
                                    manufacturing_order_id.sale_order_line_id.printing_details_id.printing_details_ids.location.mapped(
                                        'code')) or False,
                                'order_hours': hours,
                                'order_days': days,
                                'product_id': rec.product_id.display_name or False,
                                'size': [attribute.name for attribute in
                                         manufacturing_order_id.sale_order_line_id.product_id.product_template_attribute_value_ids
                                         if
                                         'size' in attribute.attribute_id.name.lower()][0] if [attribute.name for
                                                                                               attribute in
                                                                                               manufacturing_order_id.sale_order_line_id.product_id.product_template_attribute_value_ids
                                                                                               if
                                                                                               'size' in attribute.attribute_id.name.lower()] else " ",
                                'color_type': [attribute.name for attribute in
                                               manufacturing_order_id.sale_order_line_id.product_id.product_template_attribute_value_ids
                                               if
                                               'color' in attribute.attribute_id.name.lower()][0] if [attribute.name for
                                                                                                      attribute in
                                                                                                      manufacturing_order_id.sale_order_line_id.product_id.product_template_attribute_value_ids
                                                                                                      if
                                                                                                      'color' in attribute.attribute_id.name.lower()] else " ",
                                'operations': ' + '.join(
                                    manufacturing_order_id.sale_order_line_id.printing_details_id.printing_details_ids.location.mapped(
                                        'location')) or False,
                                'operation': rec.name or False,
                                'printing_detail_id': manufacturing_order_id.sale_order_line_id.printing_details_id.id or False,
                                'work_order_id': rec.id or False,
                                'filter_img': rec.printing_detail_line_id.mockup_img.decode() if rec.printing_detail_line_id.mockup_img else False,
                                'second_img': image_1,
                                'third_img': image_2,
                                'art_work_img': rec.printing_detail_line_id.artwork_img.decode() if rec.printing_detail_line_id.artwork_img else False,
                                'art_work_img_name': str(
                                    rec.printing_detail_line_id.setup or "") + "_" +
                                                     str(rec.printing_detail_line_id.pallet or "") + "_" +
                                                     "Id" + str(rec.id) +
                                                     str(manufacturing_order_id.sale_order_line_id.printing_details_id.color_type or "")
                                                     + str(
                                    manufacturing_order_id.sale_order_line_id.printing_details_id.size or "") + str(
                                    rec.printing_detail_line_id.location.location or "") + "_" + str(
                                    int(manufacturing_order_id.sale_order_line_id.product_uom_qty) or "") + "_" +
                                                     str(rec.printing_detail_line_id.offset_x or "") + "_" +
                                                     str(rec.printing_detail_line_id.offset_y or "") or False
                            })
                        return json.dumps(lines)
                    else:
                        work_order_ready_state = manufacturing_order_id.workorder_ids.filtered(
                            lambda l: l.state == 'ready')
                        if work_order_ready_state:
                            return json.dumps(
                                {'error': 'not found ready current operation',
                                 'message': 'Wrong Print Location Selected'})
                        else:
                            return json.dumps(
                                {'error': 'not found ready',
                                 'message': f'No records found in ready state of order {barcode}', 'barcode': barcode})
            else:
                return json.dumps({'error': 'not found', 'message': 'No record found.'})
        except Exception as e:
            return e

    @http.route('/print/label', type='http', auth='public', csrf=False)
    def get_print_label(self, **kwargs):
        """
        get print label report form
        """
        print_details_id = kwargs.get('print_details_id', False)
        return json.dumps(request.env['printing.details'].print_label(print_details_id))

    @http.route('/scan/work/order/again', type='http', auth='public', csrf=False)
    def get_manufacturing_order_again(self, *args, **params):
        """
        fetch records from work orders and doing operations
        """
        days = 0
        hours = 0
        try:
            # barcode = params.get('barcode')
            # filter_value = params.get('filter_value')
            # if filter_value == 'select_filter':
            #     return json.dumps({'error': 'no filter', 'message': 'No filter is selected.Please select a filter.'})
            filter_value = params.get('filter_value')
            if filter_value == 'select_filter':
                return json.dumps({'error': 'no filter', 'message': 'No filter is selected.Please select a filter.'})
            searched_value = params.get('value')
            if searched_value and not params.get('barcode'):
                barcode = searched_value
            else:
                barcode = params.get('barcode')
                match = re.search(r'M.*', barcode)
                if match:
                    barcode = match.group(0)
                barcode = ''.join(barcode.splitlines())
            manufacturing_order_id = request.env['mrp.production'].search([('name', 'like', f"%{barcode}")])
            if manufacturing_order_id:
                manufacturing_order_id = manufacturing_order_id.filtered(lambda l: l.scrapped == False)
            work_center = int(params.get('work_center'))
            work_center = request.env['mrp.workcenter'].search([('id', '=', work_center)])
            lines = []
            image_1 = False
            image_2 = False
            if manufacturing_order_id:
                for rec in manufacturing_order_id.workorder_ids:
                    if rec.name.lower() == filter_value:
                        "update work order work center"
                        rec.write(
                            {'state': 'ready'

                             }
                        )
                        rec.write(
                            {
                                'state': 'done',
                                'workcenter_id': work_center.id or request.env.ref(
                                    'sale_order_customization.work_center_unallocated').id
                            }
                        )
                        if manufacturing_order_id.date_planned_start:
                            diff = datetime.now() - manufacturing_order_id.sale_order_line_id.order_id.date_order
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
                            images = []
                            if len(manufacturing_order_id.workorder_ids.printing_detail_line_id) > 1:
                                for img in manufacturing_order_id.workorder_ids.printing_detail_line_id:
                                    if img.id != rec.printing_detail_line_id.id:
                                        images.append(img.mockup_img)
                            try:
                                image_1 = images[1].decode()
                            except Exception as e:
                                pass
                            try:
                                image_2 = images[2].decode()
                            except Exception as e:
                                pass

                            lines.append({
                                'manufacturing_order_id': manufacturing_order_id.id,
                                'manufacturing_order_name': manufacturing_order_id.name,
                                'sale_order_id': manufacturing_order_id.sale_order_line_id.order_id.name or False,
                                'partner_id': manufacturing_order_id.sale_order_line_id.order_id.partner_id.name or False,
                                'client_id': manufacturing_order_id.sale_order_line_id.order_id.partner_invoice_id.name or False,
                                'quantity_order': manufacturing_order_id.product_qty or False,
                                'item': str(manufacturing_order_id.sale_order_line_id.number) + " of " + str(
                                    len(manufacturing_order_id.sale_order_line_id.order_id.order_line)) or False,
                                'operations': ' + '.join(
                                    manufacturing_order_id.sale_order_line_id.printing_details_id.printing_details_ids.location.mapped(
                                        'code')) or False,
                                'order_hours': hours,
                                'order_days': days,
                                'product_id': rec.product_id.display_name or False,
                                'size': [attribute.name for attribute in
                                         manufacturing_order_id.sale_order_line_id.product_id.product_template_attribute_value_ids
                                         if
                                         'size' in attribute.attribute_id.name.lower()][0] if [attribute.name for
                                                                                               attribute in
                                                                                               manufacturing_order_id.sale_order_line_id.product_id.product_template_attribute_value_ids
                                                                                               if
                                                                                               'size' in attribute.attribute_id.name.lower()] else " ",
                                'color_type': [attribute.name for attribute in
                                               manufacturing_order_id.sale_order_line_id.product_id.product_template_attribute_value_ids
                                               if
                                               'color' in attribute.attribute_id.name.lower()][0] if [attribute.name for
                                                                                                      attribute in
                                                                                                      manufacturing_order_id.sale_order_line_id.product_id.product_template_attribute_value_ids
                                                                                                      if
                                                                                                      'color' in attribute.attribute_id.name.lower()] else " ",
                                'operations': ' + '.join(
                                    manufacturing_order_id.sale_order_line_id.printing_details_id.printing_details_ids.location.mapped(
                                        'location')) or False,
                                'operation': rec.name or False,
                                'printing_detail_id': manufacturing_order_id.sale_order_line_id.printing_details_id.id or False,
                                'work_order_id': rec.id or False,
                                'filter_img': rec.printing_detail_line_id.mockup_img.decode() if rec.printing_detail_line_id.mockup_img else False,
                                'second_img': image_1,
                                'third_img': image_2,
                                'art_work_img': rec.printing_detail_line_id.artwork_img.decode() if rec.printing_detail_line_id.artwork_img else False,
                                'art_work_img_name': str(
                                    rec.printing_detail_line_id.setup or "") + "_" +
                                                     str(rec.printing_detail_line_id.pallet or "") + "_" +
                                                     "Id" + str(rec.id) +
                                                     str(manufacturing_order_id.sale_order_line_id.printing_details_id.color_type or "")
                                                     + str(
                                    manufacturing_order_id.sale_order_line_id.printing_details_id.size or "") + str(
                                    rec.printing_detail_line_id.location.location or "") + "_" + str(
                                    int(manufacturing_order_id.sale_order_line_id.product_uom_qty) or "") + "_" +
                                                     str(rec.printing_detail_line_id.offset_x or "") + "_" +
                                                     str(rec.printing_detail_line_id.offset_y or "") or False
                            })

                        return json.dumps(lines)
                else:
                    return json.dumps({'error': 'not found', 'message': 'No record found.'})
            else:
                return json.dumps({'error': 'not found', 'message': 'No record found.'})
        except Exception as e:
            return e
