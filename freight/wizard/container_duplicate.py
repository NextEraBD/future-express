# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class ContainerWizard(models.TransientModel):
    _name = 'container.wizard'

    number = fields.Integer(string='number')
    name = fields.Char(string='Description')
    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    lead_id = fields.Many2one('crm.lead', 'CRM Lead')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ('vas', 'Vas')]),
                                 string='Transport')
    line_id = fields.Many2one('freight.order', 'Container')
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    standard_volume = fields.Float(related='container_id.standard_volume', string='Standard Volume')
    standard_weight = fields.Float(related='container_id.standard_weight', string='Standard Weight')
    package = fields.Many2one('freight.package', 'Package')
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Operation")
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    qty = fields.Float('Quantity')
    teu = fields.Float('Teu (CBM)')

    def action_apply(self):
        container_obj = self.env['freight.order']
        products = []
        order_name = '/'
        for rec in range(self.number):
            vals = {
                'shipment_id': self.shipment_id.id,
                'container_id': self.container_id.id,
                'name': self.name,
                # 'container_no_id': self.container_no_id.id,
                'package': self.package.id,
                'type': self.type,
                'teu': self.teu,
                'transport': self.transport,
                'qty': self.qty,
            }
            container_obj.create(vals)
        return True


class ContainerCRMWizard(models.TransientModel):
    _name = 'container.lead.wizard'

    number = fields.Integer(string='number')
    name = fields.Char(string='Description')
    lead_id = fields.Many2one('crm.lead', 'CRM Lead')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ('vas', 'Vas')]),
                                 string='Transport')
    line_id = fields.Many2one('freight.order', 'Container')
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    standard_volume = fields.Float(related='container_id.standard_volume', string='Standard Volume')
    standard_weight = fields.Float(related='container_id.standard_weight', string='Standard Weight')
    package = fields.Many2one('freight.package', 'Package')
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Operation")
    volume = fields.Float('Volume (CBM)')
    teu = fields.Float('Teu (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    weight = fields.Float('Weight (KG)')
    qty = fields.Float('Quantity')

    def action_apply(self):
        container_obj = self.env['crm.container.line']
        products = []
        order_name = '/'
        for rec in range(self.number):
            vals = {
                'crm_id': self.lead_id.id,
                'container_id': self.container_id.id,
                'name': self.name,
                # 'container_no_id': self.container_no_id.id,
                'type': self.type,
                'teu': self.teu,
                'package': self.package.id,
                'transport': self.transport,
                'qty': self.qty,
            }
            container_obj.create(vals)
        return True

