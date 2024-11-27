from odoo import models,fields,api
from odoo.exceptions import UserError


class Stage(models.Model):
    _inherit = 'crm.stage'

    order = fields.Integer()
    is_proposition = fields.Boolean()
    is_pricing = fields.Boolean()
    is_ready = fields.Boolean()


class VasShipmentStage(models.Model):
    _name = 'freight.local.stage'
    _description = 'shipment Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)


