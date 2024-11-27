# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import datetime
from odoo.osv import expression

class Followers(models.Model):

    _inherit = 'mail.followers'

    _sql_constraints = [
        ('mail_followers_res_partner_res_model_id_uniq', 'Check(1=1)', 'Error, a partner cannot follow twice the same object.'),
        ]

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    has_checked = fields.Boolean()

class ProductProduct(models.Model):
    _inherit = 'product.product'

    has_checked = fields.Boolean()


class DistributeBill(models.Model):
    _name = 'distribute.bill'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'console_id'
    _description = 'Distribute Bill'

    console_id = fields.Many2one('console.operation', 'Console Operation')
    total_frt = fields.Float()
    distribute_type = fields.Selection(([('bill', 'Vendor Bill'), ('expense', 'Expense'), ('official', 'Official Receipt')]), string='Distribute Type')
    # distribute_amount_type = fields.Selection(([('equal', 'Equal'), ('distribute', 'Distribute')]), string='Type')
    bill_id = fields.Many2one('account.move',string="Bill", copy=False)
    partner_id = fields.Many2one('res.partner',string="Vendor", related='bill_id.partner_id',)
    amount_total = fields.Monetary(string="Total Amount", store=True)

    @api.onchange('bill_id')
    def onchange_bill_id(self):
        for rec in self:
            rec.amount_total = rec.bill_id.amount_untaxed

    @api.depends('console_id')
    def compute_bill_ids(self):
        move_ids = []
        for rec in self:
            move_ids += self.env['account.move'].search(
                [('console_id', '=', rec.console_id.id), ('move_type', '=', 'in_invoice')]).ids
            if rec.console_id:
                self.bill_ids = move_ids
            else:
                self.bill_ids = False

    bill_ids = fields.Many2many('account.move',string="Invoices",compute='compute_bill_ids')
    line_ids = fields.One2many('distribute.bill.operation','distribute_bill_id',string='Operations',readonly=True)
    is_computed = fields.Boolean(compute="_compute_operation_count")
    equal = fields.Boolean()
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')],store=True, default='draft')
    currency_id = fields.Many2one('res.currency', 'Currency')

    @api.depends('console_id')
    def _compute_operation_count(self):
        for record in self:
            operation_ids = self.env['console.operation.line'].search([('console_id', '=', record.console_id.id)])
            line_ids = []
            record.line_ids = [(5, 0, 0)]  # Clear existing line_ids
            for operation in operation_ids:
                if operation.id:
                    line_ids.append((0, 0, {
                        'distribute_bill_id': record.id,
                        'operation_id': operation.operation_id.id,
                        'shipment_name': operation.name,
                        'weight': operation.gross_weight,
                        'net_weight': operation.net_weight,
                        'volume': operation.volume,
                        'frt': operation.largest,
                    }))
            record.update({'line_ids': line_ids})
            record.is_computed = True

    def action_confirm(self):
        analytic_account_id = False
        for rec in self:
            product = rec.bill_id.invoice_line_ids.search(
                [('move_id', '=', rec.bill_id.id), ('product_id', '!=', False)], limit=1)
            # rec.bill_id.message_follower_ids.unlink()
            product_id = product.product_id
            rec.bill_id.invoice_line_ids.unlink()
            # raise ValidationError(product_id)
            one_frt = rec.amount_total / rec.total_frt
            for line in rec.line_ids:                    
                if not rec.equal:
                    total_cost = line.frt * one_frt
                else:
                    total_cost = rec.amount_total / len(rec.line_ids)

                user_id = self.env['res.users'].browse(self.env.uid)
                expense = rec.env['hr.cover.letter.expense'].create(
                    {
                        'shipment_number': line.operation_id.id,
                        'reference': rec.bill_id.name,
                        'cover_letter_id': rec.bill_id.cover_letter_id.id,
                        'employee_id': rec.bill_id.employee_id.id,
                        'operator_id': user_id.id,
                        'product_id': product_id.id,
                        'expense_service_type': product_id.expense_service_type,
                        'amount_cost': total_cost,
                        'distribute': True,
                    })
                # raise ValidationError(expense.operator_id)
                expense.action_approve_operator()
                vals = []
                vals.append((0, 0, {
                    'product_id': product_id.id,
                    # 'analytic_account_id': line.analytic_account_id.id,
                    'analytic_distribution': {str(analytic_account_id): 100.00},
                    'shipment_number': line.operation_id.id,
                    'price_unit': total_cost,
                }))

                rec.bill_id.write({'invoice_line_ids': vals})
            rec.state = 'confirmed'


class DistributeBillOperation(models.Model):
    _name = 'distribute.bill.operation'

    distribute_bill_id = fields.Many2one('distribute.bill', string='distribute Bill')
    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    operation_id = fields.Many2one('freight.operation', 'Shipment ID')
    shipment_name = fields.Char()
    weight = fields.Float('Gross Weight')
    net_weight = fields.Float('Net Weight')
    volume = fields.Float('Volume')
    frt = fields.Float()

