import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrExpense(models.Model):
    _inherit = 'hr.cover.letter.official'

    console_id_domain = fields.Char(compute="_compute_console_id_domain", readonly=True, store=False)
    console_id = fields.Many2one('console.operation', check_company=True)
    is_console = fields.Boolean()
    amount_sale = fields.Float()
    analytic_account_id = fields.Many2one('account.analytic.account')
    plan_id = fields.Many2one(related='analytic_account_id.plan_id')

    def action_create_journal(self):
        # raise ValidationError(_(self.currency_id.name))
        company_currency = self.company_id.currency_id
        vals = {
            'ref': 'Official Expense',
            'date': fields.Date.today(),
            'currency_id': self.sale_currency_id.id,
            'console_id': self.console_id.id,
            'company_id': self.company_id.id,
            'journal_id': self.journal_id.id,
            'employee_id':self.employee_id.id,
            'freight_operation_id':self.shipment_number.id,
            'move_type': 'entry',
            'line_ids': [],
        }
        total = 0
        for line in self:
            if not line.product_id.property_account_expense_id:
                raise ValidationError(_('Expense Account for the expense category is not set. Please, set it and try again.'))
            amount_currency = line.taxed_amount_cost
            if line.sale_currency_id and line.sale_currency_id != company_currency:
                rate = line.sale_currency_id.rate_ids.filtered(
                    lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year)[0].mapped(
                    'inverse_company_rate')
                if rate:
                    amount_currency = line.taxed_amount_cost * rate[0]
                else:
                    raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))
            vals['line_ids'].append((0, 0, {
                'account_id': line.product_id.property_account_expense_id.id,
                'currency_id': line.currency_id.id,
                'shipment_number': line.shipment_number.id,
                'amount_currency': line.taxed_amount_cost,
                'debit': amount_currency,
                'credit': 0,
            }))
            total += amount_currency

        vals['line_ids'].append((0, 0, {
            'account_id': self.account_id.id,
            'currency_id': self.sale_currency_id.id,
            'partner_id': self.partner_id.id,
            'debit': 0,
            'credit': total,
        }))

        move_id = self.env['account.move'].create(vals)
        move_id.action_post()
        self.journal_created = True

    # @api.onchange('product_id', 'shipment_number')
    # def onchange_product_id_extend(self):
    #     # self.amount_cost = self.product_id.list_price
    #     # self.amount_sale = self.product_id.standard_price
    #     for line in self:
    #         analytic_account_id = False
    #         if line.product_id and line.shipment_number:
    #             if line.shipment_number.direction == 'import' and self.shipment_number.ocean_shipment_type != 'lcl':
    #                 analytic_account_id = self.product_id.import_analytic_account_id.id
    #             elif line.shipment_number.direction == 'export' and self.shipment_number.ocean_shipment_type != 'lcl':
    #                 analytic_account_id = self.product_id.export_analytic_account_id.id
    #             elif line.shipment_number.direction == 'import' and self.shipment_number.ocean_shipment_type == 'lcl':
    #                 analytic_account_id = self.product_id.lcl_import_analytic_account_id.id
    #             elif line.shipment_number.direction == 'export' and self.shipment_number.ocean_shipment_type == 'lcl':
    #                 analytic_account_id = self.product_id.lcl_export_analytic_account_id.id
    #         if analytic_account_id:
    #             line.analytic_account_id = analytic_account_id

    # def action_approve(self):
    #     if not self.analytic_account_id:
    #         raise ValidationError(
    #             _("Please Add Analytic Account to this Official"))
    #     result = super(HrExpense, self).action_approve()
    #     return result

    @api.depends('cover_letter_id.company_id', 'cover_letter_id.employee_id')
    def _compute_console_id_domain(self):
        for rec in self:
            rec.console_id_domain = json.dumps(
                [('company_id', '=', rec.company_id.id), ('employee_ids', 'in', [rec.employee_id.id])]
            )

    @api.onchange('console_id')
    def onchange_console_id(self):
        if self.console_id:
            self.master = self.console_id.master
            self.housing = self.console_id.housing