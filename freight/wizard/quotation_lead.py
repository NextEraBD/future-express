from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from collections import defaultdict


class QuotationLeadWizard(models.TransientModel):
    _name = 'quotation.lead.wizard'

    lead_id = fields.Many2one('crm.lead', 'Lead ID')
    customer_id = fields.Many2one('res.partner', 'Customer')

    @api.depends('lead_id')
    def compute_partner_domain_ids(self):
        partner_ids = []
        partners = self.env['res.partner'].search([])
        for part in partners:
            partner_ids += partners.search(
                [('id', 'in', (self.lead_id.partner_id.id, self.lead_id.shipper_id.id,
                               self.lead_id.shipping_line_id.id,
                               self.lead_id.agent_id.id,
                               self.lead_id.consignee_id.id,
                               ))]).ids
            if self.lead_id:
                self.partner_domain_ids = partner_ids
            else:
                self.partner_domain_ids = partners.ids

    partner_domain_ids = fields.Many2many('res.partner', 'res_lead_wizard_partner_domain_rel',
                                          compute='compute_partner_domain_ids',
                                          string="Allowed Partners")


    def action_confrim(self):
        # Step 1: Check if there are insurance lines and create insurance quotation if applicable
        if self.lead_id.insurance_line_ids:
            self.lead_id.action_create_insurance_quotation()

        product_id = []
        sale_orders = defaultdict(lambda: defaultdict(list))

        # Step 2: Collect existing sale order lines related to the lead
        existing_order_lines = {
            line.product_id.id: True
            for order in self.env['sale.order'].search([('opportunity_id', '=', self.lead_id.id)])
            for line in order.order_line
        }

        # Step 3: Process different types of lines related to the lead
        line_types = [
            self.lead_id.freight_line_ids,
            self.lead_id.transport_line_ids,
            self.lead_id.transit_line_ids,
            self.lead_id.clearance_line_ids,

        ]

        for lines in line_types:
            for line in lines:
                self._process_line(line, product_id, sale_orders, existing_order_lines)

        # Step 4: Create sale orders based on the collected lines
        for currency, partners in sale_orders.items():
            for partner_id, lines in partners.items():
                order_lines = []
                clearance_inspection_line_ids = []

                for line in lines:
                    order_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'product_uom_qty': line.qty if hasattr(line, 'qty') else 1.0,
                        'price_unit': line.sale_price if hasattr(line,
                                                                 'sale_price') else line.price_sale if hasattr(line,
                                                                                                               'price_sale') else line.price if hasattr(
                            line, 'price') else line.amount,
                        'package': line.package.id if hasattr(line, 'package') else False,
                        'container_id': line.container_id.id if hasattr(line, 'container_id') else False,
                        'gross_weight': line.gross_weight if hasattr(line, 'gross_weight') else False
                    }))

                # Add clearance inspection lines to the sale order
                for f in self.lead_id.clearance_inspection_line_ids:
                    clearance_inspection_line_ids.append((0, 0, {
                        'product_id': f.product_id.id,
                        'name': f.product_id.name,
                        'qty': f.qty,
                        'price': f.price,
                    }))

                if order_lines:
                    partner = partner_id if partner_id else self.customer_id.id
                    vals = {
                        'partner_id': partner,
                        'contact_id': partner,
                        'currency_id': currency,
                        # 'incoterm_id': self.lead_id.incoterm_id.id,
                        # 'commodity_id': self.lead_id.commodity_id.id,
                        'pricelist_id': self._get_pricelist_id(currency),
                        'opportunity_id': self.lead_id.id,
                        'weight': self.lead_id.weight,
                        'net_weight': self.lead_id.net_weight,
                        'chargeable_weight': self.lead_id.chargeable_weight,
                        'source_location_id': self.lead_id.source_location_id.id,
                        'destination_location_id': self.lead_id.destination_location_id.id,
                        'transport': self.lead_id.transport,
                        'ocean_shipment_type': self.lead_id.ocean_shipment_type,
                        'volume': self.lead_id.volume,
                        'order_line': order_lines,
                        'clearance_inspection_line_ids': clearance_inspection_line_ids,
                        # Include the clearance inspection lines here
                    }

                    # Step 5: Create the sale order with all related lines
                    sale_order = self.env['sale.order'].create(vals)

                    # Step 6: Update sale_id in lead lines for the created sale order
                    for so_line in sale_order.order_line:
                        # Update sale_id for each line
                        for line in lines:
                            if line.product_id == so_line.product_id:
                                line.write({'sale_id': sale_order.id})

    
        return {'type': 'ir.actions.act_window_close'}

    def _process_line(self, line, product_id, sale_orders, existing_order_lines):
        # Step 1: Ensure line has valid currency and customer
        currency_id = line.sale_currency_id.id if line.sale_currency_id else False
        if not currency_id:
            raise UserError(_('Currency not found for line'))

        customer_id = line.customer_id.id if line.customer_id else False
        if not customer_id:
            raise UserError(_('Customer not found for line'))

        # Step 2: Check if the product is already processed or in an existing order line
        if line.product_id.id not in product_id and line.check and line.product_id.id not in existing_order_lines:
            sale_orders[(currency_id,)][(customer_id,)].append(line)

    def _get_pricelist_id(self, currency_id):
        pricelist = self.env['product.pricelist'].search([('currency_id', '=', currency_id)], limit=1)
        return pricelist.id if pricelist else False
