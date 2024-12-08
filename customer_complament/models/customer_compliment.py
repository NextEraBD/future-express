from odoo import models, fields, api

class CustomerCompliment(models.Model):
    _name = 'customer.compliment'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add this line
    _description = 'Customer Compliment'

    @api.model
    def _group_expand_stage(self, stages, domain, order):
        return stages.search([], order=order)

    name = fields.Char(string='Serial Number', required=True, copy=False, readonly=True, index=True, default=lambda self: self.env['ir.sequence'].next_by_code('customer.compliment.serial') or 'New')
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    date_created = fields.Datetime(string='Date Created', default=fields.Datetime.now, readonly=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    number_of_operations = fields.Many2one('freight.operation', string='Operation')
    description = fields.Text(string='Description', required=True)
    feedback = fields.Text(string='Feedback')
    complaint_type_id = fields.Many2one('compliment.type', string='Compliment Type')
    police = fields.Char(string="Police")
    dead_line = fields.Date('Deadline')
    ticket_ids = fields.One2many('customer.ticket', 'compliment_id', string='Tickets')
    ticket_count = fields.Integer(string="Ticket Count", compute='_compute_ticket_count')
    stage_id = fields.Many2one('compliment.stage', string='Stage', group_expand='_group_expand_stage')
    color = fields.Integer(string='Color Index')

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        for record in self:
            record.ticket_count = len(record.ticket_ids)

    def action_view_tickets(self):
        return {
            'name': 'Related Tickets',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'customer.ticket',
            'domain': [('compliment_id', '=', self.id)],
            'context': {
                'default_compliment_id': self.id,
                'default_customer_id': self.customer_id.id,
                'default_description': self.description,
                'default_feedback': self.feedback,
                'default_complaint_type_id': self.complaint_type_id.id,
                'default_number_of_operations': self.number_of_operations.id,
                'default_police': self.police,
                'default_date_created': self.date_created,

            },
        }


class ComplimentType(models.Model):
    _name = 'compliment.type'
    _description = 'Compliment Type'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')

class ComplimentStage(models.Model):
    _name = 'compliment.stage'
    _description = 'Compliment Stage'
    _order = 'sequence'

    name = fields.Char(string='Stage Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    fold = fields.Boolean(string='Folded in Kanban', help='This stage is folded in the kanban view when there are no records in that stage.')
    is_closed = fields.Boolean(string='Is a Closed Stage', help='Tasks in this stage are considered as done/closed.')



