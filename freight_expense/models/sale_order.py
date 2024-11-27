# -*- coding: utf-8 -*-

from odoo import _, fields, models
from collections import defaultdict



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    SO_TYPE_SELECTION = [
        ('operation', 'Operation'),
        ('official_receipt', 'Official Receipt')
    ]

    so_type = fields.Selection(SO_TYPE_SELECTION, string='Sales Order Type')
    freight_operation_id = fields.Many2one('freight.operation', string="Operation")
    weight = fields.Float('Gross Weight')
    net_weight = fields.Float('Net Weight')
    chargeable_weight = fields.Float('chargeable Weight')
    volume = fields.Float('Volume (CBM)')

    source_location_id = fields.Many2one('freight.port', 'Port of Loading', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', )
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ('vas', 'Vas')]),
                                 string='Activity')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')
    contact_id = fields.Many2one('res.partner')
    booking_no = fields.Char(string="Booking No")
    certificate_number = fields.Char('Certificate Number')
    certificate_date = fields.Date('Certificate Date')
    is_claimed = fields.Boolean()
    incoterm_id = fields.Many2one('lead.incoterm', 'Incoterm', )
    commodity_id = fields.Many2one('lead.commodity', 'Commodity', )


    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.freight_operation_id:
            res['weight'] = self.weight
            res['net_weight'] = self.net_weight
            res['source_location_id'] = self.source_location_id.id
            res['destination_location_id'] = self.destination_location_id.id
            res['transport'] = self.transport
            res['booking_no'] = self.booking_no
            res['certificate_number'] = self.certificate_number
            res['certificate_date'] = self.certificate_date
            res['ocean_shipment_type'] = self.ocean_shipment_type
            res['freight_operation_id'] = self.freight_operation_id.id
        return res

    def action_create_journal_invoice_official(self):
        invoice_lines = []
        total = 0

        # Iterate over order lines of the current sale order
        for order_line in self.order_line:
            if not self.is_claimed:  # Check if the order has already been claimed
                invoice_lines.append((0, 0, {
                    'account_id': order_line.product_id.property_account_expense_id.id or order_line.product_id.categ_id.property_account_expense_categ_id.id,
                    'product_id': order_line.product_id.id,
                    'quantity': 1,
                    'price_unit': order_line.price_unit,
                    'shipment_number': self.freight_operation_id.id,
                }))
                total += order_line.price_unit

        if invoice_lines:
            invoice_vals = {
                'move_type': 'out_invoice',
                'is_claim': True,
                'currency_id': self.currency_id.id,
                'journal_id': self.env.ref('freight_expense.els_claim_customer_journal').id,
                'invoice_date': fields.Date.today(),
                'partner_id': self.partner_id.id,
                'invoice_line_ids': invoice_lines,
                # Add other fields related to the invoice
                'weight': self.freight_operation_id.weight,
                'net_weight': self.freight_operation_id.net_weight,
                'chargeable_weight': self.freight_operation_id.chargeable_weight,
                'source_location_id': self.freight_operation_id.source_location_id.id,
                'destination_location_id': self.freight_operation_id.destination_location_id.id,
                'transport': self.freight_operation_id.transport,
                'freight_operation_id': self.freight_operation_id.id,
            }
            invoice = self.env['account.move'].create(invoice_vals)
            # Update the current sale order
            self.write({'invoice_status': 'no', 'is_claimed': True})

        return {'type': 'ir.actions.act_window_close'}


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    container_id = fields.Many2one('freight.container', 'Container Type')
    opportunity_id = fields.Many2one('crm.lead', related='order_id.opportunity_id')
    total_qty = fields.Float()
    price_for_one_container = fields.Float()
    package = fields.Many2one('freight.package', 'Package')
    container_from_to = fields.Char()
    gross_weight = fields.Float('Gross Weight (KG)')
    chargeable_weight = fields.Float('chargeable Weight')
    # freight_operation_id = fields.Many2one('freight.operation', related='order_id.freight_operation_id')

