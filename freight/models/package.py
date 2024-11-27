from odoo import api, fields, models


class FreightPackage(models.Model):
    _name = 'freight.package'
    _description = 'Freight Package'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    container = fields.Boolean('Is Container?')
    refrigerated = fields.Boolean('Refrigerated')
    active = fields.Boolean(default=True, string='Active')
    size = fields.Float('Size')
    volume = fields.Float('Volume')
    air = fields.Boolean(string='Air')
    ocean = fields.Boolean(string='Ocean')
    land = fields.Boolean(string='Land')

