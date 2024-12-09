from odoo import models, fields, api
from odoo.exceptions import UserError

class PaymentWizard(models.TransientModel):
    _name = 'payment.wizard'
    _description = 'Payment Wizard'

    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    bank_or_cash_account_id = fields.Many2one('account.account', string='Bank or Cash Account')
    # payment_amount = fields.Float(string='Payment Amount')

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            return {
                'domain': {
                    'bank_or_cash_account_id': [('id', 'in', self.journal_id.default_account_id.mapped('id'))]
                }
            }

    def action_confirm(self):
        self.ensure_one()
        payment_record = self.env['online.payment'].browse(self._context.get('active_id'))

        # Fetch configuration
        config = self.env['online.payment.config'].sudo().search([], limit=1)

        if not config.crm_paid_credit_account_id:
            raise UserError("Payment configuration is missing credit account information.")

        # Create journal entry
        journal_entry_vals = {
            'journal_id': self.journal_id.id,
            'date': payment_record.date,
            'ref': payment_record.description,
            'online_payment_id': payment_record.id,
            'line_ids': [
                (0, 0, {
                    'name': payment_record.description,
                    'partner_id': payment_record.partner_id.id,
                    'credit': payment_record.amount,
                    'debit': 0.0,
                    'account_id': self.bank_or_cash_account_id.id,
                }),
                (0, 0, {
                    'name': payment_record.description,
                    'partner_id': self.env.user.partner_id.id,
                    'credit': 0.0,
                    'debit': payment_record.amount,
                    'account_id': config.crm_paid_credit_account_id.id,
                }),
            ],
        }
        self.env['account.move'].create(journal_entry_vals)

        payment_record.state = 'paid'  # Update state to reflect the action taken
        return {'type': 'ir.actions.act_window_close'}
