from odoo import models,fields,api

class POrderLine(models.Model):
    _inherit = 'purchase.order.line'
    main_account_id = fields.Many2one('account.group', 'Main Account', related='product_id.property_main_account_expense_id', store=True)
    sub_account_id = fields.Many2one('account.account', related='product_id.property_account_expense_id', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', related='product_id.analytic_account_id', store=True)

    def _prepare_account_move_line(self, move=False):
        res = super(POrderLine, self)._prepare_account_move_line(move)
        analytic_account_id = self.product_id.analytic_account_id
        if analytic_account_id:
            analytic_distribution = {str(analytic_account_id): 100.00}
        else:
            analytic_distribution = False
        res['analytic_distribution'] = analytic_distribution
        res['analytic_account_id'] = analytic_account_id.id
        return res
