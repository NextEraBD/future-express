from odoo import models,fields,api
from datetime import timedelta


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    PO_TYPE_SELECTION = [
        ('operation', 'Operation'),
        ('official_receipt', 'Official Receipt')
    ]

    po_type = fields.Selection(PO_TYPE_SELECTION, string='Purchase Order Type', )
    weight = fields.Float('Gross Weight')
    net_weight = fields.Float('Net Weight')
    chargeable_weight = fields.Float('chargeable Weight')
    volume = fields.Float('Volume (CBM)')

    source_location_id = fields.Many2one('freight.port', 'Port of Loading', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', )
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land'), ('vas', 'Vas')]),
                                 string='Activity')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')

    freight_operation_id = fields.Many2one('freight.operation', string='Freight operation')
    # lead_id = fields.Many2one('crm.lead', "Opportunity", readonly=True)
    booking = fields.Char()
    booking_no = fields.Char(string="Booking No")
    certificate_number = fields.Char('Certificate Number')
    certificate_date = fields.Date('Certificate Date')
    is_claimed = fields.Boolean()


    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        res['freight_operation_id'] = self.freight_operation_id.id
        res['weight'] = self.weight
        res['net_weight'] = self.net_weight
        res['booking_no'] = self.booking_no
        res['certificate_number'] = self.certificate_number
        res['certificate_date'] = self.certificate_date
        res['source_location_id'] = self.source_location_id.id
        res['destination_location_id'] = self.destination_location_id.id
        res['transport'] = self.transport
        res['ocean_shipment_type'] = self.ocean_shipment_type
        return res

    def action_create_journal_official(self):
        invoice_lines = []
        total = 0

        # Iterate over order lines of the current purchase order
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

        # Create the claim invoice if there are invoice lines
        if invoice_lines:
            invoice_vals = {
                'move_type': 'in_invoice',
                'is_claim': True,
                'currency_id': self.currency_id.id,
                'journal_id': self.env.ref('freight_expense.els_claim_vendor_journal').id,
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

            # Update the current purchase order
            self.write({'invoice_status': 'no', 'is_claimed': True})

        return {'type': 'ir.actions.act_window_close'}


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    container_id = fields.Many2one('freight.container', 'Container Type')
    total_qty = fields.Float()
    price_for_one_container = fields.Float()
    container_from_to = fields.Char()
    package = fields.Many2one('freight.package', 'Package')
    gross_weight = fields.Float('Gross Weight (KG)')
