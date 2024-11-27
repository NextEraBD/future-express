from odoo import api, fields, models


class CustomerInvoiceLine(models.Model):
    _inherit = 'account.move.line'
    asset_created = fields.Boolean()


class CustomerInvoice(models.Model):
    _inherit = 'account.move'

    freight_operation_id = fields.Many2one('freight.operation', string='Freight operation')
    amount_total_words = fields.Char("Total (In Words)",store=True, compute="_compute_amount_total_words")
    console_id = fields.Many2one('console.operation', 'Console Operation')
    weight = fields.Float('Gross Weight')
    net_weight = fields.Float('Net Weight')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ('vas', 'Vas')]),
                                 string='Activity')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')
    contact_id = fields.Many2one('res.partner')
    is_claim = fields.Boolean()

    bill_to_id = fields.Many2one('res.partner', string='Bill To')
    shipper_id = fields.Many2one('res.partner', string='Shipper')
    consignee_id = fields.Many2one('res.partner', string='Consignee')
    invoice_no = fields.Char(string="Invoice No")
    invoice_date = fields.Date(string="Invoice Date")
    invoice_ref = fields.Char(string="Invoice REF")
    operation_file = fields.Char(string="Operation File")
    operation_sn = fields.Char(string="Operation S/N")
    mawb = fields.Char(string="MAWB/MB-L#")
    hawb = fields.Char(string="HAWB/HB-L#")
    origin = fields.Char(string="Origin")
    destination = fields.Char(string="Destination")
    pieces = fields.Integer(string="Pieces")
    weight = fields.Float(string="Weight")
    shipping_mode = fields.Char(string="Shipping Mode")
    carrier = fields.Char(string="Carrier")
    flight_details = fields.Char(string="Flight Details")
    currency = fields.Char(string="Currency")
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        compute='_compute_journal_id', inverse='_inverse_journal_id', store=True, readonly=False, precompute=True,
        required=True,
        states={'draft': [('readonly', False)]},
        check_company=True,

    )
    suitable_journal_ids = fields.Many2many(
        'account.journal',
        compute='_compute_suitable_journal_ids',
    )
    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        for m in self:
            journal_type = m.invoice_filter_type_domain or 'general'
            company_id = m.company_id.id or self.env.company.id
            domain = [('company_id', '=', company_id)]
            m.suitable_journal_ids = self.env['account.journal'].search(domain)

    # amount_in_words = fields.Char("Amount in Words", compute="_onchange_amount",
    #                               readonly=False)
    #
    # @api.depends('amount_total')
    # def _onchange_amount(self):
    #     for pay in self:
    #         if pay.amount_total and pay.currency_id:
    #             pay.amount_in_words = pay.currency_id.with_context(lang='ar_001').amount_to_text(
    #                 pay.amount_total) if pay.currency_id else False
    @api.depends('freight_operation_id', 'move_type')
    def compute_partner_domain_ids(self):
        partner_ids = []
        partners = self.env['res.partner'].search([])
        for part in partners:
            partner_ids += partners.search(
                [('id', 'in', (self.freight_operation_id.customer_id.id, self.freight_operation_id.shipper_id.id,
                               self.freight_operation_id.agent_id.id,
                               self.freight_operation_id.consignee_id.id,
                               self.freight_operation_id.second_agent.id,))]).ids
            if self.freight_operation_id:
                self.partner_domain_ids = partner_ids
            else:
                self.partner_domain_ids = partners.ids

    partner_domain_ids = fields.Many2many('res.partner', 'res_partner_domain_rel',
                                          compute='compute_partner_domain_ids',
                                          string="Allowed Partners")

    @api.depends('amount_total')
    def _compute_amount_total_words(self):
        for invoice in self:
            invoice.amount_total_words = invoice.currency_id.amount_to_text(invoice.amount_total)
