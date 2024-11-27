import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HROfficial(models.Model):
    _name = 'hr.cover.letter.official'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']
    _description = "Cover letter official"
    _check_company_auto = True

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        if not employee and not self.env.user.has_group('hr_expense.group_hr_expense_team_approver'):
            raise ValidationError(_('The current user has no related employee. Please, create one.'))
        return employee

    outside_port = fields.Boolean()
    description = fields.Char()
    date = fields.Date(default=fields.Date.today())
    clearance_company = fields.Many2one('res.partner')
    clearance_operator = fields.Many2one('res.users', related='shipment_number.clearance_operator', readonly=False,store=True)
    tracking_agent = fields.Many2one('res.partner', string='Trucking Agent')
    agent_id = fields.Many2one('res.partner', 'Agent', readonly=False,store=True)
    analytic_account_id = fields.Many2one('account.analytic.account')
    ref = fields.Char()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    shipment_number = fields.Many2one('freight.operation')
    sale_id = fields.Many2one('sale.order')
    purchase_id = fields.Many2one('purchase.order')
    is_console = fields.Boolean()
    product_id_domain = fields.Char(compute="_compute_product_id_domain", readonly=True, store=False, )
    product_id = fields.Many2one('product.product',check_company=True ,string="Product")
    expense_type_id = fields.Many2one('hr.expense.type', store=True)
    cover_letter_type = fields.Selection([('expense', 'Expenses'), ('official', 'Official Receipt')],default='official')
    expense_service = fields.Many2one('hr.expense.service', store=True,string="Official Receipt Type")
    cover_state = fields.Selection([
        ('draft', 'To Submit'),
        ('approved', 'Approved'),
        ('refused', 'Refused')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft')
    attachment_id = fields.Binary(attachment=True)
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True,
                                  help="Forces all journal items in this account to have a specific currency (i.e. bank journals). If no currency is set, entries can use any currency.")
    employee_id = fields.Many2one('hr.employee',default=_default_employee_id,store=True,check_company=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', default=lambda r: r.product_id.uom_id.id)
    tax_id = fields.Many2one('account.tax')
    taxed_amount_cost = fields.Float(compute='_compute_taxed_cost_amount',store=True)
    amount_sale = fields.Float()
    amount_cost = fields.Float()
    reference = fields.Char()
    type = fields.Char()
    claim_status = fields.Selection([('draft','Draft'),('done','Done')],default='draft')
    account_id = fields.Many2one('account.account')
    journal_id = fields.Many2one('account.journal')
    port_id = fields.Many2one('freight.port')
    number = fields.Integer('Number OF')
    master = fields.Many2one('freight.master')
    current_account_type = fields.Many2one('cover.account.type')
    housing = fields.Char(string="Housing")
    container_id = fields.Many2one('freight.container', 'Container Type')
    expense_service_type = fields.Selection(
        [('clearance', 'Clearance'), ('freight', 'Freight'), ('transportation', 'Transportation'),
         ('transit', 'Transit')],string="Official Receipt Type")
    operator_id = fields.Many2one('res.users', string='Opertor')
    line_state = fields.Selection([
        ('draft', 'To Submit'),
        ('approved_operator', 'Operator Approved'),
        ('approved', 'Approved'),
        ('refused', 'Refused')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft')
    bill_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    invoice_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')

    quantity = fields.Float(string="Quantity")
    total_cost = fields.Float(compute='_onchange_get_tot_cost')
    total_sale = fields.Float(compute='_onchange_get_tot_cost', store=True)
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')
    customer_id = fields.Many2one('res.partner', )
    vendor_id = fields.Many2one('res.partner', )
    cover_letter_id = fields.Many2one('hr.cover.letter', )
    journal_created = fields.Boolean(copy=False)

    shipment_number_domain = fields.Char(compute="_compute_shipment_number_domain", readonly=True, store=False, )

    marge = fields.Float(string="Marge", compute="_compute_marge", store=True)
    event_state_id = fields.Many2one('els.event.state')
    event_state_domain = fields.Char(compute='compute_event_state_domain', readonly=True, store=False, )
    event_check = fields.Boolean(copy=False)
    current_account = fields.Boolean(copy=False)
    partner_id = fields.Many2one('res.partner', )
    branch_id = fields.Many2one('res.branch', string='Branch')

    @api.depends('expense_service_type')
    def compute_event_state_domain(self):
        for rec in self:
            rec.event_state_domain = json.dumps(
                [('operator_service', '=', rec.expense_service_type)]
            )

    @api.depends('company_id', 'employee_id')
    def _compute_shipment_number_domain(self):
        for rec in self:
            rec.shipment_number_domain = json.dumps(
                [('company_id', '=', rec.company_id.id), ('employee_ids', 'in', [rec.cover_letter_id.employee_id.id])]
            )

    @api.depends('amount_sale', 'amount_cost')
    def _compute_marge(self):
        for record in self:
            record.marge = record.amount_sale - record.amount_cost

    @api.onchange('shipment_number', )
    def onchange_shipment_number(self):
        for rec in self:
            rec.agent_id = rec.shipment_number.agent_id.id
            rec.housing = rec.shipment_number.housing

    @api.depends('quantity', 'amount_sale', 'amount_cost')
    def _onchange_get_tot_cost(self):
        for rec in self:
            rec.total_cost = rec.quantity * rec.amount_cost
            rec.total_sale = rec.quantity * rec.amount_sale

    @api.model_create_multi
    def default_get(self, default_fields):
        res = super(HROfficial, self).default_get(default_fields)
        if self.currency_id:
            res.update({
                'sale_currency_id': self.currency_id.id or False
            })
        return res

    @api.onchange('currency_id', )
    def onchange_currency_id(self):
        for rec in self:
            if not rec.sale_currency_id:
                rec.sale_currency_id = rec.currency_id.id

    def action_approve(self):
        if self.shipment_number.customer_service_id == self.env.user:
            self.line_state = 'approved'
            self._activity_done()
        else:
            raise ValidationError(
                _("You are not authorised to approve this request only cover letter customer servicer"))

    def action_refuse(self):
        if self.operator_id == self.env.user:
            self.line_state = 'refused'
            self._activity_done()
        elif self.shipment_number.customer_service_id == self.env.user:
            self.line_state = 'refused'
            self._activity_done()
            self.send_activity(self.operator_id, 'Official cover letter is refused from customer service')

        else:
            raise ValidationError(_("You are not authorised to refuse this request only cover letter account manager"))

    def _activity_done(self):
        activity_ids = self.env['mail.activity'].sudo().search([('res_id', '=', self.id)])
        if activity_ids:
            for act in activity_ids:
                act.action_done()


    @api.depends('tax_id','amount_cost')
    def _compute_taxed_cost_amount(self):
        for line in self:
            if line.tax_id:
                line.taxed_amount_cost = (1 + (line.tax_id.amount / 100)) * line.amount_cost
            else:
                line.taxed_amount_cost =  line.amount_cost

    @api.depends( 'product_id', 'company_id')
    def _compute_product_id_domain(self):
        for rec in self:
            rec.product_id_domain = json.dumps(
                [('company_id', '=', rec.company_id.id), ('cover_letter_type', '=', 'official')]
            )

    def action_create_journal(self):
        # raise ValidationError(_(self.currency_id.name))
        company_currency = self.company_id.currency_id
        vals = {
            'ref': 'Official Expense',
            'date': fields.Date.today(),
            'currency_id': self.sale_currency_id.id,
            'company_id': self.company_id.id,
            'journal_id': self.journal_id.id,
            'employee_id': self.employee_id.id,
            'freight_operation_id': self.shipment_number.id,
            'move_type': 'entry',
            'line_ids': [],
        }
        total = 0
        for line in self:
            if not line.product_id.property_account_expense_id:
                raise ValidationError(
                    _('Expense Account for the expense category is not set. Please, set it and try again.'))
            amount_currency = line.taxed_amount_cost
            if line.sale_currency_id and line.sale_currency_id != company_currency:
                rate = line.sale_currency_id.rate_ids.filtered(
                    lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year)[0].mapped(
                    'inverse_company_rate')
                if rate:
                    amount_currency = line.taxed_amount_cost * rate[0]
                else:
                    raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))
            vals['line_ids'].append((0, 0, {
                'account_id': line.product_id.property_account_expense_id.id,
                'currency_id': line.currency_id.id,
                'shipment_number': line.shipment_number.id,
                'amount_currency': line.taxed_amount_cost,
                'debit': amount_currency,
                'credit': 0,
            }))
            total += amount_currency

        vals['line_ids'].append((0, 0, {
            'account_id': self.account_id.id,
            'currency_id': self.sale_currency_id.id,
            'partner_id': self.partner_id.id,
            'debit': 0,
            'credit': total,
        }))

        move_id = self.env['account.move'].create(vals)
        move_id.action_post()
        self.journal_created = True

    def send_activity(self,user,summary):
        now = fields.datetime.now()
        date_deadline = now.date()
        activ_list = []
        if user and user != 'None':
            activity_id = self.sudo().activity_schedule(
                'mail.mail_activity_data_todo', date_deadline,
                note=_(
                    '<a>Activity </a> for <a>Notify</a>') % (
                     ),
                user_id=user.id,
                res_id=self.id,

                summary=summary
            )
            activ_list.append(activity_id.id)
        [(4, 0, rec) for rec in activ_list]

    def action_print_report(self):
        active_ids = self._context.get('active_ids', [])
        data = self.read()[0]
        return self.env.ref('freight_expense.action_report_official_receipt_templates').report_action(self, data=data)

