from datetime import datetime

from odoo import api, fields, models


class FreightRoadWayBill(models.Model):
    _name = 'road.way.bill'
    _description = 'Road Way Bill'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    operation_id = fields.Many2one('freight.operation')
    console_id = fields.Many2one('console.operation', 'Console Operation')

    transport = fields.Selection(
        ([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ('vas', 'Vas')]),
        string='Transport', related='operation_id.transport', store=True)

    pieces = fields.Text('Number & kind Of  Packages')
    weight = fields.Text('Gross Weight')
    net_weight = fields.Text('Net Weight')
    weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    net_weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    chargeable_weight = fields.Float('Chargeable Weight')
    volume = fields.Text('Number of Containers')
    notify = fields.Char(string="Notify", copy=False)
    shipper_id = fields.Many2one('res.partner', 'Shipper')
    consignee_id = fields.Many2one('res.partner', 'Consignee')
    agent_id = fields.Many2one('res.partner', 'Agent')
    customer_id = fields.Many2one('res.partner', 'Customer')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', )
    master = fields.Many2one('freight.master')
    housing = fields.Char()
    other_charge = fields.Char('Other Charge')
    truching_charge = fields.Char('Egypt Trucking Charge')
    delivery = fields.Char('Place Of  Delivery')

    type = fields.Selection([('final', 'Final'), ('new', 'New')])
    company_id = fields.Many2one('res.company', string='Company')
    date_of_creation = fields.Datetime(string="Date ", related='create_date', readonly=True)
    today_date = fields.Date(string="Date", default=fields.Date.today, readonly=True)

    bill_of_lading_no = fields.Char(string='Bill Of Lading No.')
    from_location = fields.Char(string='From')
    to_location = fields.Char(string='To')
    port_of_export = fields.Char(string='Port of Export')
    port_of_import = fields.Char(string='Port of Import')
    forwarder = fields.Char(string='Forwarder')
    freight_payable = fields.Char(string='Freight Payable')
    notation = fields.Text(string='Notation')
    no_of_track = fields.Integer(string='No. of Track')
    pick_up = fields.Char(string='Pick Up')
    drop_location = fields.Char(string='Drop Location')
    agent = fields.Char(string='Agent')

    total_g_w = fields.Float(string='Total Gross Weight', compute='_compute_totals')
    total_n_w = fields.Float(string='Total Net Weight', compute='_compute_totals')
    total_no_of_pieces = fields.Integer(string='Total Number of Pieces', compute='_compute_totals')
    total_number_of_containers = fields.Integer(string='Total Number of Containers', compute='_compute_totals')

    @api.depends('weight', 'net_weight', 'pieces', 'volume')
    def _compute_totals(self):
        for shipment in self:
            total_g_w = 0.0
            total_n_w = 0.0
            total_no_of_pieces = 0
            total_number_of_containers = 0
            # Parse weight, net_weight, pieces, and volume to compute totals
            for line in shipment:
                if line.weight:
                    total_g_w += sum(float(w) for w in line.weight.split() if w.isdigit())
                if line.net_weight:
                    total_n_w += sum(float(n_w) for n_w in line.net_weight.split() if n_w.isdigit())
                if line.pieces:
                    total_no_of_pieces += sum(int(piece) for piece in line.pieces.split() if piece.isdigit())
                if line.volume:
                    total_number_of_containers += len(line.volume.split('\n'))
            shipment.total_g_w = total_g_w
            shipment.total_n_w = total_n_w
            shipment.total_no_of_pieces = total_no_of_pieces
            shipment.total_number_of_containers = total_number_of_containers

    def get_company_logo(self):
        """
        Get the logo of the company associated with the record.
        """
        if self.company_id:
            return self.company_id.logo
        return False