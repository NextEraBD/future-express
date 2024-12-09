from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import re
from odoo.osv import expression


ACCOUNT_REGEX = re.compile(r'(?:(\S*\d+\S*))?(.*)')
ACCOUNT_CODE_REGEX = re.compile(r'^[A-Za-z0-9.]+$')

class BankRecWidget(models.Model):

    _inherit = 'bank.rec.widget'

    group_id = fields.Many2one('account.group', tracking=True, readonly=False, string='Main Account',
                               help="Account prefixes can determine account groups.")

class account_bank_statement_line(models.Model):

    _inherit = 'account.bank.statement.line'

    group_id = fields.Many2one('account.group', tracking=True, readonly=False, string='Main Account',
                               help="Account prefixes can determine account groups.")

class AccountAccount(models.Model):
    _inherit = 'account.account'

    group_id = fields.Many2one('account.group', tracking=True, readonly=False,string='Main Account', help="Account prefixes can determine account groups.")
    reference_code = fields.Char(size=64, string="Reference", tracking=True)
    main_account_code = fields.Char(related='group_id.code', string='M.A Code',store=True)
    main_account_type = fields.Selection(related='group_id.account_type', string='M.A Type')
    hide_parent_id = fields.Many2one('account.group', related='group_id.hide_parent_id', store=True, readonly=False, string='Main Account Parent' , help="Account prefixes can determine account groups.")
    is_main = fields.Boolean('Main')
    out_analytic = fields.Boolean('No Analytic')
    is_compute_ref = fields.Boolean('Main', compute='_compute_reference_code')

    @api.constrains('code')
    def _check_unique_code_per_company_group(self):
        for record in self:
            if record.code and record.company_id and record.group_id:
                existing_records = self.env['account.account'].search([
                    ('code', '=', record.code),
                    ('company_id', '=', record.company_id.id),
                    ('group_id', '=', record.group_id.id),
                    ('id', '!=', record.id)  # Exclude the current record
                ])
                if existing_records:
                    raise ValidationError("The code of the account must be unique per company and group!")

    @api.depends('main_account_code', 'code')
    def _compute_reference_code(self):
        for account in self:
            account.is_compute_ref = False
            if account.main_account_code:
                account.reference_code = account.main_account_code + account.code
                account.is_compute_ref = True

    _sql_constraints = [
        ('code_company_group_uniq', 'unique (code, company_id, group_id)',
         'The code of the account must be unique per company and group!')
    ]

    _sql_constraints = [
        ('reference_code_company_uniq', 'check(1=1)', 'The code of the account must be unique per company !')
    ]


    _sql_constraints = [('code_company_uniq', 'check(1=1)', 'The code of the account must be unique per company !'), ]

    @api.constrains('reference_code')
    def _check_account_code(self):
        for account in self:
            if not re.match(ACCOUNT_CODE_REGEX, account.reference_code):
                raise ValidationError(_(
                    "The account Reference can only contain alphanumeric characters and dots."
                ))

    @api.onchange('account_type')
    def _set_main_account_domain(self):
        group_ids = self.env['account.group'].search([('company_id', '=', self.company_id.id),('account_type','=',self.account_type)]).ids
        return {'domain': {'group_id': [('id', 'in', group_ids)]}}

    @api.onchange('account_type')
    def _onchange_account_type(self):
        self.main_account_type = self.account_type

    @api.onchange('is_main')
    def _onchange_is_main(self):
        if self.is_main:
            if not self.code:
                raise ValidationError(_('You need to enter account code first'))
            if not self.name:
                raise ValidationError(_('You need to enter account name first'))
            if not self.account_type:
                raise ValidationError(_('You need to enter account account type first'))
            self.env['account.group'].create({'name':self.name, 'code':self.code, 'account_type':self.account_type, 'company_id':self.company_id.id})

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            criteria_operator = ['|'] if operator not in expression.NEGATIVE_TERM_OPERATORS else ['&', '!']
            domain = criteria_operator + [
                '|',
                ('code', '=ilike', name + '%'),  # Include searching by 'code'
                ('reference_code', '=ilike', name + '%'),
                ('name', operator, name)
            ]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

class journal(models.Model):
    _inherit = 'account.journal'

    branch_id = fields.Many2one('res.branch','Branch')
    default_account_id = fields.Many2one(
        comodel_name='account.account', check_company=True, copy=False, ondelete='restrict',
        string='Default Account',
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]")
    suspense_account_id = fields.Many2one(
        comodel_name='account.account', check_company=True, ondelete='restrict', readonly=False, store=True,
        compute='_compute_suspense_account_id',
        help="Bank statements transactions will be posted on the suspense account until the final reconciliation "
             "allowing finding the right account.", string='Suspense Account',
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]")

    profit_account_id = fields.Many2one(
        comodel_name='account.account', check_company=True,
        help="Used to register a profit when the ending balance of a cash register differs from what the system computes",
        string='Profit Account',
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]")
    loss_account_id = fields.Many2one(
        comodel_name='account.account', check_company=True,
        help="Used to register a loss when the ending balance of a cash register differs from what the system computes",
        string='Loss Account',
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]")
