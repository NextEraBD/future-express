# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import datetime
from odoo.osv import expression


class WayBill(models.Model):
    _name = 'way.bill'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _description = 'Way Bill'

    name = fields.Char(string="Bill Way No.", index=True, default='New')
    vehicle_no = fields.Char(string="Vehicle No.")
    card_no = fields.Char(string="Card No.")
    license_no = fields.Char(string="License No.")
    created_from = fields.Char()
    customer_id = fields.Many2one('res.partner', 'Customer')
    deriver_id = fields.Many2one('res.partner', 'Deriver')
    transport_line_id = fields.Many2one('freight.transport.line', string='Transport')
    vessel_id = fields.Many2one('freight.vessel', 'Vessel')
    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    creator = fields.Many2one('hr.employee', string='Creator', required=False,
                              default=lambda self: self.env.user.employee_id.id)
    date = fields.Date(string='Time/Date of Departure')
    expected_arrival_date = fields.Date(string="Expected Arrival Date")
    expected_arrival_hour = fields.Datetime(string="Expected Arrival Hour")
    expected_departure_date = fields.Date(string="Expected Departure Date")
    expected_departure_hour = fields.Datetime(string="Expected Departure Hour")
    delay_reason = fields.Char('Reasons of Delay if any')
    transport_ids = fields.One2many('way.bill.transport', 'way_bill_id')
    note = fields.Text(string='Note')

    shipper_id = fields.Many2one('res.partner', 'Shipper')
    consignee_id = fields.Many2one('res.partner', 'Consignee')
    agent_id = fields.Many2one('res.partner', 'Agent')
    forwarder_id = fields.Many2one('res.partner',string='Forwarder')
    notify = fields.Char(string="Notify", copy=False)
    pick_up = fields.Char(string='Pick Up')
    drop_location = fields.Char(string='Drop Location')
    type = fields.Selection([('original', 'Original'), ('copy', 'Copy')])
    freight_payable = fields.Char(string='Freight Payable')
    from_location = fields.Char(string='From')
    to_location = fields.Char(string='To')
    source_location_id = fields.Many2one('freight.port', string='Port of Import',related='transport_ids.source_location_id')
    destination_location_id = fields.Many2one('freight.port', string='Port of Export',related='transport_ids.destination_location_id')
    today_date = fields.Date(string="Date", default=fields.Date.today, readonly=True)
    notation = fields.Text(string='Notation')
    no_trucks = fields.Char(string='No. Of Trucks:')
    issued_at = fields.Char(string='Issued at:')
    issued_on = fields.Char(string='Issued On:')
    issued_No = fields.Char(string='Number Of B/L Issued')
    teems_carriage = fields.Char(string='Terms Of Carriage')


class WayBillTransport(models.Model):

    _name = 'way.bill.transport'

    way_bill_id = fields.Many2one('way.bill', string='Way Bill')
    product_id = fields.Many2one('product.product', string='Service')
    qty = fields.Float(string='Quantity', default=1.0)
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float('net Weight (KG)')
    package = fields.Many2one('freight.package', 'Package')
    name = fields.Char(string='Description')
    volume = fields.Float('Volume (CBM)')
    source_location_id = fields.Many2one('freight.port', string='Port of Loading')
    destination_location_id = fields.Many2one('freight.port', string='Port of Destination')