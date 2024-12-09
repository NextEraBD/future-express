from odoo import models,fields,api,_
from odoo.tools import frozendict
from odoo.tools import frozendict, formatLang, format_date, float_compare, Query
from odoo.exceptions import UserError

class Account_move(models.Model):
    _inherit = 'account.move'
    freight_operation_id = fields.Many2one('freight.operation')
    exchange_invoice_id = fields.Many2one('account.move')
    is_claim = fields.Boolean()


class Account_move_line(models.Model):
    _inherit = 'account.move.line'

    main_income_account_id = fields.Many2one('account.group', 'Main Income Account',store=True)
    sub_income_account_id = fields.Many2one('account.account', store=True)

    main_expense_account_id = fields.Many2one('account.group', 'Main Expense Account', related='product_id.property_main_account_expense_id', store=True)
    sub_expense_account_id = fields.Many2one('account.account', related='product_id.property_account_expense_id', store=True)

    product_analytic_account_id = fields.Many2one('account.analytic.account')
    analytic_account_id = fields.Many2one('account.analytic.account')

    combination_code = fields.Char(compute='_compute_combination_code')

    main_account_id = fields.Many2one('account.group', 'Main Account', compute='get_main_account_id',readonly=False)
    is_computed_tax = fields.Boolean(compute='is_compute_tax')
    is_computed = fields.Boolean()
    amount_tax = fields.Float('VAT', digits=(10, 2), compute='_compute_amount_tax',
                              help="The Value Added Tax amount appropriated for the activity.", store=True)
    gross_total_amount = fields.Float(string='Gross', store=True, compute='_compute_total_amount')
    # analytic_distribution = fields.Json(
    #     string='Analytic Distribution',
    #     store=True,
    #     copy=True,
    #     readonly=False
    # )

    def _create_analytic_lines(self):
        """ Create analytic items upon validation of an account.move.line having an analytic distribution.
        """

        if self.move_id.job_order_id:
            return
        self._validate_analytic_distribution()
        analytic_line_vals = []
        for line in self:
            analytic_line_vals.extend(line._prepare_analytic_lines())

        self.env['account.analytic.line'].create(analytic_line_vals)


    @api.depends('quantity', 'price_unit')
    def _compute_total_amount(self):
        """ Calculate subtotal amount of product line """
        for line in self:
            line.gross_total_amount = line.price_unit * line.quantity

    @api.depends('quantity', 'price_unit', 'tax_ids.amount')
    def _compute_amount_tax(self):
        for record in self:
            if record.tax_ids:
                taxes_amount = sum(record.tax_ids.mapped('amount'))
                record.amount_tax = record.gross_total_amount * taxes_amount / 100
            else:
                record.amount_tax = 0

    @api.depends('account_id.group_id')
    def get_main_account_id(self):
        for rec in self:
            rec.main_account_id = rec.account_id.group_id.id

    @api.onchange('product_id')
    def is_computed_code(self):
        for rec in self:
            if rec.product_id:
                rec.main_income_account_id = rec.product_id.property_main_account_income_id.id
                rec.sub_income_account_id = rec.product_id.property_account_income_id.id
                rec.product_analytic_account_id = rec.product_id.analytic_account_id.id
                rec.is_computed = True
                
    @api.onchange('main_account_id')
    def _return_account_domain(self):
        for rec in self:
            if rec.main_account_id:
                return {'domain': {'account_id': [('group_id', '=', rec.main_account_id.id)]}}
            else:
                return {'domain': {'account_id': [('id', 'in', self.env['account.account'].search([]).ids)]}}

    @api.depends('move_id.partner_id')
    def is_compute_tax(self):
        for rec in self:
            rec.is_computed_tax = False
            if rec.move_id.move_type == 'out_invoice' and rec.move_id.partner_id.approved_tax_exempt:
                rec.tax_ids = [(5, 0, 0)]
                rec.is_computed_tax = True
    @api.depends('account_id', 'main_income_account_id', 'main_expense_account_id', 'analytic_account_id',
                 'product_analytic_account_id', 'branch_id', 'company_id')
    def _compute_combination_code(self):
        for rec in self:
            # Set analytic_account_id if it's not set
            if not rec.analytic_account_id:
                rec.analytic_account_id = rec.product_analytic_account_id.id

            # Create a list with basic combination parts
            combination_parts = [
                str(rec.env.company.code),
                str(rec.branch_id.code),
                str(rec.analytic_account_id.code),
                str(rec.main_account_id.code),
                str(rec.account_id.code)
            ]
    
            # If business_unit_id is not set, use '0000', otherwise use business_unit_id.code
            if rec.business_unit_id:
                combination_parts.append(str(rec.business_unit_id.code))
            else:
                combination_parts.append('0000')
    
            # Check if out_analytic flag is true
            if rec.account_id.out_analytic:
                # Replace analytic_account_id and business_unit_id with '000000' and '0000' respectively if they exist in the combination_parts
                combination_parts = [
                    '000000' if part == str(rec.analytic_account_id.code) else part for part in combination_parts
                ]
                combination_parts = [
                    '0000' if part == str(rec.business_unit_id.code) else part for part in combination_parts
                ]
            
            # Join the parts into the final combination code
            rec.combination_code = ','.join(combination_parts)
    # @api.depends('account_id', 'main_income_account_id', 'main_expense_account_id', 'analytic_account_id',
    #              'product_analytic_account_id', 'branch_id', 'company_id')
    # def _compute_combination_code(self):
    #     for rec in self:
    #         if not rec.analytic_account_id:
    #             rec.analytic_account_id = rec.product_analytic_account_id.id
    #         combination_parts = [
    #             str(rec.env.company.code),
    #             str(rec.branch_id.code),
    #             str(rec.analytic_account_id.code),
    #             str(rec.main_account_id.code),
    #             str(rec.account_id.code),
    #             str(rec.business_unit_id.code)
    #         ]

    #         if rec.account_id.out_analytic:
    #             if str(rec.analytic_account_id.code) in combination_parts:
    #                 combination_parts[combination_parts.index(str(rec.analytic_account_id.code))] = '000000'
    #             if str(rec.business_unit_id.code) in combination_parts:
    #                 combination_parts[combination_parts.index(str(rec.business_unit_id.code))] = '0000'
    #         rec.combination_code = ','.join(combination_parts)

    @api.depends('tax_ids', 'currency_id', 'partner_id', 'analytic_distribution', 'balance', 'partner_id',
                 'move_id.partner_id', 'price_unit')
    def _compute_all_tax(self):
        super(Account_move_line, self)._compute_all_tax()
        for line in self:
            sign = line.move_id.direction_sign
            if line.display_type == 'tax':
                line.compute_all_tax = {}
                line.compute_all_tax_dirty = False
                continue
            if line.display_type == 'product' and line.move_id.is_invoice(True):
                amount_currency = sign * line.price_unit * (1 - line.discount / 100)
                handle_price_include = True
                quantity = line.quantity
            else:
                amount_currency = line.amount_currency
                handle_price_include = False
                quantity = 1
            compute_all_currency = line.tax_ids.compute_all(
                amount_currency,
                currency=line.currency_id,
                quantity=quantity,
                product=line.product_id,
                partner=line.move_id.partner_id or line.partner_id,
                is_refund=line.is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=line.move_id.always_tax_exigible,
                fixed_multiplicator=sign,
            )
            rate = line.amount_currency / line.balance if line.balance else 1
            line.compute_all_tax_dirty = True
            line.compute_all_tax = {
                frozendict({
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'group_tax_id': tax['group'] and tax['group'].id or False,
                    'account_id': tax['account_id'] or line.product_id.property_account_expense_id.id or line.account_id.id
                    if line.move_type == 'in_invoice' else tax['account_id'] or line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'analytic_distribution': (tax['analytic'] or not tax[
                        'use_in_tax_closing']) and line.analytic_distribution,
                    'tax_ids': [(6, 0, tax['tax_ids'])],
                    'tax_tag_ids': [(6, 0, tax['tag_ids'])],
                    'partner_id': line.move_id.partner_id.id or line.partner_id.id,
                    'move_id': line.move_id.id,
                }): {
                    'name': tax['name'],
                    'balance': tax['amount'] / rate,
                    'amount_currency': tax['amount'],
                    'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
                }
                for tax in compute_all_currency['taxes']
                if tax['amount']
            }
            if not line.tax_repartition_line_id:
                line.compute_all_tax[frozendict({'id': line.id})] = {
                    'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
                }


class AccountPaymentRegisterInv(models.TransientModel):
    _inherit = 'account.payment.register'

    by_account = fields.Boolean()
    account_id = fields.Many2one('account.account')
