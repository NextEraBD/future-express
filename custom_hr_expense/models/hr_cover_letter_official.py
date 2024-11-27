import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HROfficial(models.Model):
    _name = 'hr.cover.letter.official'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']
    _description = "Cover letter official"
    _check_company_auto = True

    # @api.model
    # def default_get(self, flds):
    #     """ Override to get default branch from employee """
    #     result = super(HROfficial, self).default_get(flds)
    #
    #     employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    #
    #     if employee_id:
    #         if employee_id.branch_id:
    #             result['branch_id'] = employee_id.branch_id.id
    #     return result

    outside_port = fields.Boolean(copy=False)
    description = fields.Char()
    date = fields.Date(default=fields.Date.today())
    ref = fields.Char()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    shipment_number = fields.Many2one('freight.operation')
    is_console = fields.Boolean(copy=False)
    journal_created = fields.Boolean(copy=False)
    product_id_domain = fields.Char(compute="_compute_product_id_domain", readonly=True, store=False, )
    product_id = fields.Many2one('product.product',check_company=True ,string="Category")
    expense_type_id = fields.Many2one('hr.expense.type', store=True)
    cover_letter_type = fields.Selection([('expense', 'Expenses'), ('official', 'Official Receipt')],default='official')
    expense_service = fields.Many2one('hr.expense.service', store=True)

    attachment_id = fields.Binary(attachment=True)
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True,
                                  help="Forces all journal items in this account to have a specific currency (i.e. bank journals). If no currency is set, entries can use any currency.")
    shipment_number_domain = fields.Char(compute="_compute_shipment_number_domain", readonly=True, store=False, )
    employee_id = fields.Many2one('hr.employee',store=True,check_company=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', default=lambda r: r.product_id.uom_id.id)
    tax_id = fields.Many2one('account.tax')
    taxed_amount_cost = fields.Float(compute='_compute_taxed_cost_amount',store=True)
    cover_letter_id = fields.Many2one('hr.cover.letter',check_company=True)
    amount_sale = fields.Float()
    amount_cost = fields.Float()
    marge = fields.Float(string="Marge", compute="_compute_marge", store=True)

    @api.depends('amount_sale', 'amount_cost')
    def _compute_marge(self):
        for record in self:
            record.marge = record.amount_sale - record.amount_cost

    reference = fields.Char()
    type = fields.Char()
    branch_id = fields.Many2one('res.branch', string='Branch', )
    claim_status = fields.Selection([('draft','Draft'),('done','Done')],default='draft')
    account_id = fields.Many2one('account.account')
    journal_id = fields.Many2one('account.journal')
    port_id = fields.Many2one('freight.port')
    number = fields.Integer('Number OF')
    master = fields.Many2one('freight.master', string="Master")
    current_account_type = fields.Many2one('cover.account.type')
    housing = fields.Char(string="Housing")
    container_id = fields.Many2one('freight.container', 'Container Type')
    expense_service_type = fields.Selection(
        [('clearance', 'Clearance'), ('freight', 'Freight'), ('transportation', 'Transportation'),
         ('transit', 'Transit')])
    operator_id = fields.Many2one('res.users', string='Opertor',compute='get_opertor')
    line_state = fields.Selection([
        ('draft', 'To Submit'),
        ('approved_operator', 'Operator Approved'),
        ('approved', 'Approved'),
        ('refused', 'Refused')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft')

    event_state_id = fields.Many2one('els.event.state')
    event_state_domain = fields.Char(compute='compute_event_state_domain', readonly=True, store=False, )
    event_check = fields.Boolean()
    current_account = fields.Boolean()
    cover_state = fields.Selection(related='cover_letter_id.state', store=True)
  
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
    partner_id = fields.Many2one('res.partner', )

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


    @api.depends('expense_service_type')
    def compute_event_state_domain(self):
        for rec in self:
            rec.event_state_domain = json.dumps(
                [('operator_service', '=', rec.expense_service_type)]
            )

    # def action_submit_event(self):
    #     if self.shipment_number:
    #         if self.expense_service_type == 'freight':
    #             self.shipment_number.freight_check = True
    #             self.shipment_number.freight_event_state = self.event_state_id
    #         elif self.expense_service_type == 'transportation':
    #             self.shipment_number.transport_check = True
    #             self.shipment_number.transport_event_state = self.event_state_id
    #         elif self.expense_service_type == 'clearance':
    #             self.shipment_number.clearance_check = True
    #             self.shipment_number.clearance_event_state = self.event_state_id
    #         elif self.expense_service_type == 'transit':
    #             self.shipment_number.transit_check = True
    #             self.shipment_number.transit_event_state = self.event_state_id
    #         elif self.expense_service_type == 'warehousing':
    #             self.shipment_number.warehousing_check = True
    #             self.shipment_number.warehousing_event_state = self.event_state_id
    #         else:
    #             raise ValidationError('You must select service before submit')

    @api.depends('expense_service_type', 'shipment_number')
    def get_opertor(self):
        for rec in self:
            if rec.expense_service_type and rec.shipment_number:
                if rec.expense_service_type == 'clearance':
                    rec.operator_id = rec.shipment_number.clearance_operator.id
                if rec.expense_service_type == 'transportation':
                    rec.operator_id = rec.shipment_number.transport_operator.id
                if rec.expense_service_type == 'freight':
                    rec.operator_id = rec.shipment_number.freight_operator.id
                if rec.expense_service_type == 'transit':
                    rec.operator_id = rec.shipment_number.transit_operator.id
            else:
                rec.operator_id = False

    def action_approve_operator(self):
        if self.operator_id == self.env.user:
            self.line_state = 'approved_operator'
            self._activity_done()
            self.send_activity(self.shipment_number.customer_service_id,
                               'Official cover letter is approved from operator and need approval from you')
        else:
            raise ValidationError(_("You are not authorised to approve this request only cover letter account manager"))

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


    # @api.onchange('product_id', 'cover_letter_id')
    # def set_shipment_number_domain(self):
    #     if self.cover_letter_id.employee_id:
    #         ids = self.env['freight.operation'].search(
    #             [('employee_ids', 'in', self.cover_letter_id.employee_id.id)]).ids
    #         return {'domain': {'shipment_number': [('id', 'in', ids)]}}


    @api.depends('tax_id','amount_cost')
    def _compute_taxed_cost_amount(self):
        for line in self:
            if line.tax_id:
                line.taxed_amount_cost = (1 + (line.tax_id.amount / 100)) * line.amount_cost
            else:
                line.taxed_amount_cost =  line.amount_cost


    ####################################################################################################################
    ###############################################CRUD METHODS#########################################################

    @api.model
    def create(self, vals):
        res = super(HROfficial, self).create(vals)
        vals = res._convert_to_write(res._cache)
        vals['ref'] = res.id
        vals['reference'] = res.cover_letter_id.name
        vals['type'] = 'Official Receipt'
        self.env['hr.cover.letter.line'].create(vals)
        return res

    def write(self, vals):
        res = super(HROfficial, self).write(vals)
        line = self.env['hr.cover.letter.line'].search([('ref', '=', self.id)])
        line.write(vals)
        return res

    def unlink(self):
        for rec in self:
            line = self.env['hr.cover.letter.line'].search([('ref', '=', rec.id)])
            line.unlink()
        return super(HROfficial, self).unlink()

    @api.depends('cover_letter_id.company_id', 'cover_letter_id.employee_id')
    def _compute_shipment_number_domain(self):
        for rec in self:
            rec.shipment_number_domain = json.dumps(
                [('company_id', '=', rec.company_id.id), ('employee_ids', 'in',[rec.cover_letter_id.employee_id.id])]
            )

    ####################################################################################################################
    @api.depends('cover_letter_id', 'product_id', 'cover_letter_id.company_id')
    def _compute_product_id_domain(self):
        for rec in self:
            rec.product_id_domain = json.dumps(
                [('company_id', '=', rec.company_id.id), ('cover_letter_type', '=', 'official')]
            )

    @api.onchange('port_id', 'product_id', 'cover_letter_id', 'shipment_number',)
    def onchange_product_id(self):
        self.expense_type_id = self.product_id.expense_type_id
        self.cover_letter_type = 'official'
        self.expense_service = self.product_id.expense_service
        self.expense_service_type = self.product_id.expense_service_type
        self.amount_cost = self.product_id.standard_price
        self.amount_sale = self.product_id.list_price
        if self.cover_letter_id:
            self.employee_id = self.cover_letter_id.employee_id
            self.company_id = self.cover_letter_id.company_id
            self.branch_id = self.cover_letter_id.branch_id
        if self.shipment_number:
            self.port_id = self.shipment_number.destination_location_id
            self.master = self.shipment_number.master
            self.housing = self.shipment_number.housing


    @api.onchange('master', 'housing', 'employee_id')
    def onchange_master_housing(self):
        if self.master or self.housing:
            ids = self.env['freight.operation'].search(
                ['&', ('employee_ids', 'in', [self.employee_id.id]), '|', ('master', '=', self.master.id),
                 ('housing', '=', self.housing)]).ids
            return {'domain': {'shipment_number': [('id', 'in', ids)]}}
        else:
            ids = self.env['freight.operation'].search(
                [('employee_ids', 'in', [self.employee_id.id])]).ids
            return {'domain': {'shipment_number': [('id', 'in', ids)]}}

    def action_create_journal(self):
        # raise ValidationError(_(self.currency_id.name))
        company_currency = self.company_id.currency_id
        vals = {
            'ref': 'Official Expense',
            'date': fields.Date.today(),
            'currency_id': self.sale_currency_id.id,
            'company_id': self.company_id.id,
            'journal_id': self.journal_id.id,
            'employee_id':self.employee_id.id,
            'freight_operation_id':self.shipment_number.id,
            'move_type': 'entry',
            'line_ids': [],
        }
        total = 0
        for line in self:
            if not line.product_id.property_account_expense_id:
                raise ValidationError(_('Expense Account for the expense category is not set. Please, set it and try again.'))
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
        return self.env.ref('custom_hr_expense.action_report_official_receipt_templates').report_action(self, data=data)

