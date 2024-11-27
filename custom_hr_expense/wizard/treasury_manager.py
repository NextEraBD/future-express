from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


class Treasury(models.TransientModel):
    _name = 'treasury.manager.wizard'

    branch_id = fields.Many2one('res.branch', string='Branch')
    custody_id = fields.Many2one('custody.custody', 'Custody ID')

    def action_confirm(self):
        self.custody_id.branch_id = self.branch_id.id
