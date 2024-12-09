from odoo import api, fields, models

class ImportShipmentStage(models.Model):
    _name = 'freight.import.stage.courier'
    _description = 'Import Shipment Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)


class ExportShipmentStage(models.Model):
    _name = 'freight.export.stage.courier'
    _description = 'Export Shipment Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)

class LocalShipmentStage(models.Model):
    _name = 'freight.local.stage.courier'
    _description = 'Local Shipment Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
