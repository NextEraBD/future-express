from odoo import models,fields,api,_
from odoo.fields import Command
from odoo.exceptions import UserError, ValidationError


class OrderLine(models.Model):
    _inherit = 'sale.order.line'

    main_account_id = fields.Many2one('account.group', 'Main Account', related='product_template_id.property_main_account_income_id',stoe=True)
    sub_account_id = fields.Many2one('account.account', related='product_template_id.property_account_income_id', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', related='product_template_id.analytic_account_id', store=True,readonly=False)

    def _prepare_invoice_line(self, **optional_values):
        res = super(OrderLine, self)._prepare_invoice_line(**optional_values)
        analytic_account_id = self.product_id.analytic_account_id
        if analytic_account_id:
            analytic_distribution = {str(analytic_account_id): 100.00}
        else:
            analytic_distribution = False
        res['analytic_account_id'] = analytic_account_id.id
        res['analytic_distribution'] = analytic_distribution
        return res

