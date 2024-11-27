from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from collections import defaultdict


class QuotationWizard(models.TransientModel):
    _name = 'quotation.wizard'

    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    customer_id = fields.Many2one('res.partner', 'Customer'
                                  )
    partner_domain_ids = fields.Many2many('res.partner', 'res_wizard_partner_domain_rel',
                                          compute='compute_partner_domain_ids',
                                          string="Allowed Partners")

    @api.depends('shipment_id')
    def compute_partner_domain_ids(self):
        partner_ids = self.env['res.partner']

        if self.shipment_id:
            for transport_line in self.shipment_id.transport_line_ids:
                if transport_line.check and transport_line.tracking_agent:
                    partner_ids |= transport_line.tracking_agent

            for freight_line in self.shipment_id.freight_line_ids:
                if freight_line.check and freight_line.carrier_id:
                    partner_ids |= freight_line.carrier_id
                    partner_ids |= freight_line.shipping_line_id
                    partner_ids |= freight_line.agent_id

            partner_ids |= self.shipment_id.shipping_line_id
            partner_ids |= self.shipment_id.agent_id
            partner_ids |= self.shipment_id.customer_id
            partner_ids |= self.shipment_id.shipper_id
            partner_ids |= self.shipment_id.consignee_id
            partner_ids |= self.shipment_id.second_agent

        self.partner_domain_ids = partner_ids



    def action_confrim(self):
        product_ids = []
        sale_orders = defaultdict(lambda: defaultdict(list))
        existing_order_lines = {}
        if self.shipment_id.lead_id:
            for order in self.env['sale.order'].search([
                '|',
                ('freight_operation_id', '=', self.shipment_id.id),
                ('opportunity_id', '=', self.shipment_id.lead_id.id)
            ]):
                for line in order.order_line:
                    existing_order_lines[line.product_id.id] = True
        else:
            for order in self.env['sale.order'].search([
                ('freight_operation_id', '=', self.shipment_id.id),
            ]):
                for line in order.order_line:
                    existing_order_lines[line.product_id.id] = True

        # Process different types of lines in the shipment
        line_types = [
            self.shipment_id.freight_line_ids,
            self.shipment_id.transport_line_ids,
            self.shipment_id.transit_line_ids,
            self.shipment_id.clearance_line_ids,
        ]

        for lines in line_types:
            for line in lines:
                self._process_line(line, product_ids, sale_orders, existing_order_lines)

        # Create sale orders
        for currency, partners in sale_orders.items():
            for partner_id, lines in partners.items():
                order_lines = []
                for line in lines:
                    order_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'product_uom_qty': line.qty,
                        'price_unit': line.sale_price if hasattr(line, 'sale_price') else line.price_sale if hasattr(
                            line, 'price_sale') else line.price if hasattr(line, 'price') else line.amount,
                        'package': line.package.id if line.package else False,
                        'container_id': line.container_id.id if line.container_id else False,
                    }))
                if order_lines:
                    partner = partner_id if partner_id else self.customer_id.id
                    if not partner:
                        raise UserError(_('Customer not found for order line.'))

                    vals = {
                        'partner_id': partner,
                        'contact_id': self.shipment_id.customer_id.id,
                        # 'commodity_id': self.shipment_id.commodity_id.id,
                        'currency_id': currency,
                        'so_type': 'operation',
                        'pricelist_id': self._get_pricelist_id(currency),
                        'opportunity_id': self.shipment_id.lead_id.id,
                        'freight_operation_id': self.shipment_id.id,
                        'weight': self.shipment_id.weight,
                        'net_weight': self.shipment_id.net_weight,
                        'chargeable_weight': self.shipment_id.chargeable_weight,
                        'source_location_id': self.shipment_id.source_location_id.id,
                        'destination_location_id': self.shipment_id.destination_location_id.id,
                        'transport': self.shipment_id.transport,
                        'volume': self.shipment_id.volume,
                        'ocean_shipment_type': self.shipment_id.ocean_shipment_type,
                        'order_line': order_lines,
                    }
                    sale_order = self.env['sale.order'].create(vals)
                    for so_line in sale_order.order_line:
                        for line in lines:
                            if line.product_id == so_line.product_id:
                                line.write({'sale_id': sale_order.id})

        return {'type': 'ir.actions.act_window_close'}

    def _process_line(self, line, product_ids, sale_orders, existing_order_lines):
        if not line.product_id:
            raise UserError(_('Product not found for line'))

        currency_id = line.sale_currency_id.id if line.sale_currency_id else False
        if not currency_id:
            raise UserError(_('Currency not found for line'))

        customer_id = line.customer_id.id if line.customer_id else False
        if not customer_id:
            raise UserError(_('Customer not found for line'))

        if line.product_id.id not in product_ids and line.check and line.product_id.id not in existing_order_lines:
            sale_orders[(currency_id,)][(customer_id,)].append(line)

    def _get_pricelist_id(self, currency_id):
        pricelist = self.env['product.pricelist'].search([('currency_id', '=', currency_id)], limit=1)
        return pricelist.id if pricelist else False
