
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

class MoveLine(models.Model):
    _inherit = 'account.analytic.account'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


class MainAccount(models.Model):
    _inherit = 'account.group'

    code = fields.Char()
    deprecated = fields.Boolean()
    account_type = fields.Selection(
        selection=[
            ("asset_receivable", "Receivable"),
            ("asset_cash", "Bank and Cash"),
            ("asset_current", "Current Assets"),
            ("asset_non_current", "Non-current Assets"),
            ("asset_prepayments", "Prepayments"),
            ("asset_fixed", "Fixed Assets"),
            ("liability_payable", "Payable"),
            ("liability_credit_card", "Credit Card"),
            ("liability_current", "Current Liabilities"),
            ("liability_non_current", "Non-current Liabilities"),
            ("equity", "Equity"),
            ("equity_unaffected", "Current Year Earnings"),
            ("income", "Income"),
            ("income_other", "Other Income"),
            ("expense", "Expenses"),
            ("expense_depreciation", "Depreciation"),
            ("expense_direct_cost", "Cost of Revenue"),
            ("off_balance", "Off-Balance Sheet"),
        ],
        string="Type", tracking=True,
        help="Account Type is used for information purpose, to generate country-specific legal reports, and set the rules to close a fiscal year and generate opening entries."
    )
    group_parent_id = fields.Many2one('account.group', readonly=False, string='Parent Account', help="Account prefixes can determine account groups.")
    parent_id = fields.Many2one('account.group', store=False, string='Parent Account', help="Account prefixes can determine account groups.")
    child_ids = fields.One2many('account.group', 'group_parent_id', string='Child Groups')

    hide_parent_id = fields.Many2one('account.group', readonly=False, string='Main Account', help="Account prefixes can determine account groups.")
    is_compute = fields.Boolean(compute='onchange_parent_id')

    _sql_constraints = [
        ('code_group_uniq', 'unique (code,company_id)', 'Main Account codes must be unique .'),
    ]

    # def name_get(self):
    #     result = []
    #     for group in self:
    #         prefix = group.code_prefix_start and str(group.code_prefix_start)
    #         if prefix and group.code_prefix_end != group.code_prefix_start:
    #             prefix += '-' + str(group.code_prefix_end)
    #         name = (prefix and (prefix + ' ') or '') + group.name
    #         result.append((group.id, name))
    #     return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        """This is"""
        args = list(args or [])
        if name:
            args += ['|',
                     ('code', operator, name),
                     ('name', operator, name), ]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)

    @api.depends('group_parent_id')
    def onchange_parent_id(self):
        for rec in self:
            hide_parent_id = rec.group_parent_id
            while hide_parent_id and hide_parent_id.group_parent_id:
                hide_parent_id = hide_parent_id.group_parent_id
            rec.hide_parent_id = hide_parent_id or rec
            rec.is_compute = True

    @api.model
    def name_create(self, name):
        """ Split the account name into account code and account name in import.
        When importing a file with accounts, the account code and name may be both entered in the name column.
        In this case, the name will be split into code and name.
        """
        if 'import_file' in self.env.context:
            code, name = self._split_code_name(name)
            return self.create({'code': code, 'name': name}).name_get()[0]
        raise UserError(_("Please create new Main accounts from the Main Accounts menu."))


