from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from odoo.http import request



class HrCoverLetter(models.Model):
    _name = 'hr.cover.letter'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']
    _description = "Cover letter"
    _order = "date desc, id desc"
    _check_company_auto = True

    # @api.model
    # def default_get(self, fields):
    #     res = super(HrCoverLetter, self).default_get(fields)
    #     branch_id = False
    #     if self.env.user.branch_id:
    #         branch_id = self.env.user.branch_id.id
    #     res.update({
    #         'branch_id': branch_id
    #     })
    #     return res

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        if not employee and not self.env.user.has_group('hr_expense.group_hr_expense_team_approver'):
            raise ValidationError(_('The current user has no related employee. Please, create one.'))
        return employee

    name = fields.Char()
    date = fields.Date(default=fields.Date.today())
    employee_id = fields.Many2one('hr.employee',string="Employee",
                                  store=True, required=True, readonly=False, tracking=True,
                                  states={'approved': [('readonly', True)], 'done': [('readonly', True)]},
                                  default=_default_employee_id,
                                  check_company=True)

    company_id = fields.Many2one('res.company',default=lambda self:self.env.company)
    refuse_user_id = fields.Many2one('res.users')
    refuse_reason = fields.Char()
    refuse_date = fields.Date()
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('account_approve', 'Account Approved'),
        # ('done', 'Paid'),
        ('refused', 'Refused')
    ],string='Status', copy=False, index=True, readonly=True, store=True, default='draft')

    total_ex_sale_amount = fields.Float()
    total_ex_cost_amount = fields.Float()

    total_of_sale_amount = fields.Float()
    total_of_cost_amount = fields.Float()

    total_sale_amount = fields.Float()
    total_cost_amount = fields.Float()

    # expense_line_ids = fields.One2many('hr.cover.letter.expense', 'cover_letter_id')
    # official_line_ids = fields.One2many('hr.cover.letter.official', 'cover_letter_id')
    # cov_line_ids = fields.One2many('hr.cover.letter.line', 'cover_letter_id')
    move_line_ids = fields.Many2many('account.move.line')
    bill_count = fields.Integer()
    entry_count = fields.Integer()

    branch_id = fields.Many2one('res.branch', string='Branch', default=lambda self: self.env.user.branch_id, readonly=True)
    ex_is_console = fields.Boolean( store=True)
    off_is_console = fields.Boolean( store=True)
    all_approved = fields.Boolean()
    checked = fields.Boolean()
    total_gl = fields.Float( store=True)
    remaining_balance = fields.Float( store=True)

    # @api.depends('expense_line_ids.line_state','official_line_ids.line_state')
    # def compute_all_approved(self):
    #     for rec in self:
    #         rec.all_approved = False
    #         if rec.expense_line_ids:
    #             for line in rec.expense_line_ids:
    #                 if line.line_state == 'approved':
    #                     rec.all_approved = True
    #                     self._send_activity([self.employee_id.cover_letter_manager_id.id])
    #                 else:
    #                     rec.all_approved = False
    #
    #         if rec.official_line_ids:
    #             for line in rec.official_line_ids:
    #                 if line.line_state == 'approved':
    #                     rec.all_approved = True
    #                     self._send_activity([self.employee_id.cover_letter_manager_id.id])
    #                 else:
    #                     rec.all_approved = False

        # for record in self:
        #     flag = False
        #     if any(line.line_state == 'approved' for line in record.expense_line_ids):
        #         flag = True
        #     if not flag:
        #         record['all_approved'] = True
        #     else:
        #         record['all_approved'] = False


    # @api.onchange('employee_id')
    # def get_branch(self):
    #     if self.employee_id:
    #         if self.employee_id.branch_id:
    #             self.update({'branch_id': self.employee_id.branch_id})
    #         else:
    #             self.update({'branch_id': False})

    # @api.depends('expense_line_ids')
    # def compute_ex_is_console(self):
    #     for rec in self:
    #         for line in rec.expense_line_ids:
    #             if line.is_console == True:
    #                 rec.ex_is_console = True
    #                 return
    #             else:
    #                 rec.ex_is_console = False
    #
    # @api.depends('official_line_ids')
    # def compute_off_is_console(self):
    #     for rec in self:
    #         for line in rec.official_line_ids:
    #             if line.is_console == True:
    #                 rec.off_is_console = True
    #                 return
    #             else:
    #                 rec.off_is_console = False

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.cover.letter') or '/'
        res = super(HrCoverLetter, self).create(vals)
        return res

    # @api.depends('expense_line_ids','official_line_ids')
    # def _compute_total_sale_amount(self):
    #     for rec in self:
    #         rec.total_ex_sale_amount = rec.total_ex_cost_amount = rec.total_of_sale_amount = \
    #             rec.total_of_cost_amount = rec.total_sale_amount = rec.total_cost_amount = 0
    #         for line in rec.expense_line_ids:
    #             rec.total_ex_sale_amount += line.amount_sale
    #             rec.total_ex_cost_amount += line.taxed_amount_cost
    #         for line in rec.official_line_ids:
    #             rec.total_of_sale_amount += line.amount_sale
    #             rec.total_of_cost_amount += line.taxed_amount_cost
    #         for line in rec.cov_line_ids:
    #             rec.total_sale_amount += line.amount_sale
    #             rec.total_cost_amount += line.taxed_amount_cost

    # def _compute_bill_count(self):
    #     for rec in self:
    #         count = self.env['account.move'].search_count([('cover_letter_id','=',self.id), ('move_type', '=', 'in_invoice')])
    #         rec.bill_count = count
    #
    # def _compute_entry_count(self):
    #     for rec in self:
    #         count = self.env['account.move'].search_count([('cover_letter_id','=',self.id), ('move_type', '=', 'entry')])
    #         rec.entry_count = count
    #
    # def action_submit(self):
    #     self.state = 'reported'
    #     for rec in self.expense_line_ids:
    #         rec.send_activity(rec.operator_id,'Expense need operator service approval')
    #     for offi in self.official_line_ids:
    #         operator_id = offi.operator_id.id
    #         offi.send_activity(offi.operator_id,'Official receipt need operator service approval')
    #     self.action_submit_events()
    #
    # def action_manager_approve(self):
    #     if self.employee_id.expense_manager_id == self.env.user:
    #         self.state = 'approved'
    #         self._activity_done()
    #         self._send_activity([self.employee_id.cover_letter_manager_id.id])
    #     else:
    #         raise ValidationError(_("You are not authorised to approve this request only expense manager"))
    # def action_manager_approve(self):
    #     # Remove or comment out the verification logic
    #     # if self.employee_id.expense_manager_id == self.env.user:
    #     self.state = 'approved'
    #     self._activity_done()
    #     self._send_activity([self.employee_id.cover_letter_manager_id.id])

    def action_account_approve(self):
        self.checked = True
        if self.employee_id.cover_letter_manager_id == self.env.user:
            self.state = 'account_approve'
            self._activity_done()
            self.action_create_journal_entries()
        else:
            raise ValidationError(_("You are not authorised to approve this request only Branch account manager"))

    def action_paid(self):
        if self.env.user in self.branch_id.treasury_manager:
            self.state = 'done'
            self._activity_done()
        else:
            raise ValidationError(_("You are not authorised to approve this request only cover letter account manager"))
    # def action_paid(self):
    #     # if self.env.user in self.branch_id.treasury_manager:
    #     self.state = 'done'
    #     self._activity_done()

    def action_refuse(self):
        if self.employee_id.cover_letter_manager_id == self.env.user:
            self.state = 'refused'
            self.refuse_user_id = self.env.user
            self.refuse_date = fields.Date.today()
            self._activity_done()
        else:
            raise ValidationError(_("You are not authorised to refuse this request only cover letter account manager"))

    # def action_create_journal_expense(self):
    #     company_currency = self.company_id.currency_id
    #     vals = {
    #         'ref': self.name,
    #         'date': fields.Date.today(),
    #         'company_id': self.company_id.id,
    #         'journal_id': self.employee_id.journal_id.id,
    #         'employee_id': self.employee_id.id,
    #         'cover_letter_id': self.id,
    #         # 'branch_id': self.branch_id.id,
    #         'move_type': 'entry',
    #         'line_ids': [],
    #     }
    #     total = 0
    #     emp_account_id = False
    #     for line in self.expense_line_ids:
    #         if not line.currency_id:
    #             raise ValidationError(_('You Should Add Currency first.'))
    #         if not line.product_id.sub_account_id:
    #             raise ValidationError(
    #                 _('Borking Account for the expense categury is not set. Please, set it and try again.'))
    #         amount_currency = line.taxed_amount_cost
    #         if line.currency_id and line.currency_id != company_currency:
    #             if not line.currency_id.rate_ids:
    #                 raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))
    #             rate = line.currency_id.rate_ids.filtered(
    #                 lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year)[0].mapped(
    #                 'inverse_company_rate')
    #             if rate:
    #                 amount_currency = line.taxed_amount_cost * rate[0]
    #             else:
    #                 raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))
    #         vals['line_ids'].append((0, 0, {
    #             'account_id': line.product_id.property_account_expense_id.id,
    #             'currency_id': line.currency_id.id,
    #             'analytic_account_id': line.analytic_account_id.id,
    #             'analytic_distribution': {str(line.analytic_account_id.id): 100.00},
    #             'shipment_number': line.shipment_number.id,
    #             'amount_currency': line.taxed_amount_cost,
    #             'debit': amount_currency,
    #             'credit': 0,
    #         }))
    #         total += amount_currency
    #     emp_account_id = False
    # 
    #     vals['line_ids'].append((0, 0, {
    #         'account_id': emp_account_id,
    #         'partner_id': self.employee_id.user_id.partner_id.id,
    #         'debit': 0,
    #         'credit': total,
    #     }))
    # 
    #     move_id = self.env['account.move'].create(vals)
    #     move_id.action_post()

    # def action_create_journal_official(self):
    #     company_currency = self.company_id.currency_id
    #     vals = {
    #         'ref': self.name,
    #         'date': fields.Date.today(),
    #         'company_id': self.company_id.id,
    #         'journal_id': self.employee_id.journal_id.id,
    #         'employee_id': self.employee_id.id,
    #         'cover_letter_id': self.id,
    #         'branch_id': self.branch_id.id,
    #         'move_type': 'entry',
    #         'line_ids': [],
    #     }
    #     total = 0
    #     emp_account_id = False
    #     for line in self.official_line_ids:
    #         amount_currency = line.taxed_amount_cost
    #         if line.current_account:
    #             emp_account_id = line.current_account_type.journal_id.default_account_id.id
    #         else:
    #             emp_account_id = self.employee_id.employee_account_id.id
    #         if line.currency_id != company_currency:
    #             rate = line.currency_id.rate_ids.filtered(
    #                 lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year).mapped(
    #                 'inverse_company_rate')
    #             if rate:
    #                 amount_currency = line.taxed_amount_cost * rate[0]
    #             else:
    #                 raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))
    # 
    #         vals['line_ids'].append((0, 0, {
    #             'account_id': line.product_id.property_account_expense_id.id,
    # 
    #             'currency_id': line.currency_id.id,
    #             # 'analytic_account_id': line.analytic_account_id.id,
    #             'analytic_distribution': {str(line.analytic_account_id.id): 100.00},
    #             'shipment_number': line.shipment_number.id,
    #             'amount_currency': line.taxed_amount_cost,
    #             'debit': amount_currency,
    #             'credit': 0,
    #         }))
    #         total += amount_currency
    # 
    #     vals['line_ids'].append((0, 0, {
    #             'account_id': emp_account_id,
    #             'partner_id': self.employee_id.user_id.partner_id.id,
    #             'debit': 0,
    #             'credit': total,
    #         }))
    # 
    #     move_id = self.env['account.move'].create(vals)
    #     move_id.action_post()

    # def action_create_journal_entries(self):
    #     self.action_create_journal_expense()
    #     self.action_create_journal_official()

    def action_viw_vendor_bill(self):
        related_bill_ids = self.env['account.move'].search([
            ('cover_letter_id','=',self.id),('move_type', '=', 'in_invoice')
        ]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Coverage Vendor Bill'),
            'res_model': 'account.move',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', related_bill_ids)],
        }

    def action_viw_journals(self):
        related_journal_ids = self.env['account.move'].search([
            ('cover_letter_id', '=', self.id), ('move_type', '=', 'entry')
        ]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Coverage Journal entries'),
            'res_model': 'account.move',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', related_journal_ids)],
        }

    def _send_activity(self,user_ids):
        date_deadline = fields.Date.today()
        activ_list = []
        for user_id in user_ids:
            if user_id and user_id != 'None':
                activity_id = self.sudo().activity_schedule(
                    'mail.mail_activity_data_todo', date_deadline,
                    note=_(
                        '<a>Task </a> for <a>Approve</a>') % (
                         ),
                    user_id=user_id,
                    res_id=self.id,

                    summary=_("PLZ Approve this cover letter for the employee %s")% self.employee_id.name
                )
                activ_list.append(activity_id.id)
        [(4, 0, rec) for rec in activ_list]

    def _activity_done(self):
        activity_ids = self.env['mail.activity'].sudo().search([('res_id', '=', self.id)])
        if activity_ids:
            for act in activity_ids:
                act.action_done()

    # def daily_update_notification_cron(self):
    #     base_urL = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     letters = self.env['hr.cover.letter'].search([('all_approved','=',True),('state','!=','account_approve')])
    #     for letter in letters:
    #         base_url = base_urL + \
    #                    f'/web#id={letter.id}&view_type=form&model=hr.cover.letter'
    #         notification_ids = [(0, 0, {
    #             'res_partner_id': letter.employee_id.cover_letter_manager_id.id,
    #             'notification_type': 'inbox'
    #         })]
    #         letter.message_post(record_name=f'Task {letter.name} - update',
    #                           body=f"""
    #             <p>Dear {letter.employee_id.cover_letter_manager_id.id},</p>
    #             <p>Good day,</p>
    #             <br/>
    #             <p>Please Approve Cover Letter No:</p>
    #
    #             <br/>
    #             <a href="{base_url}"  style="background-color:#875A7B; padding: 10px; text-decoration: none; color: #fff; border-radius: 5px;">
    #             {letter.name}
    #                                     </a>
    #             <br/>
    #             <br/>
    #         """, message_type="notification",
    #                           subtype_xmlid="mail.mt_comment",
    #                           author_id=letter.create_uid.partner_id.id,
    #                           notification_ids=notification_ids,
    #                           )

    # def send_to_operator(self):
    #     base_urL = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     letters = self.env['hr.cover.letter'].search([('all_approved', '=', True), ('state', '!=', 'account_approve')])
    #     for letter in self.expense_line_ids:
    #         base_url = base_urL + \
    #                    f'/web#id={letter.id}&view_type=form&model=hr.cover.letter.expense'
    #         email_from = self.env.user.email
    #         email_to = str(letter.operator_id.login)
    #         html = f"""
    #             <p>Dear {letter.operator_id.name},</p>
    #             <p>Good day,</p>
    #             <br/>
    #
    #             <p>Please Approve Expense No.{letter.cover_letter_id.name}</p>
    #             <br/>
    #             <p> Approve Expense No.</p>
    #             <a href="{base_url}"  style="background-color:#875A7B; padding: 10px; text-decoration: none; color: #fff; border-radius: 5px;">
    #             {letter.cover_letter_id.id}
    #                                     </a>
    #             <br/>
    #             <br/>
    #
    #         """
    #         template_data = {
    #             'subject': f'Pricing',
    #             'body_html': html,
    #             'email_from': email_from,
    #             'email_to': email_to,
    #         }
    #
    #         mail = self.env['mail.mail'].sudo().create(template_data)
    #         mail.send(raise_exception=False)
    #         notification_ids = [(0, 0, {
    #             'res_partner_id': letter.operator_id.partner_id.id,
    #             'notification_type': 'inbox'
    #         })]
    #         self.message_post(record_name=f'Pricing Reject',
    #                           body=f"""
    #             <p>Dear {letter.operator_id.name},</p>
    #             <p>Good day,</p>
    #             <br/>
    #             <p>Please update your pricing No.{letter.shipment_number.name}</p>
    #
    #             <br/>
    #             <a href="{base_url}"  style="background-color:#875A7B; padding: 10px; text-decoration: none; color: #fff; border-radius: 5px;">
    #             {letter.shipment_number.id}
    #                                     </a>
    #             <br/>
    #
    #         """, message_type="notification",
    #                           subtype_xmlid="mail.mt_comment",
    #                           author_id=letter.operator_id.partner_id.id,
    #                           notification_ids=notification_ids,
    #                           )

    # def action_submit_events(self):
    #     for line in self.expense_line_ids:
    #         if line.shipment_number:
    #             if not line.event_check:
    #                 vals = {
    #                     'date': fields.Date.today(),
    #                     'freight_operation_id': line.shipment_number.id,
    #                     'branch_id': self.branch_id.id,
    #                     'company_id': self.company_id.id,
    #                     'operator_service': line.expense_service_type,
    #                     'state_id': line.event_state_id.id,
    #                 }
    #                 event = self.env['els.events'].create(vals)
    #                 line.event_check = True
    #                 event.action_submit()
    #     for line in self.official_line_ids:
    #         if line.shipment_number:
    #             if not line.event_check:
    #                 vals = {
    #                     'date': fields.Date.today(),
    #                     'freight_operation_id': line.shipment_number.id,
    #                     'branch_id': self.branch_id.id,
    #                     'company_id': self.company_id.id,
    #                     'operator_service': line.expense_service_type,
    #                     'state_id': line.event_state_id.id,
    #                 }
    #                 event = self.env['els.events'].create(vals)
    #                 line.event_check = True
    #                 event.action_submit()
    #
    # def get_employee_balance(self):
    #     for rec in self:
    #         partner = rec.employee_id.custody_manager_id.partner_id
    #         if partner:
    #             lines_opj = rec.env['account.move.line'].sudo()
    #             move_lines = lines_opj.search(
    #                 [('partner_id', '=', partner.id),
    #                  ('account_id', '=', rec.employee_id.employee_account_id.id),
    #                  ('parent_state', '=', 'posted'),
    #                  ]
    #             )
    #             debit, credit = 0.0, 0.0
    #             for line in move_lines:
    #                 credit += line.credit
    #                 debit += line.debit
    #             balance = debit - credit
    #             return balance
    #         else:
    #             return  0
    #
    @api.depends('total_cost_amount','employee_id')
    def compute_remaining_balance(self):
        for rec in self:
            rec.total_gl = rec.get_employee_balance()
            rec.remaining_balance = rec.total_gl - rec.total_cost_amount
