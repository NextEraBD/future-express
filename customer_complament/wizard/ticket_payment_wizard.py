from odoo import fields, models, api


class TicketApprovalWizard(models.TransientModel):
    _name = 'ticket.approval.wizard'
    _description = 'Ticket Approval Wizard'

    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    debit_account_id = fields.Many2one('account.account', string='Debit Account', required=True)
    credit_account_id = fields.Many2one('account.account', string='Credit Account', required=True)

    def action_confirm(self):
        # Get the active ticket
        ticket_id = self.env.context.get('active_id')
        ticket = self.env['customer.ticket'].browse(ticket_id)

        # Prepare the values for the journal entry
        move_vals = {
            'journal_id': self.journal_id.id,
            'date': fields.Date.context_today(self),
            'ref': ticket.name,  # Reference to the ticket
            'line_ids': [
                (0, 0, {
                    'account_id': self.debit_account_id.id,
                    'name': ticket.name,
                    'debit': ticket.amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': self.credit_account_id.id,
                    'name': ticket.name,
                    'debit': 0.0,
                    'credit': ticket.amount,
                }),
            ],
        }

        # Create the journal entry
        move = self.env['account.move'].create(move_vals)
        move.post()

        # Set the ticket to 'approved' state
        ticket.write({'state': 'approved'})
        # Mark related activities as done
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'customer.ticket'),
            ('res_id', '=', ticket.id),
            ('user_id', '=', self.env.user.id),  # Optional: filter by the current user
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),# Assuming it's a To Do activity
            ('state', '=', 'active')  # Only mark active activities as done
        ])
        activities.action_done()
