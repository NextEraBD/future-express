from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
import math
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class Console(models.Model):
    _name = 'console.operation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Console'

    color = fields.Integer('Color')
    name = fields.Char('Reference', copy=False, readonly=True, default=lambda x: _('New'))
    direction = fields.Selection(([('import', 'Import'), ('export', 'Export')]), required=True, string='Direction')
    weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    pieces = fields.Float('Pieces')
    weight = fields.Float('Gross Weight', compute='compute_gross_weight')
    net_weight = fields.Float('Net Weight', compute='compute_net_weight')
    chargeable_weight = fields.Float('chargeable Weight',compute='compute_total_chargeable_weight')  # todo how to compute this field
    volume = fields.Float('Volume (CBM)', compute='compute_total_volume')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ('vas', 'Vas')]),
                                 string='Activity')
    operation = fields.Selection([('direct', 'Direct'), ('house', 'House'), ('master', 'Master')], string='Operation')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')
    inland_shipment_type = fields.Selection(([('ftl', 'FTL'), ('ltl', 'LTL')]), string='Inland Shipment Type')
    teu = fields.Float('TEU')
    cbm = fields.Float('CBM')
    frt = fields.Float('FRT')
    seal_no = fields.Char('Seal No')
    shipper_id = fields.Many2one('res.partner', 'Shipper')
    consignee_id = fields.Many2one('res.partner', 'Consignee')
    shipping_line_id = fields.Many2one('res.partner', 'Shipping Line')
    agent_id = fields.Many2one('res.partner', 'Agent')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', )
    obl = fields.Char('OBL Type', help='Original Bill Of Landing')
    voyage_no = fields.Char('Voyage No')
    vessel_id = fields.Many2one('freight.vessel', 'Vessel')
    mawb_no = fields.Char('MAWB No')
    airline_id = fields.Many2one('freight.airline', 'Airline')
    flight_no = fields.Char('Flight No')
    datetime = fields.Datetime('Arrival Date')
    truck_ref = fields.Char('CMR/RWB#/PRO#:')
    trucker = fields.Many2one('freight.trucker', 'Trucker')
    trucker_number = fields.Char('Trucker No')
    dangerous_goods = fields.Boolean('Dangerous Goods')
    dangerous_goods_notes = fields.Text('Dangerous Goods Info')
    declaration_number = fields.Char('Declaration Number')
    declaration_date = fields.Date('Declaration Date')
    date_from = fields.Date('File Creation Date', default=lambda self: fields.Date.context_today(self))
    date_end = fields.Date('File End Date')
    console_operation_ids = fields.One2many('console.operation.line', 'console_id',copy=True)
    console_freight_ids = fields.One2many('console.freight.line', 'console_id')
    console_transport_ids = fields.One2many('console.transport.line', 'console_id')
    console_package_ids = fields.One2many('console.package.line', 'console_id')
    console_container_ids = fields.One2many('console.container.line', 'console_id')
    invoice_count = fields.Float('Invoice Count', compute='_compute_invoice')
    shipment_count = fields.Float('Shipment Count', compute='_compute_shipment')
    vendor_bill_count = fields.Float('Vendor Count', compute='_compute_invoice')
    total_house = fields.Integer('Total Housing')
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.company)
    with_console = fields.Boolean()
    expenses_consul = fields.Boolean('Expenses Consul')
    expenses_amount = fields.Float('expenses Amount', compute='_compute_expense')
    freight_check = fields.Boolean(string='Freight')
    transport_check = fields.Boolean(string='Transportation')
    storage_check = fields.Boolean(string='Storage')

    rec_no = fields.Char(string="REC No.")

    # awb = fields.Many2one('freight.awb', string="AWB")
    master = fields.Many2one('freight.master')
    housing = fields.Char()

    total_frt = fields.Float(compute='compute_total_frt')

    Cut_off = fields.Datetime()
    estimated_time_departure = fields.Datetime()
    actual_time_departure = fields.Datetime()
    estimated_time_arrival = fields.Datetime()
    actual_time_arrival = fields.Datetime()
    second_agent = fields.Many2one('res.partner')
    customer_service_id = fields.Many2one('res.users', readonly=False,
                                          store=True, string='Customer Service', copy=True)
    control = fields.Selection(([('con', 'Control'), ('notcon', 'Not Control')]), string='Control')
    master_id = fields.Char(translate=True, string="Master ACID")
    distribute = fields.Boolean(copy=False)
    manifest_count = fields.Integer('manifest Count', compute='_compute_manifest_count')

    def _compute_manifest_count(self):
        for order in self:
            order.manifest_count = self.env['freight.manifest'].search_count([('console_id', '=', order.id)])

    def action_view_manifest(self):
        ids = self.env['freight.manifest'].search([('console_id', '=', self.id)])

        return {
            'type': 'ir.actions.act_window',
            'name': _('Console Manifest'),
            'res_model': 'freight.manifest',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids.ids)],
            'context': {
                'default_console_id': self.id,
            }
        }

    def action_create_manifest(self):
        for line in self.console_operation_ids:
            if line.transport == "air":
                name = self.env["ir.sequence"].next_by_code("freight.manifest.air")
            elif line.transport == "ocean":
                name = self.env["ir.sequence"].next_by_code("freight.manifest.ocean")
            else:
                name = '',
            vals = {
                'console_id': self.id,
                'operation_id': line.operation_id.id,
                'housing': name,
                'master': self.master.id,
                'shipper_id': line.shipper_id.id,
                'consignee_id': line.consignee_id.id,
                'agent_id': line.agent_id.id,
                'customer_id': line.customer_id.id,
                'source_location_id': self.source_location_id.id,
                'destination_location_id': self.destination_location_id.id,
                'pieces': self.pieces,
                'transport': line.transport,
                'weight': line.gross_weight,
                'net_weight': line.net_weight,
                'weight_type': self.weight_type,
                # 'net_weight_type': line.net_weight_type,
                'chargeable_weight': line.chargeable_weight,
                'volume': line.volume,
            }
            self.env['freight.manifest'].create(vals)



    def action_create_master_way_bill(self):
        if self.transport == "air":
            name = self.env["ir.sequence"].next_by_code("freight.way.bill.air")
        elif self.transport == "ocean":
            name = self.env["ir.sequence"].next_by_code("freight.way.bill.ocean")
        else:
            name = self.housing,
        for line in self.console_operation_ids:
            vals = {
                'console_id': self.id,
                # 'operation_id': line.operation_id.id,
                'way_bill_type': 'master',
                'housing': name,
                'master': self.master.id,
                'pieces': self.pieces,
                'weight': self.weight,
                'net_weight': line.net_weight,
                'weight_type': self.weight_type,
                # 'net_weight_type': self.net_weight_type,
                'chargeable_weight': line.chargeable_weight,
                'volume': line.volume,
                'shipper_id': self.shipper_id.id,
                'consignee_id': line.consignee_id.id,
                'agent_id': line.agent_id.id,
                'customer_id': line.customer_id.id,
                'source_location_id': self.source_location_id.id,
                'destination_location_id': self.destination_location_id.id,
                'obl': self.obl,
                'mawb_no': self.mawb_no,
                'airline_id': self.airline_id.id,
                'datetime': self.datetime,
                # 'flight_no': self.airline_id,id,
            }
        self.env['freight.way.bill'].create(vals)


    @api.depends('console_operation_ids.largest')
    def compute_total_frt(self):

        for rec in self:
            gross_weight = sum(rec.console_operation_ids.mapped('gross_weight')) / 1000
            volume = sum(rec.console_operation_ids.mapped('volume'))
            if gross_weight < 2:
                rec.total_frt = volume
            elif volume >= math.ceil(gross_weight):
                rec.total_frt = volume
            elif gross_weight > math.ceil(volume):
                rec.total_frt = sum(rec.console_operation_ids.mapped('gross_weight'))
            else:
                rec.total_frt = 0

    def check_totals(self):
        for rec in self:
            if rec.console_operation_ids:
                volume = sum(rec.console_package_ids.mapped('volume'))
                chargeable_weight = sum(rec.console_package_ids.mapped('chargeable_weight'))
                weight = sum(rec.console_package_ids.mapped('gross_weight'))
                net_weight = sum(rec.console_package_ids.mapped('net_weight'))
                if volume != rec.volume:
                    raise ValidationError(f"volume not the same in operation and package")
                if rec.transport == 'air':
                    if chargeable_weight != rec.chargeable_weight:
                        raise ValidationError(f"Chargeable Weight not the same in operation and package")
                if weight != rec.weight:
                    raise ValidationError(f"Gross Weight not the same in operation and package")
                if rec.transport != 'air':
                    if net_weight != rec.net_weight:
                        raise ValidationError(f"Net Weight not the same in operation and package")

    @api.depends('console_operation_ids.volume')
    def compute_total_volume(self):
        for rec in self:
            rec.volume = sum(self.console_operation_ids.mapped('volume'))

    @api.depends('console_operation_ids.chargeable_weight')
    def compute_total_chargeable_weight(self):
        for rec in self:
            rec.chargeable_weight = sum(self.console_operation_ids.mapped('chargeable_weight'))

    @api.depends('console_operation_ids.gross_weight')
    def compute_gross_weight(self):
        for rec in self:
            rec.weight = sum(self.console_operation_ids.mapped('gross_weight'))

    @api.depends('console_operation_ids.net_weight')
    def compute_net_weight(self):
        for rec in self:
            rec.net_weight = sum(self.console_operation_ids.mapped('net_weight'))

    @api.constrains('console_operation_ids')
    def _onchange_check_lines(self):
        if len(self.console_operation_ids) != self.total_house:
            raise ValidationError(f"number of line must be {self.total_house} ")

    @api.depends()
    def _compute_invoice(self):
        for order in self:
            order.invoice_count = self.env['account.move'].sudo().search_count(
                [('console_id', '=', order.id), ('move_type', '=', 'out_invoice')])
            order.vendor_bill_count = self.env['account.move'].sudo().search_count(
                [('console_id', '=', order.id), ('move_type', '=', 'in_invoice')])

    @api.depends()
    def _compute_shipment(self):
        for order in self:
            order.shipment_count = self.env['freight.operation'].sudo().search_count(
                [('console_id', '=', order.id)])

    @api.depends()
    def _compute_expense(self):
        for order in self:
            expenses_amounts = self.env['hr.expense'].sudo().search([('console_id', '=', order.id)])
            order.expenses_amount = 0.0
            for am in expenses_amounts:
                order.expenses_amount += am.total_amount

    @api.depends('transport')
    @api.onchange('source_location_id')
    def onchange_source_location_id(self):
        for line in self:
            if line.transport == 'air':
                return {'domain': {'source_location_id': [('air', '=', True)]}}
            elif line.transport == 'ocean':
                return {'domain': {'source_location_id': [('ocean', '=', True)]}}
            elif line.transport == 'land':
                return {'domain': {'source_location_id': [('land', '=', True)]}}

    @api.depends('transport')
    @api.onchange('destination_location_id')
    def onchange_destination_location_id(self):
        for line in self:
            if line.transport == 'air':
                return {'domain': {'destination_location_id': [('air', '=', True)]}}
            elif line.transport == 'ocean':
                return {'domain': {'destination_location_id': [('ocean', '=', True)]}}
            elif line.transport == 'land':
                return {'domain': {'destination_location_id': [('land', '=', True)]}}

    @api.model
    def create(self, vals):
        if not vals.get('name', False) or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].get('console.operation.seq') or _('New')
        res = super(Console, self).create(vals)
        return res

    def action_shipment_house_create(self):
        if len(self.console_operation_ids) == self.total_house:
            orders = self.console_operation_ids.mapped('customer_id')
            for order in orders:
                lines = []
                for rec in self.console_operation_ids.filtered(lambda x: x.customer_id == order):
                    lines.append((0, 0, {
                        'container_id': rec.container_id.id,
                        'container_no_id': rec.container_no_id.id,
                        'package': rec.package.id,
                        'name': rec.container_id.name,
                        'qty': rec.qty,
                        'type': rec.type,
                        'volume': rec.volume,
                        'gross_weight': rec.gross_weight,
                        'net_weight': rec.net_weight,

                    }))
                freight_house = self.env['freight.operation'].create({
                    'operation': 'house',
                    'transport': rec.console_id.transport,
                    'direction': rec.console_id.direction,
                    'customer_id': rec.customer_id.id,
                    'customer_service_id': rec.console_id.customer_service_id.id,
                    # 'hbl': rec.hbl,
                    # 'control': rec.console_id.control,
                    'hwb': rec.hwb,
                    'source_location_id': rec.console_id.source_location_id.id,
                    'destination_location_id': rec.console_id.destination_location_id.id,
                    'shipper_id': rec.console_id.shipper_id.id,
                    'consignee_id': rec.console_id.consignee_id.id,
                    'console_id': rec.console_id.id,
                    'company_id': rec.console_id.company_id.id,
                    'freight_orders': lines,

                })
        elif len(self.console_operation_ids) != self.total_house:
            raise ValidationError(f"number of line must be {self.total_house} ")



    def create_package(self):
        for line in self.console_operation_ids:
            console_package_ids = {
                'console_id': self.id,
                'package': line.package.id,
                'name': line.package.name,
                'qty': line.qty,
                'gross_weight': line.gross_weight,
                'chargeable_weight': line.chargeable_weight,
                'volume': line.volume,
                'net_weight': line.net_weight,
            }
            # Create the package line record
            console_package_ids = self.env['console.package.line'].create(console_package_ids)

    def action_shipment_house_create2(self):
        # self.check_totals()
        if len(self.console_operation_ids) == self.total_house:
            transport_code = ''
            direction_code = ''
            lines = []
            for line in self.console_operation_ids:
                if line.transport == 'air':
                    transport_code = 'A'
                if line.transport == 'land':
                    transport_code = 'L'
                if line.transport == 'ocean':
                    transport_code = 'O'
                # if line.vas:
                #     transport_code = 'V'
                if self.direction == 'import':
                    direction_code = 'I'
                if self.direction == 'export':
                    direction_code = 'E'
                if self.direction == 'local':
                    direction_code = 'L'
                # seq = str('console') + ('/') + str(direction_code) + ('/') + str(transport_code)
                seq = str(direction_code) + ('/') + str(transport_code) + self.env['ir.sequence'].next_by_code(
                    'operation.seq')

                if not line.checked:
                    freight_house = self.env['freight.operation'].create({
                        'operation': 'console',
                        'operation_air': 'console',
                        'transport': line.console_id.transport,

                        'customer_id': line.customer_id.id,
                        'customer_service_id': line.console_id.customer_service_id.id,
                        'name': seq,
                        'frt': line.largest,
                        'freight_check': True,
                        'source_location_id': line.console_id.source_location_id.id,
                        'destination_location_id': line.console_id.destination_location_id.id,
                        'shipper_id': line.shipper_id.id,
                        'agent_id': line.agent_id.id,
                        'consignee_id': line.consignee_id.id,
                        'console_id': line.console_id.id,
                        'company_id': line.console_id.company_id.id,
                        'weight': line.gross_weight,
                        'net_weight': line.net_weight,
                        'direction': 'import',
                        # 'storage_location': line.storage_location,
                        'control': line.control,
                        # 'storage_check': line.storage_check,
                        'chargeable_weight': line.chargeable_weight,
                        # 'flight_no': self.flight_no_ids.ids,
                        'airline_id': self.airline_id.id,
                        'master': self.master.id,
                        'housing': line.housing,
                    })
                    if line.package.id:
                        console_package_ids = {
                            'shipment_id': freight_house.id,
                            'container_id': line.container_id.id,
                            'package': line.package.id,
                            'name': line.package.name,
                            'qty': line.qty,
                            'gross_weight': line.gross_weight,
                            'charger_weight': line.chargeable_weight,
                            'volume': line.volume,
                            'net_weight': line.net_weight,
                        }
                        if console_package_ids:
                            console_package_ids = self.env['freight.package.line'].create(console_package_ids)
                    lines = {
                        'container_id': line.container_id.id,
                        'container_no_id': line.container_no_id.id,
                        'package': line.package.id,
                        'name': line.container_id.name,
                        'qty': line.qty,
                        'type': line.type,
                        'volume': line.volume,
                        'gross_weight': line.gross_weight,
                        'shipment_id': freight_house.id,
                    }
                    container_ids = self.env['freight.order'].create(lines)
                    # storage_line = {
                    #     'shipment_id': freight_house.id,
                    #     'agent_id': line.agent_id.id,
                    #     'storage_location': line.storage_location,
                    #     # Add other fields as needed
                    # }
                    # Create the storage line record
                    # storage_line_record = self.env['freight.storage.line'].create(storage_line)
                    line.checked = True
                    line.operation_id = freight_house.id
        elif len(self.console_operation_ids) != self.total_house:
            raise ValidationError(f"number of line must be {self.total_house} ")


    def button_customer_invoices(self):
        invoices = self.env['account.move'].sudo().search(
            [('console_id', '=', self.id), ('move_type', '=', 'out_invoice')])
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['context'] = {'default_console_id': self.id, 'default_move_type': 'out_invoice', }
        if len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
        return action

    def button_vendor_bills(self):
        invoices = self.env['account.move'].sudo().search(
            [('console_id', '=', self.id), ('move_type', '=', 'in_invoice')])
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        action['context'] = {'default_console_id': self.id, 'default_move_type': 'in_invoice', }
        if len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
        return action

    def button_expense(self):
        expenses = self.env['hr.expense'].sudo().search([('console_id', '=', self.id)])
        action = self.env["ir.actions.actions"]._for_xml_id("hr_expense.hr_expense_actions_my_all")
        action['context'] = {'default_console_id': self.id}
        action['domain'] = [('id', 'in', expenses.ids)]
        return action



    def action_open_shipment(self):
        """ Return the list of shipment. """
        self.ensure_one()
        operation_ids = self.env['freight.operation'].search([('console_id', '=', self.id)])
        print("'''''''''", operation_ids)
        action = {
            'name': _('Shipment'),
            'view_type': 'tree',
            'view_mode': 'list,form',
            'res_model': 'freight.operation',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'domain': [('console_id', 'in', self.ids)],
        }
        return action


class ConsoleOperationLine(models.Model):
    _name = 'console.operation.line'

    console_id = fields.Many2one('console.operation', 'Console Operation')
    operation_id = fields.Many2one('freight.operation', 'Shipment ID')
    customer_id = fields.Many2one('res.partner', 'Customer')
    seal_no = fields.Char('Seal No')
    control = fields.Selection(([('con', 'Control'), ('notcon', 'Not Control')]), string='Control',)
    transport = fields.Selection(related='console_id.transport', string='Activity')
    storage_check = fields.Boolean(related='console_id.storage_check', string='Storage')
    name = fields.Char(string='Description')
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    package = fields.Many2one('freight.package', 'Package')
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Operation")
    qty = fields.Float('Quantity')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    chargeable_weight = fields.Float('chargeable Weight (KG)')  # todo how to compute this field
    incoterm_id = fields.Many2one('lead.incoterm', 'Incoterm', )
    housing = fields.Char()
    # hwb = fields.Char(string="HWB")
    largest = fields.Float('Largest', compute='compute_largest')
    dangerous_goods = fields.Boolean('Dangerous Goods')
    class_number = fields.Char('Class Number')
    un_number = fields.Char('UN Number')
    checked = fields.Boolean()
    notify = fields.Char()
    shipper_id = fields.Many2one('res.partner')
    consignee_id = fields.Many2one('res.partner')
    agent_id = fields.Many2one('res.partner')
    second_agent_id = fields.Many2one('res.partner', 'Second Agent')
    description = fields.Text()
    way_number = fields.Char()
    storage_location = fields.Char()
    house_id = fields.Char(translate=True, string="House EC ID")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    available_container_id = fields.Many2many('freight.container', string='Container Type',
                                              compute='compute_available_container')

    @api.depends('console_id')
    def compute_available_container(self):
        for rec in self:
            rec.available_container_id = rec.console_id.console_container_ids.mapped('container_id.id')

    @api.depends('volume', 'gross_weight')
    def compute_largest(self):
        for rec in self:
            gross = math.ceil(rec.gross_weight / 100)
            if rec.gross_weight / 1000 < 2:
                rec.largest = rec.volume
            elif rec.volume >= gross:
                rec.largest = rec.volume
            elif gross > rec.volume:
                rec.largest = rec.gross_weight
            else:
                rec.largest = 0


class ConsoleFreightLine(models.Model):
    _name = 'console.freight.line'

    name = fields.Char(string='Description')
    console_id = fields.Many2one('console.operation', 'Console Operation')
    product_id = fields.Many2one('product.product', string='service')
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    currency_id = fields.Many2one('res.currency', 'Currency')
    qty = fields.Float(string='Quantity')
    price_sale = fields.Float(string='Price Sale')
    price_cost = fields.Float(string='Price Cost')
    volume = fields.Float(string='Volume (CBM)')
    gross_weight = fields.Float(string='Gross Weight (KG)')
    source_location_id = fields.Many2one('freight.port', string='Port of Loading', compute='compute_location_id')
    destination_location_id = fields.Many2one('freight.port', string='Port of Discharge', compute='compute_location_id')
    carrier_id = fields.Many2one('res.partner', string="Carrier")
    shipping_line_id = fields.Many2one('res.partner', 'Shipping Line')
    agent_id = fields.Many2one('res.partner', 'Agent')

    rates_id = fields.Many2one('freight.rate.price', string='Freight Rates')
    available_fright_rates_id = fields.Many2many('freight.rate.price', string='Freight Rates',
                                                 compute='compute_available_frights_rates')
    available_container_id = fields.Many2many('freight.container', string='Container Type',
                                              compute='compute_available_container')

    @api.depends('container_id', 'console_id', 'destination_location_id', 'source_location_id')
    def compute_available_frights_rates(self):
        for rec in self:
            self.available_fright_rates_id = self.env['freight.rate.price'].sudo().search(
                [('product_id', '=', rec.product_id.id),
                 ('container_id', '=', rec.container_id.id),
                 ('pod_id', '=', rec.destination_location_id.id),
                 ('pol_id', '=', rec.source_location_id.id),
                 ('state', '=', 'run'),
                 ]).ids
            print(self.available_fright_rates_id.ids, 'uuuuu')

    @api.depends('console_id')
    def compute_available_container(self):
        for rec in self:
            rec.available_container_id = rec.console_id.console_container_ids.mapped('container_id.id')

    @api.onchange('rates_id', 'container_id', 'product_id')
    def get_cost_price(self):
        for rec in self:
            rec.price_cost = rec.rates_id.freight_price
            rec.currency_id = rec.rates_id.currency_id.id
            if rec.rates_id.is_shipping_line == False:
                rec.carrier_id = rec.rates_id.carrier_id.id
                rec.agent_id = rec.rates_id.agent_id.id
                rec.shipping_line_id = False
            if rec.rates_id.is_shipping_line == True:
                rec.shipping_line_id = rec.rates_id.partner_id.id
                rec.carrier_id = False
                rec.agent_id = False

    @api.depends('console_id.destination_location_id', 'console_id.source_location_id', 'console_id', 'product_id')
    def compute_location_id(self):
        for line in self:
            line.destination_location_id = False
            line.source_location_id = False
            if line.console_id.freight_check:
                line.destination_location_id = line.console_id.destination_location_id.id
                line.source_location_id = line.console_id.source_location_id.id


class ConsoleTransportLine(models.Model):
    _name = 'console.transport.line'

    name = fields.Char(string='Description')
    console_id = fields.Many2one('console.operation', 'Console Operation')
    product_id = fields.Many2one('product.product', string='Service')
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    currency_id = fields.Many2one('res.currency', 'Currency')
    tracking_agent = fields.Many2one('res.partner', string='Trucking Agent')
    source_location_id = fields.Many2one('freight.port', string='Port of Loading')
    destination_location_id = fields.Many2one('freight.port', string='Port of Discharge')
    qty = fields.Float(string='Quantity')
    sale_price = fields.Float(string='Sale Price')
    cost_price = fields.Float(string='Cost Price')


class ConsolePackageLine(models.Model):
    _name = 'console.package.line'

    name = fields.Char(string='Description', )
    description = fields.Text(string='Description')
    seal_no = fields.Char('Seal No')
    transport = fields.Selection(related='console_id.transport', string='Transport')
    control = fields.Selection(([('con', 'Control'), ('notcon', 'Not Control')]), string='Control')
    console_id = fields.Many2one('console.operation', 'Console Operation')
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    package = fields.Many2one('freight.package', 'Package', required=True)
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Operation")
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float(string='Net Weight (KG)')
    qty = fields.Float('Quantity')
    harmonize = fields.Char('Harmonize')
    temperature = fields.Char('Temperature')
    vgm = fields.Char('VGM', help='Verified gross mass')
    carrier_seal = fields.Char('Carrier Seal')
    shipper_seal = fields.Char('Shipper Seal')
    reference = fields.Char('Reference')
    dangerous_goods = fields.Boolean('Dangerous Goods')
    class_number = fields.Char('Class Number')
    un_number = fields.Char('UN Number')
    Package_group = fields.Char('Packaging Group:')
    imdg_code = fields.Char('IMDG Code', help='International Maritime Dangerous Goods Code')
    flash_point = fields.Char('Flash Point')
    material_description = fields.Text('Material Description')
    chargeable_weight = fields.Float('chargeable Weight')



class ConsoleContainerLine(models.Model):
    _name = 'console.container.line'

    console_id = fields.Many2one('console.operation', 'Console Operation')
    transport = fields.Selection(related='console_id.transport', string='Transport')
    control = fields.Selection(([('con', 'Control'), ('notcon', 'Not Control')]), string='Control')
    seal_no = fields.Char('Seal No')
    name = fields.Char(string='Description')
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    package = fields.Many2one('freight.package', 'Package', required=True)
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Operation")
    volume = fields.Float('Volume (CBM)', compute='update_volume_gross_weight')
    gross_weight = fields.Float('Gross Weight (KG)', compute='update_volume_gross_weight')
    qty = fields.Float('Quantity')
    largest = fields.Float('Largest', compute='compute_largest')
    dangerous_goods = fields.Boolean('Dangerous Goods')
    class_number = fields.Char('Class Number')
    un_number = fields.Char('UN Number')

    @api.onchange('package')
    def onchange_package_id(self):
        for line in self:
            if line.console_id.transport == 'air':
                return {'domain': {'package': [('air', '=', True)]}}
            if line.console_id.transport == 'ocean':
                return {'domain': {'package': [('ocean', '=', True)]}}
            if line.console_id.transport == 'land':
                return {'domain': {'package': [('land', '=', True)]}}

    @api.onchange('transport', 'console_id')
    def onchange_transport(self):
        for line in self:
            if line.console_id.transport == 'ocean' and line.console_id.ocean_shipment_type in ['bulk', 'break']:
                line.volume = line.console_id.frt

    @api.depends('container_id', 'console_id')
    def update_volume_gross_weight(self):
        for rec in self:
            container = rec.console_id.console_operation_ids.search(
                [('container_id', '=', rec.container_id.id), ('container_no_id', '=', rec.container_no_id.id)])
            if container:
                print(container, 'container')
                volume = sum(container.mapped('volume'))
                gross_weight = sum(container.mapped('gross_weight'))
                rec.update({
                    'volume': volume,
                    'gross_weight': gross_weight
                })
            else:
                rec.update({
                    'volume': 0,
                    'gross_weight': 0
                })

    @api.depends('volume', 'gross_weight')
    def compute_largest(self):
        for rec in self:
            if rec.volume >= rec.gross_weight:
                rec.largest = rec.volume
            elif rec.gross_weight >= rec.volume:
                rec.largest = rec.gross_weight
            else:
                rec.largest = 0

