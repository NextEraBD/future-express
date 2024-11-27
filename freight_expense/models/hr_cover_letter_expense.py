import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.http import request


class HrExpense(models.Model):
    _name = 'hr.cover.letter.expense'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']
    _description = "Cover letter expense"
    _check_company_auto = True

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        if not employee and not self.env.user.has_group('hr_expense.group_hr_expense_team_approver'):
            raise ValidationError(_('The current user has no related employee. Please, create one.'))
        return employee

    outside_port = fields.Boolean()
    ref = fields.Char()
    description = fields.Char()
    date = fields.Date(default=fields.Date.today(),string='Date OF')
    product_id_domain = fields.Char(compute="_compute_product_id_domain",readonly=True,store=False,)
    taxed_amount_cost = fields.Float(compute='_compute_taxed_cost_amount',store=True)

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    shipment_number = fields.Many2one('freight.operation')
    is_console = fields.Boolean()
    product_id = fields.Many2one('product.product',check_company=True, string="Product")

    expense_type_id = fields.Many2one('hr.expense.type',store=True)
    # cover_letter_type = fields.Selection(related='product_id.cover_letter_type',store=True)
    cover_letter_type = fields.Selection([('expense', 'Expenses'), ('official', 'Official Receipt')],default='expense')
    expense_service = fields.Many2one('hr.expense.service',store=True)
    expense_service_type = fields.Selection([('clearance', 'Clearance'), ('freight', 'Freight'), ('transportation', 'Transportation'), ('transit', 'Transit'), ('warehousing', 'Warehousing')])
    clearance_company = fields.Many2one('res.partner')
    clearance_operator = fields.Many2one('res.users', related='shipment_number.clearance_operator', readonly=False,
                                         store=True)
    tracking_agent = fields.Many2one('res.partner', string='Trucking Agent')
    agent_id = fields.Many2one('res.partner', 'Agent', readonly=False, store=True)
    employee_id = fields.Many2one('hr.employee',default=_default_employee_id,store=True,check_company=True)
    attachment_id = fields.Binary(attachment=True)
    operator_id = fields.Many2one('res.users', string='Opertor',)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', default=lambda r: r.product_id.uom_id.id)
    tax_id = fields.Many2one('account.tax')
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True,
                                  help="Forces all journal items in this account to have a specific currency (i.e. bank journals). If no currency is set, entries can use any currency.")

    master = fields.Many2one('freight.master')
    housing = fields.Char()
    reference = fields.Char()
    amount_sale = fields.Float()
    amount_cost = fields.Float()
    type = fields.Char()
    claim_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    account_id = fields.Many2one('account.account')
    journal_id = fields.Many2one('account.journal')
    port_id = fields.Many2one('freight.port')
    number = fields.Integer('Number OF')
    delegate_name = fields.Char('Delegate Name')
    id_number = fields.Char('ID Number')
    container_id = fields.Many2one('freight.container', 'Container Type')
    cover_state = fields.Selection([
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
    bill_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    invoice_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    quantity = fields.Float(string="Quantity")
    total_cost = fields.Float(compute='_onchange_get_tot_cost')
    total_sale = fields.Float(compute='_onchange_get_tot_cost', store=True)
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')
    customer_id = fields.Many2one('res.partner', )
    vendor_id = fields.Many2one('res.partner', )
    cover_letter_id = fields.Many2one('hr.cover.letter', )


    shipment_number_domain = fields.Char(compute="_compute_shipment_number_domain", readonly=True, store=False)

    taxed_amount = fields.Float(compute='_compute_taxed_cost_amount', store=True)
    product_tem_id = fields.Many2one('product.product', check_company=True, string="Category")
    branch_id = fields.Many2one('res.branch', string='Branch')
    event_state_id = fields.Many2one('els.event.state')
    event_state_domain = fields.Char(compute='compute_event_state_domain', readonly=True, store=False, )
    event_check = fields.Boolean()
    analytic_account_id = fields.Many2one('account.analytic.account')
    expens_journal_created = fields.Boolean(copy=False)
    partner_id = fields.Many2one('res.partner', )

    @api.depends('cover_letter_id.company_id', 'cover_letter_id.employee_id')
    def _compute_shipment_number_domain(self):
        for rec in self:
            rec.shipment_number_domain = json.dumps(
                [('company_id', '=', rec.company_id.id), ('employee_ids', 'in', [rec.cover_letter_id.employee_id.id])]
            )

    @api.depends('quantity', 'amount_sale', 'amount_cost')
    def _onchange_get_tot_cost(self):
        for rec in self:
            rec.total_cost = rec.quantity * rec.amount_cost
            rec.total_sale = rec.quantity * rec.amount_sale

    @api.model_create_multi
    def default_get(self, default_fields):
        res = super(HrExpense, self).default_get(default_fields)
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
    @api.onchange('shipment_number', )
    def onchange_shipment_number(self):
        for rec in self:
            rec.agent_id = rec.shipment_number.agent_id.id
            # rec.master = rec.shipment_number.master
            # rec.housing = rec.shipment_number.housing

    def create_shipment_line(self):
        if self.shipment_number and self.amount_sale:
            if self.expense_service_type == 'freight':
                self.shipment_number.freight_check = True
                freight_lines = self.env['freight.freight.line'].search([('shipment_id', '=', self.shipment_number.id)])
                so = False
                if freight_lines:
                    line = freight_lines.filtered(lambda l: l.sale_id.currency_id == self.sale_currency_id)
                    if line:
                        so = line.sale_id

                    if so:
                        so.order_line = [(0, 0, {
                            'product_id': self.product_id.id,
                            'name': self.product_id.name,
                            'product_uom_qty': 1,
                            'currency_id': self.sale_currency_id.id,
                            'price_unit': self.amount_sale,
                        })]
                        so = so.id
                self.env['freight.freight.line'].create({
                    'shipment_id': self.shipment_number.id,
                    'agent_id': self.agent_id.id,
                    'product_id': self.product_id.id,
                    'currency_id': self.sale_currency_id.id,
                    'price_sale': self.amount_sale,
                    'price_cost': self.amount_cost,
                    'destination_location_id': self.port_id.id,
                    'qty': 1,
                    'sale_id': so,
                    'freight_operator': self.shipment_number.freight_operator.id,
                })
            elif self.expense_service_type == 'transportation':
                self.shipment_number.transport_check = True
                freight_lines = self.env['freight.transport.line'].search(
                    [('shipment_id', '=', self.shipment_number.id)])
                so = False
                if freight_lines:
                    line = freight_lines.filtered(lambda l: l.sale_id.currency_id == self.sale_currency_id)
                    if line:
                        so = line.sale_id
                    if so:
                        so.order_line = [(0, 0, {
                            'product_id': self.product_id.id,
                            'name': self.product_id.name,
                            'product_uom_qty': 1,
                            'currency_id': self.sale_currency_id.id,
                            'price_unit': self.amount_sale,
                        })]
                        so = so.id

                self.env['freight.transport.line'].create({
                    'shipment_id': self.shipment_number.id,
                    'product_id': self.product_id.id,
                    'tracking_agent': self.tracking_agent.id,
                    'currency_id': self.sale_currency_id.id,
                    'sale_price': self.amount_sale,
                    'cost_price': self.amount_cost,
                    'destination_location_id': self.port_id.id,
                    'qty': 1,
                    'sale_id': so,
                    'transport_operator': self.shipment_number.transport_operator.id,
                })
            elif self.expense_service_type == 'clearance':
                self.shipment_number.clearance_check = True
                freight_lines = self.env['freight.clearance.line'].search(
                    [('shipment_id', '=', self.shipment_number.id)])
                so = False
                if freight_lines:
                    line = freight_lines.filtered(lambda l: l.sale_id.currency_id == self.sale_currency_id)
                    if line:
                        so = line.sale_id
                    if so:
                        so.order_line = [(0, 0, {
                            'product_id': self.product_id.id,
                            'name': self.product_id.name,
                            'product_uom_qty': 1,
                            'currency_id': self.sale_currency_id.id,
                            'price_unit': self.amount_sale,
                        })]
                        so = so.id
                self.env['freight.clearance.line'].create({
                    'shipment_id': self.shipment_number.id,
                    'product_id': self.product_id.id,
                    'clearance_company': self.clearance_company.id,
                    'currency_id': self.sale_currency_id.id,
                    'price': self.amount_sale,
                    'cost': self.amount_cost,
                    'destination_location_id': self.port_id.id,
                    'qty': 1,
                    'sale_id': so,
                    'clearance_operator': self.shipment_number.clearance_operator.id,
                })
            elif self.expense_service_type == 'transit':
                self.shipment_number.transit_check = True
                freight_lines = self.env['freight.transit.line'].search(
                    [('shipment_id', '=', self.shipment_number.id)])
                so = False
                if freight_lines:
                    line = freight_lines.filtered(lambda l: l.sale_id.currency_id == self.sale_currency_id)
                    if line:
                        so = line.sale_id
                    if so:
                        so.order_line = [(0, 0, {
                            'product_id': self.product_id.id,
                            'name': self.product_id.name,
                            'product_uom_qty': 1,
                            'currency_id': self.sale_currency_id.id,
                            'price_unit': self.amount_sale,
                        })]
                        so = so.id
                self.env['freight.transit.line'].create({
                    'shipment_id': self.shipment_number.id,
                    'product_id': self.product_id.id,
                    'currency_id': self.sale_currency_id.id,
                    'final_amount': self.amount_sale,
                    'amount': self.amount_cost,
                    'qty': 1,
                    'sale_id': so,
                    'transit_operator': self.shipment_number.transit_operator.id,
                })
            elif self.expense_service_type == 'warehousing':
                self.shipment_number.warehousing_check = True
                freight_lines = self.env['freight.transit.line'].search(
                    [('shipment_id', '=', self.shipment_number.id)])
                so = False
                if freight_lines:
                    line = freight_lines.filtered(lambda l: l.sale_id.currency_id == self.sale_currency_id)
                    if line:
                        so = line.sale_id
                    if so:
                        so.order_line = [(0, 0, {
                            'product_id': self.product_id.id,
                            'name': self.product_id.name,
                            'product_uom_qty': 1,
                            'currency_id': self.sale_currency_id.id,
                            'price_unit': self.amount_sale,
                        })]
                        so = so.id
                self.env['freight.warehouse.line'].create({
                    'shipment_id': self.shipment_number.id,
                    'product_id': self.product_id.id,
                    'currency_id': self.sale_currency_id.id,
                    'amount': self.amount_sale,
                    'qty': 1,
                    'sale_id': so,
                    'warehousing_operator': self.shipment_number.warehousing_operator.id,
                })
            else:
                raise ValidationError('You must select service before approve')

    def action_approve(self):
        self.create_shipment_line()
        self.line_state = 'approved'

    def action_refuse(self):
        if self.operator_id == self.env.user:
            self.line_state = 'refused'
            self._activity_done()
        elif self.shipment_number.customer_service_id == self.env.user:
            self.line_state = 'refused'
            self._activity_done()
            self.send_activity(self.operator_id, 'Expense cover letter is refused from customer service')
        else:
            raise ValidationError(_("You are not authorised to refuse this request only cover letter account manager"))

    def _activity_done(self):
        activity_ids = self.env['mail.activity'].sudo().search([('res_id', '=', self.id)])
        if activity_ids:
            for act in activity_ids:
                act.action_done()

    @api.depends('tax_id', 'amount_cost')
    def _compute_taxed_cost_amount(self):
        for line in self:
            if line.tax_id:
                line.taxed_amount_cost = (1 + (line.tax_id.amount / 100)) * line.amount_cost
            else:
                line.taxed_amount_cost = line.amount_cost

    @api.depends('product_id','company_id')
    def _compute_product_id_domain(self):
        for rec in self:
            rec.product_id_domain = json.dumps(
                [('company_id', '=', rec.company_id.id),('cover_letter_type', '=', 'expense')]
            )

    def action_create_so(self):
        if self:
            vals = {
                'partner_id': self[0].shipment_number.customer_id.id,
                'order_line': []
            }
            for line in self:
                if line.claim_status != 'done':
                    vals['order_line'].append((0,0,{
                        'product_id': line.product_id.id,
                        'currency_id': line.sale_currency_id.id,
                        'name': line.product_id.name,
                        'company_id': line.company_id.id,
                        'product_uom_qty': 1,
                        'tax_id': [(6,0,[line.tax_id.id])] if line.tax_id else False,
                        'product_uom': line.uom_id.id if line.uom_id.id else line.product_id.uom_id.id,
                        'price_unit': line.amount_sale,

                    }))
                    line.claim_status = 'done'
            so = self.env['sale.order'].create(vals)

    def send_activity(self,user,summary):
        now = fields.datetime.now()
        date_deadline = now.date()
        activ_list = []
        if user and user != 'None':
            activity_id = self.sudo().activity_schedule(
                'mail.mail_activity_data_todo', date_deadline,
                note=_(summary),
                user_id=user.id,
                res_id=self.id,

                summary=summary
            )
            activ_list.append(activity_id.id)
        [(4, 0, rec) for rec in activ_list]

    def action_create_journal(self):
        company_currency = self.company_id.currency_id
        vals = {
            'ref': 'Expense',
            'date': fields.Date.today(),
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'journal_id': self.journal_id.id,
            'freight_operation_id': self.shipment_number.id,
            'employee_id':self.employee_id.id,
            'move_type': 'entry',
            'line_ids': [],
        }
        total = 0
        for line in self:
            if not line.product_id.property_account_expense_id:
                raise ValidationError(_('Expense Account for the expense categury is not set. Please, set it and try again.'))
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
                'currency_id': line.sale_currency_id.id,
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
        self.expens_journal_created = True