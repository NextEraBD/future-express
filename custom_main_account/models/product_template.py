from odoo import models,fields,api,_
import re
from odoo.exceptions import ValidationError



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_main_account_income_id = fields.Many2one('account.group', company_dependent=True, store=True)
    property_main_account_expense_id = fields.Many2one('account.group', company_dependent=True, store=True)
    import_analytic_account_id = fields.Many2one('account.analytic.account',string="Import Analytic Account Air")
    export_analytic_account_id = fields.Many2one('account.analytic.account',string="Export Analytic Account Air")
    lcl_export_analytic_account_id = fields.Many2one('account.analytic.account',string="Export Analytic Account Ocean")
    lcl_import_analytic_account_id = fields.Many2one('account.analytic.account',string="Import Analytic Account Ocean")
    set_account = fields.Boolean(compute="onchange_categ_id",store=True)
    arabic_name = fields.Char()
    product_code = fields.Char()

    property_account_income_id = fields.Many2one('account.account',
                                                 string="Income Account",store=True,
                                                 help="Keep this field empty to use the default value from the product category.")
    property_account_expense_id = fields.Many2one('account.account',
                                                  string="Expense Account",store=True,

                                                  help="Keep this field empty to use the default value from the product category. If anglo-saxon accounting with automated valuation method is configured, the expense account on the product category will be used.")
    product_account_income_id = fields.Many2one('account.account', company_dependent=True,
                                                 string="Product Income Account", store=True,
                                                 help="Keep this field empty to use the default value from the product category.")
    product_account_expense_id = fields.Many2one('account.account', company_dependent=True,
                                                  string="Product Expense Account", store=True,
                                                  help="Keep this field empty to use the default value from the product category. If anglo-saxon accounting with automated valuation method is configured, the expense account on the product category will be used.")
    is_compute_main = fields.Boolean( compute='_compute_reference_code')

    @api.depends('property_account_expense_id', 'property_account_income_id')
    def _compute_reference_code(self):
        for account in self:
            account.is_compute_main = False
            if account.property_account_expense_id or account.property_account_income_id:
                account.property_main_account_expense_id = account.property_account_expense_id.group_id.id
                account.property_main_account_income_id = account.property_account_income_id.group_id.id
                account.is_compute_main = True

    @api.onchange('property_account_income_id')
    def _set_property_main_account_income_id(self):
        for rec in self:
            rec.property_main_account_income_id = rec.property_account_income_id.group_id.id

    @api.onchange('property_account_income_id')
    def _set_property_main_account_income_id(self):
        for rec in self:
            rec.property_main_account_income_id = rec.property_account_income_id.group_id

    @api.onchange('property_main_account_income_id')
    def _set_property_account_income_id(self):
        return {'domain': {
            'property_account_income_id': [('group_id', '=', self.property_main_account_income_id.id)]}}

    @api.onchange('property_main_account_expense_id')
    def _set_property_account_expense_id(self):
        return {'domain': {
            'property_account_expense_id': [('group_id', '=', self.property_main_account_expense_id.id)]}}

    # @api.constrains('name')
    # def _check_english_chars(self):
    #     for record in self:
    #         cleaned_name = record.name.strip()
    #         if cleaned_name and not re.match("^[A-Za-z]+$", cleaned_name):
    #             raise ValidationError(_("Only English characters are allowed in Name."))
    @api.constrains('arabic_name')
    def _check_arabic_name(self):
        for rec in self:
            if rec.arabic_name:
                if not re.match(r'[\u0600-\u06FF-(.*?)(\S*\d+\S*)?\s]+', self.arabic_name):
                    raise ValidationError(_("Only Arabic characters are allowed in Arabic Name."))


    @api.onchange('categ_id')
    @api.depends('categ_id')
    def onchange_categ_id(self):
        for rec in self:
            rec.set_account = True
            if rec.categ_id:
                rec.import_analytic_account_id = rec.categ_id.import_analytic_account_id
                rec.export_analytic_account_id = rec.categ_id.export_analytic_account_id
                rec.lcl_export_analytic_account_id = rec.categ_id.lcl_export_analytic_account_id
                rec.lcl_import_analytic_account_id = rec.categ_id.lcl_import_analytic_account_id
                rec.property_account_expense_id = rec.categ_id.property_account_expense_categ_id.id
                rec.property_account_income_id = rec.categ_id.property_account_income_categ_id.id
            if rec.product_variant_id:
                rec.product_variant_id.import_analytic_account_id = rec.categ_id.import_analytic_account_id
                rec.product_variant_id.lcl_export_analytic_account_id = rec.categ_id.lcl_export_analytic_account_id
                rec.product_variant_id.lcl_import_analytic_account_id = rec.categ_id.lcl_import_analytic_account_id
                rec.property_account_expense_id = rec.categ_id.property_account_expense_categ_id.id
                rec.property_account_income_id = rec.categ_id.property_account_income_categ_id.id


class ProductProduct(models.Model):
    _inherit = 'product.product'

    import_analytic_account_id = fields.Many2one('account.analytic.account', string="Import Analytic Account Air")
    export_analytic_account_id = fields.Many2one('account.analytic.account', string="Export Analytic Account Air")
    lcl_export_analytic_account_id = fields.Many2one('account.analytic.account', string="Export Analytic Account Ocean")
    lcl_import_analytic_account_id = fields.Many2one('account.analytic.account', string="Import Analytic Account Ocean")

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        if self.categ_id:
            self.import_analytic_account_id = self.categ_id.import_analytic_account_id
            self.export_analytic_account_id = self.categ_id.export_analytic_account_id
            self.lcl_export_analytic_account_id = self.categ_id.lcl_export_analytic_account_id
            self.lcl_import_analytic_account_id = self.categ_id.lcl_import_analytic_account_id
            self.property_account_expense_id = self.categ_id.property_account_expense_categ_id.id
            self.property_account_income_id = self.categ_id.property_account_income_categ_id.id
