import datetime

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HrVariableAllowanceRequest(models.Model):
    _name = 'hr.variable.allowance.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.onchange('select_type', 'department_id', 'employee_id')
    def _get_employee(self):
        for rec in self:
            employee_ids = []
            rec.employee_ids = False
            employees = False
            if rec.select_type == 'employee':
                employees = self.env['hr.employee'].search(
                    [('id', '=', rec.employee_id.id)])
            elif rec.select_type == 'department':
                employees = self.env['hr.employee'].search(
                    [('department_id', '=', rec.department_id.id)])
            elif rec.select_type == 'all':
                employees = self.env['hr.employee'].search([])
            if employees:
                for emp in employees:
                    employee_ids.append(emp.id)
                rec.employee_ids = employee_ids

    employee_ids = fields.Many2many('hr.employee', string='Employees')
    name = fields.Char()
    date = fields.Date()
    tmp_amount = fields.Float()
    amount_rate_multiplier = fields.Float(default=1.0)
    amount = fields.Float()
    branch_id = fields.Many2one('res.branch', default=lambda self: self.env.user.branch_id, string='Branch')
    # absent_id = fields.Many2one('hr.employee.absent', string="Absent Employee")
    department_id = fields.Many2one(comodel_name="hr.department")

    rule_id = fields.Many2one('hr.variable.allowance.rule')
    structure_id = fields.Many2one('hr.payroll.structure', related='rule_id.structure_id', string="Salary Structure",
                                   store=True)
    allowance_or_deduction = fields.Selection([('allowance', 'Allowance'), ('deduction', 'Deduction')],
                                              related='rule_id.allowance_or_deduction', store=True,readonly=False)
    rule_id_allowance_type = fields.Selection(related='rule_id.allowance_type', store=False)
    employee_id = fields.Many2one('hr.employee', default=lambda self: self.env.user.employee_id.id)
    contract_id = fields.Many2one('hr.contract', compute='_get_contract_id', store=True)
    payslip_id = fields.Many2one('hr.payslip')

    allowance_approvals = fields.One2many('variable.allow.valid.status', 'variable_allowance_request_id',
                                          string='Allowance Validators',
                                          )
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Legal Affairs'),('lawyer_approved', 'Legal Affair Approved'), ('hr_approve', 'Approve'),
                              ('refused', 'Refused'), ('hr_refused', 'HR Refused')], string='Status', copy=False,
                             default='draft')

    type = fields.Selection([('var_internal_travel_exp_allow', 'Travel Allow Internal'),
                             ('var_external_travel_reward_allow', 'External Travel Reward Allow'),
                             ('var_accomod_allow', 'Accomod Allow'),
                             ('var_overtime_allow', 'Over Time Allow'),
                             ('var_collection_comm_allow', 'Collections Commissions'),
                             ('var_sales_comm_allow', 'Sales Commissions'),
                             ('var_manufacturing_comm_allow', 'Manufacturing Commissions'),
                             ('var_night_shift_allow', 'Night Shifts')],
                            string='Applied On', copy=False)
    select_type = fields.Selection([
        ('employee', 'Employee'),
        ('department', 'Department'),
        ('all', 'All Employees')
    ], default='employee', string='Applied On', required=True)
    deduction_type_id = fields.Many2one('hr.variable.allowance.type', string='Deduction Type')
    deduction_type_rule_ids = fields.Many2many('hr.variable.allowance.type.rule', relation='deduction_type_rule_rel',)
    deduction_type_rule_id = fields.Many2one('hr.variable.allowance.type.rule',domain="[('type_id', '=', deduction_type_id)]")
    action = fields.Selection([
        ('suspended', 'Suspended'), ('penalize', 'Penalize And Suspend'),
    ])
    penalty = fields.Boolean()
    absent_times = fields.Integer()
    @api.onchange('employee_id', 'date')
    def get_employee_name(self):
        for rec in self:
            if rec.select_type == 'employee' and rec.employee_id:
                rec.department_id = rec.employee_id.department_id.id

    @api.depends('employee_id')
    def _get_contract_id(self):
        running_contracts = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id),
                                                            ('state', '=', 'open')])
        if running_contracts:
            self.contract_id = running_contracts[0].id
        else:
            self.contract_id = False

    # @api.depends('contract_id', 'rule_id', 'amount_rate_multiplier', 'type')
    # def _compute_amount(self):
    #     for rec in self:
    #         # if rec.employee_id and rec.contract_id and rec.rule_id and rec.rule_id.allowance_type == 'rule':
    #         #     try:
    #         #         rec.tmp_amount = rec.amount_rate_multiplier * eval(rec.rule_id.rule, {'contract': rec.contract_id, 'employee': rec.employee_id})
    #         #         if rec.rule_id.allowance_or_deduction == 'deduction':
    #         #             rec.tmp_amount = abs(rec.tmp_amount) * -1
    #         #         rec.amount = rec.tmp_amount
    #         #     except:
    #         #         raise ValidationError("Wrong rule's syntax, please fix it and try again.")
    #         # else:
    #         #     rec.tmp_amount = 0
    #         if rec.type:
    #             if rec.type == 'var_internal_travel_exp_allow':
    #                 rec.tmp_amount = rec.contract_id.grade_id.var_internal_travel_exp_allow
    #                 rec.amount = rec.tmp_amount
    #             elif rec.type == 'var_external_travel_reward_allow':
    #                 rec.tmp_amount = rec.contract_id.grade_id.var_external_travel_reward_allow
    #                 rec.amount = rec.tmp_amount
    #             elif rec.type == 'var_accomod_allow':
    #                 rec.tmp_amount = rec.contract_id.grade_id.var_accomod_allow
    #                 rec.amount = rec.tmp_amount
    #             elif rec.type == 'var_overtime_allow':
    #                 rec.tmp_amount = rec.contract_id.grade_id.var_overtime_allow
    #                 rec.amount = rec.tmp_amount
    #             elif rec.type == 'var_collection_comm_allow':
    #                 rec.tmp_amount = rec.contract_id.grade_id.var_collection_comm_allow
    #                 rec.amount = rec.tmp_amount
    #             elif rec.type == 'var_sales_comm_allow':
    #                 rec.tmp_amount = rec.contract_id.grade_id.var_sales_comm_allow
    #                 rec.amount = rec.tmp_amount
    #             elif rec.type == 'var_manufacturing_comm_allow':
    #                 rec.tmp_amount = rec.contract_id.grade_id.var_manufacturing_comm_allow
    #                 rec.amount = rec.tmp_amount
    #             elif rec.type == 'var_night_shift_allow':
    #                 rec.tmp_amount = rec.contract_id.grade_id.var_night_shift_allow
    #                 rec.amount = rec.tmp_amount
    #         else:
    #             rec.tmp_amount = 0

    def write(self, vals):
        if self.rule_id.allowance_or_deduction == 'deduction':
            amount = vals.get('amount', None)
            if amount:
                vals['amount'] = abs(amount) * -1
        res = super(HrVariableAllowanceRequest, self).write(vals)
        return res

    @api.onchange('deduction_type_id')
    def onchange_deduction_type_id(self):
        self.deduction_type_rule_ids = self.deduction_type_id.rule_ids

    # by kh.hb
    @api.onchange('employee_id')
    def load_allowance_approvals(self):
        if self.employee_id:
            ## validations
            if not self.employee_id.department_id.manager_id:
                raise UserError(_("this employee Department not have a Manager plz set manager to this department"))
            current_manager = None
            arr = [(5, 0, 0)]
            if self.employee_id.parent_id:
                current_manager = self.employee_id.parent_id
                arr.append((0, 0, {
                    'validating_user': self.employee_id.parent_id.user_id.id,
                }))
            count = 0
            while current_manager != self.employee_id.department_id.manager_id:
                if current_manager and current_manager.parent_id:
                    arr.append((0, 0, {
                        'validating_user': current_manager.parent_id.user_id.id,
                    }))
                    current_manager = current_manager.parent_id
                count += 1
                if count == 15:
                    raise UserError(_("the hierarchy position for this employee not specified correctly"))

            if arr:
                self.allowance_approvals = arr
                # self.update({'allowance_approvals': arr})
                # return arr

    # @api.model
    # def create(self, values):
    #     result = super(HrVariableAllowanceRequest, self).create(values)
    #     validators = self.load_allowance_approvals()
    #     result.allowance_approvals = validators
    #     return result

    def approval_check(self):
        current_employee = self.employee_id
        active_id = self.env.context.get('active_id') if self.env.context.get(
            'active_id') else self.id

        allowance = self.env['hr.variable.allowance.request'].search([('id', '=', active_id)], limit=1)
        is_validator = False
        for user_obj in allowance.allowance_approvals.mapped(
                'validating_user').filtered(lambda l: l.id == self.env.uid):
            validation_obj = allowance.allowance_approvals.search(
                [('variable_allowance_request_id', '=', allowance.id),
                 ('validating_user', '=', self.env.uid)])
            validation_obj.validating_state = 'accepted'
            is_validator = True
        if not is_validator:
            raise UserError(_("you are not allowed to confirm to this employee"))
        approval_flag = True
        for user_obj in allowance.allowance_approvals:
            if not user_obj.validating_state == 'accepted':
                approval_flag = False
        if approval_flag:
            allowance.write({'state': 'confirmed'})
        else:
            return False

    def action_refuse(self):
        approval_access = False
        for user in self.allowance_approvals:
            if user.validating_user.id == self.env.uid:
                approval_access = True
        if approval_access:
            is_refused = False
            for user_obj in self.allowance_approvals.mapped(
                    'validating_user').filtered(lambda l: l.id == self.env.uid):
                validation_obj = self.allowance_approvals.search(
                    [('variable_allowance_request_id', '=', self.id),
                     ('validating_user', '=', self.env.uid)])
                validation_obj.validating_state = 'refused'
                is_refused = True
            if is_refused:
                self.state = 'refused'
        else:
            raise UserError(_("you are not allowed to Refuse to this employee"))

    def hr_approve(self):
        if self.state == 'lawyer_approved':
            self.state = 'hr_approve'
        else:
            raise UserError(_("the allowance should be in Affair State"))
    def action_deduction(self):
        self.state = 'hr_approve'
    def lawyer_approve(self):
        if self.branch_id.lawyer_manager_id == self.env.user.employee_id.branch_id.lawyer_manager_id:
            if self.state == 'confirmed':
                self.state = 'lawyer_approved'
            else:
                raise UserError(_("the allowance should be in confirmed State"))


    def hr_refuse(self):
        if self.state == 'confirmed':
            self.state = 'hr_refused'

            ## For employee and department budget
            request_date = self.date.date()
            if not self.budget_id.date_from <= request_date <= self.budget_id.date_to:
                raise ValidationError("Request date is out budget period.")

            employee_budget_line = self.env['allowance.employee.budget'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('budget_id', '=', self.budget_id.id)])
            department_budget_line = self.env['allowance.department.budget'].search(
                [('department_id', '=', self.department_id.id),
                 ('budget_id', '=', self.budget_id.id)])

            flag1 = flag2 = False
            if employee_budget_line and (employee_budget_line[0].consumed_amount + self.amount) <= employee_budget_line[
                0].amount:
                flag1 = True

            if department_budget_line and (department_budget_line[0].consumed_amount + self.amount) <= \
                    department_budget_line[0].amount:
                flag2 = True

            if flag1 and flag2:
                employee_budget_line[0].consumed_amount += self.amount
                department_budget_line[0].consumed_amount += self.amount
                self.budget_id.consumed_budget += self.amount
            elif not flag1:
                raise ValidationError("This Employee is not added to this budget or have exceeded his limit")

            elif not flag2:
                raise ValidationError(
                    "This Employee's department is not added to this budget or have exceeded the department limit.")
        else:
            raise UserError(_("the allowance should be in confirmed State"))

    def send_notify(self):
        to_x = []
        to_x.append(self.allowance_approvals[0].validating_user.partner_id.id)
        self.message_post(body='This Allowance has been Notified!', message_type='snailmail',
                          subtype_xmlid='mail.mt_note', author_id=self.employee_id.user_id.partner_id.id,
                          partner_ids=to_x)
    def action_suspend(self):
        self.employee_id.suspended = True
        self.action = 'suspended'
        if not self.penalty:
            self.state = 'hr_approve'

    def action_suspend_penalty(self):
        self.action_suspend()
        self.action = "penalize"

    @api.onchange('deduction_type_id')
    def onchange_deduction_type_id(self):
        if self.deduction_type_id.period == 'month':
            # Get the current date
            current_date = fields.Datetime.now()
            first_day_of_month = current_date.replace(day=1)
            last_day_of_month = first_day_of_month + relativedelta(months=1, days=-1)
            no_of_times = self.search_count([('employee_id', '=', self.employee_id.id),('date', '>=', first_day_of_month),('date', '<=', last_day_of_month)])
            if no_of_times:
                deduction_type_rule_id = self.deduction_type_id.rule_ids.filtered(lambda r: r.sequence == no_of_times)
                if not deduction_type_rule_id:
                    deduction_type_rule_id = self.deduction_type_id.rule_ids[-1]
                self.deduction_type_rule_id = deduction_type_rule_id
        elif self.deduction_type_id.period == 'year':
            # Get the current date
            current_date = fields.Datetime.now()
            first_day_of_year = current_date.replace(month=1, day=1)
            first_day_of_next_year = current_date.replace(year=current_date.year + 1, month=1, day=1)

            last_day_of_year = first_day_of_next_year + relativedelta(days=-1)
            no_of_times = self.search_count(
                [('employee_id', '=', self.employee_id.id), ('date', '>=', first_day_of_year),
                 ('date', '<=', last_day_of_year)])
            if no_of_times:
                deduction_type_rule_id = self.deduction_type_id.rule_ids.filtered(
                    lambda r: r.sequence == no_of_times)
                if not deduction_type_rule_id:
                    deduction_type_rule_id = self.deduction_type_id.rule_ids[-1]
                self.deduction_type_rule_id = deduction_type_rule_id

    @api.onchange('deduction_type_rule_id')
    def onchange_deduction_type_rule_id(self):
        if self.deduction_type_rule_id:
            # Get the current date
            amount = (self.employee_id.contract_id.wage / 30) * self.deduction_type_rule_id.rate
            self.amount = amount


class LeaveValidationStatus(models.Model):
    _name = 'variable.allow.valid.status'

    variable_allowance_request_id = fields.Many2one('hr.variable.allowance.request')

    validating_user = fields.Many2one('res.users', string='Allowance Validators')
    validating_state = fields.Selection([('accepted', 'Accepted'), ('refused', 'Refused')])
    note = fields.Text(string='Comments', help="Comments")

    @api.onchange('validating_user')
    def prevent_change(self):
        raise UserError(_(
            "Changing Allowance validators is not permitted. You can only change "))
