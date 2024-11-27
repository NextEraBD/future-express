from odoo import api, fields, models


class FreightAirline(models.Model):
    _name = 'freight.airline'
    _description = 'Freight Airline'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    icao = fields.Char(string='ICAO')
    country = fields.Many2one('res.country', 'Country')
    active = fields.Boolean(default=True, string='Active')

