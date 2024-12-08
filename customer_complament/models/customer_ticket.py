from odoo import fields, models, api


class CustomerTicket(models.Model):
    _name = 'customer.ticket'
    _description = 'Customer Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add this line

    name = fields.Char(string='Serial Number', required=True, copy=False, readonly=True, index=True, default=lambda self: self.env['ir.sequence'].next_by_code('customer.ticket.serial') or 'New')
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    date_created = fields.Datetime(string='Date Created', default=fields.Datetime.now, readonly=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    number_of_operations = fields.Many2one('freight.operation', string='Operation')
    description = fields.Text(string='Description', required=True)
    complaint_type_id = fields.Many2one('compliment.type', string='Compliment Type')
    feedback = fields.Text(string='Feedback')
    amount = fields.Float(string="Amount")
    police = fields.Char(string="Police")
    compliment_id = fields.Many2one('customer.compliment', string='Compliment', ondelete='cascade')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved')
    ], string='Status', default='draft', tracking=True)

    def action_approve(self):
        return {
            'name': 'Ticket Approval',
            'type': 'ir.actions.act_window',
            'res_model': 'ticket.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_ticket_id': self.id},
        }

    def action_submit(self):
        self.state = 'submitted'
        self._create_activity_for_account_manager()

    def _create_activity_for_account_manager(self):
        account_manager_group = self.env.ref('account.group_account_manager')
        if account_manager_group:
            account_manager_users = account_manager_group.users
            for user in account_manager_users:
                self.env['mail.activity'].create({
                    'res_model_id': self.env['ir.model']._get(self._name).id,
                    'res_id': self.id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': 'Ticket Submitted for Approval',
                    'note': f'The ticket {self.name} has been submitted. Please review and approve.',
                    'user_id': user.id,
                    'date_deadline': fields.Date.today(),
                })
