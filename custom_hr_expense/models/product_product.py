from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    expense_type_id = fields.Many2one('hr.expense.type')
    cover_letter_type = fields.Selection([('expense', 'Expenses'), ('official', 'Official Receipt')])
    expense_service_type = fields.Selection([('clearance', 'Clearance'), ('freight', 'Freight'), ('transportation', 'Transportation'), ('transit', 'Transit')])
    expense_service = fields.Many2one('hr.expense.service')

    main_account_id = fields.Many2one('account.group')
    sub_account_id = fields.Many2one('account.account')
    has_checked = fields.Boolean()
    inside_outside = fields.Boolean(default=True)

    @api.model
    def default_get(self, fields):
        """ Allow support of company """
        result = super(ProductProduct, self).default_get(fields)

        if self.categ_id:
            self.property_account_expense_id = self.categ_id.property_account_expense_categ_id.id
            self.property_account_income_id = self.categ_id.property_account_income_categ_id.id
        return result