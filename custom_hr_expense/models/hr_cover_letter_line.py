from odoo import models, fields, api, _


class HrExpense(models.Model):
    _name = 'hr.cover.letter.line'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']
    _description = "Cover Letter Lines"
    _check_company_auto = True
    BILL_STATUS_SELECTION = [
        ('draft', 'Draft'),
        ('billed', 'Billed'),
        ('partial', 'Partial')
    ]

    outside_port = fields.Boolean()
    ref = fields.Char()
    description = fields.Char()
    date = fields.Date()
    taxed_amount_cost = fields.Float(compute='_compute_taxed_cost_amount')

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    shipment_number = fields.Many2one('freight.operation', check_company=True)
    shipment_number_domain = fields.Char()
    is_console = fields.Boolean()
    product_id_domain = fields.Char()
    product_id = fields.Many2one('product.product', string='Category', check_company=True)
    expense_type_id = fields.Many2one('hr.expense.type')
    cover_letter_type = fields.Selection([('expense', 'Expenses'), ('official', 'Official Receipt')])
    expense_service = fields.Many2one('hr.expense.service', store=True)

    attachment_id = fields.Binary(attachment=True)

    uom_id = fields.Many2one('uom.uom', string='Unit of Measure',)
    tax_id = fields.Many2one('account.tax')
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True,
                                  help="Forces all journal items in this account to have a specific currency (i.e. bank journals). If no currency is set, entries can use any currency.")

    employee_id = fields.Many2one('hr.employee', store=True, check_company=True)
    cover_letter_id = fields.Many2one('hr.cover.letter', check_company=True)
    amount_sale = fields.Float()
    amount_cost = fields.Float()
    type = fields.Char()
    reference = fields.Char()
    branch_id = fields.Many2one('res.branch', string='Branch')
    claim_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    account_id = fields.Many2one('account.account')
    journal_id = fields.Many2one('account.journal')
    port_id = fields.Many2one('freight.port')
    number = fields.Integer('Number OF')
    master = fields.Many2one('freight.master', string="Master")
    housing = fields.Char(string="Housing")
    delegate_name = fields.Char('Delegate Name')
    id_number = fields.Char('ID Number')
    container_id = fields.Many2one('freight.container', 'Container Type')
    expense_service_type = fields.Selection([('clearance', 'Clearance'), ('freight', 'Freight'),
                                             ('transportation', 'Transportation'), ('transit', 'Transit')])
    operator_id = fields.Many2one('res.users', string='Opertor')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('approved', 'Approved'),
        ('refused', 'Refused')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft')
    line_state = fields.Selection([
        ('draft', 'To Submit'),
        ('approved_operator', 'Operator Approved'),
        ('approved', 'Approved'),
        ('refused', 'Refused')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft')

    event_state_id = fields.Many2one('els.event.state')
    event_state_domain = fields.Char()
    event_check = fields.Boolean()
    current_account = fields.Boolean()
    cover_state = fields.Selection(related='cover_letter_id.state', store=True)
    current_account_type = fields.Many2one('cover.account.type')
    master = fields.Many2one(related='shipment_number.master', store=True)
    housing = fields.Char(related='shipment_number.housing', store=True)
    bill_status = fields.Selection(BILL_STATUS_SELECTION, string='Bill Status', default='draft')
    analytic_account_id = fields.Many2one('account.analytic.account')
    quantity = fields.Float(string="Quantity")
    total_cost = fields.Float(compute='_onchange_get_tot_cost')
    total_sale = fields.Float(compute='_onchange_get_tot_cost', store=True)
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')
    customer_id = fields.Many2one('res.partner', )
    vendor_id = fields.Many2one('res.partner', )
    clearance_company = fields.Many2one('res.partner')
    clearance_operator = fields.Many2one('res.users', related='shipment_number.clearance_operator', readonly=False,
                                         store=True)
    tracking_agent = fields.Many2one('res.partner', string='Trucking Agent')
    agent_id = fields.Many2one('res.partner', 'Agent', readonly=False, store=True)
    journal_created = fields.Boolean(copy=False)
    partner_id = fields.Many2one('res.partner', )
    expens_journal_created = fields.Boolean(copy=False)

    @api.depends('quantity', 'amount_sale', 'amount_cost')
    def _onchange_get_tot_cost(self):
        for rec in self:
            rec.total_cost = rec.quantity * rec.amount_cost
            rec.total_sale = rec.quantity * rec.amount_sale

    @api.depends('tax_id', 'amount_cost')
    def _compute_taxed_cost_amount(self):
        for line in self:
            if line.tax_id:
                line.taxed_amount_cost = (1 + (line.tax_id.amount / 100)) * line.amount_cost
            else:
                line.taxed_amount_cost = line.amount_cost
