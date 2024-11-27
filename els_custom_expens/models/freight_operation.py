from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, date


class Freight(models.Model):
    _inherit = 'freight.operation'


