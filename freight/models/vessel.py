from odoo import api, fields, models


class FreightVessel(models.Model):
    _name = 'freight.vessel'
    _description = 'Freight Vessel'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    global_zone = fields.Char(string='Global Zone')
    country = fields.Many2one('res.country', 'Country')
    active = fields.Boolean(default=True, string='Active')
