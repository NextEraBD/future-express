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


class RegisterMissionInvoice(models.TransientModel):
    _name = "mission.wizard"
    _description = "Create Journal"

    journal_id = fields.Many2one('account.journal')
    mission_id = fields.Many2one('hr.missions')

    def create_entry(self):
        company_currency = self.mission_id.company_id.currency_id

        vals2 = {
            'ref': self.mission_id.name,
            'date': fields.Date.today(),
            'company_id': self.mission_id.company_id.id,
            'journal_id': self.journal_id.id,
            'employee_id': self.mission_id.employee_id.id,
            # 'custody_id': self.custody_id.id,
            'branch_id': self.mission_id.branch_id.id,
            'line_ids': [],
        }
        vals2['line_ids'].append((0, 0, {
            'account_id': self.mission_id.employee_id.employee_account_id.id,
            'partner_id':self.mission_id.employee_id.user_id.partner_id.id,
            'currency_id':self.mission_id.company_id.currency_id.id,
            # 'amount_currency': self.custody_id.amount,
            'debit': self.mission_id.total_amount,
            'credit': 0,
        }))

        vals2['line_ids'].append((0, 0, {
            'account_id': self.journal_id.default_account_id.id,
            'currency_id': self.mission_id.company_id.currency_id.id,
            # 'amount_currency': self.custody_id.amount,
            'debit': 0,
            'credit':self.mission_id.total_amount,
        }))

        move_id = self.env['account.move'].create(vals2)
        self.mission_id.move_id = move_id
        move_id.action_post()


