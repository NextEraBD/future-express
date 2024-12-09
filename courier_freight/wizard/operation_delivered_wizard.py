from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class OperationDeliveredWizard(models.TransientModel):
    _name = 'delivered.wizard'
    _description = 'Delivered Wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add this line


    operation_ids = fields.Many2many('freight.operation', string='Operations')

    def action_deliver(self):
        for operation in self.operation_ids:
            operation.action_delivered()

