from odoo import models,fields,api

class ResCompany(models.Model):
    _inherit = 'res.company'

    expense_currency_exchange_account_id = fields.Many2one(
        comodel_name='account.account',
        string="Loss Exchange Rate Account",domain="[('deprecated', '=', False), ('company_id', '=', id)]"
    )
    income_currency_exchange_account_id = fields.Many2one(
        comodel_name='account.account',
        string="Gain Account",domain="[('deprecated', '=', False), ('company_id', '=', id)]"
        )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    income_currency_exchange_account_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.income_currency_exchange_account_id",
        string="Gain Account",
        readonly=False,
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]"
        )
    expense_currency_exchange_account_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.expense_currency_exchange_account_id",
        string="Loss Account",
        readonly=False,
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]"
        )

class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    income_currency_exchange_account_id = fields.Many2one('account.account.template',
                                                          string="Gain Exchange Rate Account")
    expense_currency_exchange_account_id = fields.Many2one('account.account.template',
                                                           string="Loss Exchange Rate Account")
