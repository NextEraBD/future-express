from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from collections import defaultdict


class OfficialQuotationWizard(models.TransientModel):
    _name = 'official.quotation.wizard'

    shipment_number = fields.Many2one('freight.operation', 'Shipment ID')
    customer_id = fields.Many2one('res.partner', 'Customer')

    def action_confirm(self):
        selected_records = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))

        # Dictionary to store records grouped by expense service type and currency
        grouped_records = defaultdict(lambda: self.env[self.env.context.get('active_model')].browse())

        for record in selected_records:
            if not record.currency_id:
                raise UserError(_('Please Check Currency'))
            key = (record.currency_id.id)
            grouped_records[key] |= record

        # Create a sale order for each group of records
        for key, group in grouped_records.items():
            currency_id = key
            vals = {
                'partner_id': group[0].shipment_number.customer_id.id,
                'currency_id': currency_id,
                'order_line': [],
                'so_type': 'official_receipt',
                'freight_operation_id': group[0].shipment_number.id,
                'weight': group[0].shipment_number.weight,
                'net_weight': group[0].shipment_number.net_weight,
                'chargeable_weight': group[0].shipment_number.chargeable_weight,
                'source_location_id': group[0].shipment_number.source_location_id.id,
                'destination_location_id': group[0].shipment_number.destination_location_id.id,
                'transport': group[0].shipment_number.transport,
                'volume': group[0].shipment_number.volume,
                'ocean_shipment_type': group[0].shipment_number.ocean_shipment_type,
            }
            product_ids = []
            for line in group:
                if not line.shipment_number:
                    raise UserError(_('Please Check Shipment Number'))

                if not line.sale_id:
                    vals['order_line'].append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'product_uom_qty': 1,
                        'price_unit': line.amount_sale,
                        'opportunity_id': line.shipment_number.lead_id.id,
                    }))
                    # Add the product ID to the list of added product IDs
                    product_ids.append(line.product_id.id)
            if vals['order_line']:
                sale_order = self.env['sale.order'].create(vals)
                group.sale_id = sale_order.id
