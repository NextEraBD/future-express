from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class OperationWizard(models.TransientModel):
    _name = 'assign.operation.wizard'
    _description = 'Assign To Pick Wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add this line


    operation_ids = fields.Many2many('freight.operation', string='Operations')
    user_id = fields.Many2one('res.users', string='Assigned To')

    def action_assign_to_pick(self):
        for operation in self.operation_ids:
            operation.assigned_to = self.user_id
            operation.action_assign_to_pick()

