from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
import math
import logging
from datetime import datetime


class Console(models.Model):
    _inherit = 'console.operation'

    distribute_count = fields.Float('Distribute Count', compute='_compute_distribute_count')
    distribute = fields.Boolean(copy=False)

    def _compute_distribute_count(self):
        for rec in self:
            rec.distribute_count = self.env['distribute.bill'].sudo().search_count([('console_id', '=', self.id)])

    def button_distribute(self):
        distribute = self.env['distribute.bill'].sudo().search([('console_id', '=', self.id)])
        action = self.env["ir.actions.actions"]._for_xml_id("els.action_distribute_bill_view")
        action['context'] = {
            'default_console_id': self.id,
            'default_total_frt': self.total_frt,
        }
        action['domain'] = [('id', 'in', distribute.ids)]
        return action

    def action_create_distribute(self):
        for rec in self:
            self.env['distribute.bill'].create(
                {
                    'console_id': rec.id,
                    'total_frt': rec.total_frt,
                    'distribute_type': 'bill',
                })
            rec.distribute = True

    employee_ids = fields.Many2many('hr.employee')
    expenses_counter = fields.Integer(compute='compute_expenses_counter')
    official_counter = fields.Integer(compute='compute_official_counter')

    cov_line_counter = fields.Integer(compute='compute_cov_line_counter')
    claim_counter = fields.Integer(compute='compute_claim_counter')
    entry_counter = fields.Integer(compute='compute_entry_counter')
    event_counter = fields.Integer(compute='compute_event_counter')

    ######################## COMPUTE METHODS ##################################
    def compute_expenses_counter(self):
        for rec in self:
            rec.expenses_counter = self.env['hr.cover.letter.expense'].search_count([('console_id', '=', rec.id)])

    def compute_official_counter(self):
        for rec in self:
            rec.official_counter = self.env['hr.cover.letter.official'].search_count([('console_id', '=', rec.id)])

    def compute_cov_line_counter(self):
        for rec in self:
            rec.cov_line_counter = self.env['hr.cover.letter.line'].search_count([('console_id', '=', rec.id)])

    def compute_claim_counter(self):
        for rec in self:
            rec.claim_counter = self.env['account.move'].search_count(
                [('console_id', '=', rec.id), ('move_type', '=', 'out_invoice')])

    def compute_entry_counter(self):
        for rec in self:
            rec.entry_counter = self.env['account.move'].search_count(
                [('console_id', '=', rec.id), ('move_type', '=', 'entry')])

    def compute_event_counter(self):
        for rec in self:
            rec.event_counter = self.env['els.events'].search_count(
                [('console_id', '=', rec.id), ('state', '=', 'submit')])

    ############ ACTION METHODS ####################################################################
    def action_viw_expenses(self):
        ids = self.env['hr.cover.letter.expense'].search([('console_id', '=', self.id)]).ids
        tree_view_id = self.env.ref('freight_expense.hr_cover_letter_exp_tree').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Expenses'),
            'res_model': 'hr.cover.letter.expense',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[tree_view_id, 'list'], [False, 'form']],
            'search_view_id': [self.env.ref('freight_expense.hr_cover_letter_expense_search').id],
            'domain': [('id', 'in', ids)],
            'context': {'default_shipment_number': self.id}
        }

    def action_viw_official(self):
        ids = self.env['hr.cover.letter.official'].search([('console_id', '=', self.id)]).ids
        tree_view_id = self.env.ref('freight_expense.hr_cover_letter_off_tree').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Official Receipt'),
            'res_model': 'hr.cover.letter.official',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[tree_view_id, 'list'], [False, 'form']],
            'search_view_id': [self.env.ref('freight_expense.hr_cover_letter_official_search').id],
            'domain': [('id', 'in', ids)],
            'context': {'default_shipment_number': self.id}
        }

    def action_view_cov_lines(self):
        ids = self.env['hr.cover.letter.line'].search([('console_id', '=', self.id)]).ids
        tree_view_id = self.env.ref('freight_expense.hr_cover_letter_line_tree').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cov Lines'),
            'res_model': 'hr.cover.letter.line',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[tree_view_id, 'list'], [False, 'form']],
            'search_view_id': [self.env.ref('freight_expense.hr_cover_letter_line_search').id],
            'domain': [('id', 'in', ids)],
        }

    def action_view_claims(self):
        ids = self.env['account.move'].search([('console_id', '=', self.id), ('move_type', '=', 'out_invoice')]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('CLAIMS'),
            'res_model': 'account.move',
            'view_type': 'list',
            'view_mode': 'list',
            'context': "{'move_type':'out_invoice'}",
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids)],
        }

    def action_view_entries(self):
        ids = self.env['account.move'].search([('console_id', '=', self.id), ('move_type', '=', 'entry')]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entry'),
            'res_model': 'account.move',
            'view_type': 'list',
            'view_mode': 'list',
            'context': "{'move_type':'entry'}",
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids)],
        }

    def action_view_event(self):
        ids = self.env['els.events'].search([('console_id', '=', self.id), ('state', '=', 'submit')]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Events'),
            'res_model': 'els.events',
            'view_type': 'list',
            'view_mode': 'list',
            'context': {'move_type': 'entry', 'default_console_id': self.id},
            'views': [[False, 'list']],
            'domain': [('id', 'in', ids)],
        }

    '''
        date:10/05/2023
        auther:mohamed eldeeb
        description:function to create claim sale invoice for all receipt and expenses lines
        '''

    def action_create_claim(self):

        official_lines = self.env['hr.cover.letter.official'].search(
            [('console_id', '=', self.id), ('claim_status', '!=', 'done')])
        if official_lines:
            lines = []
            for line in official_lines:
                if line.product_id.property_account_income_id.id:
                    income_account = line.product_id.property_account_income_id.id
                elif line.product_id.categ_id.property_account_income_categ_id.id:
                    income_account = line.product_id.categ_id.property_account_income_categ_id.id
                else:
                    raise UserError(_('Please define income '
                                      'account for this product: "%s" (id:%d).')
                                    % (line.product_id.name, line.product_id.id))

                lines.append((0, 0, {'name': line.product_id.name,
                                     # 'origin': line.name,
                                     'account_id': income_account,
                                     'quantity': 1,
                                     # 'shipment_number': line.shipment_number.id,
                                     'company_id': line.company_id.id,
                                     'business_unit_id': line.business_unit_id.id,
                                     'product_uom_id': line.uom_id.id,
                                     'price_unit': line.amount_sale,
                                     'product_id': line.product_id.id,
                                     'tax_ids': [(6, 0, [line.tax_id.id])] if line.tax_id else False,
                                     }))

            if self.company_id.id == 1:
                journal_id = self.env.ref('freight_expense.els_claim_customer_journal').id
            elif self.company_id.id == 2:
                journal_id = self.env.ref('freight_expense.etal_claim_customer_journal').id
            claim_id = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'is_claim': True,
                'partner_id': self.shipper_id.id,
                'company_id': self.company_id.id,
                'business_unit_id': self.business_unit_id.id,
                'journal_id': journal_id if journal_id else False,
                # 'account_id': self.partner_id.property_account_receivable_id.id,
                'invoice_line_ids': lines,
                'console_id': self.id
            })

            self.action_create_so()
            self.action_create_journal_entries()

    def action_create_so(self):
        self.ensure_one()
        expense_lines = self.env['hr.cover.letter.expense'].search(
            [('console_id', '=', self.id), ('claim_status', '!=', 'done')])

        if expense_lines:
            currency_groups = expense_lines.read_group(
                domain=[('console_id', '=', self.id), ('claim_status', '!=', 'done')],
                fields=['currency_id'],
                groupby=['currency_id'],
                lazy=False,
            )
            print(currency_groups)
            # todo end
            if currency_groups:
                for currency in currency_groups:
                    pricelist_id = self.env['product.pricelist'].search(
                        [('currency_id', '=', currency.get('currency_id')[0])], limit=1).id
                    vals = {
                        'partner_id': self.shipper_id.id,
                        'currency_id': currency.get('currency_id')[0],
                        'pricelist_id': pricelist_id,
                        # 'freight_operation_id': self.id,
                        'order_line': []
                    }
                    for line in expense_lines:
                        if line.currency_id.id == currency.get('currency_id')[0]:
                            vals['order_line'].append((0, 0, {
                                'product_id': line.product_id.id,
                                'name': line.product_id.name,
                                'company_id': line.company_id.id,
                                'currency_id': currency.get('currency_id')[0],
                                'product_uom_qty': 1,
                                'tax_id': [(6, 0, [line.tax_id.id])] if line.tax_id else False,
                                'product_uom': line.uom_id.id if line.uom_id.id else line.product_id.uom_id.id,
                                'price_unit': line.amount_sale,

                            }))
                            # line.claim_status = 'done'
                    so = self.env['sale.order'].create(vals)

    def action_create_journal_entries(self):
        company_currency = self.company_id.currency_id
        expense_lines = self.env['hr.cover.letter.expense'].search(
            [('console_id', '=', self.id), ('claim_status', '!=', 'done')])
        official_lines = self.env['hr.cover.letter.official'].search(
            [('console_id', '=', self.id), ('claim_status', '!=', 'done')])
        if expense_lines or official_lines:
            if expense_lines:
                sub_account_id = expense_lines[0].product_id.sub_account_id
            elif official_lines:
                sub_account_id = official_lines[0].product_id.sub_account_id
            else:
                raise ValidationError(
                    _('Broking Account for the expense category is not set. Please, set it and try again.'))
            vals = {
                'ref': self.name,
                'date': fields.Date.today(),
                'company_id': self.company_id.id,
                # 'journal_id': employee_id.journal_id.id,

                'console_id': self.id,
                'line_ids': [],
            }

            total = 0
            for line in expense_lines:
                if not line.product_id.property_account_expense_id:
                    raise ValidationError(
                        _('Expense Account for the expense categury is not set. Please, set it and try again.'))
                amount_currency = line.taxed_amount_cost
                if line.currency_id and line.currency_id != company_currency:
                    rate = line.currency_id.rate_ids.filtered(
                        lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year)[
                        0].mapped('inverse_company_rate')
                    if rate:
                        amount_currency = line.taxed_amount_cost * rate[0]
                    else:
                        raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))
                vals['line_ids'].append((0, 0, {
                    'account_id': line.product_id.property_account_expense_id.id,
                    'currency_id': line.currency_id.id,
                    # 'shipment_number': line.shipment_number.id,
                    'amount_currency': -line.taxed_amount_cost,
                    'credit': amount_currency,
                    'debit': 0,
                }))
                total += amount_currency
                line.claim_status = 'done'

            for line in official_lines:
                amount_currency = line.taxed_amount_cost
                if line.currency_id != company_currency:
                    rate = line.currency_id.rate_ids.filtered(
                        lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year)[
                        0].mapped(
                        'inverse_company_rate')
                    if rate:
                        amount_currency = line.taxed_amount_cost * rate[0]
                    else:
                        raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))

                vals['line_ids'].append((0, 0, {
                    'account_id': line.product_id.property_account_expense_id.id,

                    'currency_id': line.currency_id.id,
                    # 'shipment_number': line.shipment_number.id,
                    'amount_currency': -line.taxed_amount_cost,
                    'debit': 0,
                    'credit': amount_currency,
                }))
                total += amount_currency
                line.claim_status = 'done'

            vals['line_ids'].append((0, 0, {
                'account_id': sub_account_id.id,
                # 'partner_id': self.employee_id.user_id.partner_id.id,
                'debit': total,
                'credit': 0,
            }))

            move_id = self.env['account.move'].create(vals)
            move_id.action_post()
