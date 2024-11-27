from random import randint

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ClearanceRatePrice(models.Model):
    _inherit = 'clearance.rate.price'



    inside_outside = fields.Boolean(related="product_id.inside_outside")


