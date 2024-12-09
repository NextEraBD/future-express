from odoo import models, fields

class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    zone = fields.Char(string='Zone')

class ResCountry(models.Model):
    _inherit = 'res.country'

    zone = fields.Char(string='Zone')
