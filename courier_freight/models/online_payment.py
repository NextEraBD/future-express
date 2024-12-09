from odoo import models, fields, api
from odoo.exceptions import UserError


class OnlinePayment(models.Model):
    _name = 'online.payment'
    _description = 'Online Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Serial Number', required=True, copy=False, readonly=True, index=True, default=lambda self: self.env['ir.sequence'].next_by_code('online.payment.serial') or 'New')
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, default=lambda self: self.env.user.partner_id)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True,)
    amount = fields.Float(string='Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    description = fields.Text(string='Description')
    crm_lead_id = fields.Many2one('crm.lead', string='Lead', ondelete='cascade', required=False)
    freight_operation_id = fields.Many2one('freight.operation', string='Freight Operation', ondelete='cascade', required=False)
    # New fields for journal entries



    state = fields.Selection([
        ('draft', 'Draft'),
        ('create_payment', 'Create Payment'),
        ('paid', 'Paid')
    ], string='Status', readonly=True, default='draft')
    message_main_attachment_id = fields.Many2one('ir.attachment', string='Main Attachment', index=True)
    activity_ids = fields.One2many('mail.activity', 'res_id', domain=lambda self: [('res_model', '=', self._name)], auto_join=True)
    message_ids = fields.One2many('mail.message', 'res_id', domain=lambda self: [('model', '=', self._name)], auto_join=True)
    journal_id = fields.Many2one('account.journal', string='Journal')

    journal_entry_count = fields.Integer(string='Journal Entry Count', compute='_compute_journal_entry_count')

    @api.depends('journal_id')
    def _compute_journal_entry_count(self):
        for payment in self:
            payment.journal_entry_count = self.env['account.move'].search_count([('online_payment_id', '=', payment.id)])

    def action_view_journal_entries(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entries',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('online_payment_id', '=', self.id)],
            'context': {'default_online_payment_id': self.id},
        }

    def action_create_payment_custom(self):
        config = self.env['online.payment.config'].sudo().search([], limit=1)
        journal_id = config.crm_partner_journal_id.id

        if not journal_id:
            raise UserError('The CRM Partner Journal ID is not configured.')
        journal_entry_vals = {
            'journal_id': journal_id,
            'date': self.date,
            'ref': self.description,
            'online_payment_id': self.id,  # Link to the payment
            'line_ids': [
                (0, 0, {
                    'name': self.description,
                    'partner_id': self.customer_id.id,
                    'debit': 0.0,
                    'credit': self.amount,
                    'account_id': config.crm_partner_credit_account_id.id,
                }),
                (0, 0, {
                    'name': self.description,
                    'partner_id': self.partner_id.id,
                    'debit': self.amount,
                    'credit': 0.0,
                    'account_id': config.crm_partner_debit_account_id.id,
                }),
            ],
        }
        journal_entry = self.env['account.move'].create(journal_entry_vals)

        # Additional logic for creating activities and updating state
        group_account_advisor = self.env.ref('account.group_account_manager')
        if group_account_advisor:
            account_users = group_account_advisor.users
            if account_users:
                for user in account_users:
                    self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'summary': 'New Payment Created',
                        'note': f'A new payment has been created for {self.partner_id.name} with an amount of {self.amount}.',
                        'res_id': self.id,
                        'res_model_id': self.env.ref('courier_freight.model_online_payment').id,
                        'user_id': user.id,
                        'date_deadline': fields.Date.context_today(self),
                    })

        self.state = 'create_payment'  # Update state to reflect the action taken

    def action_paid(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Wizard',
            'view_mode': 'form',
            'res_model': 'payment.wizard',
            'view_id': self.env.ref('courier_freight.view_payment_wizard_form').id,
            'target': 'new',
            'context': {'active_id': self.id},
        }
    # def action_paid(self):
    #     config = self.env['online.payment.config'].sudo().browse(1)
    #     journal_entry_vals = {
    #         'journal_id': config.crm_paid_journal_id.id,
    #         'date': self.date,
    #         'ref': self.description,
    #         'line_ids': [(0, 0, {
    #             'name': self.description,
    #             'partner_id': self.partner_id.id,
    #             'debit': 0.0,
    #             'credit': self.amount,
    #             'account_id': config.crm_paid_credit_account_id.id,
    #         }),
    #         (0, 0, {
    #             'name': self.description,
    #             'partner_id': self.partner_id.id,
    #             'debit': self.amount,
    #             'credit': 0.0,
    #             'account_id': config.crm_paid_debit_account_id.id,
    #         })
    #                      ],
    #     }
    #     journal_entry = self.env['account.move'].create(journal_entry_vals)
    #     self.state = 'paid'  # Update state to reflect the action taken


class OnlinePaymentConfig(models.TransientModel):
    _name = 'online.payment.config'
    _description = 'Online Payment Configuration'
    _rec_name = 'active'  # Enables archiving by default
    _inherit = ['mail.thread', 'mail.activity.mixin']


    active = fields.Boolean(default=True)
    crm_partner_credit_account_id = fields.Many2one('account.account', string='Credit Account')
    crm_partner_debit_account_id = fields.Many2one('account.account', string='Debit Account')
    crm_partner_journal_id = fields.Many2one('account.journal', string='Journal')

    crm_paid_credit_account_id = fields.Many2one('account.account', string='Credit Account')
    crm_paid_debit_account_id = fields.Many2one('account.account', string='Debit Account')
    crm_paid_journal_id = fields.Many2one('account.journal', string='Journal')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    crm_partner_credit_account_id = fields.Many2one('account.account', store=True)
    crm_partner_debit_account_id = fields.Many2one('account.account',store=True )
    crm_partner_journal_id = fields.Many2one('account.journal',store=True)

    crm_paid_credit_account_id = fields.Many2one('account.account',store=True )
    crm_paid_debit_account_id = fields.Many2one('account.account', store=True)
    crm_paid_journal_id = fields.Many2one('account.journal',store=True)

class AccountMove(models.Model):
    _inherit = 'account.move'

    online_payment_id = fields.Many2one('online.payment', string='Online Payment', ondelete='cascade')