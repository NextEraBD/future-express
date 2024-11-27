from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from collections import defaultdict


class ElsHrCoverLetter(models.Model):
    _inherit = 'hr.cover.letter'

    @api.model
    def create(self, vals):
        if 'company_id' in vals and vals['company_id'] == 1:
            cov_name = self.env['ir.sequence'].get('hr.cover.letter.els')
            vals['name'] = cov_name or '/'
        else:
            cov_name = self.env['ir.sequence'].next_by_code('hr.cover.letter')
            vals['name'] = cov_name or '/'
        res = super(ElsHrCoverLetter, self).create(vals)
        return res

    def action_create_journal_expense(self):
        company_currency = self.company_id.currency_id
        vals = {
            'ref': self.name,
            'date': fields.Date.today(),
            'company_id': self.company_id.id,
            'journal_id': self.employee_id.journal_id.id,
            'employee_id': self.employee_id.id,
            'cover_letter_id': self.id,
            'move_type': 'entry',
            'line_ids': [],
        }
        total = 0
        for line in self.expense_line_ids:
            if not line.currency_id:
                raise ValidationError(_('You Should Add Currency first.'))
            if not line.product_id.property_account_expense_id:
                raise ValidationError(
                    _('Expense Account for the expense Category is not set. Please, set it and try again.'))
            amount_currency = line.taxed_amount_cost
            if line.currency_id and line.currency_id != company_currency:
                if not line.currency_id.rate_ids:
                    raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))
                rate = line.currency_id.rate_ids.filtered(
                    lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year)[0].mapped(
                    'inverse_company_rate')
                if rate:
                    amount_currency = line.taxed_amount_cost * rate[0]
                else:
                    raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))
            vals['line_ids'].append((0, 0, {
                'account_id': line.product_id.property_account_expense_id.id,
                'currency_id': line.currency_id.id,
                # 'analytic_distribution': {str(line.analytic_account_id.id): 100.00},
                'shipment_number': line.shipment_number.id,
                'amount_currency': line.taxed_amount_cost,
                'debit': amount_currency,
                'credit': 0,
            }))
            total += amount_currency
        vals['line_ids'].append((0, 0, {
            'account_id': self.employee_id.employee_account_id.id,
            'partner_id': self.employee_id.user_id.partner_id.id,
            'debit': 0,
            'credit': total,
        }))
        if self.expense_line_ids:
            move_id = self.env['account.move'].create(vals)
            move_id.action_post()

    def action_create_journal_official(self):
        company_currency = self.company_id.currency_id
        # Grouping lines based on current_account value and respective account, partner, and journal
        grouped_lines = defaultdict(lambda: defaultdict(list))
        for line in self.official_line_ids:
            journal_id = self.employee_id.journal_id.id
            account_id = self.employee_id.employee_account_id.id
            partner_id = self.employee_id.user_id.partner_id.id
            grouped_lines[journal_id]['journal'] = journal_id
            grouped_lines[journal_id]['account'] = account_id
            grouped_lines[journal_id]['partner'] = partner_id
            grouped_lines[journal_id]['lines'].append(line)

        # Creating journal entries for each group of lines
        for journal_id, data in grouped_lines.items():
            vals = {
                'ref': self.name,
                'date': fields.Date.today(),
                'journal_id': journal_id,
                'company_id': self.company_id.id,
                'employee_id': self.employee_id.id,
                'cover_letter_id': self.id,
                'move_type': 'entry',
                'line_ids': [],
            }
            total = 0

            # Processing lines within the group
            for line in data['lines']:
                amount_currency = line.taxed_amount_cost
                if line.currency_id != company_currency:
                    rate = line.currency_id.rate_ids.filtered(
                        lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year).mapped(
                        'inverse_company_rate')
                    if rate:
                        amount_currency = line.taxed_amount_cost * rate[0]
                    else:
                        raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))

                vals['line_ids'].append((0, 0, {
                    'account_id': line.product_id.property_account_expense_id.id,
                    'currency_id': line.currency_id.id,
                    # 'analytic_distribution': {str(line.analytic_account_id.id): 100.00},
                    'shipment_number': line.shipment_number.id,
                    'amount_currency': amount_currency,
                    'debit': amount_currency,
                    'credit': 0,
                }))
                total += amount_currency

            # Adding a line for the total of the group
            vals['line_ids'].append((0, 0, {
                'account_id': data['account'],
                'partner_id': data['partner'],
                'debit': 0,
                'credit': total,
            }))

            # Creating the journal entry
            if self.official_line_ids:
                move_id = self.env['account.move'].create(vals)
                move_id.action_post()

    def action_create_journal_entries(self):
        self.action_create_journal_expense()
        self.action_create_journal_official()



