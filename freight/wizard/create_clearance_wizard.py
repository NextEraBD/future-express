# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class ClearanceRfqWizard(models.TransientModel):
    _name = 'clearance.rfq.wizard'

    vendor_id = fields.Many2one('res.partner')
    clearance_line_id = fields.Many2one('crm.clearance.line')
    def action_apply(self):
        if self.clearance_line_id:
            lines_rfq = []
            lines_rfq.append((0, 0, {
                'product_id': self.clearance_line_id.product_id.id,
                'product_uom_qty': self.clearance_line_id.qty,
                'price_unit': self.clearance_line_id.cost,
            }))
            self.env['purchase.order'].create(
                {'partner_id': self.vendor_id.id,
                 'lead_id': self.clearance_line_id.crm_id.id,
                 'partner_ref': self.clearance_line_id.crm_id.name,
                 'weight': self.clearance_line_id.crm_id.weight,
                 'net_weight': self.clearance_line_id.crm_id.net_weight,
                 'source_location_id': self.clearance_line_id.crm_id.source_location_id.id,
                 'destination_location_id': self.clearance_line_id.crm_id.destination_location_id.id,
                 'transport': self.clearance_line_id.crm_id.transport,
                 'ocean_shipment_type': self.clearance_line_id.crm_id.ocean_shipment_type,
                 'order_line': lines_rfq,
                 })

