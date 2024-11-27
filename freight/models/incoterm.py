from odoo import api, fields, models


class FreightIncoterms(models.Model):
    _name = 'freight.incoterms'
    _description = 'Freight Incoterms'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name',
                       help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")
    active = fields.Boolean(default=True, string='Active')

