from odoo import api, fields, models


class ShipmentStage(models.Model):
    _name = 'freight.import.stage'
    _description = 'shipment Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)


class ShipmentStage(models.Model):
    _name = 'freight.export.stage'
    _description = 'shipment Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)

