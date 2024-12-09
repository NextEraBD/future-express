# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang


class AccountDistributionset(models.Model):
    _name = "account.distribution.set"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry', readonly=True, ondelete='cascade',
        check_company=True)
    name = fields.Char(
        string='Name',
        store=True,
        copy=False,
        tracking=True,
        index='trigram',
    )
    ref = fields.Char(string='Reference', copy=False, tracking=True)
    date = fields.Date(
        string='Date',
        index=True,
        store=True, required=True, readonly=False, precompute=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.user.company_id,

        required=True
    )
    distribution_line_ids = fields.One2many('account.distribution.set.line', 'distribution_id')
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        required=True,
        store=True, readonly=False,
        check_company=True, domain=[('account_type', '=', 'expense')])
    branch_id = fields.Many2one('res.branch', string='Branch', default=lambda self: self.env.user.branch_id)


class AccountDistributionsetLine(models.Model):
    _name = "account.distribution.set.line"

    distribution_id = fields.Many2one('account.distribution.set',string='distribution')
    branch_id = fields.Many2one(related="distribution_id.branch_id", string='Branch',store=True)
    department_id = fields.Many2one('hr.department', 'Department')
    total_employee_no = fields.Integer(string="Emp Total Number", compute='compute_total_emp', store=True, default=0)
    num_power = fields.Integer(string="Emp Power")
    analytic_account_id = fields.Many2one(related="department_id.account_analytic_id", store=True, string="Analytic Account")
    percentage = fields.Float()

    @api.depends('distribution_id', 'department_id')
    def compute_total_emp(self):
        for rec in self:
            rec.total_employee_no = self.env['hr.employee'].search_count([('branch_id','=',rec.distribution_id.branch_id.id),('department_id', 'child_of', rec.department_id.id)])


