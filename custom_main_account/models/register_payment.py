from odoo import models, fields, api,_, Command

from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    pre_payment = fields.Boolean()
    allocate = fields.Boolean(copy=False,)
    normal_transaction = fields.Boolean()
    normal_account = fields.Many2one('account.account', string='Account')
    normal_account_group_id = fields.Many2one('account.group', tracking=True, readonly=False, string='Main Account',
                                              help="Account prefixes can determine account groups.")
    normal_analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', )
    residual_amount = fields.Monetary(string='Residual Amount', copy=False,compute='_compute_residual_amount', store=True)
    allocated_amount = fields.Monetary(copy=False,string='Allocated Amount')

    

    @api.depends('amount', 'allocated_amount')
    def _compute_residual_amount(self):
        """
        Compute the residual amount based on the payment amount and the allocated amount.
        """
        for record in self:
            if record.allocated_amount:
                # Subtract allocated amount from the payment amount if allocated
                record.residual_amount = record.amount - record.allocated_amount
            else:
                # Default residual amount to payment amount
                record.residual_amount = record.amount

    def _get_counterpart_account(self):
        """
        Return the counterpart account to use for the payment move.
        If the payment is a prepayment, use the prepayment account instead of the receivable/payable account.
        """
        self.ensure_one()

        # Handle prepayment logic
        if self.pre_payment:
            prepayment_account = False
            if  self.payment_type == 'inbound':
                prepayment_account = self.partner_id.with_company(
                    self.company_id).pre_payment_property_account_receivable_id
            if  self.payment_type == 'outbound':
                prepayment_account = self.partner_id.with_company(
                    self.company_id).pre_payment_property_account_payable_id
            if not prepayment_account:
                raise UserError(_('Prepayment account not found. Please configure the prepayment account for the partner.'))
            return prepayment_account.id

        # Handle normal transaction logic
        elif self.normal_transaction:
            normal_transaction_account = self.normal_account
            if not normal_transaction_account:
                raise UserError(_('Normal transaction account not found. Please configure the normal account.'))
            return normal_transaction_account.id

        # Fall back to the default behavior if neither prepayment nor normal_transaction
        return super(AccountPayment, self)._get_counterpart_account()

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        """
        Prepare the default values for the move lines.
        Override this to use the prepayment account when the payment is a prepayment or
        normal transaction account when applicable.
        """
        self.ensure_one()

        # Call the parent method to get the default values
        line_vals_list = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals)
        # Modify account ID based on payment type
        if self.pre_payment or self.normal_transaction:
            counterpart_account = self._get_counterpart_account()


            for line_vals in line_vals_list:
                # Fetch the account record based on the account ID in line_vals
                account = self.env['account.account'].browse(line_vals['account_id'])

                # For normal transactions, check if the payment is inbound or outbound
                if self.normal_transaction:
                    if self.normal_analytic_account_id:
                        analytic_account_id = self.normal_analytic_account_id
                        analytic_distribution = {str(analytic_account_id.id): 100.00}

                    if self.payment_type == 'inbound' and line_vals['credit'] > 0:
                        # Replace account_id for credit lines in inbound payments
                        if line_vals['account_id'] != self.normal_account:
                            line_vals['account_id'] = counterpart_account
                            if self.normal_analytic_account_id:
                                line_vals['analytic_account_id'] = analytic_account_id.id
                                # line_vals['analytic_distribution'] = analytic_distribution
                    elif self.payment_type == 'outbound' and line_vals['debit'] > 0:
                        # Replace account_id for debit lines in outbound payments
                        if line_vals['account_id'] != self.normal_account:
                            line_vals['account_id'] = counterpart_account
                            if self.normal_analytic_account_id:
                                line_vals['analytic_account_id'] = analytic_account_id.id
                                # line_vals['analytic_distribution'] = analytic_distribution

                # For prepayments, replace the receivable or payable account for the partner
                if self.pre_payment and self.partner_id:
                    if line_vals['account_id'] == self.partner_id.property_account_receivable_id.id:
                        line_vals['account_id'] = counterpart_account
                    elif line_vals['account_id'] == self.partner_id.property_account_payable_id.id:
                        line_vals['account_id'] = counterpart_account

        return line_vals_list


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    prepayment_payments = fields.Many2many(
        'account.payment',
        string='Prepayment Payments',
        compute='_compute_prepayment_payments',readonly=False
    )
    prepayment_details_ids = fields.Many2many(
        'account.prepayment.details',
        'rel_prepayment_details_ids',
        string='Prepayment Details',
        compute='_compute_prepayment_details',
        readonly=False,
        store=True
    )

    @api.depends('amount')
    def _compute_prepayment_details(self):
        for record in self:
            partner = record.partner_id

            prepayments = record.env['account.payment'].search([
                ('partner_id', '=', partner.id),
                ('pre_payment', '=', True),
                ('allocate', '=', False),
                # ('amount_residual', '!=', 0),
            ])
            print(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;', prepayments)
            prepayment_details = []
            for payment in prepayments:

                print(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;',payment.date)
                currency_rate = self._get_currency_rate_on_date(payment.currency_id, payment.date)
                prepayment_detail = record.env['account.prepayment.details'].create({
                    'payment_id': payment.id,
                    'currency_rate': currency_rate,

                })
                prepayment_details.append(prepayment_detail.id)
            record.prepayment_details_ids = [(6, 0, prepayment_details)]

    def _get_currency_rate_on_date(self, currency, date):
        """Fetch the currency rate for the given currency on the specified date."""
        CurrencyRate = self.env['res.currency.rate']
        rate = CurrencyRate.search([
            ('currency_id', '=', currency.id),
            ('name', '<=', date)
        ], limit=1, order='name desc')
        return rate.inverse_company_rate if rate else 1.0

    def apply_prepayment_to_invoice(self, invoice):
        total_prepayment_amount_egp = 0
        total_allocated_invoice_amount_egp = 0
        allocated_prepayments = []

        if self.prepayment_details_ids:
            for prepayment_detail in self.prepayment_details_ids:
                if prepayment_detail.allocate:
                    payment = prepayment_detail.payment_id
                    payment.action_draft()

                    # Fetch the payment currency rate
                    payment_currency_rate = prepayment_detail.currency_rate
                    # Fetch the invoice currency rate
                    invoice_currency_rate = self._get_currency_rate_on_date(invoice.currency_id, invoice.date)

                    # Amount allocated in USD (same as prepayment amount in this case)
                    allocated_amount_usd = self.amount

                    # Convert the allocated amount to EGP at the payment rate
                    prepayment_amount_egp = allocated_amount_usd * payment_currency_rate
                    # Convert the allocated amount to EGP at the invoice rate
                    allocated_invoice_amount_egp = allocated_amount_usd * invoice_currency_rate

                    # Accumulate the total amounts in EGP
                    total_prepayment_amount_egp += prepayment_amount_egp
                    total_allocated_invoice_amount_egp += allocated_invoice_amount_egp

                    # Keep track of allocated prepayments to mark them as allocated later
                    allocated_prepayments.append(prepayment_detail)

            # Calculate the currency difference in EGP
            currency_diff_in_egp = total_allocated_invoice_amount_egp - total_prepayment_amount_egp

            if currency_diff_in_egp != 0:
                if currency_diff_in_egp > 0:
                    # Loss: debit expense account, credit receivable account
                    debit_account_id = payment.company_id.expense_currency_exchange_account_id.id
                    credit_account_id = invoice.partner_id.property_account_receivable_id.id
                else:
                    # Gain: credit income account, debit receivable account
                    debit_account_id = invoice.partner_id.property_account_receivable_id.id
                    credit_account_id = payment.company_id.income_currency_exchange_account_id.id

                # Create the journal entry for currency exchange difference
                move_vals = {
                    'move_type': 'entry',
                    'payment_id': payment.id,
                    'exchange_invoice_id': invoice.id,
                    'date': fields.Date.today(),
                    'journal_id': payment.company_id.currency_exchange_journal_id.id,
                    'ref': _('Currency Exchange Difference for Invoice %s') % invoice.name,
                    'line_ids': [
                        (0, 0, {
                            'account_id': debit_account_id,
                            'name': _('Currency Exchange Difference'),
                            'debit': abs(currency_diff_in_egp) if currency_diff_in_egp < 0 else 0.0,
                            'credit': abs(currency_diff_in_egp) if currency_diff_in_egp > 0 else 0.0,
                        }),
                        (0, 0, {
                            'account_id': credit_account_id,
                            'name': _('Currency Exchange Difference'),
                            'debit': abs(currency_diff_in_egp) if currency_diff_in_egp > 0 else 0.0,
                            'credit': abs(currency_diff_in_egp) if currency_diff_in_egp < 0 else 0.0,
                        }),
                    ]
                }
                move_id = self.env['account.move'].create(move_vals)
                move_id.sudo().write({'date': fields.Date.today()})
                # raise UserError(_(move_id.id))
                move_id.action_post()

            # Mark all prepayments as allocated and update the allocated amount
            for prepayment_detail in allocated_prepayments:
                payment = prepayment_detail.payment_id
                payment.action_draft()

                # Fetch the existing allocated amount
                pre_allocated_amount = payment.allocated_amount

                # Update allocated amount only once
                new_allocated_amount = pre_allocated_amount + self.amount
                payment.sudo().write({'allocated_amount': new_allocated_amount})
                # raise UserError(_(payment.allocated_amount))

                # Check if the residual amount is zero, mark the payment as fully allocated
                if prepayment_detail.residual_amount == 0.0:
                    payment.allocate = True

                # Post the payment again after allocation
                payment.action_post()



    # def _create_payment_vals_from_wizard(self, batch_result):
    #     payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
    #
    #     allocated_details = self.prepayment_details_ids.filtered(lambda d: d.allocate)
    #
    #     if allocated_details:
    #         earliest_payment_date = min(allocated_details.mapped('payment_date'))
    #         payment_vals['date'] = earliest_payment_date  # Set the payment date
    #
    #     return payment_vals
    #
    # def _create_payment_vals_from_batch(self, batch_result):
    #     payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_batch(batch_result)
    #
    #     allocated_details = self.prepayment_details_ids.filtered(lambda d: d.allocate)
    #
    #     if allocated_details:
    #         earliest_payment_date = min(allocated_details.mapped('payment_date'))
    #         payment_vals['date'] = earliest_payment_date  # Set the payment date
    #
    #     return payment_vals

    def _create_payments(self):
        # Get the result from the super method
        res = super(AccountPaymentRegister, self)._create_payments()

        # Handle multiple invoices from the list view
        invoice_ids = self._context.get('active_ids', [])
        invoices = self.env['account.move'].browse(invoice_ids)

        remaining_amount = self.amount  # Track the remaining amount to allocate

        # Iterate through the payment records
        for rec in self:
            for invoice in invoices:
                # Apply prepayment to the current invoice
                rec.apply_prepayment_to_invoice(invoice)

                # Recalculate the remaining amount after each invoice payment
                remaining_amount -= invoice.amount_total

                # Compare the residual amount with the remaining allocation
                # for prepayment_detail in self.prepayment_details_ids:
                #     if prepayment_detail.allocate:
                #         if prepayment_detail.residual_amount < remaining_amount:
                #             raise UserError(_('Payment Amount Exceeds Residual Amount'))

        return res


class AccountPrepaymentDetails(models.Model):
    _name = 'account.prepayment.details'
    _description = 'Prepayment Details'

    payment_id = fields.Many2one('account.payment', string='Payment', required=True)
    payment_date = fields.Date(related='payment_id.date', string='Payment Date', store=True)
    payment_amount = fields.Monetary(related='payment_id.amount', string='Payment Amount', store=True)
    residual_amount = fields.Monetary(related='payment_id.residual_amount',string='Residual Amount', store=True)
    currency_id = fields.Many2one(related='payment_id.currency_id', string='Currency', store=True)
    currency_rate = fields.Float(string='Currency Rate at Payment Date')
    allocate = fields.Boolean()
    allocated_amount = fields.Monetary(related='payment_id.allocated_amount',string='Allocated Amount')

    @api.onchange('payment_id')
    def _onchange_payment_id(self):
        if self.payment_id:
            self.currency_rate = self._get_currency_rate_on_date(self.payment_id.currency_id,
                                                                 self.payment_id.date)

    def _get_currency_rate_on_date(self, currency, date):
        """Fetch the currency rate for the given currency on the specified date."""
        CurrencyRate = self.env['res.currency.rate']
        rate = CurrencyRate.search([
            ('currency_id', '=', currency.id),
            ('name', '<=', date)
        ], limit=1, order='name desc')
        return rate.inverse_company_rate if rate else 1.0
