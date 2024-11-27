# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import os.path
import base64
import time

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import date, datetime
from time import gmtime, strftime

_logger = logging.getLogger(__name__)


class RegisterInvoice(models.TransientModel):
    _name = "custody.custody.wizard"
    _description = "Create Journal"

    journal_id = fields.Many2one('account.journal')
    custody_id = fields.Many2one('custody.custody')
    branch_id = fields.Many2one('res.branch', string='Branch')

    def create_entry(self):
        company_currency = self.custody_id.company_id.currency_id

        vals2 = {
            'ref': self.custody_id.name,
            'date': fields.Date.today(),
            'company_id': self.custody_id.company_id.id,
            'journal_id': self.journal_id.id,
            'employee_id': self.custody_id.employee_id.id,
            'custody_id': self.custody_id.id,
            # 'branch_id': self.branch_id.id,
            'line_ids': [],
        }
        amount_currency = self.custody_id.amount
        if self.custody_id.currency_id and self.custody_id.currency_id != company_currency:
            rate = self.custody_id.currency_id.rate_ids.filtered(
                lambda r: r.company_id == self.custody_id.company_id and r.name.year == fields.Date.today().year)[0].mapped(
                'inverse_company_rate')
            if rate:
                amount_currency = self.custody_id.amount * rate[0]
            else:
                raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))

        vals2['line_ids'].append((0, 0, {
            'account_id': self.custody_id.employee_id.employee_account_id.id,
            'partner_id':self.custody_id.employee_id.user_id.partner_id.id,
            'currency_id':self.custody_id.currency_id.id,
            # 'amount_currency': self.custody_id.amount,
            'debit': amount_currency,
            'credit': 0,
        }))

        vals2['line_ids'].append((0, 0, {
            'account_id': self.journal_id.default_account_id.id,
            'currency_id': self.custody_id.currency_id.id,
            # 'amount_currency': self.custody_id.amount,
            'debit': 0,
            'credit': amount_currency,
        }))

        move_id = self.env['account.move'].create(vals2)
        self.custody_id.move_id = move_id
        self.custody_id.state = 'done'
        self.custody_id._activity_done()
        move_id.action_post()


