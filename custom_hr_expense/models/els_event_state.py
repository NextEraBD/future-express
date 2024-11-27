import json

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class ELSeventState(models.Model):
    _name = 'els.event.state'
    _description = "Events State"
    _order = "id desc"

    name = fields.Char()
    operator_service = fields.Selection(
        [('freight', 'Freight'), ('clearance', 'Clearance'), ('transportation', 'Transportation')
            , ('transit', 'Transit'), ('warehousing', 'Warehousing')],string='Service')

    operator_service_id = fields.Many2many('event.state.type')