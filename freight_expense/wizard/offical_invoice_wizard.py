# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from collections import defaultdict

_logger = logging.getLogger(__name__)


class POWizard(models.TransientModel):
    _name = 'official.purchase.wizard'

    shipment_number = fields.Many2one('freight.operation', 'Shipment ID')
    customer_id = fields.Many2one('res.partner', 'Vendor')


    def action_confirm(self):
        selected_records = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))

        # Dictionary to store records grouped by clearance company, tracking agent, and agent ID
        grouped_records = defaultdict(lambda: defaultdict(list))

        # Group records by clearance company, tracking agent, and agent ID
        for record in selected_records:
            if not record.currency_id:
                raise UserError(_('Please Check Currency'))

            key = (record.expense_service_type, record.currency_id.id)
            clearance_company = record.clearance_company.id if record.clearance_company else None
            tracking_agent = record.tracking_agent.id if record.tracking_agent else None
            agent_id = record.agent_id.id if record.agent_id else None

            grouped_records[key][(clearance_company, tracking_agent, agent_id)].append(record)

        # Create purchase orders for each group of records
        for key, partners in grouped_records.items():
            expense_service_type, currency_id = key
            for partner_key, group in partners.items():
                clearance_company_id, tracking_agent_id, agent_id = partner_key

                partner_ids = [id for id in [clearance_company_id, tracking_agent_id, agent_id] if id]

                if len(set(partner_ids)) == 1:
                    # If there is only one partner, create a single purchase order
                    partner_id = partner_ids[0]
                    vals = {
                        'partner_id': partner_id,
                        'po_type': 'official_receipt',
                        'freight_operation_id': group[0].shipment_number.id,
                        'weight': group[0].shipment_number.weight,
                        'net_weight': group[0].shipment_number.net_weight,
                        'chargeable_weight': group[0].shipment_number.chargeable_weight,
                        'source_location_id': group[0].shipment_number.source_location_id.id,
                        'destination_location_id': group[0].shipment_number.destination_location_id.id,
                        'transport': group[0].shipment_number.transport,
                        'volume': group[0].shipment_number.volume,
                        'ocean_shipment_type': group[0].shipment_number.ocean_shipment_type,
                        'currency_id': currency_id,
                        'state': 'purchase',
                        'order_line': [],
                    }

                    for record in group:
                        if not record.shipment_number:
                            raise UserError(_('Please Check Shipment Number'))

                        if not record.purchase_id:
                            vals['order_line'].append((0, 0, {
                                'product_id': record.product_id.id,
                                'name': record.product_id.name,
                                'product_qty': 1,
                                'price_unit': record.amount_cost,
                            }))

                    if vals['order_line']:
                        purchase_order = self.env['purchase.order'].create(vals)
                        # Set purchase_id for each record in the group
                        for record in group:
                            record.purchase_id = purchase_order.id  # Set purchase_id for each record
                else:
                    # If there are multiple partners, create one purchase order for each partner
                    for partner_id in partner_ids:
                        vals = {
                            'partner_id': partner_id,
                            'po_type': 'official_receipt',
                            'freight_operation_id': group[0].shipment_number.id,
                            'weight': group[0].shipment_number.weight,
                            'net_weight': group[0].shipment_number.net_weight,
                            'chargeable_weight': group[0].shipment_number.chargeable_weight,
                            'source_location_id': group[0].shipment_number.source_location_id.id,
                            'destination_location_id': group[0].shipment_number.destination_location_id.id,
                            'transport': group[0].shipment_number.transport,
                            'volume': group[0].shipment_number.volume,
                            'ocean_shipment_type': group[0].shipment_number.ocean_shipment_type,
                            'currency_id': currency_id,
                            'state': 'purchase',
                            'order_line': [],
                        }

                        for record in group:
                            if not record.shipment_number:
                                raise UserError(_('Please Check Shipment Number'))

                            if not record.purchase_id:
                                vals['order_line'].append((0, 0, {
                                    'product_id': record.product_id.id,

                                    'name': record.product_id.name,
                                    'product_qty': 1,
                                    'price_unit': record.amount_cost,
                                }))

                        if vals['order_line']:
                            purchase_order = self.env['purchase.order'].create(vals)
                            # Set purchase_id for each record in the group
                            for record in group:
                                record.purchase_id = purchase_order.id  # Set purchase_id for each record


class ClaimWizard(models.TransientModel):
    _name = 'claim.wizard'

    # Define fields necessary for creating an invoice
    # Example:
    partner_id = fields.Many2one('res.partner', string='Customer')
    journal_id = fields.Many2one('account.journal')
    invoice_date = fields.Date(string='Invoice Date')
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.company)

    def action_create_journal_invoice_official(self):
        # Dictionary to store sale orders grouped by currency
        grouped_orders = defaultdict(lambda: self.env['sale.order'])

        selected_records = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))

        # Group sale orders by currency
        for record in selected_records:
            for line in record.order_line:
                grouped_orders[line.currency_id] |= record

        # Create an invoice for each group of sale orders
        for currency, orders in grouped_orders.items():
            invoice_lines = []
            total = 0

            # Collect invoice lines for all orders in the group
            for order in orders:
                if not order.is_claimed:  # Check if the order has already been claimed
                    for order_line in order.order_line:
                        invoice_lines.append((0, 0, {
                            'account_id': order_line.product_id.property_account_expense_id.id or order_line.product_id.categ_id.property_account_expense_categ_id.id,
                            'product_id': order_line.product_id.id,
                            'quantity': 1,
                            'price_unit': order_line.price_unit,
                            'shipment_number': order.freight_operation_id.id,
                        }))
                        total += order_line.price_unit

            if invoice_lines:
                invoice_vals = {
                    'move_type': 'out_invoice',
                    'is_claim': True,
                    'currency_id': currency.id,
                    'journal_id': self.env.ref('freight_expense.els_claim_customer_journal').id,
                    'invoice_date': fields.Date.today(),
                    'partner_id': self.partner_id.id,
                    'invoice_line_ids': invoice_lines,
                    # Add other fields related to the invoice
                    'weight': orders[0].freight_operation_id.weight,
                    'net_weight': orders[0].freight_operation_id.net_weight,
                    'chargeable_weight': orders[0].freight_operation_id.chargeable_weight,
                    'source_location_id': orders[0].freight_operation_id.source_location_id.id,
                    'destination_location_id': orders[0].freight_operation_id.destination_location_id.id,
                    'transport': orders[0].freight_operation_id.transport,
                    'freight_operation_id': orders[0].freight_operation_id.id,
                }
                invoice = self.env['account.move'].create(invoice_vals)
                # Update the selected orders
                orders.filtered(lambda o: not o.is_claimed).write({'invoice_status': 'no', 'is_claimed': True})

        return {'type': 'ir.actions.act_window_close'}


class OfficialBillWizard(models.TransientModel):
    _name = 'official.bill.wizard'

    # Define fields necessary for creating an invoice
    # Example:
    partner_id = fields.Many2one('res.partner', string='Vendor')
    journal_id = fields.Many2one('account.journal')
    invoice_date = fields.Date(string='Invoice Date')
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.company)

    def action_create_journal_official(self):
        # Dictionary to store purchase orders grouped by currency
        grouped_orders = defaultdict(lambda: self.env['purchase.order'])

        selected_records = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))

        # Group purchase orders by currency
        for record in selected_records:
            for line in record.order_line:
                grouped_orders[line.currency_id] |= record

        # Create a claim invoice for each group of purchase orders
        for currency, orders in grouped_orders.items():
            invoice_lines = []
            total = 0

            # Collect invoice lines for all orders in the group
            for order in orders:
                if not order.is_claimed:  # Check if the order has already been claimed
                    for order_line in order.order_line:
                        invoice_lines.append((0, 0, {
                            'account_id': order_line.product_id.property_account_expense_id.id or order_line.product_id.categ_id.property_account_expense_categ_id.id,
                            'product_id': order_line.product_id.id,
                            'quantity': 1,
                            'price_unit': order_line.price_unit,
                            'shipment_number': order.freight_operation_id.id,
                        }))
                        total += order_line.price_unit

            # Create the claim invoice if there are invoice lines
            if invoice_lines:
                invoice_vals = {
                    'move_type': 'in_invoice',
                    'is_claim': True,
                    'currency_id': currency.id,
                    'journal_id': self.env.ref('freight_expense.els_claim_vendor_journal').id,
                    'invoice_date': fields.Date.today(),
                    'partner_id': self.partner_id.id,
                    'invoice_line_ids': invoice_lines,
                    # Add other fields related to the invoice
                    'weight': orders[0].freight_operation_id.weight,
                    'net_weight': orders[0].freight_operation_id.net_weight,
                    'chargeable_weight': orders[0].freight_operation_id.chargeable_weight,
                    'source_location_id': orders[0].freight_operation_id.source_location_id.id,
                    'destination_location_id': orders[0].freight_operation_id.destination_location_id.id,
                    'transport': orders[0].freight_operation_id.transport,
                    'freight_operation_id': orders[0].freight_operation_id.id,
                }

                invoice = self.env['account.move'].create(invoice_vals)

                # Update the selected orders
                orders.filtered(lambda o: not o.is_claimed).write({'invoice_status': 'no', 'is_claimed': True})

        return {'type': 'ir.actions.act_window_close'}
