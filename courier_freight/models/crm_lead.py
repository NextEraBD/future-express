from odoo import api, fields, models, _
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError



class Lead(models.Model):
    _inherit = 'crm.lead'

    _sql_constraints = [
        ('account_number_wb_unique', 'unique(account_number_wb)', 'The Account Number WB must be unique!')
    ]

    address = fields.Text(string='Address', compute='_compute_address_tax_account', store=True)
    tax_id = fields.Char(string='Tax ID', compute='_compute_address_tax_account', store=True)
    account_number = fields.Char(string='Account Number', compute='_compute_address_tax_account', store=True)

    @api.depends('partner_id')
    def _compute_address_tax_account(self):
        for rec in self:
            if rec.partner_id:
                rec.address = rec.partner_id.contact_address
                rec.tax_id = rec.partner_id.vat
                rec.account_number = rec.partner_id.unique_id
            else:
                rec.address = False
                rec.tax_id = False
                rec.account_number = False

    @api.onchange('partner_id')
    def _onchange_customer_id(self):
        if self.partner_id:
            self.address = self.partner_id.contact_address
            self.tax_id = self.partner_id.vat
            self.account_number = self.partner_id.unique_id
        else:
            self.address = False
            self.tax_id = False
            self.account_number = False

    operation_type = fields.Selection([('cruise', 'Courier'), ('cargo', 'Cargo')],
                                      string='Operation Type', readonly=False)

    shipment_order_name = fields.Char(string='Order Reference')
    account_number_wb = fields.Char(string='AWB')
    received_date = fields.Date(string='Received Date')
    sale_order_date = fields.Date(string='Sale Order Date')
    competitors = fields.Char(string='Competitors')
    sale_order_type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase')], string='Sale Order Type')
    shipment_type = fields.Selection([('doc', 'Doc'), ('nondoc', 'Non Doc')], string='Shipment Type')
    courier = fields.Char(string='Courier')
    payment_terms = fields.Many2one('account.payment.term', string='Payment Terms',
                                    related='partner_id.property_payment_term_id')

    sender_name = fields.Char(string='Sender Name')
    sender_mobile = fields.Char(string='Sender Mobile')
    sender_address = fields.Text(string='Address From')
    sender_country_id = fields.Many2one('res.country', string='Country From', compute='_compute_sender_country_id',
                                        store=True)
    sender_state_id = fields.Many2one('res.country.state', string='State From',
                                      domain="[('country_id', '=', sender_country_id)]")
    sender_town = fields.Many2one('res.branch.town', string='Sender Town')
    receiver_town = fields.Many2one('res.branch.town', string='Receiver Town')
    receiver_name = fields.Char(string='Receiver Name')
    receiver_mobile = fields.Char(string='Receiver Mobile')
    receiver_address = fields.Text(string='Address To')
    receiver_country_id = fields.Many2one('res.country', string='Country To', compute='_compute_receiver_country_id',
                                          store=True)
    receiver_state_id = fields.Many2one('res.country.state', string='State To',
                                        domain="[('country_id', '=', receiver_country_id)]")

    shipment_order_line_ids = fields.One2many('shipment.order.line', 'shipment_order_crm_id',
                                              string='Shipment Order Lines', readonly=False)

    cruise_type = fields.Selection(
        [('local', 'Local'), ('international', 'International')],
        string='Courier Type',
        store=True
    )
    local_type = fields.Selection(
        [('online', 'Online'), ('not_online', 'Not Online')],
        string='Local Type',
        readonly=False
    )
    collection_amount = fields.Float(string="Collection amount")

    pricelist_id = fields.Many2one('product.pricelist', string="Price List", compute='_compute_pricelist_id')
    currency_id = fields.Many2one('res.currency', string="Currency", compute='_compute_currency_id', readonly=1)
    sale_order_count = fields.Integer(string='Quotations', compute='_compute_sale_order_count')
    employee_ids = fields.Many2many('hr.employee')
    shipment_order_count = fields.Integer(string='Shipment Orders Count', compute='_compute_shipment_order_count')
    price_list_id = fields.Many2one(
        'custom.price.list',
        string='Price List',
        domain="[('price_list_type', '=', cruise_type)]",
        store=True
    )
    custom_pricelist_domain = fields.Many2many('custom.price.list', string="Domain", compute='_compute_custom_pricelist_domian')

    untaxed_amount = fields.Float(string="Untaxed Amount", compute='_compute_totals')
    services = fields.Float(string="Services", compute='_compute_totals')
    local_taxes = fields.Float(string="Local Tax", compute='_compute_totals')
    international_taxes = fields.Float(string="International Tax", compute='_compute_totals')
    vat = fields.Float(string="Vat", compute='_compute_totals')
    total_usd = fields.Float(string="Total USD", compute='_compute_totals')
    total_egp = fields.Float(string="Total EGP", compute='_compute_totals')

    ks_global_discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')],
                                               string='Universal Discount Type',
                                               readonly=False,
                                               default='percent')
    ks_global_discount_rate = fields.Float('Universal Discount',
                                           readonly=False,)
    ks_amount_discount = fields.Monetary(string='Universal Discount', readonly=True, store=True,
                                         compute='_amount_all',
                                         track_visibility='always')
    ks_enable_discount = fields.Boolean()
    cash = fields.Selection([
        ('cash', 'Cash'),
        ('invoice', 'Invoice')
    ], string="Payment Type",required=False,)

    @api.onchange('partner_id', 'direction', 'cruise_type')
    def _onchange_partner_info(self):
        # Detect if 'direction' has actually changed
        direction_changed = self._origin.direction != self.direction

        if direction_changed or not self.sender_name or not self.receiver_name:
            if self.direction == 'export':
                # Set sender details for export
                self.sender_name = self.partner_id.name
                self.sender_mobile = self.partner_id.mobile
                self.sender_address = self.partner_id.contact_address

                # Clear receiver fields for export
                self.receiver_name = False
                self.receiver_mobile = False
                self.receiver_address = False

            elif self.direction == 'import':
                # Set receiver details for import
                self.receiver_name = self.partner_id.name
                self.receiver_mobile = self.partner_id.mobile
                self.receiver_address = self.partner_id.contact_address

                # Clear sender fields for import
                self.sender_name = False
                self.sender_mobile = False
                self.sender_address = False

            elif self.cruise_type == 'local':
                # Set sender details for local cruise type
                self.sender_name = self.partner_id.name
                self.sender_mobile = self.partner_id.mobile
                self.sender_address = self.partner_id.contact_address

                # Clear receiver fields for local cruise type
                self.receiver_name = False
                self.receiver_mobile = False
                self.receiver_address = False

    @api.onchange('sender_town')
    def _onchange_sender_town(self):
        for record in self:
            record.sender_state_id = record.sender_town.state_id.id if record.sender_town else False

    @api.onchange('receiver_town')
    def _onchange_receiver_town(self):
        for record in self:
            record.receiver_state_id = record.receiver_town.state_id.id if record.receiver_town else False

    @api.depends('company_id.ks_enable_discount')
    def ks_verify_discount(self):
        for rec in self:
            rec.ks_enable_discount = rec.company_id.ks_enable_discount

    @api.depends('total_egp', 'ks_global_discount_rate', 'ks_global_discount_type')
    def _amount_all(self):
        for rec in self:
            rec.ks_calculate_discount()
    #
    def ks_calculate_discount(self):
        for rec in self:
            if rec.ks_global_discount_type == "amount":
                rec.ks_amount_discount = rec.ks_global_discount_rate if rec.untaxed_amount > 0 else 0

            elif rec.ks_global_discount_type == "percent":
                if rec.ks_global_discount_rate != 0.0:
                    rec.ks_amount_discount = (rec.untaxed_amount + rec.vat) * rec.ks_global_discount_rate / 100
                else:
                    rec.ks_amount_discount = 0
            elif not rec.ks_global_discount_type:
                rec.ks_amount_discount = 0
                rec.ks_global_discount_rate = 0
            # rec.amount_total = rec.amount_untaxed + rec.amount_tax - rec.ks_amount_discount

    @api.onchange('sender_town')
    def _onchange_sender_town(self):
        for record in self:
            record.sender_state_id = record.sender_town.state_id.id if record.sender_town else False

    @api.onchange('receiver_town')
    def _onchange_receiver_town(self):
        for record in self:
            record.receiver_state_id = record.receiver_town.state_id.id if record.receiver_town else False

    @api.depends('shipment_order_line_ids.net_rate',
                 'shipment_order_line_ids.services_amount',
                 'shipment_order_line_ids.international_tax','shipment_order_line_ids.local_tax')

    def _compute_totals(self):
        for order in self:
            untaxed_amount = 0.0
            services = 0.0
            local_taxes = 0.0
            international_taxes = 0.0
            vat = 0.0
            rate = 1.0

            # Retrieve the latest rate for the currency based on the most recent date
            usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
            if usd_currency:
                # Get the latest rate for USD
                latest_rate = usd_currency.rate_ids.sorted('name', reverse=True)[:1]
                if latest_rate:
                    rate = latest_rate.company_rate
                    print(f"Latest USD Rate: {rate}")  # Debugging purpose

            for line in order.shipment_order_line_ids:
                untaxed_amount += line.net_rate
                services += line.services_amount
                # local_taxes += line.international_tax.amount/100 *(line.net_rate)
                if order.cruise_type == 'local':
                    # Calculate local taxes for local cruise type
                    if line.local_tax:
                        for tax in line.local_tax:
                            local_taxes = (tax.amount / 100.0) * (untaxed_amount + services)
                elif order.cruise_type == 'international':
                    # Calculate international taxes for international cruise type
                    if line.international_tax:
                        for tax in line.international_tax:
                            international_taxes = (tax.amount / 100.0) * (untaxed_amount + services)
                # if line.international_tax:
                #     for tax in line.international_tax:
                #         local_taxes = (tax.amount / 100.0) * (untaxed_amount + services)
                if line.tax_id:
                    for tax in line.tax_id:
                        vat = (tax.amount / 100.0) * (untaxed_amount + services + local_taxes)

            total_usd = untaxed_amount + services + local_taxes + vat

            order.untaxed_amount = untaxed_amount
            order.services = services
            order.local_taxes = local_taxes
            order.international_taxes = international_taxes
            order.vat = vat
            order.total_usd = total_usd
            order.total_egp = total_usd * rate


    @api.depends('partner_id', 'cruise_type')
    def _compute_pricelist_id(self):
        for record in self:
            if record.partner_id:
                if record.cruise_type == 'local':
                    record.pricelist_id = record.partner_id.local_currency_id or False
                elif record.cruise_type == 'international':
                    record.pricelist_id = record.partner_id.international_currency_id or False
                else:
                    record.pricelist_id = False
            else:
                record.pricelist_id = False

    @api.depends('partner_id', 'cruise_type')
    def _compute_custom_pricelist_domian(self):
        for rec in self:
            if rec.partner_id:
                if rec.cruise_type == 'local':
                    rec.custom_pricelist_domain = rec.partner_id.local_price_list_id or False
                elif rec.cruise_type == 'international':
                    rec.custom_pricelist_domain = rec.partner_id.international_price_list_id or False
                else:
                    rec.custom_pricelist_domain = False
            else:
                rec.custom_pricelist_domain = False

    @api.depends('price_list_id')
    def _compute_currency_id(self):
        for record in self:
            if record.price_list_id:
                record.currency_id = record.price_list_id.currency_id or False
            else:
                record.currency_id = False

    @api.onchange('partner_id', 'cruise_type')
    def _compute_price_list_id(self):
        for record in self:
            # Clear the existing price_list_id
            record.price_list_id = False

            if record.partner_id:
                if record.cruise_type == 'local':
                    price_lists = record.partner_id.local_price_list_id
                elif record.cruise_type == 'international':
                    price_lists = record.partner_id.international_price_list_id
                else:
                    price_lists = False

                # Select the first price list if any are available
                if price_lists:
                    record.price_list_id = price_lists[0]

    def _compute_shipment_order_count(self):
        # Example computation method
        for order in self:
            order.shipment_order_count = self.env['shipment.order.payment'].sudo().search_count(
                [('lead_id', '=', order.id)])

    @api.depends()
    def _compute_sale_order_count(self):
        for order in self:
            order.sale_order_count = self.env['sale.order'].sudo().search_count(
                [('lead_id', '=', order.id)])

    def action_view_online_payments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Online Payments',
            'view_mode': 'tree,form',
            'res_model': 'online.payment',
            'domain': [('crm_lead_id', '=', self.id)],
            'context': {'default_crm_lead_id': self.id, 'default_amount': self.collection_amount},
        }

    def action_view_shipment_orders(self):
        current_record_id = self.id
        return {
            'name': 'Shipment Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'shipment.order.payment',
            'view_mode': 'tree,form',
            'target': 'current',  # or 'new' if you want to open it in a new windowcontext
            'domain': [('lead_id', '=', current_record_id)],
            # Replace `related_model_id` with the actual field linking to `shipment.order`
            'context': {
                'default_lead_id': self.id
                # Replace `default_freight_shipment_id` with the actual field name you want to filter on
            }
        }

    @api.depends('cruise_type', 'direction')
    def _compute_sender_country_id(self):
        for record in self:
            if record.cruise_type == 'local':
                record.sender_country_id = self.env.ref(
                    'base.eg').id  # Replace 'base.eg' with the actual XML ID for Egypt
            elif record.cruise_type == 'international' and record.direction == 'export':
                record.sender_country_id = self.env.ref(
                    'base.eg').id  # Replace 'base.eg' with the actual XML ID for Egypt
            else:
                record.sender_country_id = False

    @api.depends('cruise_type', 'direction')
    def _compute_receiver_country_id(self):
        for record in self:
            if record.cruise_type == 'local':
                record.receiver_country_id = self.env.ref(
                    'base.eg').id  # Replace 'base.eg' with the actual XML ID for Egypt
            elif record.cruise_type == 'international' and record.direction == 'import':
                record.receiver_country_id = self.env.ref(
                    'base.eg').id  # Replace 'base.eg' with the actual XML ID for Egypt
            else:
                record.receiver_country_id = False

    # @api.onchange('transport')
    # def onchange_transport(self):
    #     if self.transport == 'air':
    #         self.operation_type = 'cruise'
    #         return {'domain': {'operation_type': [('cruise', 'Cruise'), ('cargo', 'Cargo')]}}
    #     else:
    #         self.operation_type = False
    #         return {'domain': {'operation_type': []}}

    def _prepare_shipment_order_vals(self):
        # Common method to prepare ShipmentOrder values from Lead
        return {
            'customer_id': self.partner_id.id,
            'account_number_wb': self.account_number_wb,
            'received_date': self.received_date,
            'sale_order_date': self.sale_order_date,
            'competitors': self.competitors,
            'sale_order_type': self.sale_order_type,
            'shipment_type': self.shipment_type,
            'courier': self.courier,
            'operation_type': self.operation_type,
            'cruise_type': self.cruise_type,
            'local_type': self.local_type,
            'cash': self.cash,
            'direction': self.direction,
            'price_list_id': self.price_list_id.id,
            'currency_id': self.currency_id.id,
            'pricelist_id': self.pricelist_id.id,
            'payment_terms': self.payment_terms.id,
            'sender_name': self.sender_name,
            'sender_mobile': self.sender_mobile,
            'sender_address': self.sender_address,
            'sender_country_id': self.sender_country_id.id,
            'sender_state_id': self.sender_state_id.id,
            'sender_town': self.sender_town.id,
            'receiver_name': self.receiver_name,
            'receiver_mobile': self.receiver_mobile,
            'receiver_address': self.receiver_address,
            'receiver_country_id': self.receiver_country_id.id,
            'receiver_state_id': self.receiver_state_id.id,
            'receiver_town': self.receiver_town.id,
            'order_lines': [(0, 0, {
                'product': line.product.id,
                'weight': line.weight,
                'width': line.width,
                'height': line.height,
                'size': line.size,
                'cbm': line.cbm,
                'gross_weight': line.gross_weight,
                'vendor': line.vendor.id,
                'source': line.source,
                'destination': line.destination,
                'services': [(6, 0, [service.id for service in line.services])],
                'services_amount': line.services_amount,
                'departial_date': line.departial_date,
                'description': line.description,
                'no_of_item': line.no_of_item,
                'analytic_tag': line.analytic_tag,
                'international_tax': [(6, 0, [tax.id for tax in line.international_tax])],
                'tax_id': [(6, 0, [tax_id.id for tax_id in line.tax_id])],
                'net_rate': line.net_rate,
                'sale_price': line.sale_price,
                'cost_price': line.cost_price,
                'discount': line.discount,
                'total_price': line.total_price,
            }) for line in self.shipment_order_line_ids]
        }

    def create_freight_shipment(self):
        # Call super to get original values (assuming super returns a dictionary of values)
        vals = super(Lead, self).create_freight_shipment()

        # Prepare shipment order values
        shipment_order_vals = self._prepare_shipment_order_vals()

        # Merge additional fields into vals
        vals.update({
            'operation_type': self.operation_type,
            'shipment_order_name': self.shipment_order_name,
            'account_number_wb': self.account_number_wb,
            'received_date': self.received_date,
            'sale_order_date': self.sale_order_date,
            'competitors': self.competitors,
            'sale_order_type': self.sale_order_type,
            'shipment_type': self.shipment_type,
            'cruise_type': self.cruise_type,
            'local_type': self.local_type,
            'direction': self.direction,
            'courier': self.courier,
            'cash': self.cash,
            'price_list_id': self.price_list_id.id,
            'currency_id': self.currency_id.id,
            'pricelist_id': self.pricelist_id.id,
            'payment_terms': self.payment_terms.id,
            'sender_name': self.sender_name,
            'sender_mobile': self.sender_mobile,
            'sender_address': self.sender_address,
            'sender_country_id': self.sender_country_id.id,
            'sender_town': self.sender_town.id,
            'sender_state_id': self.sender_state_id.id,
            'receiver_name': self.receiver_name,
            'receiver_mobile': self.receiver_mobile,
            'receiver_address': self.receiver_address,
            'receiver_country_id': self.receiver_country_id.id,
            'receiver_state_id': self.receiver_state_id.id,
            'receiver_town': self.receiver_town.id,
            'shipment_order_line_ids': shipment_order_vals['order_lines'],
        })

        if self.operation_type != 'cruise':
            vals['transport'] = self.transport  # Add transport if operation type is not cruise

        # Uncomment to actually create the shipment order
        # shipment_order = self.env['freight.operation'].create(vals)
        # return shipment_order

    def select_all(self):
        res = super(Lead, self).select_all()
        for line in self.shipment_order_line_ids:
            if not line.processed_so:
                line.check = True
            if not line.processed_po:
                line.check = True
        return res

    # def action_view_sale_quotation(self):
    #     self.ensure_one()
    #     # Call super to get the base action
    #     action = super(Lead, self).action_view_sale_quotation()
    #     # Search for sale orders related to the lead
    #     sale_orders = self.env['sale.order'].search([('opportunity_id', '=', self.id)])
    #     # Prepare the custom action
    #     action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
    #     action['context'] = self._prepare_opportunity_quotation_context()
    #     action['context']['search_default_draft'] = 1
    #     action['domain'] = [('id', 'in', sale_orders.ids)]
    #     if len(sale_orders) == 1:
    #         action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
    #         action['res_id'] = sale_orders.id
    #     elif len(sale_orders) > 1:
    #         action['domain'] = [('id', 'in', sale_orders.ids)]
    #
    #     return action

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    account_number_wb = fields.Char('AWB', readonly=True)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'




class SaleOrder(models.Model):
    _inherit = 'sale.order'

    total_services_amount = fields.Float(
        string='Additional Services',
        compute='_compute_total_services_amount',
        store=True
    )
    cash = fields.Selection([
        ('cash', 'Cash'),
        ('invoice', 'Invoice')
    ], string="Payment Type", required=True, )

    account_number_wb = fields.Char('AWB', readonly=True)


    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()

        # Fetch the 'Statement' journal, or create it if it doesn't exist
        statement_journal = self.env['account.journal'].search([('name', '=', 'Statement'), ('type', '=', 'sale')], limit=1)
        invoice_journal = self.env['account.journal'].search([('name', '=', 'Customer Invoices'), ('type', '=', 'sale')], limit=1)
        if not statement_journal:
            statement_journal = self.env['account.journal'].create({
                'name': 'Statement',
                'type': 'sale',  # Ensure it's an invoice type journal
                'code': 'STM',
                'company_id': self.env.company.id,
            })

        for order in self:
            # Check for cash journal condition
            if (order.freight_operation_id and order.freight_operation_id.cash == 'cash'
                    or order.opportunity_id and order.opportunity_id.cash == 'cash'
                    or order.cash == 'cash'):
                # Assign the 'Statement' journal for cash payments
                res['journal_id'] = statement_journal.id
            else:
                # Assign the default journal if no cash condition is met
                res['journal_id'] = invoice_journal.id if invoice_journal else None
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if not order.freight_operation_id:
                freight_id = self.env['freight.operation'].search([('lead_id', '=', self.opportunity_id.ids)],limit=1)
                if freight_id:
                    order.freight_operation_id =freight_id
                    order.account_number_wb = freight_id.account_number_wb
        return res


    # def _create_invoices(self, grouped=False, final=False):
    #     # Call the original invoice creation method
    #     invoices = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final)
    #
    #     # Check if the sale order is linked to a freight operation and if 'cash' is checked
    #     for order in self:
    #         if order.freight_operation_id and order.freight_operation_id.cash:
    #             # Search for the cash journal
    #             cash_journal = self.env['account.journal'].search([('type', '=', 'cash')], limit=1)
    #
    #             if cash_journal:
    #                 # Assign the cash journal to the newly created invoices
    #                 for invoice in invoices:
    #                     invoice.journal_id = cash_journal
    #
    #                     # Ensure each invoice line has an account set
    #                     for line in invoice.invoice_line_ids:
    #                         if not line.account_id:
    #                             product = line.product_id
    #                             if product:
    #                                 # Set default income account from the product or fallback to the journal's default account
    #                                 line.account_id = product.property_account_income_id or product.categ_id.property_account_income_categ_id or invoice.journal_id.default_account_id
    #                             if not line.account_id:
    #                                 raise UserError(
    #                                     f'Missing required account for product {product.name} or its category.')
    #
    #     return invoices

    @api.depends('order_line.services_amount')
    def _compute_total_services_amount(self):
        for order in self:
            order.total_services_amount = sum(line.services_amount for line in order.order_line)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'



