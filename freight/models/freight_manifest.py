from datetime import datetime

from odoo import api, fields, models


class FreightManifest(models.Model):
    _name = 'freight.manifest'
    _description = 'Freight Manifest'
    _rec_name = 'name'


    name = fields.Char(string='Name')
    operation_id = fields.Many2one('freight.operation')
    console_id = fields.Many2one('console.operation', 'Console Operation')

    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ('vas', 'Vas')]),
                                 string='Transport',related='operation_id.transport',store=True)

    pieces = fields.Float('Pieces')
    weight = fields.Float('Gross Weight')
    net_weight = fields.Float('Net Weight')
    weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    net_weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    chargeable_weight = fields.Float('Chargeable Weight')
    volume = fields.Float('Volume')
    shipper_id = fields.Many2one('res.partner', 'Shipper')
    consignee_id = fields.Many2one('res.partner', 'Consignee')
    agent_id = fields.Many2one('res.partner', 'Agent')
    customer_id = fields.Many2one('res.partner', 'Customer')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', )
    master = fields.Many2one('freight.master')
    housing = fields.Char()

    type = fields.Selection([('original','Original'), ('copy','Copy'), ('opportunity','Copy')])

