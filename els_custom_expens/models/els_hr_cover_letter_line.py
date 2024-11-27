from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrCoverLetterLine(models.Model):
    _inherit = 'hr.cover.letter.line'

    console_id_domain = fields.Char(readonly=True, store=False)
    console_id = fields.Many2one('console.operation', check_company=True)
    is_console = fields.Boolean()
    amount_sale = fields.Float()
    analytic_account_id = fields.Many2one('account.analytic.account')
    distribute = fields.Boolean(copy=False)
    plan_id = fields.Many2one(related='analytic_account_id.plan_id')
    product_tem_id = fields.Many2one('product.product',check_company=True, string="Category")
    bill_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    invoice_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    quantity = fields.Float(string="Quantity")
    total_cost = fields.Float(compute='_onchange_get_tot_cost')
    total_sale = fields.Float(compute='_onchange_get_tot_cost', store=True)
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')
    customer_id = fields.Many2one('res.partner', )
    vendor_id = fields.Many2one('res.partner', )

    @api.depends('quantity', 'amount_sale', 'amount_cost')
    def _onchange_get_tot_cost(self):
        for rec in self:
            rec.total_cost = rec.quantity * rec.amount_cost
            rec.total_sale = rec.quantity * rec.amount_sale






