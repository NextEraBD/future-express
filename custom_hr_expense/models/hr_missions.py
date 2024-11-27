from odoo import fields, models, api

class FreightHRMissions(models.Model):
    _inherit = 'hr.missions'

    operation_id = fields.Many2one('freight.operation')

    @api.onchange('operation_id')
    def _onchange_operation_id(self):
        if self.operation_id:
            self.operation_id.employee_ids |= self.employee_id
