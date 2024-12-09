from odoo import fields, models, api

class FreightOperationDeliveredWizard(models.TransientModel):
    _name = 'freight.operation.delivered.wizard'
    _description = 'Delivered Issue Wizard'

    operation_id = fields.Many2one('freight.operation', string='Operation', required=True)
    date = fields.Date(string='Issue Date', required=True, default=fields.Date.context_today)
    stage_id = fields.Many2one('freight.local.stage.courier', string='Return To Stage', required=True)
    reason = fields.Text(string='Reason', required=True)

    def confirm(self):
        """When the user confirms the wizard, set the operation to the selected stage."""
        self.operation_id.write({
            'stage_id_local_cruise': self.stage_id.id,
        })
        return {
            'type': 'ir.actions.act_window_close',
        }

