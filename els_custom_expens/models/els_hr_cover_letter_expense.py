import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrExpense(models.Model):
    _inherit = 'hr.cover.letter.expense'

    console_id_domain = fields.Char(compute="_compute_console_id_domain",readonly=True,store=False)
    console_id = fields.Many2one('console.operation', check_company=True)
    is_console = fields.Boolean()
    amount_sale = fields.Float()
    analytic_account_id = fields.Many2one('account.analytic.account')
    distribute = fields.Boolean(copy=False)
    bill_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    invoice_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    quantity = fields.Float(string="Quantity")
    total_cost = fields.Float(compute='_onchange_get_tot_cost')
    total_sale = fields.Float(compute='_onchange_get_tot_cost', store=True)
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')
    customer_id = fields.Many2one('res.partner', )
    vendor_id = fields.Many2one('res.partner', )


    def action_create_journal(self):
        company_currency = self.company_id.currency_id
        vals = {
            'ref': 'Expense',
            'date': fields.Date.today(),
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'freight_operation_id': self.shipment_number.id,
            'console_id': self.console_id.id,
            'journal_id': self.journal_id.id,
            'employee_id':self.employee_id.id,
            'move_type': 'entry',
            'line_ids': [],
        }
        total = 0
        for line in self:
            if not line.product_id.property_account_expense_id:
                raise ValidationError(_('Expense Account for the expense categury is not set. Please, set it and try again.'))
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
                'currency_id': line.sale_currency_id.id,
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
        self.expens_journal_created = True


    @api.depends('quantity', 'amount_sale', 'amount_cost')
    def _onchange_get_tot_cost(self):
        for rec in self:
            rec.total_cost = rec.quantity * rec.amount_cost
            rec.total_sale = rec.quantity * rec.amount_sale

    @api.model_create_multi
    def default_get(self, default_fields):
        res = super(HrExpense, self).default_get(default_fields)
        if self.currency_id:
            res.update({
                'sale_currency_id': self.currency_id.id or False
            })
        return res

    @api.depends('cover_letter_id.company_id', 'cover_letter_id.employee_id')
    def _compute_shipment_number_domain(self):
        for rec in self:
            rec.shipment_number_domain = json.dumps(
                [('company_id', '=', rec.company_id.id), ('employee_ids', 'in', [rec.cover_letter_id.employee_id.id])]
            )

    @api.onchange('product_id', 'shipment_number')
    def onchange_product_id_extend(self):
        # self.amount_cost = self.product_id.list_price
        # self.amount_sale = self.product_id.standard_price
        for line in self:
            analytic_account_id = False
            if line.product_id and line.shipment_number:
                if line.shipment_number.direction == 'import' and line.shipment_number.ocean_shipment_type != 'lcl':
                    analytic_account_id = line.product_id.id
                elif line.shipment_number.direction == 'export' and line.shipment_number.ocean_shipment_type != 'lcl':
                    analytic_account_id = line.product_id.id
                elif line.shipment_number.direction == 'import' and line.shipment_number.ocean_shipment_type == 'lcl':
                    analytic_account_id = line.product_id.id
                elif line.shipment_number.direction == 'export' and line.shipment_number.ocean_shipment_type == 'lcl':
                    analytic_account_id = line.product_id.lcl_export_analytic_account_id.id
            if analytic_account_id:
                line.analytic_account_id = analytic_account_id

    @api.depends('cover_letter_id.company_id', 'cover_letter_id.employee_id')
    def _compute_console_id_domain(self):
        for rec in self:
            rec.console_id_domain = json.dumps(
                [('company_id', '=', rec.company_id.id), ('employee_ids', 'in', [rec.employee_id.id])]
            )

    def action_approve(self):
        if self.shipment_number.customer_service_id == self.env.user:
            self.create_shipment_line()
            self.line_state = 'approved'
        else:
            raise ValidationError(
                _("You are not authorised to approve this request only cover letter customer servicer"))

    def create_shipment_line(self):
        if self.shipment_number and self.amount_sale:
            if self.expense_service_type == 'freight':
                self.shipment_number.freight_check = True
                freight_lines = self.env['freight.freight.line'].search([('shipment_id', '=', self.shipment_number.id)])
                so = False
                if freight_lines:
                    line = freight_lines.filtered(lambda l: l.sale_id.currency_id == self.sale_currency_id and l.customer_id == self.customer_id)
                    if line:
                        so = line.sale_id

                    if so:
                        so.order_line = [(0, 0, {
                            'product_id': self.product_id.id,
                            'name': self.product_id.name,
                            'product_uom_qty': 1,
                            'currency_id': self.sale_currency_id.id,
                            'price_unit': self.amount_sale,
                        })]
                        so = so.id
                self.env['freight.freight.line'].create({
                    'shipment_id': self.shipment_number.id,
                    'product_id': self.product_id.id,
                    'agent_id': self.agent_id.id,
                    'customer_id': self.customer_id.id,
                    'currency_id': self.sale_currency_id.id,
                    'sale_currency_id': self.sale_currency_id.id,
                    'price_sale': self.amount_sale,
                    'price_cost': self.amount_cost,
                    'destination_location_id': self.port_id.id,
                    'qty': 1,
                    'sale_id': so,
                    'freight_operator': self.shipment_number.freight_operator.id,
                })
            elif self.expense_service_type == 'transportation':
                self.shipment_number.transport_check = True
                freight_lines = self.env['freight.transport.line'].search(
                    [('shipment_id', '=', self.shipment_number.id)])
                so = False
                if freight_lines:
                    line = freight_lines.filtered(lambda l: l.sale_id.currency_id == self.sale_currency_id and l.customer_id == self.customer_id)
                    if line:
                        so = line.sale_id
                    if so:
                        so.order_line = [(0, 0, {
                            'product_id': self.product_id.id,
                            'name': self.product_id.name,
                            'product_uom_qty': 1,
                            'currency_id': self.sale_currency_id.id,
                            'price_unit': self.amount_sale,
                        })]
                        so = so.id

                self.env['freight.transport.line'].create({
                    'shipment_id': self.shipment_number.id,
                    'product_id': self.product_id.id,
                    'tracking_agent': self.tracking_agent.id,
                    'customer_id': self.customer_id.id,
                    'currency_id': self.sale_currency_id.id,
                    'sale_currency_id': self.sale_currency_id.id,
                    'sale_price': self.amount_sale,
                    'cost_price': self.amount_cost,
                    'destination_location_id': self.port_id.id,
                    'qty': 1,
                    'sale_id': so,
                    'transport_operator': self.shipment_number.transport_operator.id,
                })
            elif self.expense_service_type == 'clearance':
                self.shipment_number.clearance_check = True
                freight_lines = self.env['freight.clearance.line'].search(
                    [('shipment_id', '=', self.shipment_number.id)])
                so = False
                if freight_lines:
                    line = freight_lines.filtered(lambda l: l.sale_id.currency_id == self.sale_currency_id and l.customer_id == self.customer_id)
                    if line:
                        so = line.sale_id
                    if so:
                        so.order_line = [(0, 0, {
                            'product_id': self.product_id.id,
                            'name': self.product_id.name,
                            'product_uom_qty': 1,
                            'currency_id': self.sale_currency_id.id,
                            'price_unit': self.amount_sale,
                        })]
                        so = so.id
                self.env['freight.clearance.line'].create({
                    'shipment_id': self.shipment_number.id,
                    'product_id': self.product_id.id,
                    'clearance_company': self.clearance_company.id,
                    'customer_id': self.customer_id.id,
                    'currency_id': self.sale_currency_id.id,
                    'sale_currency_id': self.sale_currency_id.id,
                    'price': self.amount_sale,
                    'cost': self.amount_cost,
                    'destination_location_id': self.port_id.id,
                    'qty': 1,
                    'sale_id': so,
                    'clearance_operator': self.shipment_number.clearance_operator.id,
                })
            elif self.expense_service_type == 'transit':
                self.shipment_number.transit_check = True
                freight_lines = self.env['freight.transit.line'].search(
                    [('shipment_id', '=', self.shipment_number.id)])
                so = False
                if freight_lines:
                    line = freight_lines.filtered(lambda l: l.sale_id.currency_id == self.sale_currency_id and l.customer_id == self.customer_id)
                    if line:
                        so = line.sale_id
                    if so:
                        so.order_line = [(0, 0, {
                            'product_id': self.product_id.id,
                            'name': self.product_id.name,
                            'product_uom_qty': 1,
                            'currency_id': self.sale_currency_id.id,
                            'price_unit': self.amount_sale,
                        })]
                        so = so.id
                self.env['freight.transit.line'].create({
                    'shipment_id': self.shipment_number.id,
                    'product_id': self.product_id.id,
                    'currency_id': self.sale_currency_id.id,
                    'final_amount': self.amount_sale,
                    'amount': self.amount_cost,
                    'qty': 1,
                    'sale_id': so,
                    'transit_operator': self.shipment_number.transit_operator.id,
                })
            elif self.expense_service_type == 'warehousing':
                self.shipment_number.warehousing_check = True
                freight_lines = self.env['freight.transit.line'].search(
                    [('shipment_id', '=', self.shipment_number.id)])
                so = False
                if freight_lines:
                    line = freight_lines.filtered(lambda l: l.sale_id.currency_id == self.sale_currency_id)
                    if line:
                        so = line.sale_id
                    if so:
                        so.order_line = [(0, 0, {
                            'product_id': self.product_id.id,
                            'name': self.product_id.name,
                            'product_uom_qty': 1,
                            'currency_id': self.sale_currency_id.id,
                            'price_unit': self.amount_sale,
                        })]
                        so = so.id
                self.env['freight.warehouse.line'].create({
                    'shipment_id': self.shipment_number.id,
                    'product_id': self.product_id.id,
                    'currency_id': self.sale_currency_id.id,
                    'amount': self.amount_sale,
                    'qty': 1,
                    'sale_id': so,
                    'warehousing_operator': self.shipment_number.warehousing_operator.id,
                })
            else:
                raise ValidationError('You must select service before approve')

    @api.onchange('console_id')
    def onchange_console_id(self):
        if self.console_id:
            self.master = self.console_id.master
            self.housing = self.console_id.housing
