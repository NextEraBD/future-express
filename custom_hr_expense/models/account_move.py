import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        return employee

    is_cover_letter = fields.Boolean()
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", store=True,
                                  readonly=True, tracking=True,
                                  default=_default_employee_id,
                                  check_company=True)
    cover_letter_id = fields.Many2one('hr.cover.letter', )
    custody_id = fields.Many2one('custody.custody')
    official_counter = fields.Integer(compute='compute_official_counter')
    booking_no = fields.Char(string="Booking No")

    weight = fields.Float('Gross Weight')
    net_weight = fields.Float('Net Weight')
    chargeable_weight = fields.Float('chargeable Weight')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land'), ('vas', 'Vas')]),
                                 string='Activity')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')
    contact_id = fields.Many2one('res.partner')
    is_claim = fields.Boolean()
    certificate_number = fields.Char('Certificate Number')
    certificate_date = fields.Date('Certificate Date')


    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        for move in res:
            for line in move.invoice_line_ids:
                move.cover_letter_id.move_line_ids |= line
        return res

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        for move in self:
            for line in move.invoice_line_ids:
                if line.id not in move.cover_letter_id.move_line_ids.ids:
                    move.cover_letter_id.move_line_ids |= line
        return res

    def action_viw_official(self):
        ids = self.env['hr.cover.letter.official'].search([('reference', '=', self.name)]).ids
        tree_view_id = self.env.ref('custom_hr_expense.hr_cover_letter_off_tree').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Official Receipt'),
            'res_model': 'hr.cover.letter.official',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[tree_view_id, 'list'], [False, 'form']],
            'search_view_id': [self.env.ref('custom_hr_expense.hr_cover_letter_official_search').id],
            'domain': [('id', 'in', ids)],
        }

    def compute_official_counter(self):
        for rec in self:
            rec.official_counter = self.env['hr.cover.letter.official'].search_count([('reference', '=', rec.name)])

    def action_generate(self):
        for line in self.invoice_line_ids:
            if line.tax_ids:
                tax_id = line.tax_ids[0].id
            else:
                tax_id = False
            if line.shipment_number:
                vals = {
                    'date': line.move_id.date,
                    'description': line.name,
                    'reference': line.move_id.name,
                    'company_id': line.company_id.id,
                    'shipment_number': line.shipment_number.id,
                    'product_id': line.product_id.id,
                    'currency_id': line.currency_id.id,
                    'uom_id': line.product_uom_id.id,
                    'tax_id': tax_id,
                    'taxed_amount_cost': line.price_total,
                    'amount_cost': line.price_unit
                }

                self.env['hr.cover.letter.expense'].create(vals)
                vals['type'] = 'Expense'
                self.env['hr.cover.letter.line'].create(vals)

    def action_bil_paid(self):
        company_currency = self.company_id.currency_id

        vals2 = {
            # 'currency_id': self.currency_id.id,
            'date': fields.Date.today(),
            'company_id': self.company_id.id,
            'journal_id': self.employee_id.journal_id.id,
            'employee_id': self.employee_id.id,
            'line_ids': [],
        }
        amount_currency = self.amount_total
        if self.currency_id and self.currency_id != company_currency:
            rate = self.currency_id.rate_ids.filtered(
                lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year)[
                0].mapped(
                'inverse_company_rate')
            amount_currency = self.amount_total * rate[0]

        vals2['line_ids'].append((0, 0, {
            'account_id': self.partner_id.property_account_payable_id.id,
            'partner_id': self.partner_id.id,
            # 'currency_id': self.currency_id.id,
            'amount_currency': self.amount_total,
            'debit': amount_currency,
            'credit': 0,
        }))

        vals2['line_ids'].append((0, 0, {
            'account_id': self.employee_id.employee_account_id.id,
            # 'currency_id': self.currency_id.id,
            'partner_id': self.employee_id.user_id.partner_id.id,
            'amount_currency': -self.amount_total,
            'debit': 0,
            'credit': amount_currency,
        }))

        journal_entry = self.create(vals2)
        print((journal_entry))
        self.payment_state = 'paid'

    @api.onchange('employee_id')
    def set_cover_letter_domain(self):
        if self.employee_id:
            ids = self.env['hr.cover.letter'].search([('employee_id', '=', self.employee_id.id)]).ids
            return {'domain': {'cover_letter_id': [('id', 'in', ids)]}}


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    shipment_number = fields.Many2one('freight.operation')
    shipment_number_domain = fields.Char(compute="_compute_shipment_number_domain", readonly=True, store=False, )

    @api.depends('move_id.company_id', 'move_id.employee_id')
    def _compute_shipment_number_domain(self):
        for rec in self:
            rec.shipment_number_domain = json.dumps(
                [('company_id', '=', rec.company_id.id), ('employee_ids', 'in', [rec.move_id.employee_id.id])]
            )

    # def unlink(self):
    #     for line in self:
    #         cover_line = line.move_id.cover_letter_id.move_line_ids.search([('id', '=', line.id)])
    #         cover_line.unlink()
    #     return super(AccountMoveLine,self).unlink()
