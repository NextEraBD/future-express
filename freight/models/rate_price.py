from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class FreightRatePrice(models.Model):
    _name = 'freight.rate.price'
    _description = 'Freight Rate Price'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    partner_id = fields.Many2one('res.partner', string="Shipping Line")
    container_type_id = fields.Many2one('product.product', string="Container Type")
    product_id = fields.Many2one('product.product', string="Product")
    freight_price = fields.Float(string="Ocean Freight")
    freight_air_price = fields.Float(string="Air Freight")
    currency_id = fields.Many2one('res.currency', string='Currency')
    country_id = fields.Many2one('res.country', string='Country')
    pol_id = fields.Many2one('freight.port', string="POL")
    pod_id = fields.Many2one('freight.port', string="POD")
    free_out_days = fields.Integer(string="Free Out (Days)")
    free_in_time = fields.Integer(string="FreeTime (Days)")
    t_time = fields.Integer(string="T.time (Days)")
    date_from = fields.Date(string='From')
    vessel_date = fields.Date()
    date_to = fields.Date(string='To')
    remaining_days = fields.Float(string="Rate Expiration", compute='compute_remaining_days', store=True)
    user_id = fields.Many2one('res.users', string="Updated By", default=lambda self: self.env.user)
    state = fields.Selection([
        ('new', 'New'),
        ('run', 'Run'),
        ('expired', 'Expired'),
        ('cancel', 'Cancel'),
        ('holding', 'Holding')], string='Status', store=True, readonly=True, default='new')
    action = fields.Selection([
        ('cancel', 'Cancel'),
        ('holding', 'Holding')], string='Action')
    active = fields.Boolean(default=True)
    agent_id = fields.Many2one('res.partner', string="Agent")
    carrier_id = fields.Many2one('res.partner', string="Carrier")
    is_shipping_line = fields.Boolean(string='Is Shipping Line')
    container_id = fields.Many2one('freight.container', string='Container Type')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ('vas', 'Vas')]),
                                 string='Activity')
    package = fields.Many2one('freight.package', 'Package')
    weight_per_kg = fields.Float(default='1', readonly=1)
    air_freight_per_kg = fields.Float('Air Freight(Kg)')
    cost_price_kg = fields.Float()
    Selling_price_kg = fields.Float()
    minimum_weight = fields.Float()
    minimum_cost_price = fields.Float()
    minimum_selling_price = fields.Float()
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Shipment Type')
    volume = fields.Float('CBM')
    is_compute = fields.Boolean(compute='compute_state')

    @api.model
    def update_state(self):
        print('JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ',)
        contracts = self.search([])
        for rec in contracts:
            if rec.date_from and rec.date_to:
                if fields.Date.today() > rec.date_to and rec.action not in ('cancel', 'holding'):
                    rec.write({'state': 'expired'})
                elif fields.Date.today() <= rec.date_to and rec.action not in ('cancel', 'holding'):
                    rec.write({'state': 'run'})
                elif rec.date_from and rec.date_to and rec.action == 'cancel':
                    rec.state = 'cancel'
                elif rec.date_from and rec.date_to and rec.action == 'holding':
                    rec.state = 'holding'
            else:
                rec.state = 'new'
        return True

    @api.depends('date_from', 'date_to')
    def compute_remaining_days(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                days = (rec.date_to - rec.date_from).days
                rec.remaining_days = days
            else:
                rec.remaining_days = 0.0

    @api.depends('date_from', 'date_to', 'remaining_days', 'action')
    def compute_state(self):
        for rec in self:
            print("Hello Computed")
            if rec.date_from and rec.date_to:
                if fields.Date.today() > rec.date_to and rec.action not in ('cancel', 'holding'):
                    rec.state = 'expired'
                    rec.is_compute = True
                elif fields.Date.today() <= rec.date_to and rec.action not in ('cancel', 'holding'):
                    rec.state = 'run'
                    rec.is_compute = True
                elif rec.date_from and rec.date_to and rec.action == 'cancel':
                    rec.state = 'cancel'
                    rec.is_compute = True
                elif rec.date_from and rec.date_to and rec.action == 'holding':
                    rec.state = 'holding'
                    rec.is_compute = True
            else:
                rec.state = 'new'
                rec.is_compute = True

    @api.constrains('date_to', 'date_from')
    def check_dates(self):
        if self.date_from:
            if self.date_from > self.date_to:
                raise ValidationError(_("you must enter EndDate after FromDate"))



