from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


class Treasury(models.TransientModel):
    _name = 'treasury.manager.wizard'


    custody_id = fields.Many2one('custody.custody', 'Custody ID')


