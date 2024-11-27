# -*- coding: utf-8 -*-

from odoo import _, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    SO_TYPE_SELECTION = [
        ('operation', 'Operation'),
        ('official_receipt', 'Official Receipt')
    ]
    so_type = fields.Selection(SO_TYPE_SELECTION, string='Sales Order Type')
    freight_operation_id = fields.Many2one('freight.operation', string="Operation")
    weight = fields.Float('Gross Weight')
    net_weight = fields.Float('Net Weight')
    chargeable_weight = fields.Float('chargeable Weight')
    volume = fields.Float('Volume (CBM)')

    source_location_id = fields.Many2one('freight.port', 'Port of Loading', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', )
    transport = fields.Selection(
        ([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ('vas', 'Vas')]),
        string='Activity')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')
    contact_id = fields.Many2one('res.partner')
    booking_no = fields.Char(string="Booking No")
    certificate_number = fields.Char('Certificate Number')
    certificate_date = fields.Date('Certificate Date')
    is_claimed = fields.Boolean()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    container_id = fields.Many2one('freight.container', 'Container Type')
    opportunity_id = fields.Many2one('crm.lead', related='order_id.opportunity_id')
    total_qty = fields.Float()
    price_for_one_container = fields.Float()
    package = fields.Many2one('freight.package', 'Package')
    container_from_to = fields.Char()
    gross_weight = fields.Float('Gross Weight (KG)')
    chargeable_weight = fields.Float('chargeable Weight')
    # freight_operation_id = fields.Many2one('freight.operation', related='order_id.freight_operation_id')
