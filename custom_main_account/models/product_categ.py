from odoo import models,fields,api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_main_account_income_categ_id = fields.Many2one('account.group', related='property_account_income_categ_id.group_id')
    property_main_account_expense_categ_id = fields.Many2one('account.group', related='property_account_expense_categ_id.group_id')

    import_analytic_account_id = fields.Many2one('account.analytic.account', string="Import Analytic Account Air")
    export_analytic_account_id = fields.Many2one('account.analytic.account', string="Export Analytic Account Air")
    lcl_export_analytic_account_id = fields.Many2one('account.analytic.account', string="Export Analytic Account Ocean")
    lcl_import_analytic_account_id = fields.Many2one('account.analytic.account', string="Import Analytic Account Ocean")



