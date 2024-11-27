from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from collections import defaultdict



class PurchaseWizard(models.TransientModel):
    _name = 'create.lead.po.wizard'

    lead_id = fields.Many2one('crm.lead', 'Lead ID')
    customer_id = fields.Many2one('res.partner', 'Vendor',)

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

    partner_domain_ids = fields.Many2many('res.partner', 'res_po_lead_wizard_partner_domain_rel',
                                          compute='compute_partner_domain_ids',
                                          string="Allowed Partners")

    def action_confrim(self):
        product_id = []
        purchase_orders = defaultdict(lambda: defaultdict(list))
        ids = False
        if self.lead_id:
            ids = self.env['purchase.order'].search(
                [('lead_id', '=', self.lead_id.id)])
        for line in ids.order_line:
            product_id.append(line.product_id.id)

        for f in self.lead_id.freight_line_ids:
            try:
                currency = f.currency_id.id
            except:
                raise UserError(_('Currency not found for freight line'))

            key = (currency,)
            partner_key = (f.agent_id.id,)
            if not f.agent_id:
                raise UserError(_('agent not found for Freight line'))
            if f.product_id.id not in product_id and f.check and f.product_id:
                purchase_orders[key][partner_key].append(f)

        for f in self.lead_id.transport_line_ids:
            try:
                currency = f.currency_id.id
            except:
                raise UserError(_('Currency not found for transport line'))

            key = (currency,)
            partner_key = (f.tracking_agent.id,)
            if not f.tracking_agent:
                raise UserError(_('Trucking agent not found for transport line'))
            if f.product_id.id not in product_id and f.check and f.product_id:
                purchase_orders[key][partner_key].append(f)

        for f in self.lead_id.clearance_line_ids:
            try:
                currency = f.currency_id.id
            except:
                raise UserError(_('Currency not found for clearance line'))

            key = (currency,)
            partner_key = (f.clearance_company.id,)
            if not f.clearance_company:
                raise UserError(_('clearance company not found for clearance line'))
            if f.product_id.id not in product_id and f.check and f.product_id:
                purchase_orders[key][partner_key].append(f)

        for f in self.lead_id.transit_line_ids:
            try:
                currency = f.currency_id.id
            except:
                raise UserError(_('Currency not found for transit line'))

            key = (currency,)
            partner_key = (f.vendor_id.id,)
            if not f.vendor_id:
                raise UserError(_('Vendor  not found for clearance line'))
            if f.product_id.id not in product_id and f.check and f.product_id:
                purchase_orders[key][partner_key].append(f)

        # for f in self.shipment_id.transit_line_ids:
        #     try:
        #         currency = f.currency_id.id
        #     except:
        #         raise UserError(_('Currency not found for transit line'))
        #
        #     key = (currency,)
        #     # Assuming there's no specific partner for transit lines
        #     partner_key = None
        #     if f.product_id.id not in product_id and f.check and f.product_id:
        #         purchase_orders[key][partner_key].append(f)

        for currency, partners in purchase_orders.items():
            for partner_id, lines in partners.items():
                order_vals = {
                    'partner_id': partner_id if partner_id else self.customer_id.id,
                    'currency_id': currency,
                    'po_type': 'operation',
                    'lead_id': self.lead_id.id,
                    'weight': self.lead_id.weight,
                    'net_weight': self.lead_id.net_weight,
                    'chargeable_weight': self.lead_id.chargeable_weight,
                    'source_location_id': self.lead_id.source_location_id.id,
                    'destination_location_id': self.lead_id.destination_location_id.id,
                    'transport': self.lead_id.transport,
                    'ocean_shipment_type': self.lead_id.ocean_shipment_type,
                    'volume': self.lead_id.volume,
                    'state': 'purchase',
                    'order_line': [(0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'product_qty': line.qty,
                        'price_unit': line.cost_price if hasattr(line, 'cost_price') else line.cost if hasattr(line,'cost') else line.price_cost if hasattr(
                            line, 'price_cost') else line.amount,
                    }) for line in lines]
                }
                purchase_order = self.env['purchase.order'].create(order_vals)

        return {'type': 'ir.actions.act_window_close'}
    # def action_confrim(self):
    #     product_id = []
    #     if self.lead_id:
    #         ids = self.env['purchase.order'].search(
    #         [('lead_id', '=', self.lead_id.id)])
    #
    #     for line in ids.order_line:
    #         product_id.append(line.product_id.id)
    #     currency_groups = self.lead_id.freight_line_ids.read_group(
    #         domain=[('crm_id', '=', self.lead_id.id)],
    #         fields=['currency_id'],
    #         groupby=['currency_id'],
    #         lazy=False,
    #     )
    #     currency_groups_transport = self.lead_id.transport_line_ids.read_group(
    #         domain=[('crm_id', '=', self.lead_id.id)],
    #         fields=['currency_id'],
    #         groupby=['currency_id'],
    #         lazy=False,
    #     )
    #
    #     currency_groups_clearance = self.lead_id.clearance_line_ids.read_group(
    #         domain=[('crm_id', '=', self.lead_id.id)],
    #         fields=['currency_id'],
    #         groupby=['currency_id'],
    #         lazy=False,
    #     )
    #
    #     currency_groups_transit = self.lead_id.transit_line_ids.read_group(
    #         domain=[('crm_id', '=', self.lead_id.id)],
    #         fields=['currency_id'],
    #         groupby=['currency_id'],
    #         lazy=False,
    #     )
    #     currencies = []
    #     order_line = []
    #     for c in currency_groups:
    #         currencies.append(c.get('currency_id')[0])
    #     for c in currency_groups_transport:
    #         if c.get('currency_id')[0] not in currencies:
    #             currencies.append(c.get('currency_id')[0])
    #
    #     for c in currency_groups_clearance:
    #         if c.get('currency_id')[0] not in currencies:
    #             currencies.append(c.get('currency_id')[0])
    #
    #     for c in currency_groups_transit:
    #         if c.get('currency_id')[0] not in currencies:
    #             currencies.append(c.get('currency_id')[0])
    #     if currencies != []:
    #         for currency in currencies:
    #             vals = {
    #                 'partner_id': self.customer_id.id,
    #                 'currency_id': currency,
    #                 'lead_id': self.lead_id.id,
    #                  'weight': self.lead_id.weight,
    #                 'net_weight': self.lead_id.net_weight,
    #                 'chargeable_weight': self.lead_id.chargeable_weight,
    #                 'source_location_id': self.lead_id.source_location_id.id,
    #                 'destination_location_id': self.lead_id.destination_location_id.id,
    #                 'transport': self.lead_id.transport,
    #                 'ocean_shipment_type': self.lead_id.ocean_shipment_type,
    #                 'volume': self.lead_id.volume,
    #                 'state': 'purchase',
    #                 'order_line': []
    #             }
    #             for f in self.lead_id.freight_line_ids:
    #                 if f.currency_id.id == currency and f.product_id.id not in product_id and f.check and f.product_id:
    #                     vals['order_line'].append((0, 0, {
    #                         'product_id': f.product_id.id,
    #                         'name': f.product_id.name,
    #                         'product_qty': f.qty,
    #                         'price_unit': f.price_cost,
    #                         'package': f.package.id,
    #                         # 'total_qty': f.qty,
    #                         # 'price_for_one_container': f.price_for_one_container,
    #                         'container_id': f.container_id.id
    #                     }))
    #                     # f.sale_id = so.id
    #             for f in self.lead_id.transport_line_ids:
    #                 if f.currency_id.id == currency and f.product_id.id not in product_id and f.check and f.product_id:
    #                     vals['order_line'].append((0, 0, {
    #                         'product_id': f.product_id.id,
    #                         'name': f.product_id.name,
    #                         'product_qty': f.qty,
    #                         'price_unit': f.cost_price,
    #                         'package': f.package.id,
    #                         # 'total_qty': f.qty,
    #                         # 'price_for_one_container': f.price_for_one_container,
    #                         'container_id': f.container_id.id
    #                     }))
    #
    #                     # f.sale_id = so.id
    #             # for f in self.lead_id.clearance_line_ids:
    #             #     if f.currency_id.id == currency and f.product_id.id not in product_id and f.check and f.product_id:
    #             #         vals['order_line'].append((0, 0, {
    #             #             'product_id': f.product_id.id,
    #             #             'name': f.product_id.name,
    #             #             'product_uom_qty': f.qty,
    #             #             'price_unit': f.cost,
    #             #             'package': f.package.id,
    #             #             'container_from_to': f.container_from_to,
    #             #             # 'total_qty': f.total_qty,
    #             #             # 'price_for_one_container': f.price_for_one_container,
    #             #             'container_id': f.container_id.id
    #             #         }))
    #
    #             for f in self.lead_id.transit_line_ids:
    #                 if f.currency_id.id == currency and f.product_id.id not in product_id and f.check and f.product_id:
    #                     vals['order_line'].append((0, 0, {
    #                         'product_id': f.product_id.id,
    #                         'name': f.product_id.name,
    #                         'product_qty': 1.0,
    #                         'price_unit': f.amount,
    #                         'container_id': f.container_id.id
    #                     }))
    #                     # f.sale_id = so.id
    #             if vals['order_line'] != []:
    #                 self.env['purchase.order'].create(vals)
    #
