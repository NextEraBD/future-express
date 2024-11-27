from odoo import models, fields, api,_
from odoo.exceptions import ValidationError,UserError
from collections import defaultdict


class FreightOperation(models.Model):
    _inherit = 'freight.operation'

    @api.model_create_multi
    def default_get(self, default_fields):
        res = super(FreightOperation, self).default_get(default_fields)
        if self.env.user.branch_id:
            res.update({
                'branch_id': self.env.user.branch_id.id or False
            })
        return res

    expenses_ids = fields.One2many('hr.cover.letter.expense', 'shipment_number', string='Expenses')
    employee_ids = fields.Many2many('hr.employee')
    expenses_counter = fields.Integer(compute='compute_expenses_counter')
    official_counter = fields.Integer(compute='compute_official_counter')

    cov_line_counter = fields.Integer(compute='compute_cov_line_counter')
    claim_counter = fields.Integer(compute='compute_claim_counter')
    entry_counter = fields.Integer(compute='compute_entry_counter')
    event_counter = fields.Integer(compute='compute_event_counter')
    so_counter = fields.Integer(compute='compute_so_counter')
    po_counter = fields.Integer(compute='compute_po_counter')
    branch_id = fields.Many2one('res.branch', string='Branch')
    freight_event_state = fields.Many2one('els.event.state', domain=[('operator_service', '=', 'freight')])
    transport_event_state = fields.Many2one('els.event.state', domain=[('operator_service', '=', 'transportation')])
    clearance_event_state = fields.Many2one('els.event.state', domain=[('operator_service', '=', 'clearance')])
    transit_event_state = fields.Many2one('els.event.state', domain=[('operator_service', '=', 'transit')])
    warehousing_event_state = fields.Many2one('els.event.state', domain=[('operator_service', '=', 'warehousing')])

    freight_event_date = fields.Date('Freight Date')
    transport_event_date = fields.Date('Transport Date')
    clearance_event_date = fields.Date('Clearance Date')
    transit_event_date = fields.Date('Wransit Date')
    warehousing_event_date = fields.Date('Warehousing Date')
    total_expense_amount = fields.Float()
    total_official_amount = fields.Float()
    claim_created = fields.Boolean(string="Claim Created", compute="_compute_invised_created",store=True)
    invised_created = fields.Boolean(string="Invised Created", compute="_compute_invised_created", store=True)
    total_sale_amount = fields.Float(string="Total Sale Amount")
    total_cost_amount = fields.Float(string="Total Cost Amount")
    total_profit_amount = fields.Float(string="Total Profit Amount")

    # Fields for Expenses amounts
    total_expense_sale_amount = fields.Float(string="Total Expense Sale Amount",)
    total_expense_cost_amount = fields.Float(string="Total Expense Cost Amount",)
    total_expense_profit_amount = fields.Float(string="Total Expense Profit Amount",)

    # @api.depends('official_ids.amount_sale', 'official_ids.amount_cost',
    #              'expenses_ids.amount_sale', 'expenses_ids.amount_cost')
    # def _compute_totals(self):
    #     for record in self:
    #         # Totals for Official IDs
    #         record.total_sale_amount = sum(line.amount_sale for line in record.official_ids)
    #         record.total_cost_amount = sum(line.amount_cost for line in record.official_ids)
    #         record.total_profit_amount = record.total_sale_amount - record.total_cost_amount

    #         # Totals for Expense IDs
    #         record.total_expense_sale_amount = sum(line.amount_sale for line in record.expenses_ids)
    #         record.total_expense_cost_amount = sum(line.amount_cost for line in record.expenses_ids)
    #         record.total_expense_profit_amount = record.total_expense_sale_amount - record.total_expense_cost_amount

    @api.depends('invoice_count')
    def _compute_invised_created(self):
        for record in self:
            record.invised_created = record.invoice_count > 0
            record.claim_created = record.claim_counter > 0
   # @api.depends('expenses_ids')
   #  def _compute_expense_amount(self):
   #      for rec in self:
   #          rec.total_expense_amount = sum(self.expenses_ids.mapped('amount_sale'))

   #  @api.depends('official_ids')
   #  def _compute_official_amount(self):
   #      for rec in self:
   #          rec.total_official_amount = sum(self.official_ids.mapped('amount_sale'))


    ######################################COMPUTE FUNCTIONS################################################################################
    def compute_expenses_counter(self):
        for rec in self:
            rec.expenses_counter = self.env['hr.cover.letter.expense'].search_count([('shipment_number', '=', rec.id),('cover_state', 'not in', ['draft'])])

    def compute_official_counter(self):
        for rec in self:
            rec.official_counter = self.env['hr.cover.letter.official'].search_count([('shipment_number', '=', rec.id),('cover_state', 'not in', ['draft'])])

    def compute_cov_line_counter(self):
        for rec in self:
            rec.cov_line_counter = self.env['hr.cover.letter.line'].search_count([('shipment_number', '=', rec.id),('state', '=', 'approved')])

    def compute_claim_counter(self):
        for rec in self:
            rec.claim_counter = self.env['account.move'].search_count([('freight_operation_id', '=', rec.id), ('move_type','=','out_invoice'), ('is_claim','=',True)])

    def compute_entry_counter(self):
        for rec in self:
            rec.entry_counter = self.env['account.move'].search_count([('freight_operation_id', '=', rec.id), ('move_type','=','entry')])

    def compute_event_counter(self):
        for rec in self:
            rec.event_counter = self.env['els.events'].search_count([('freight_operation_id', '=', rec.id), ('state','=','submit')])



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
        ids = self.env['hr.cover.letter.expense'].search([('shipment_number', '=', self.id), ('cover_state', '!=', 'draft')]).ids
        tree_view_id = self.env.ref('custom_hr_expense.hr_cover_letter_exp_tree').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Expenses'),
            'res_model': 'hr.cover.letter.expense',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[tree_view_id, 'list'], [False, 'form']],
            'search_view_id': [self.env.ref('custom_hr_expense.hr_cover_letter_expense_search').id],
            'domain': [('id', 'in', ids)],
            'context': {'default_shipment_number': self.id}
        }

    def action_viw_official(self):
        ids = self.env['hr.cover.letter.official'].search([('shipment_number', '=', self.id),('cover_state', 'not in', ['draft'])]).ids
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
            'context': {'default_shipment_number':self.id}
        }

    def action_view_cov_lines(self):
        ids = self.env['hr.cover.letter.line'].search([('shipment_number', '=', self.id)]).ids
        tree_view_id = self.env.ref('custom_hr_expense.hr_cover_letter_line_tree').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cov Lines'),
            'res_model': 'hr.cover.letter.line',
            'view_type': 'list',
            'view_mode': 'list',
            'context': {'default_shipment_number':self.id},
            'views': [[tree_view_id, 'list'], [False, 'form']],
            'search_view_id': [self.env.ref('custom_hr_expense.hr_cover_letter_line_search').id],
            'domain': [('id', 'in', ids)],
        }

    def action_view_claims(self):
        ids = self.env['account.move'].search([('freight_operation_id', '=', self.id),('move_type','=','out_invoice'),('is_claim','=',True)]).ids
        # tree_view_id = self.env.ref('custom_hr_expense.hr_cover_letter_line_tree').id
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
    def action_view_event(self):
        ids = self.env['els.events'].search([('freight_operation_id', '=', self.id), ('state', '=' ,'submit')]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Events'),
            'res_model': 'els.events',
            'view_type': 'list',
            'view_mode': 'list',
            'context': {'move_type':'entry','default_freight_operation_id':self.id},
            'views': [[False, 'list']],
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
        # Group the official lines by currency
        official_lines = self.env['hr.cover.letter.official'].search(
            [('shipment_number', '=', self.id), ('claim_status', '!=', 'done')])

        if official_lines:
            currency_grouped_lines = defaultdict(list)

            # Group lines by currency
            for line in official_lines:
                currency = line.currency_id or line.company_id.currency_id  # Use line's currency or company's currency as fallback
                currency_grouped_lines[currency].append(line)

            for currency, lines in currency_grouped_lines.items():
                invoice_lines = []
                for line in lines:
                    if line.product_id.property_account_income_id.id:
                        income_account = line.product_id.property_account_income_id.id
                    elif line.product_id.categ_id.property_account_income_categ_id.id:
                        income_account = line.product_id.categ_id.property_account_income_categ_id.id
                    else:
                        raise UserError(_('Please define income '
                                          'account for this product: "%s" (id:%d).')
                                        % (line.product_id.name, line.product_id.id))

                    invoice_lines.append((0, 0, {
                        'name': line.product_id.name,
                        'account_id': income_account,
                        'quantity': 1,
                        'shipment_number': line.shipment_number.id,
                        'company_id': line.company_id.id,
                        'branch_id': line.branch_id.id,
                        'product_uom_id': line.uom_id.id,
                        'price_unit': line.amount_sale,
                        'product_id': line.product_id.id,
                        'tax_ids': [(6, 0, [line.tax_id.id])] if line.tax_id else False,
                    }))

                # Create claim (invoice) for each currency group
                journal_id = self.env.ref('custom_hr_expense.els_claim_customer_journal_custom').id

                claim_id = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'is_claim': True,
                    'partner_id': self.customer_id.id,
                    'company_id': self.company_id.id,
                    'branch_id': self.branch_id.id,
                    'journal_id': journal_id if journal_id else False,
                    'currency_id': currency.id,
                    'invoice_line_ids': invoice_lines,
                    'freight_operation_id': self.id,
                    'weight': self.weight,
                    'transport': self.transport,
                    'net_weight': self.net_weight,
                    'ocean_shipment_type': self.ocean_shipment_type,
                    'source_location_id': self.source_location_id.id,
                    'destination_location_id': self.destination_location_id.id,
                })

            # self.action_create_journal_entries()

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
                                # 'branch_id':line.branch_id.id,
                                'product_uom_qty': 1,
                                'tax_id': [(6, 0, [line.tax_id.id])] if line.tax_id else False,
                                'product_uom': line.uom_id.id if line.uom_id.id else line.product_id.uom_id.id,
                                'price_unit': line.amount_sale,

                            }))
                            # line.claim_status = 'done'
                    so = self.env['sale.order'].create(vals)


    def action_create_journal_entries(self):
        company_currency = self.company_id.currency_id
        expense_lines = self.env['hr.cover.letter.expense'].search(
            [('shipment_number', '=', self.id), ('claim_status', '!=', 'done')]
        )
        official_lines = self.env['hr.cover.letter.official'].search(
            [('shipment_number', '=', self.id), ('claim_status', '!=', 'done')]
        )

        if not expense_lines and not official_lines:
            return  # No lines to process

        # Determine sub-account
        sub_account_id = (
            expense_lines[0].employee_id.employee_account_id
            if expense_lines and expense_lines[0].employee_id
            else expense_lines[0].account_id if expense_lines
            else official_lines[0].employee_id.employee_account_id
            if official_lines and official_lines[0].employee_id
            else official_lines[0].account_id
        )
        if not sub_account_id:
            raise ValidationError(_('No valid sub-account found for the lines. Please check the setup and try again.'))

        # Group lines by currency
        lines_by_currency = {}
        for line in expense_lines:
            if not line.sale_currency_id:
                raise ValidationError(_('No Sale Currency found in Expense Line.'))
            currency = line.sale_currency_id
            if currency not in lines_by_currency:
                lines_by_currency[currency] = []
            lines_by_currency[currency].append((line, 'expense'))

        for line in official_lines:
            if not line.sale_currency_id:
                raise ValidationError(_('No Sale Currency found in Expense Line.'))
            currency = line.sale_currency_id
            if currency not in lines_by_currency:
                lines_by_currency[currency] = []
            lines_by_currency[currency].append((line, 'official'))

        # Create journal entries for each currency group
        for currency, entries in lines_by_currency.items():
            total = 0
            vals = {
                'ref': self.name,
                'date': fields.Date.today(),
                'company_id': self.company_id.id,
                'freight_operation_id': self.id,
                'currency_id': currency.id,
                'line_ids': [],
            }

            for line, line_type in entries:
                if not line.product_id.property_account_expense_id:
                    raise ValidationError(
                        _('Expense Account for the expense category is not set. Please, set it and try again.')
                    )

                amount_currency = line.taxed_amount_cost
                converted_amount = amount_currency
                if line.currency_id and line.currency_id != company_currency:
                    rate_records = line.currency_id.rate_ids.filtered(
                        lambda r: r.company_id == self.company_id and r.name.year == fields.Date.today().year
                    )
                    if rate_records:
                        rate = rate_records[0].inverse_company_rate
                        if rate:
                            converted_amount = line.taxed_amount_cost * rate
                        else:
                            raise ValidationError(_('Currency has no rate. Please, set rate for the currency first.'))
                    else:
                        raise ValidationError(_('No currency rate record found for the specified year.'))
                else:
                    amount_currency = 0  # No foreign currency difference if in company currency

                vals['line_ids'].append((0, 0, {
                    'account_id': line.product_id.property_account_expense_id.id,
                    'shipment_number': line.shipment_number.id,
                    'currency_id': currency.id,
                    'amount_currency': -line.taxed_amount_cost,
                    'credit': converted_amount,
                    'debit': 0,
                }))
                total += converted_amount
                line.claim_status = 'done'

            # Add debit line for the sub-account to balance the journal entry
            vals['line_ids'].append((0, 0, {
                'account_id': sub_account_id.id,
                'currency_id': currency.id,
                'debit': total,
                'credit': 0,
            }))

            # Create the journal entry for this currency group
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

    def write(self,values):
        res = super(FreightOperation, self).write(values)
        if 'employee_ids' in values:
            for employee in self.employee_ids:
                self.send_activity(employee.user_id,'you have been assigned to this shipment')
        return res
