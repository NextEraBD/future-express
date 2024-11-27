from odoo import fields, models, api, _
from datetime import datetime, timedelta, time
from pytz import timezone, utc
import pytz
from datetime import datetime, date
import calendar

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError


def make_aware(dt):
    """ Return ``dt`` with an explicit timezone, together with a function to
        convert a datetime to the same (naive or aware) timezone as ``dt``.
    """
    if dt.tzinfo:
        return dt, lambda val: val.astimezone(dt.tzinfo)
    else:
        return dt.replace(tzinfo=utc), lambda val: val.astimezone(utc).replace(tzinfo=None)


class HRMissions(models.Model):
    _name = 'hr.missions'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    def _get_is_manager(self):
        for rec in self:
            is_manager = False
            if rec.env.user.id == rec.manager_id.user_id.id or self.env.user.has_group(
                    'hr_holidays.group_hr_holidays_user'):
                is_manager = True
            rec.write({'is_manager': is_manager})
    name = fields.Char()
    with_accommodation = fields.Boolean()
    with_transportation = fields.Boolean()
    employee_id = fields.Many2one('hr.employee', tracking=True, required=True)
    user_id = fields.Many2one('res.users', related='employee_id.user_id', store=True)
    operation_id = fields.Many2one('freight.operation')
    branch_id = fields.Many2one('res.branch', default=lambda self: self.env.user.branch_id, string='Branch')
    workday = fields.Selection([
        ('weekend', 'WeekEnd'),
        ('weekday', 'WeekDay'),
    ], string='Mission at', copy=False, tracking=True, )
    category_type = fields.Selection([
        ('day', 'Day'),
        ('hour', 'Hour'),
    ], default='day', string='Type', copy=False, tracking=True, )
    mission_type = fields.Selection([
        ('in_city', 'In City'),
        ('out_city', 'Out City'),
    ], default='in_city', string='Mission Type', copy=False, tracking=True, )
    # job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id')
    manager_id = fields.Many2one('hr.employee', related='employee_id.parent_id')
    move_id = fields.Many2one('account.move')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('man_approve', 'Direct Manager Approved'),
        ('dept_approve', 'Department Manager Approved'),
        ('hr_approve', 'Hr Mission Manager Approved'),
        ('administrative_affairs', 'Administrative affairs Approved'),
        ('close', 'Closed'),
        ('second_hr_approve', 'Hr Mission Manager Approved'),
        ('account_approve', 'Account Approved'),
        ('confirmed', 'Confirmed'),
    ], default='draft', string='Status', copy=False, tracking=True, )
    status = fields.Selection([
        ('draft', 'Draft'),
        ('run', 'Running'),
        ('close', 'Closed'),
    ])
    date_from = fields.Datetime(tracking=True,  string='From')
    date_to = fields.Datetime(tracking=True, string='To')
    mission_from_city = fields.Many2one('res.city',string="From City")
    from_city = fields.Char(string="From City")
    mission_to_city = fields.Many2one('res.city',string="To City")
    to_city = fields.Char(string="To City")
    duration = fields.Float("Duration", compute='_onchange_start_end')
    mission_duration = fields.Integer("Duration", compute='_compute_number_of_days' )
    is_manager = fields.Boolean(compute='_get_is_manager')
    overtime_hours = fields.Float("Overtime")
    amount = fields.Float('Amount', compute='_compute_amount')
    comments = fields.Text('Notes')
    expense_line_ids = fields.One2many('hr.mission.expense', 'mission_id')
    bill_ids = fields.One2many('hr.mission.bill', 'mission_id')
    total_amount = fields.Float('Total Amount', compute='_compute_total_amount')
    move_ids = fields.One2many('account.move','mission_id')
    move_count = fields.Integer(compute='_compute_move_count')
    billed = fields.Boolean()
    mission_purpose = fields.Selection([('meeting', 'Meeting'), ('operation', 'Operation'), ('delivery', 'Delivery')])

    def _compute_move_count(self):
        self.move_count = 0
        for rec in self:
            rec.move_count = self.env["account.move"].search_count([('mission_id','=',self.id),('move_type', '=', 'in_invoice')])

    def action_view_vendor_bill(self):
        related_bill_ids = self.env['account.move'].search([
            ('mission_id','=',self.id),('move_type', '=', 'in_invoice')
        ]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bill'),
            'res_model': 'account.move',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', related_bill_ids)],
        }

    def action_create_bill(self):
        """
        A method to create invoices grouped by partner
        """
        for partner in self.bill_ids.mapped('partner_id'):
            partner_bills = self.bill_ids.filtered(lambda b: b.partner_id == partner)
            invoice_lines = []
            for bill in partner_bills:
                invoice_lines.append((0, 0, {
                    'product_id': bill.product_id.id,
                    'quantity': 1,
                    'price_unit': bill.amount,
                }))
            if invoice_lines:
                vals = {
                    'move_type': 'in_invoice',
                    'journal_id': self.company_id.mission_journal_id.id,
                    'mission_id': self.id,
                    'partner_id': partner.id,
                    'invoice_line_ids': invoice_lines,
                }

                move_id = self.env['account.move'].create(vals)
                self.write({'billed': True})

        return True

    @api.depends('expense_line_ids.amount')
    def _compute_total_amount(self):
        for rec in self:
            if rec.expense_line_ids:
                rec.total_amount = sum(rec.expense_line_ids.mapped('amount'))
            else:
                rec.total_amount = 0.0

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.mission')
        res = super(HRMissions, self).create(vals)
        return res

    @api.constrains('employee_id', 'date_from', 'date_to')
    def _check_multiple_missions_per_month(self):
        for rec in self:
            if rec.employee_id and rec.date_from and rec.date_to:
                # Extract the year and month from the mission dates
                mission_month = rec.date_from.month
                mission_year = rec.date_from.year

                # Calculate the first and last day of the month
                first_day_of_month = date(mission_year, mission_month, 1)
                last_day_of_month = date(mission_year, mission_month, 28)  # Set to 28, assuming February

                # Calculate the last day of the month more accurately
                # last_day_of_month = last_day_of_month.replace(day=31)
                if last_day_of_month.month != mission_month:
                    last_day_of_month = last_day_of_month.replace(day=30)

                # Search for other missions for the same employee in the same month
                domain = [
                    ('employee_id', '=', rec.employee_id.id),
                    ('date_from', '>=', first_day_of_month),
                    ('date_to', '<=', last_day_of_month),
                    ('state', 'not in', ['confirmed']),
                    ('id', '!=', rec.id),  # Exclude the current mission
                ]
                missions_in_month = self.search_count(domain)

                if missions_in_month >= 2:
                    raise ValueError("Employee has already taken a mission in this month.")

    # hr.mission.expense
    def action_submit(self):
        vals = []
        meal_product = self.env.ref('hr_missions.meal_mission_product')
        accommodation_product = self.env.ref('hr_missions.accommodation_mission_product')
        transportation_product = self.env.ref('hr_missions.transportation_mission_product')
        for rec in self:
            if rec.mission_type == 'out_city' and rec.category_type == 'day':
                vals.append((0, 0, {
                    'product_id': meal_product.id,
                    'description': meal_product.description,
                    'amount':  rec.employee_id.contract_id.mission_per_day_amount * rec.mission_duration,
                }))
            if rec.mission_type == 'out_city' and rec.with_accommodation:
                vals.append((0, 0, {
                    'product_id': accommodation_product.id,
                    'description': accommodation_product.description,
                    'amount': rec.employee_id.contract_id.mission_with_accommodation_amount * rec.mission_duration,
                }))
            if rec.mission_type == 'out_city' and rec.with_transportation:
                vals.append((0, 0, {
                    'product_id': transportation_product.id,
                    'description': transportation_product.description,
                    'amount': rec.employee_id.contract_id.mission_travel_allowance * rec.mission_duration,
                }))
                # raise ValidationError(vals)
            rec.write({'expense_line_ids': vals})
        self.write({'state': "submit"})

    @api.depends('date_from', 'date_to')
    def _compute_number_of_days(self):
        for rec in self:
            permission_from = rec.date_from
            permission_to = rec.date_to
            if permission_from and permission_to and permission_from > permission_to:
                raise UserError(_("The from date can't be before to date"))
            if rec.date_from and rec.date_to:
                rec.mission_duration = (rec.date_to - rec.date_from).days
            else:
                rec.mission_duration = 0

    def _compute_amount(self):
        for rec in self:
            rec.amount = 0.0
            if rec.mission_type == 'out_city' and rec.with_accommodation:
                rec.amount = rec.employee_id.contract_id.mission_with_accommodation_amount * rec.mission_duration
            if rec.mission_type == 'out_city' and not rec.with_accommodation:
                rec.amount = rec.employee_id.contract_id.mission_per_day_amount * rec.mission_duration
            # amount = 0
            # if rec.overtime_hours:
            #     if rec.workday == 'weekday' and rec.company_id.config_mission_rate_overtime:
            #         amount = rec.overtime_hours * rec.company_id.config_mission_rate_overtime * (
            #                     (rec.employee_id.contract_id.wage / 30) / 8)
            #     elif rec.workday == 'weekend' and rec.company_id.config_mission_rate_weekend:
            #         amount = rec.overtime_hours * rec.company_id.config_mission_rate_weekend * (
            #                     (rec.employee_id.contract_id.wage / 30) / 8)
            # rec.write({'amount': amount})

    def action_man_approve(self):
        employee_obj = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if self.employee_id.parent_id.id != employee_obj.id:
            raise UserError(_("Only %s manager can approve this Mission") % (self.employee_id.name))
        else:
            self.write({'state': "man_approve"})

    def action_emp_close(self):
        if self.user_id.id != self.env.user.id:
            raise UserError(_("Only %s can approve this Mission") % (self.user_id.name))
        else:
            self.write({'state': "close"})

    def action_dept_approve(self):
        employee_obj = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if self.department_id.manager_id.id != employee_obj.id:
            raise UserError(_("Only %s manager can approve this Mission") % (self.department_id.name))
        else:
            self.write({'state': "dept_approve"})

    def action_hr_approve(self):
        employee_obj = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if self.employee_id.mission_manager_id.id != employee_obj.id:
            raise UserError(_("Only %s Mission Manager can approve this Mission") % (self.employee_id.name))
        else:
            self.write({'state': "hr_approve"})

    def action_second_hr_approve(self):
        employee_obj = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if self.employee_id.mission_manager_id.id != employee_obj.id:
            raise UserError(_("Only %s Mission Manager can approve this Mission") % (self.employee_id.name))
        else:
            self.write({'state': "second_hr_approve"})

    def action_administrative_affairs(self):
        if self.env.user not in self.branch_id.administrative_affairs_ids:
            raise UserError(_("Only Administrative affairs Manager in branch %s can approve this Mission") % (self.branch_id.name))
        else:
            self.write({'state': "administrative_affairs"})

    def action_account_approve(self):
        if self.env.user not in self.branch_id.account_mission_ids:
            raise UserError(_("Only Account Manager in branch %s can approve this Mission") % (self.branch_id.name))
        else:
            if not self.employee_id.employee_account_id:
                raise UserError(_("Please Add Account For this Employee %s") % (self.employee_id.name))
            self.write({'state': "account_approve"})
            return {
                'name': _('Mission Entry'),
                'view_mode': 'form',
                'view_id': self.env.ref('hr_missions.mission_wizard_view_form').id,
                'res_model': 'mission.wizard',
                'context': {'default_mission_id': self.id},
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

    def action_confirm(self):
        self.ensure_one()
        user = self.env['res.users'].browse(self.env.uid)
        utc = pytz.UTC
        for rec in self:
            if rec.mission_type == 'in_city':
                date_from = utc.localize(rec.date_from)
                date_to = utc.localize(rec.date_to)
                # print('KKKKKKKKKKKKKKKKKKKKKKKKKKKKK',date_from,date_to)
                rec.overtime_hours = (date_to - date_from).total_seconds() / 3600.0
                attendance = self.env['hr.attendance'].create({
                    'employee_id': rec.employee_id.id,
                    'check_in': fields.Datetime.to_string(date_from - timedelta(hours=2)),
                    'check_out': fields.Datetime.to_string(date_to - timedelta(hours=2))
                })
            elif rec.mission_type == 'out_city':
                working_hours = rec.employee_id.resource_calendar_id
                hours_ber_day = working_hours.hours_per_day
                # date_from = utc.localize(challenge.datetime_end)
                date_to = utc.localize(rec.date_to)
                start, revert_start_tz = make_aware(rec.date_from)
                # Before the calculation of check_in
                print("Debug: start =", start)

                # Calculate check_in
                check_in = working_hours._get_closest_work_time(start)

                # Check if check_in is a valid datetime value before proceeding
                if check_in:
                    planned_check_out = check_in + timedelta(hours=hours_ber_day)
                    if planned_check_out < date_to:
                        rec.overtime_hours = (date_to - planned_check_out).total_seconds() / 3600.0
                        check_out = date_to
                    else:
                        check_out = fields.Datetime.to_string(
                            pytz.timezone(self.env.context['tz']).localize(fields.Datetime.from_string(planned_check_out),
                                                                           is_dst=None).astimezone(pytz.utc))
                    # attendances = self.env['hr.attendance'].filtered(lambda line: line.check_in.date() == rec.date_from.date())
                    attendance = self.env['hr.attendance'].create({
                        'employee_id': rec.employee_id.id,
                        'check_in': fields.Datetime.to_string(check_in - timedelta(hours=2)),
                        'check_out': fields.Datetime.to_string(check_out - timedelta(hours=2))
                    })
            rec.state = 'confirmed'
            # for attendance in self.env['hr.attendance'].search([]):
            #     if attendance.check_in.date() == rec.date_from.date():
            #         if not once:
            #             once = True
            #             # att_check_in = attendance.check_in.replace(tzinfo=pytz.utc).astimezone(local_tz)
            #             # att_check_out = attendance.check_out.replace(tzinfo=pytz.utc).astimezone(local_tz)
            #             if attendance.check_in.date() == rec.date_from.date() and attendance.check_in.date() == rec.date_to.date():
            #                 if attendance.check_out < rec.date_to and attendance.check_out:
            #                     rec.overtime_hours = (rec.date_to - attendance.check_out).total_seconds() / 3600.0
            #                     attendance.check_out = rec.date_to
            #                     attendance._compute_worked_hours()
            #                 if attendance.check_in > rec.date_from:
            #                     attendance.check_in = rec.date_from
            #                     attendance._compute_worked_hours()
            #                 if not attendance.check_out:
            #                     check_out = attendance.check_in + timedelta(hours=hours_ber_day)
            #                     if check_out < rec.date_to:
            #                         rec.overtime_hours = (rec.date_to - check_out).total_seconds() / 3600.0
            #                         attendance.check_out = rec.date_to
            #                         attendance._compute_worked_hours()
            #                     else:
            #                         attendance.check_out = check_out
            #                         attendance._compute_worked_hours()
            #             elif attendance.check_in.date() == rec.date_from.date() and attendance.check_in.date() != rec.date_to.date():
            #                 ext_attendances = self.env['hr.attendance'].filtered(
            #                     lambda line: line.check_in.date() != rec.date_to.date() and line.check_out.date() == rec.date_to.date())
            #                 once2 = False
            #                 for ext_attendances in self.env['hr.attendance'].search([]):
            #                     if ext_attendances.check_in.date() != rec.date_to.date() and ext_attendances.check_out.date() == rec.date_to.date():
            #                         if not once2:
            #                             once2 = True
            #                             # ext_att_check_in = ext_attendances.check_in.replace(tzinfo=pytz.utc).astimezone(local_tz)
            #                             # ext_att_check_out = ext_attendances.check_out.replace(tzinfo=pytz.utc).astimezone(local_tz)
            #                             if ext_attendances.check_out < rec.date_to and ext_attendances.check_out:
            #                                 rec.overtime_hours = (rec.date_to - ext_attendances.check_out).total_seconds() / 3600.0
            #                                 ext_attendances.check_out = rec.date_to
            #                                 ext_attendances._compute_worked_hours()
            #                             if not ext_attendances.check_out:
            #                                 ext_check_out = ext_attendances.check_out + timedelta(hours=hours_ber_day)
            #                                 if ext_check_out < rec.date_to:
            #                                     rec.overtime_hours = (rec.date_to - ext_check_out).total_seconds() / 3600.0
            #                                     ext_attendances.check_out = fields.Datetime.to_string(pytz.timezone(self.env.context['tz']).localize(fields.Datetime.from_string(rec.date_to), is_dst=None).astimezone(pytz.utc))
            #                                     ext_attendances._compute_worked_hours()
            #                                 else:
            #                                     ext_attendances.check_out = ext_check_out
            #                                     ext_attendances._compute_worked_hours()
            #         else:
            #             raise UserError(_("there is multi-able attendances this day please merge them then confirm"))
            # if not once:
            #     attendance = self.env['hr.attendance'].create({
            #         'employee_id': rec.employee_id.id,
            #         'check_in': fields.Datetime.to_string(pytz.timezone(self.env.context['tz']).localize(fields.Datetime.from_string(rec.date_from), is_dst=None).astimezone(pytz.utc)),
            #         'check_out': fields.Datetime.to_string(pytz.timezone(self.env.context['tz']).localize(fields.Datetime.from_string(rec.date_to), is_dst=None).astimezone(pytz.utc)),
            #     })
        # hours and line.end_float <= period_worked_hours)
        # if attendance.delay >= 0:
        # permission_from = rec.permission_from + 12 if rec.permission_from_period == 'pm' else rec.permission_from
        #             # permission_to = rec.permission_to + 12 if rec.permission_to_period == 'pm' else rec.permission_to
        #             # date_from =
        #             # # attendance = self.env['hr.attendance'].search([('employee_id', '=', rec.employee_id.id),
        #             # #                                                ('delay_rule_id', '!=', False),
        #             # #                                                ('check_in', '>=', date_time_from)])
        #             # for attendance in self.env['hr.attendance'].search([]):
        #             #     if attendance.employee_id.id == rec.employee_id.id and attendance.check_in.date() == rec.date:
        #             #         check_in = attendance.check_in.replace(tzinfo=pytz.utc).astimezone(
        #             #             local_tz) if attendance.check_in else False
        #             #         check_out = attendance.check_out.replace(tzinfo=pytz.utc).astimezone(local_tz) if attendance.check_out else False
        #             #         delay_rule = working_hours.delay_ids.filtered(
        #             #             lambda line: line.start_float >= period_worked_
        #             attendance.delay -= 2
        #             period_worked_hours = attendance.period_worked_hours + 2
        #             working_hours = rec.employee_id.resource_calendar_id
        #             hourly_wage, daily_wage = rec.employee_id.get_hourly_wage()
        #             delay_rule = working_hours.delay_ids.filtered(lambda line: line.start_float >= period_worked_hours and line.end_float <= period_worked_hours)
        #             delay_rate = False
        #             if delay_rule:
        #                 month_start = datetime.now().replace(day=1)
        #                 repeat_times = self.env['hr.attendance'].search_count([('employee_id', '=', attendance.employee.id),
        #                                                                        ('delay_rule_id', '=', delay_rule.id),
        #                                                                        ('check_in', '>=', month_start),
        #                                                                        ('check_in', '<', attendance.check_in)])
        #                 if not repeat_times:
        #                     rate = delay_rule.first_time
        #                 elif repeat_times == 1:
        #                     rate = delay_rule.second_time
        #                 elif repeat_times == 2:
        #                     rate = delay_rule.third_time
        #                 else:
        #                     rate = delay_rule.repeat
        #                 delay_rate = daily_wage * (rate / 100)
        #
        #         else:
        #             attendance.delay = 0
        #             delay_rate = False
        #         attendance.generate_salary_penalty_addition(delay_rate, attendance.over_time_rate, attendance.over_time)

    @api.onchange('date_from', 'date_to')
    def _onchange_start_end(self):
        for rec in self:
            if rec.category_type == 'hour':
                delta = 0
                permission_from = rec.date_from
                permission_to = rec.date_to
                if permission_from and permission_to and permission_from > permission_to:
                    raise UserError(_("The from date can't be before to date"))
                if permission_to and permission_from:
                    delta = (permission_to - permission_from).total_seconds() / 3600.0
                rec.duration = delta
                if rec.duration > 2:
                    raise UserError(_("The Duration Must Be less or equal 2 hours"))
            else:
                rec.duration = 0.0


class HrMissionExpense(models.Model):
    _name = 'hr.mission.expense'

    description = fields.Char()
    date = fields.Date(default=fields.Date.today(), string='Date OF')
    mission_id = fields.Many2one('hr.missions')
    product_id = fields.Many2one('product.product', string="Product")
    amount = fields.Float()


class HrMissionBill(models.Model):
    _name = 'hr.mission.bill'

    description = fields.Char()
    product_id = fields.Many2one('product.product', string="Product", required=True)
    date = fields.Date(default=fields.Date.today(), string='Date OF')
    partner_id = fields.Many2one('res.partner', 'Vendor')
    amount = fields.Float()
    mission_id = fields.Many2one('hr.missions')

