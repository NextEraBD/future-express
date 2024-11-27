from random import randint

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError



class LeadIncoterm(models.Model):
    _name = 'lead.incoterm'
    _description = 'Lead Incoterm'

    name = fields.Char()


class LeadUpToIncoterm(models.Model):
    _name = 'lead.up_to_incoterm'
    _description = 'Lead Up to Incoterm'

    name = fields.Char()


class LeadPeriod(models.Model):
    _name = 'lead.period'
    _description = 'Lead Period'

    name = fields.Char()


class LeadTyype(models.Model):
    _name = 'lead.type'
    _description = 'Lead Type'

    name = fields.Char()


class LeadCommodity(models.Model):
    _name = 'lead.commodity'
    _description = 'Lead Commodity'

    name = fields.Char()
    sh = fields.Char(string='SH Code')



class ClearanceRatePriceContainerLine(models.Model):
    _name = 'clearance.rate.price.container.line'

    amount_from = fields.Float(string="From")
    amount_to = fields.Float(string="To")
    container_id = fields.Many2one('freight.container', string='Container Type')
    amount_sale = fields.Float(string="Amount Sale")
    amount_cost = fields.Float(string="Amount Cost")
    price_id = fields.Many2one('clearance.rate.price', string="Price")


class ClearanceRatePriceAirLine(models.Model):
    _name = 'clearance.rate.price.air.line'

    amount_from = fields.Float(string="From")
    amount_to = fields.Float(string="To")
    amount_sale = fields.Float(string="Amount Sale")
    amount_cost = fields.Float(string="Amount Cost")
    price_id = fields.Many2one('clearance.rate.price', string="Price")

class TransportRatePriceContainerLine(models.Model):
    _name = 'transport.rate.price.container.line'

    amount_from = fields.Float(string="From")
    amount_to = fields.Float(string="To")
    container_id = fields.Many2one('freight.container', string='Container Type')
    amount_sale = fields.Float(string="Amount Sale")
    amount_cost = fields.Float(string="Amount Cost")
    price_id = fields.Many2one('transport.rate.price', string="Price")


class TransportRatePriceAirLine(models.Model):
    _name = 'transport.rate.price.air.line'

    amount_from = fields.Float(string="From")
    amount_to = fields.Float(string="To")
    amount_sale = fields.Float(string="Amount Sale")
    amount_cost = fields.Float(string="Amount Cost")
    price_id = fields.Many2one('transport.rate.price', string="Price")


class ClearanceRatePrice(models.Model):
    _name = 'clearance.rate.price'
    _description = 'Clearance Rate Price'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    direction = fields.Selection(([('import', 'Import'), ('export', 'Export'),('local', 'Trans Shipment')]), required=True, string='Direction')
    product_id = fields.Many2one('product.product', string="Product")
    currency_id = fields.Many2one('res.currency', string='Currency')
    country_id = fields.Many2one('res.country', string='Country')
    city_id = fields.Many2one('res.country.state', string='City', domain="[('country_id', '=', country_id)]")
    port_id = fields.Many2one('freight.port', string="Port")
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    user_id = fields.Many2one('res.users', string="Updated By", default=lambda self: self.env.user)
    state = fields.Selection([
        ('new', 'New'),
        ('run', 'Run'),
        ('expired', 'Expired'),
        ('cancel', 'Cancel'),
        ('holding', 'Holding')], string='Status', index=True, default='new')
    is_compute = fields.Boolean(compute='compute_state')
    action = fields.Selection([
        ('cancel', 'Cancel'),
        ('holding', 'Holding')], string='Action')
    remaining_days = fields.Float(string="Rate Expiration days", compute='compute_remaining_days')
    agent_id = fields.Many2one('res.partner', string="Agent")
    amount_cost = fields.Float(string="Amount cost")
    amount_sale = fields.Float(string="Amount Sale")
    amount_outside_cost = fields.Float(string="Cost Outside Port")
    amount_outside_sale = fields.Float(string="Sale Outside Port")
    other_air_sale = fields.Float(string="Other Air Sale")
    other_kg = fields.Float(string="Other Kg")
    other_container_sale = fields.Float(string="Other Container Sale")
    other_container = fields.Float()
    other_ocean_sale = fields.Float(string="Other Ocean Sale")
    container_id = fields.Many2one('freight.container', string='Container Type')
    company_id = fields.Many2one('res.company', required=True,  default=lambda self: self.env.company)
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')]),
                                 string='Activity')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')

    package = fields.Many2one('freight.package', 'Package')
    truck_type_id = fields.Many2one('truck.type')
    price_air_ids = fields.One2many('clearance.rate.price.air.line', 'price_id')
    price_ocean_ids = fields.One2many('clearance.rate.price.container.line', 'price_id')
    this_ocean_fcl = fields.Boolean(compute='compute_this_ocean_fcl')
    this_air_clear = fields.Boolean(compute='compute_this_air_clear')
    expense = fields.Boolean()
    inside_outside = fields.Boolean(default=True)
    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id.cover_letter_type:
            self.expense = True
        else:
            self.expense = False

    @api.depends('transport', 'ocean_shipment_type')
    def compute_this_ocean_fcl(self):
        for rec in self:
            rec.this_ocean_fcl = False
            if rec.transport == 'ocean' and rec.ocean_shipment_type == 'fcl':
                rec.this_ocean_fcl = True
            else:
                rec.this_ocean_fcl = False

    @api.depends('transport')
    def compute_this_air_clear(self):
        for rec in self:
            rec.this_air_clear = False
            if rec.transport == 'air':

                rec.this_air_clear = True
            else:
                rec.this_air_clear = False

    @api.depends('date_from', 'date_to', 'remaining_days', 'action')
    def compute_state(self):
        for rec in self:
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
                rec.is_compute = False

    @api.model
    def search_contracts_clearance(self, operator, value):
        today = fields.Date.today()

        expired_contracts = self.search([
            ('state', '=', 'expired'),
            ('action', 'not in', ['cancel', 'holding'])
        ])

        running_contracts = self.search([
            ('state', '=', 'run'),
            ('action', 'not in', ['cancel', 'holding'])
        ])

        if value == 'expired':
            return expired_contracts
        elif value == 'running':
            return running_contracts
        else:
            return self


    @api.constrains('date_to', 'date_from')
    def check_dates(self):
        if self.date_from:
            if self.date_from > self.date_to:
                raise ValidationError(_("you must enter EndDate after FromDate"))

    @api.depends('date_from', 'date_to')
    def compute_remaining_days(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                days = (rec.date_to - rec.date_from).days
                rec.remaining_days = days
            else:
                rec.remaining_days = 0.0


class TransportRatePrice(models.Model):
    _name = 'transport.rate.price'
    _description = 'Transport Rate Price'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    product_id = fields.Many2one('product.product', string="Product")
    currency_id = fields.Many2one('res.currency', string='Currency')
    country_id = fields.Many2one('res.country', string='Country')
    city_id = fields.Many2one('res.country.state', string='City', domain="[('country_id', '=', country_id)]")
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    user_id = fields.Many2one('res.users', string="Updated By", default=lambda self: self.env.user)
    state = fields.Selection([
        ('new', 'New'),
        ('run', 'Run'),
        ('expired', 'Expired'),
        ('cancel', 'Cancel'),
        ('holding', 'Holding')], string='Status', index=True, readonly=True, default='new',)
    is_compute = fields.Boolean(compute='compute_state')
    action = fields.Selection([
        ('cancel', 'Cancel'),
        ('holding', 'Holding')], string='Action')
    remaining_days = fields.Float(string="Rate Expiration days", compute='compute_remaining_days', store=True)
    agent_id = fields.Many2one('res.partner', string="Agent")
    amount_cost = fields.Float(string="Amount cost")
    amount_sale = fields.Float(string="Amount Sale")
    source_location_id = fields.Many2one('freight.port', 'Port of Loading')
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge')
    container_id = fields.Many2one('freight.container', string='Container Type')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')]),
                                 string='Activity')
    package = fields.Many2one('freight.package', 'Package')
    truck_type_id = fields.Many2one('truck.type')
    truck_no = fields.Char('Truck NO.')
    other_air_sale = fields.Float(string="Other Air Sale")
    other_kg = fields.Float(string="Other Kg")
    other_container_sale = fields.Float(string="Other Container Sale")
    other_container = fields.Float()
    other_ocean_sale = fields.Float(string="Other Ocean Sale")
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')
    price_air_ids = fields.One2many('transport.rate.price.air.line', 'price_id')
    price_ocean_ids = fields.One2many('transport.rate.price.container.line', 'price_id')
    this_ocean_fcl = fields.Boolean(compute='compute_this_ocean_fcl')
    this_air_clear = fields.Boolean(compute='compute_this_air_clear')
    direction = fields.Selection(([('import', 'Import'), ('export', 'Export'),('local', 'Trans Shipment')]), required=True, string='Direction')

    @api.depends('transport', 'ocean_shipment_type')
    def compute_this_ocean_fcl(self):
        for rec in self:
            rec.this_ocean_fcl = False
            if rec.transport == 'ocean' and rec.ocean_shipment_type == 'fcl':
                rec.this_ocean_fcl = True
            else:
                rec.this_ocean_fcl = False

    @api.depends('transport')
    def compute_this_air_clear(self):
        for rec in self:
            rec.this_air_clear = False
            if rec.transport == 'air':

                rec.this_air_clear = True
            else:
                rec.this_air_clear = False

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
                rec.is_compute = False


    @api.model
    def search_contracts_transport(self, operator, value):
        today = fields.Date.today()

        expired_contracts = self.search([
            ('date_to', '<', today),
            ('action', 'not in', ['cancel', 'holding'])
        ])

        running_contracts = self.search([
            ('date_from', '<=', today),
            ('date_to', '>=', today),
            ('action', 'not in', ['cancel', 'holding'])
        ])
        if value == 'expired':
            return expired_contracts
        elif value == 'running':
            return running_contracts
        else:
            return self

    @api.constrains('date_to', 'date_from')
    def check_dates(self):
        if self.date_from:
            if self.date_from > self.date_to:
                raise ValidationError(_("you must enter EndDate after FromDate"))

class ClearanceCRMPriceContainerLine(models.Model):
    _name = 'clearance.crm.price.container.line'

    amount_from = fields.Float(string="From")
    amount_to = fields.Float(string="To")
    container_id = fields.Many2one('freight.container', string='Container Type')
    amount_sale = fields.Float(string="Amount Sale")
    lead_id = fields.Many2one('crm.lead', string="Lead")


class ClearanceCRMPriceAirLine(models.Model):
    _name = 'clearance.crm.price.air.line'

    amount_from = fields.Float(string="From")
    amount_to = fields.Float(string="To")
    amount_sale = fields.Float(string="Amount Sale")
    lead_id = fields.Many2one('crm.lead', string="Lead")

class TruckType(models.Model):
    _name = 'truck.type'
    _description = 'Truck Type'

    name = fields.Char()
    max_weight = fields.Float('Max Weight')
    max_volume = fields.Float('Max volume')
