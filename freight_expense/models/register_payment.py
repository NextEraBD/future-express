# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import frozendict


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = 'Register Payment'

    # == Business fields ==
    journal_id = fields.Many2one(domain=[])
    journal_account_id = fields.Many2one('account.account', related='journal_id.default_account_id',store=True,readonly=False)
    default_account_type = fields.Char(string='Default Account Type', related='journal_id.default_account_type')


class CoverAccountType(models.Model):
    _name = 'cover.account.type'

    name = fields.Char()
    journal_id = fields.Many2one('account.journal',string="Expense Journal",required=True)