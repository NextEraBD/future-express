from odoo import models, fields, api,_
from odoo.exceptions import ValidationError,UserError

class FreightOperation(models.Model):
    _inherit = 'freight.operation'

    expenses_ids = fields.One2many('hr.cover.letter.expense', 'shipment_number', string='Expenses')
    official_ids = fields.One2many('hr.cover.letter.official', 'shipment_number', string='Official')
    employee_ids = fields.Many2many('hr.employee')
    expenses_counter = fields.Integer(compute='compute_expenses_counter')
    official_counter = fields.Integer(compute='compute_official_counter')

    claim_counter = fields.Integer(compute='compute_claim_counter')
    vendor_claim_counter = fields.Integer(compute='compute_vendor_claim_counter')
    entry_counter = fields.Integer(compute='compute_entry_counter')
    event_counter = fields.Integer(compute='compute_event_counter')
    so_counter = fields.Integer(compute='compute_so_counter')
    po_counter = fields.Integer(compute='compute_po_counter')
    total_expense_amount = fields.Float(compute="_compute_expense_amount")
    total_official_amount = fields.Float(compute="_compute_official_amount")
    claim_created = fields.Boolean(string="Claim Created", compute="_compute_invised_created",store=True)
    invised_created = fields.Boolean(string="Invised Created", compute="_compute_invised_created", store=True)
    total_sale_amount = fields.Float(string="Total Sale Amount",compute="_compute_totals")
    total_cost_amount = fields.Float(string="Total Cost Amount",compute="_compute_totals")
    total_profit_amount = fields.Float(string="Total Profit Amount",compute="_compute_totals" )

    # Fields for Expenses amounts
    total_expense_sale_amount = fields.Float(string="Total Expense Sale Amount",compute="_compute_totals" )
    total_expense_cost_amount = fields.Float(string="Total Expense Cost Amount",compute="_compute_totals")
    total_expense_profit_amount = fields.Float(string="Total Expense Profit Amount",compute="_compute_totals")

    @api.depends('official_ids.amount_sale', 'official_ids.amount_cost',
                 'expenses_ids.amount_sale', 'expenses_ids.amount_cost')
    def _compute_totals(self):
        for record in self:
            # Totals for Official IDs
            record.total_sale_amount = sum(line.amount_sale for line in record.official_ids)
            record.total_cost_amount = sum(line.amount_cost for line in record.official_ids)
            record.total_profit_amount = record.total_sale_amount - record.total_cost_amount

            # Totals for Expense IDs
            record.total_expense_sale_amount = sum(line.amount_sale for line in record.expenses_ids)
            record.total_expense_cost_amount = sum(line.amount_cost for line in record.expenses_ids)
            record.total_expense_profit_amount = record.total_expense_sale_amount - record.total_expense_cost_amount

    @api.depends('invoice_count')
    def _compute_invised_created(self):
        for record in self:
            record.invised_created = record.invoice_count > 0
            record.claim_created = record.claim_counter > 0
 
    @api.depends('expenses_ids')
    def _compute_expense_amount(self):
        for rec in self:
            rec.total_expense_amount = sum(self.expenses_ids.mapped('amount_sale'))

    @api.depends('official_ids')
    def _compute_official_amount(self):
        for rec in self:
            rec.total_official_amount = sum(self.official_ids.mapped('amount_sale'))

    def button_vendor_bills(self):
        action = super().button_vendor_bills()
        action['context']['default_weight'] = self.weight
        action['context']['default_net_weight'] = self.net_weight
        action['context']['default_source_location_id'] = self.source_location_id.id
        action['context']['default_destination_location_id'] = self.destination_location_id.id
        action['context']['default_transport'] = self.transport
        action['context']['default_ocean_shipment_type'] = self.ocean_shipment_type
        return action

    def button_customer_invoices(self):
        action = super().button_customer_invoices()
        action['context']['default_weight'] = self.weight
        action['context']['default_net_weight'] = self.net_weight
        action['context']['default_source_location_id'] = self.source_location_id.id
        action['context']['default_destination_location_id'] = self.destination_location_id.id
        action['context']['default_transport'] = self.transport
        action['context']['default_ocean_shipment_type'] = self.ocean_shipment_type

        return action
    ######################################COMPUTE FUNCTIONS################################################################################
    def compute_expenses_counter(self):
        for rec in self:
            rec.expenses_counter = self.env['hr.cover.letter.expense'].search_count([('shipment_number', '=', rec.id)])

    def compute_official_counter(self):
        for rec in self:
            rec.official_counter = self.env['hr.cover.letter.official'].search_count([('shipment_number', '=', rec.id)])


    def compute_claim_counter(self):
        for rec in self:
            rec.claim_counter = self.env['account.move'].search_count([('freight_operation_id', '=', rec.id), ('move_type','=','out_invoice'), ('is_claim','=',True)])
    def compute_vendor_claim_counter(self):
        for rec in self:
            rec.vendor_claim_counter = self.env['account.move'].search_count([('freight_operation_id', '=', rec.id), ('move_type','=','in_invoice'), ('is_claim','=',True)])

    def compute_entry_counter(self):
        for rec in self:
            rec.entry_counter = self.env['account.move'].search_count([('freight_operation_id', '=', rec.id), ('move_type','=','entry')])


    def compute_so_counter(self):
        for rec in self:
            if rec.lead_id:
                rec.so_counter = self.env['sale.order'].search_count(
                    ['|', ('freight_operation_id', '=', rec.id), ('opportunity_id', '=', rec.lead_id.id)])
            else:
                rec.so_counter = self.env['sale.order'].search_count([('freight_operation_id', '=', rec.id)])

    def compute_po_counter(self):
        for rec in self:
            if rec.lead_id:
                rec.po_counter = self.env['purchase.order'].search_count(
                    ['|', ('lead_id', '=', rec.lead_id.id), ('freight_operation_id', '=', rec.id)])
            else:
                rec.po_counter = self.env['purchase.order'].search_count(
                    [('freight_operation_id', '=', rec.id), ])

#################################################END############################################################################

#################################################ACTION METHODS###########################################################
    def action_viw_expenses(self):
        ids = self.env['hr.cover.letter.expense'].search([('shipment_number', '=', self.id)]).ids
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
            'context': {
                'default_shipment_number': self.id,
                'default_agent_id': self.agent_id.id,
                'default_master': self.master.id,
                'default_housing': self.housing,
                        }
        }

    def action_viw_official(self):
        ids = self.env['hr.cover.letter.official'].search([('shipment_number', '=', self.id)]).ids
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
            'context': {
                'default_shipment_number': self.id,
                'default_agent_id': self.agent_id.id,
                'default_housing': self.housing,
                        }
        }

    def action_view_cov_lines(self):
        ids = self.env['hr.cover.letter.line'].search([('shipment_number', '=', self.id)]).ids
        tree_view_id = self.env.ref('freight_expense.hr_cover_letter_line_tree').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cov Lines'),
            'res_model': 'hr.cover.letter.line',
            'view_type': 'list',
            'view_mode': 'list',
            'context': {'default_shipment_number':self.id},
            'views': [[tree_view_id, 'list'], [False, 'form']],
            'search_view_id': [self.env.ref('freight_expense.hr_cover_letter_line_search').id],
            'domain': [('id', 'in', ids)],
        }

    def action_view_claims(self):
        ids = self.env['account.move'].search([('freight_operation_id', '=', self.id),('move_type','=','out_invoice'),('is_claim','=',True)]).ids
        # tree_view_id = self.env.ref('freight_expense.hr_cover_letter_line_tree').id
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

    def action_view_vendor_claims(self):
        ids = self.env['account.move'].search([('freight_operation_id', '=', self.id),('move_type','=','in_invoice'),('is_claim','=',True)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('CLAIMS'),
            'res_model': 'account.move',
            'view_type': 'list',
            'view_mode': 'list',
            'context': "{'move_type':'in_invoice'}",
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids)],
        }

    def action_view_entries(self):
        ids = self.env['account.move'].search([('freight_operation_id', '=', self.id), ('move_type', '=' ,'entry')]).ids
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

    def action_view_so(self):
        if self.lead_id:
            ids = self.env['sale.order'].search(['|',('freight_operation_id', '=', self.id),('opportunity_id','=',self.lead_id.id)])
        else:
            ids = self.env['sale.order'].search([('freight_operation_id', '=', self.id)])
        for rec in ids:
            rec.freight_operation_id = self.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids.ids)],
        }

    def action_view_po(self):
        if self.lead_id:
            ids = self.env['purchase.order'].search(['|',('freight_operation_id', '=', self.id),('lead_id','=',self.lead_id.id)])
        else:
            ids = self.env['purchase.order'].search([('freight_operation_id', '=', self.id)])
        for rec in ids:
            rec.freight_operation_id = self.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('RFQ'),
            'res_model': 'purchase.order',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids.ids)],
            'context': {
                'default_freight_operation_id': self.id,

        }
        }

    '''
    date:10/05/2023
    auther:mohamed eldeeb
    description:function to create claim sale invoice for all receipt and expenses lines
    '''
    def action_create_claim(self):
            official_lines = self.env['hr.cover.letter.official'].search([('shipment_number', '=', self.id),('claim_status','!=', 'done')])
            if official_lines:
                lines = []
                for line in official_lines:
                    # raise UserError(_(official_lines))

                    # if line.claim_status != 'done':
                    #     line.claim_status = 'done'
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
                                        'analytic_account_id': line.analytic_account_id.id,
                                        'analytic_distribution': {str(line.analytic_account_id.id): 100.00},
                                        'shipment_number':line.shipment_number.id,
                                        'company_id':line.company_id.id,
                                        'product_uom_id':line.uom_id.id,
                                        'price_unit': line.amount_sale,
                                        'product_id': line.product_id.id,
                                         'tax_ids': [(6, 0, [line.tax_id.id])] if line.tax_id else False,
                                        }))

                # if self.company_id.id == 1:
                journal_id = self.env.ref('freight_expense.els_claim_customer_journal').id
                # elif self.company_id.id == 2:
                #     journal_id = self.env.ref('freight_expense.etal_claim_customer_journal').id
                claim_id = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'is_claim': True,
                    'partner_id': self.customer_id.id,
                    'company_id': self.company_id.id,
                    'journal_id': journal_id if journal_id else False,
                    # 'account_id': self.partner_id.property_account_receivable_id.id,
                    'invoice_line_ids': lines,
                    'freight_operation_id': self.id,
                    'weight': self.weight,
                    'transport': self.transport,
                    'booking_no': self.booking_no,
                    'certificate_number': self.certificate_number,
                    'certificate_date': self.certificate_date,
                    'net_weight': self.net_weight,
                    'ocean_shipment_type': self.ocean_shipment_type,
                    'source_location_id': self.source_location_id.id,
                    'destination_location_id': self.destination_location_id.id,
                })

                # self.action_create_so()
                self.action_create_journal_entries()

    def action_create_so(self):
        self.ensure_one()
        expense_lines = self.env['hr.cover.letter.expense'].search([('shipment_number', '=', self.id), ('claim_status','!=', 'done')])

        if expense_lines:
            currency_groups = expense_lines.read_group(
                domain=[('shipment_number', '=', self.id), ('claim_status','!=', 'done')],
                fields=['currency_id'],
                groupby=['currency_id'],
                lazy=False,
            )
            print(currency_groups)
            # todo end
            if currency_groups:
                for currency in currency_groups:
                    pricelist_id = self.env['product.pricelist'].search([('currency_id','=',currency.get('currency_id')[0])],limit=1).id
                    vals = {
                        'partner_id':self.customer_id.id,
                        'currency_id':currency.get('currency_id')[0],
                        'pricelist_id':pricelist_id,
                        'freight_operation_id':self.id,
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
        expense_lines = self.env['hr.cover.letter.expense'].search([('shipment_number', '=', self.id), ('claim_status','!=', 'done')])
        official_lines = self.env['hr.cover.letter.official'].search([('shipment_number', '=', self.id), ('claim_status', '!=', 'done')])
        if expense_lines or official_lines:
            if expense_lines:
                sub_account_id = expense_lines[0].product_id.sub_account_id
            elif official_lines:
                sub_account_id = official_lines[0].product_id.sub_account_id
            else:
                raise ValidationError(_('Brocking Account for the expense categury is not set. Please, set it and try again.'))
            vals = {
                'ref': self.name,
                'date': fields.Date.today(),
                'company_id': self.company_id.id,
                # 'journal_id': employee_id.journal_id.id,
                'freight_operation_id': self.id,
                'line_ids': [],
            }
            total = 0
            for line in expense_lines:
                if not line.product_id.property_account_expense_id:
                    raise ValidationError(_('Expense Account for the expense categury is not set. Please, set it and try again.'))
                amount_currency = line.taxed_amount_cost
                if line.currency_id and line.currency_id != company_currency:
                    rate = line.currency_id.rate_ids.filtered(lambda r:r.company_id == self.company_id and r.name.year == fields.Date.today().year)[0].mapped('inverse_company_rate')
                    if rate:
                        amount_currency = line.taxed_amount_cost * rate[0]
                    else:
                        raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))
                vals['line_ids'].append((0, 0, {
                    'account_id': line.product_id.property_account_expense_id.id,
                    'currency_id': line.currency_id.id,
                    'shipment_number':line.shipment_number.id,
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
                        lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year)[0].mapped(
                        'inverse_company_rate')
                    if rate:
                        amount_currency = line.taxed_amount_cost * rate[0]
                    else:
                        raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))

                vals['line_ids'].append((0, 0, {
                    'account_id': line.product_id.property_account_expense_id.id,

                    'currency_id': line.currency_id.id,
                    'shipment_number': line.shipment_number.id,
                    'amount_currency':-line.taxed_amount_cost,
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

    def action_ready_to_close(self):
        invoices = self.env['account.move'].sudo().search(
            [('freight_operation_id', '=', self.id), ('move_type', '=', 'out_invoice'),('state','!=','post')])
        bels = self.env['account.move'].sudo().search(
            [('freight_operation_id', '=', self.id), ('move_type', '=', 'in_invoice'),('state','!=','post')])

        official_lines = self.env['hr.cover.letter.official'].search(
            [('shipment_number', '=', self.id), ('claim_status', '!=', 'done')])
        expense_lines = self.env['hr.cover.letter.expense'].search(
            [('shipment_number', '=', self.id), ('claim_status', '!=', 'done')])
        if not invoices and not bels and not official_lines and not expense_lines:
            if self.direction == 'import':
                self.stage_id_import = self.env.ref('freight.ready_freight_import_stage').id
                self.send_activity()
            elif self.direction == 'export':
                self.stage_id_export = self.env.ref('freight.ready_freight_export_stage').id
                self.send_activity()


    def send_activity_customer_service(self):
        for rec in self:
            if rec.customer_service_id:
                if rec.freight_event_state.name =='Done':
                    self.env['mail.activity'].create({
                        'summary': 'Freight Event State Is Done ',
                        'activity_type_id': self.env.ref('mail.mail_activity_data_email').id,
                        'res_model_id': self.env['ir.model']._get(rec._name).id,
                        'res_id': rec.id,
                        'user_id': rec.customer_service_id.id
                    })
                if rec.transport_event_state.name =='Done':
                    self.env['mail.activity'].create({
                        'summary': 'Transport Event State Is Done',
                        'activity_type_id': self.env.ref('mail.mail_activity_data_email').id,
                        'res_model_id': self.env['ir.model']._get(rec._name).id,
                        'res_id': rec.id,
                        'user_id': rec.customer_service_id.id
                    })
                if rec.clearance_event_state.name =='Done':
                    self.env['mail.activity'].create({
                        'summary': 'Clearance Event State Is Done',
                        'activity_type_id': self.env.ref('mail.mail_activity_data_email').id,
                        'res_model_id': self.env['ir.model']._get(rec._name).id,
                        'res_id': rec.id,
                        'user_id': rec.customer_service_id.id
                    })
                if rec.transit_event_state.name =='Done':
                    self.env['mail.activity'].create({
                        'summary': 'Transit Event State Is Done',
                        'activity_type_id': self.env.ref('mail.mail_activity_data_email').id,
                        'res_model_id': self.env['ir.model']._get(rec._name).id,
                        'res_id': rec.id,
                        'user_id': rec.customer_service_id.id
                    })
                if rec.warehousing_event_state.name =='Done':
                    self.env['mail.activity'].create({
                        'summary': 'Warehousing Event State Is Done',
                        'activity_type_id': self.env.ref('mail.mail_activity_data_email').id,
                        'res_model_id': self.env['ir.model']._get(rec._name).id,
                        'res_id': rec.id,
                        'user_id': rec.customer_service_id.id
                    })

    def write(self, values):
        res = super(FreightOperation, self).write(values)
        if 'employee_ids' in values:
            for employee in self.employee_ids:
                self.send_activity(employee.user_id,'you have been assigned to this shipment')
        return res
