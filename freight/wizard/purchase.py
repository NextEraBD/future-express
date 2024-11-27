from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from collections import defaultdict


class PurchaseWizard(models.TransientModel):
    _name = 'create.po.wizard'

    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    customer_id = fields.Many2one('res.partner', 'Vendor')

    @api.depends('shipment_id')
    def compute_partner_domain_ids(self):
        partner_ids = []
        partners = self.env['res.partner'].search([])
        for part in partners:
            partner_ids += partners.search(
                [('id', 'in', (self.shipment_id.customer_id.id, self.shipment_id.shipper_id.id,
                               self.shipment_id.shipping_line_id.id,
                               self.shipment_id.agent_id.id,
                               self.shipment_id.consignee_id.id,
                               self.shipment_id.second_agent.id))]).ids
            if self.shipment_id:
                self.partner_domain_ids = partner_ids
            else:
                self.partner_domain_ids = partners.ids

    partner_domain_ids = fields.Many2many('res.partner', 'res_po_wizard_partner_domain_rel',
                                          compute='compute_partner_domain_ids',
                                          string="Allowed Partners")

    def action_confirm(self):
        product_id = []
        purchase_orders = defaultdict(lambda: defaultdict(list))
        if self.shipment_id.lead_id:
            ids = self.env['purchase.order'].search(
                ['|', ('freight_operation_id', '=', self.shipment_id.id),
                 ('lead_id', '=', self.shipment_id.lead_id.id)])
        else:
            ids = self.env['purchase.order'].search([('freight_operation_id', '=', self.shipment_id.id)])

        for line in ids.order_line:
            product_id.append(line.product_id.id)

        # Process freight lines
        for f in self.shipment_id.freight_line_ids:
            if not f.currency_id:
                raise UserError(_('Currency not found for freight line'))
            if not f.agent_id:
                raise UserError(_('Agent not found for freight line'))

            currency = f.currency_id.id
            partner_key = (f.agent_id.id,)
            key = (currency,)

            if f.product_id.id not in product_id and f.check and f.product_id:
                purchase_orders[key][partner_key].append(f)

        # Process transport lines
        for f in self.shipment_id.transport_line_ids:
            if not f.currency_id:
                raise UserError(_('Currency not found for transport line'))
            if not f.tracking_agent:
                raise UserError(_('Tracking agent not found for transport line'))

            currency = f.currency_id.id
            partner_key = (f.tracking_agent.id,)
            key = (currency,)

            if f.product_id.id not in product_id and f.check and f.product_id:
                purchase_orders[key][partner_key].append(f)

        # Process clearance lines
        for f in self.shipment_id.clearance_line_ids:
            if not f.currency_id:
                raise UserError(_('Currency not found for clearance line'))
            if not f.clearance_company:
                raise UserError(_('Clearance company not found for clearance line'))

            currency = f.currency_id.id
            partner_key = (f.clearance_company.id,)
            key = (currency,)

            if f.product_id.id not in product_id and f.check and f.product_id:
                purchase_orders[key][partner_key].append(f)

        # Process transit lines
        for f in self.shipment_id.transit_line_ids:
            if not f.currency_id:
                raise UserError(_('Currency not found for transit line'))

            currency = f.currency_id.id
            partner_key = None  # Assuming no specific partner for transit lines
            key = (currency,)

            if f.product_id.id not in product_id and f.check and f.product_id:
                purchase_orders[key][partner_key].append(f)

        # Process insurance lines
        for f in self.shipment_id.insurance_line_ids:
            if not f.currency_id:
                raise UserError(_('Currency not found for insurance line'))
            if not f.insurance_company:
                raise UserError(_('Insurance company not found for insurance line'))

            currency = f.currency_id.id
            partner_key = (f.insurance_company.id,)
            key = (currency,)

            if f.product_id.id not in product_id and f.check and f.product_id:
                purchase_orders[key][partner_key].append(f)

        for currency, partners in purchase_orders.items():
            for partner_id, lines in partners.items():
                order_vals = {
                    'partner_id': partner_id if partner_id else self.customer_id.id,
                    'currency_id': currency,
                    'po_type': 'operation',
                    'freight_operation_id': self.shipment_id.id,
                    'weight': self.shipment_id.weight,
                    'net_weight': self.shipment_id.net_weight,
                    'chargeable_weight': self.shipment_id.chargeable_weight,
                    'source_location_id': self.shipment_id.source_location_id.id,
                    'destination_location_id': self.shipment_id.destination_location_id.id,
                    'transport': self.shipment_id.transport,
                    'ocean_shipment_type': self.shipment_id.ocean_shipment_type,
                    'volume': self.shipment_id.volume,
                    'state': 'purchase',
                    'order_line': [(0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'product_qty': line.qty,
                        'price_unit': line.cost_price if hasattr(line, 'cost_price') else line.cost if hasattr(line, 'cost') else line.price_cost if hasattr(line, 'price_cost') else line.final_amount,
                    }) for line in lines]
                }
                purchase_order = self.env['purchase.order'].create(order_vals)

        return {'type': 'ir.actions.act_window_close'}
