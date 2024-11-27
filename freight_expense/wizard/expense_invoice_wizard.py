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


class InvoiceWizard(models.TransientModel):
    _name = 'invoice.wizard'

    # Define fields necessary for creating an invoice
    # Example:
    partner_id = fields.Many2one('res.partner', string='Customer')
    journal_id = fields.Many2one('account.journal')
    invoice_date = fields.Date(string='Invoice Date')
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.company)
    bill_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')

    def action_create_journal_invoice_expense(self):
        company_currency = self.company_id.currency_id
        total = 0
        line_ids = []
        selected_records = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))
        for line in selected_records:
            if not line.currency_id:
                raise ValidationError(_('You Should Add Currency first.'))
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
            if line.invoice_status != 'done':
                line_ids.append((0, 0, {
                    'account_id': line.product_id.property_account_expense_id.id or line.product_id.categ_id.property_account_expense_categ_id.id,
                    'currency_id': line.currency_id.id,
                    'product_id': line.product_id.id,
                    # 'analytic_account_id': line.analytic_account_id.id,
                    # 'analytic_distribution': {str(line.analytic_account_id.id): 100.00},
                    'shipment_number': line.shipment_number.id,
                    'quantity': 1,
                    'price_unit': line.amount_sale,
                }))
            total += amount_currency
            line.invoice_status ='done'
        if line_ids != []:
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'journal_id': self.journal_id.id,
                'invoice_date': fields.Date.today(),
                'partner_id': self.partner_id.id,
                # 'account_id': self.partner_id.property_account_payable_id.id,
                'invoice_line_ids': line_ids,
                'freight_operation_id': line.shipment_number.id
            })
        return {'type': 'ir.actions.act_window_close'}


class BillWizard(models.TransientModel):
    _name = 'bill.wizard'

    # Define fields necessary for creating an invoice
    # Example:
    partner_id = fields.Many2one('res.partner', string='Vendor')
    journal_id = fields.Many2one('account.journal')
    invoice_date = fields.Date(string='Invoice Date')
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.company)

    def action_create_journal_expense(self):
        company_currency = self.company_id.currency_id
        total = 0
        line_ids = []
        selected_records = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))
        for line in selected_records:
            if not line.currency_id:
                raise ValidationError(_('You Should Add Currency first.'))
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
            if line.bill_status != 'done':
                line_ids.append((0, 0, {
                    'account_id': line.product_id.property_account_expense_id.id or line.product_id.categ_id.property_account_expense_categ_id.id,
                    'currency_id': line.currency_id.id,
                    'product_id': line.product_id.id,
                    # 'analytic_account_id': line.analytic_account_id.id,
                    # 'analytic_distribution': {str(line.analytic_account_id.id): 100.00},
                    'shipment_number': line.shipment_number.id,
                    'quantity': 1,
                    'price_unit': line.amount_cost,
                }))
            total += amount_currency
            line.bill_status ='done'
        if line_ids != []:
            bill = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'journal_id': self.journal_id.id,
                'invoice_date': fields.Date.today(),
                'partner_id': self.partner_id.id,
                # 'account_id': self.partner_id.property_account_payable_id.id,
                'invoice_line_ids': line_ids,
                'freight_operation_id': line.shipment_number.id
            })
        return {'type': 'ir.actions.act_window_close'}