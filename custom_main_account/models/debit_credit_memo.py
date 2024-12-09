# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang


class AccountPaymentMemo(models.Model):
    _name = "account.debit.memo"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry', readonly=True, ondelete='cascade',
        check_company=True)
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice', readonly=True, ondelete='cascade',
        check_company=True)
    name = fields.Char(
        string='Number',
        store=True,
        copy=False,
        tracking=True,
        index='trigram',
    )
    ref = fields.Char(string='Reference', copy=False, tracking=True)
    date = fields.Date(
        string='Date',
        index=True,
        store=True, required=True, readonly=False, precompute=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        states={'draft': [('readonly', False)]},
        check_company=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        check_company=True,
        change_default=True,
        ondelete='restrict',
    )
    amount = fields.Monetary(currency_field='currency_id')
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.user.company_id,
        states={'done': [('readonly', True)]},
        required=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        states={'done': [('readonly', True)]},
        required=True,
        default=lambda self: self.env.user.company_id.currency_id
    )
    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Vendor'),
    ], default='customer', tracking=True, required=True)
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
    ], string='Payment Type', default='inbound', required=True, tracking=True)
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        required=True,
        store=True, readonly=False,
        check_company=True)
    branch_id = fields.Many2one('res.branch', string='Branch', default=lambda self: self.env.user.branch_id)

    @api.model
    def create(self, vals):
        seq_date = None
        partner_type = vals['partner_type']
        if 'date' in vals:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date']))

        if partner_type == 'customer':
            vals['name'] = self.env['ir.sequence'].next_by_code('credit.memo', sequence_date=seq_date) or _(
                'New')
            # raise ValidationError(_(vals['name']))
        elif partner_type == 'supplier':
            vals['name'] = self.env['ir.sequence'].next_by_code('debit.memo', sequence_date=seq_date) or _(
                'New')
        result = super(AccountPaymentMemo, self).create(vals)
        return result

    def button_open_journal_entry(self):
        ''' Redirect the user to this Debit Or Credit journal.
        :return:    An action on account.move.
        '''
        self.ensure_one()
        return {
            'name': _("Journal Entry"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'domain': [('id', '=', self.move_id.id)],
            'view_mode': 'form',
            'res_id': self.move_id.id,
        }

    def action_cancel(self):
        ''' draft -> cancelled '''
        self.move_id.button_cancel()
        self.write({'state': 'cancel'})
        
    def action_draft(self):
        ''' posted -> draft '''
        self.move_id.button_draft()
        self.write({'state': 'draft'})
        
    def action_confirm(self):
        company_currency = self.company_id.currency_id
        vals = {
            'ref': self.name,
            'date': fields.Date.today(),
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'journal_id': self.journal_id.id,
            'branch_id': self.branch_id.id,
            'move_type': 'entry',
            'line_ids': [],
        }
        amount_currency = self.amount
        converted_amount = amount_currency
        if self.currency_id and self.currency_id != company_currency:
            rate_records = self.currency_id.rate_ids.filtered(
                lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year
            )
            if rate_records:
                rate = rate_records[0].inverse_company_rate
                if rate:
                    converted_amount = self.amount * rate
                else:
                    raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))
            else:
                raise ValidationError(_('No currency rate record found for the specified year.'))
        if self.partner_type == 'customer':
            partner_account = self.partner_id.property_account_receivable_id.id
            vals['line_ids'].append((0, 0, {
                'account_id': partner_account,
                'partner_id': self.partner_id.id,
                'currency_id': self.currency_id.id,
                'amount_currency': -self.amount,
                'credit': converted_amount,
                'debit': 0,
            }))
            vals['line_ids'].append((0, 0, {
                'account_id': self.account_id.id,
                'amount_currency': self.amount,
                'currency_id': self.currency_id.id,
                'credit': 0.0,
                'debit': converted_amount,
            }))
        if self.partner_type == 'supplier':
            partner_account = self.partner_id.property_account_payable_id.id

            vals['line_ids'].append((0, 0, {
                'account_id': partner_account,
                'partner_id': self.partner_id.id,
                'currency_id': self.currency_id.id,
                'amount_currency': self.amount,
                'credit': 0.0,
                'debit': converted_amount,
            }))
            vals['line_ids'].append((0, 0, {
                'account_id': self.account_id.id,
                'currency_id': self.currency_id.id,
                'amount_currency': -self.amount,
                'credit': converted_amount,
                'debit': 0,
            }))
        self.move_id = self.env['account.move'].create(vals)
        self.write({'state': 'confirm'})
        self.move_id.action_post()