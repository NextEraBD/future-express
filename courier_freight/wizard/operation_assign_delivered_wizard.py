from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class OperationAssignDeliveredWizard(models.TransientModel):
    _name = 'assign.delivered.wizard'
    _description = 'Assign To Delivered Wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add this line


    operation_ids = fields.Many2many('freight.operation', string='Operations')
    user_id = fields.Many2one('res.users', string='Assigned To')

    def action_assign_to_deliver(self):
        for operation in self.operation_ids:
            operation.assigned_to_deliver = self.user_id
            operation.action_assign_to_delivered()

