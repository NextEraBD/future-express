from odoo import api, fields, models


class FreightMoveType(models.Model):
    _name = 'freight.move.type'
    _description = 'Freight Move Type'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    active = fields.Boolean(default=True, string='Active')

