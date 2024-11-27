from odoo import models,fields,api
from datetime import timedelta


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    lead_id = fields.Many2one('crm.lead', "Opportunity", readonly=True)
    contact_id = fields.Many2one('res.partner')
    

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commodity_id = fields.Many2one('lead.commodity', 'Commodity', )
    clearance_inspection_line_ids = fields.One2many('inspection.clearance.line', 'sale_id', copy=True)

