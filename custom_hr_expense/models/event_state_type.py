import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EventStateType(models.Model):
    _name = 'event.state.type'
    _description = "Events State Type"


    name = fields.Char()
