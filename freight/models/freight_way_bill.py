from datetime import datetime

from odoo import api, fields, models


class HouseWayBill(models.Model):
    _name = 'freight.way.bill'
    _description = 'Freight Way Bill'
    _rec_name = 'housing'


    name = fields.Char(string='Name')
    operation_id = fields.Many2one('freight.operation')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ('vas', 'Vas')]),
                                 string='Transport',related='operation_id.transport',store=True)

    console_id = fields.Many2one('console.operation', 'Console Operation')
    pieces = fields.Float('Pieces')
    weight = fields.Float('Gross Weight')
    net_weight = fields.Float('Net Weight')
    way_bill_type = fields.Selection(([('master', 'Master'), ('house', 'House')]), string='Way Bill Type')
    weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    net_weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    chargeable_weight = fields.Float('Chargeable Weight')
    volume = fields.Float('Volume')
    shipper_id = fields.Many2one('res.partner', 'Shipper')
    consignee_id = fields.Many2one('res.partner', 'Consignee')
    agent_id = fields.Many2one('res.partner', 'Agent')
    customer_id = fields.Many2one('res.partner', 'Customer')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', )
    obl = fields.Char('OBL', help='Original Bill Of Landing')

    mawb_no = fields.Char('MAWB No')
    airline_id = fields.Many2one('freight.airline', string='Airline')
    flight_no = fields.Char()
    datetime = fields.Datetime('Arrival Date')
    master = fields.Many2one('freight.master')
    housing = fields.Char()

    to_d1 = fields.Char('To')
    to_d2 = fields.Char('To')
    to_d3 = fields.Char('To')
    by_d1 = fields.Char('By')
    by_d2 = fields.Char('By')
    by_first_carrier = fields.Char()
    requested_flight = fields.Char('Requested Flight')
    requested_date = fields.Char('Requested Date')
    handling_info = fields.Text('Handling Information')
    commodity_item_no = fields.Char()
    rate = fields.Float()
    total = fields.Float()

    prepaid_weight_charge = fields.Float()
    prepaid_tax = fields.Float()
    collect_weight_charge = fields.Float()
    collect_tax = fields.Float()
    prepaid_valuation_charge = fields.Float()
    collect_valuation_charge = fields.Float()
    other_fuel = fields.Float()
    other_admin = fields.Float()
    other_handel = fields.Float()
    total_other_charges = fields.Float()
    total_prepaid_weight = fields.Float()
    total_collect_weight = fields.Float()
    date_formate = fields.Char(compute='_compute_date_formate', store=True)

    currency_id = fields.Many2one('res.currency')
    declared_value_for_carriage = fields.Float()
    declared_value_for_customs = fields.Float()
    insurance_amount = fields.Float()
    sci = fields.Float()
    type = fields.Selection([('original','Original'), ('copy','Copy'),('opportunity','Copy')])

    def _compute_date_formate(self):
        for rec in self:
            current_date = datetime.now()
            formatted_date = str(current_date.strftime("%d-%b-%y"))
            rec.date_formate = formatted_date
