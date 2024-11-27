import logging
import pytz
import time
import babel
import base64
import json

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.modules.module import get_module_resource

from odoo.tools.translate import html_translate

from datetime import datetime
from datetime import time as datetime_time
from dateutil import relativedelta
from odoo.tools import float_compare, float_is_zero

_logger = logging.getLogger(__name__)

class InsuranceLine(models.Model):
    _name = 'freight.insurance.line'

    name = fields.Char(string='Policy No.')
    check = fields.Boolean()
    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    product_id = fields.Many2one('product.product', string='Service')
    insurance_company = fields.Many2one('res.partner', string='Insurance Company')
    currency_id = fields.Many2one('res.currency', 'Currency')
    destination_location_id = fields.Many2one('freight.port', string='Port of Discharge')
    cost = fields.Float(string='Cost')
    qty = fields.Float(string='Quantity', default=1.0)
    price = fields.Float(string='Sale Price')
    sale_id = fields.Many2one('sale.order', )
    customer_id = fields.Many2one('res.partner', )
    vendor_id = fields.Many2one('res.partner', )


class FreightOperation(models.Model):
    _name = 'freight.operation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Freight Operation'

    def _get_default_import_stage_id(self):
        return self.env['freight.import.stage'].search([], order='sequence', limit=1)

    def _get_default_export_stage_id(self):
        return self.env['freight.export.stage'].search([], order='sequence', limit=1)

    def _get_default_local_stage_id(self):
        return self.env['freight.local.stage'].search([], order='sequence', limit=1)

    @api.model
    def _read_group_stage_local_ids(self, stages, domain, order):
        stage_ids = self.env['freight.local.stage'].search([])
        return stage_ids

    @api.onchange('freight_orders.teu')
    def compute_teu(self):
        for rec in self:
            rec.teu = sum(self.freight_orders.mapped('teu'))

    @api.depends('freight_orders')
    def _compute_container_count(self):
        for record in self:
            container_ids = list(set(record.freight_orders.mapped('container_id.id')))
            container_count_list = []
            record.total_container_ids = False
            for container in container_ids:
                order_lines = record.freight_orders.filtered(lambda c: c.container_id.id == container)
                vals = {
                    'container_id': container,
                    'container_count': len(order_lines)
                }
                container_count_list.append((0, 0, vals))
            record.total_container_ids = container_count_list
            record.is_container_computed = True




    is_container_computed = fields.Boolean(compute="_compute_container_count")
    total_container_ids = fields.One2many('total.container', 'operation_id', string='Total Container')

    stage_id_local = fields.Many2one('freight.local.stage', 'Stage', default=_get_default_local_stage_id,
                                     group_expand='_read_group_stage_local_ids')
    color = fields.Integer('Color')
    stage_id_import = fields.Many2one('freight.import.stage', 'Stage', default=_get_default_import_stage_id,
                                      group_expand='_read_group_stage_import_ids')
    stage_id_export = fields.Many2one('freight.export.stage', 'Stage', default=_get_default_export_stage_id,
                                      group_expand='_read_group_stage_export_ids')
    name = fields.Char('Operation No.', copy=False, readonly=True, default=lambda x: _('New'))
    direction = fields.Selection(([('import', 'Import'), ('export', 'Export'), ('local', 'Cross Trade')]),
                                 required=True, string='Direction')
    weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    net_weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    pieces = fields.Float('Pieces')
    weight = fields.Float('Gross Weight',compute='compute_gross_weight',)
    arrived = fields.Datetime()
    tara_weight = fields.Float('Tara Weight',)
    vgm = fields.Float('VGM',)
    net_weight = fields.Float('Net Weight',compute='compute_net_weight', )
    chargeable_weight = fields.Float('Chargeable Weight', compute='compute_chargeable_weight', )
    volume = fields.Float('Volume', compute='compute_total_volume')
    vas_transport = fields.Selection([('vas', 'Vas')], string='Activity')
    vas = fields.Boolean(default=False)
    operation = fields.Selection([('direct', 'Direct'), ('house', 'Back to Back'), ('console', 'Consolidation')], string='Operation')
    operation_air = fields.Selection([('direct', 'Direct'), ('carrier', 'Carrier'), ('master', 'Back To Back'), ('console', 'Console')], string='Operation')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bulk')]), string='Ocean Shipment Type')
    inland_shipment_type = fields.Selection(([('ftl', 'FTL'), ('ltl', 'LTL')]), string='Inland Shipment Type')
    teu = fields.Float('TEU',)
    faw = fields.Float('FEU', )
    cbm = fields.Float('CBM')
    frt = fields.Float('FRT')
    shipper_id = fields.Many2one('res.partner', 'Shipper')
    shipper_hbl_id = fields.Many2one('res.partner', 'Shipper')
    carrier_id = fields.Many2one('res.partner', string="Carrier")
    consignee_id = fields.Many2one('res.partner', 'Consignee')
    consignee_hbl_id = fields.Many2one('res.partner', 'Consignee')
    shipping_line_id = fields.Many2one('res.partner', 'Shipping Line')
    agent_id = fields.Many2one('res.partner', 'Agent')
    agent_hbl_id = fields.Many2one('res.partner', 'Agent')
    customer_id = fields.Many2one('res.partner', 'Customer')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', )
    obl = fields.Char('Type of BL', help='Original Bill Of Landing')
    voyage_no = fields.Char('Voyage No')
    vessel_id = fields.Many2one('freight.vessel', 'Vessel')
    mawb_no = fields.Char('MAWB No')
    airline_id = fields.Many2one('freight.airline', string='Airline')
    datetime = fields.Datetime('Arrival Date')
    truck_ref = fields.Char('CMR/RWB#/PRO#:')
    trucker = fields.Many2one('freight.trucker', 'Trucker')
    trucker_number = fields.Char('Trucker No')
    dangerous_goods = fields.Boolean('Dangerous Goods')
    dangerous_goods_notes = fields.Text('Dangerous Goods Info')
    declaration_number = fields.Char('Declaration Number')
    declaration_date = fields.Date('Declaration Date')
    custom_clearnce_date = fields.Datetime('Customs Clearance Date')
    date_from = fields.Date('Date From', default=lambda self: fields.Date.context_today(self))
    date_end = fields.Date('Date End')

    freight_orders = fields.One2many('freight.order', 'shipment_id')
    freight_packages = fields.One2many('freight.package.line', 'shipment_id')
    freight_services = fields.One2many('freight.service', 'shipment_id')
    freight_routes = fields.One2many('freight.route', 'shipment_id')
    parent_id = fields.Many2one('freight.operation', 'Parent')
    shipments_ids = fields.One2many('freight.operation', 'parent_id')
    service_count = fields.Float('Services Count')
    invoice_count = fields.Float('Invoice Count',compute='_compute_invoice')
    vendor_bill_count = fields.Float('Vendor Count', compute='_compute_invoice')
    way_bill_count = fields.Integer('Way Bill Count', compute='_compute_way_bill_count')
    manifest_count = fields.Integer('manifest Count', compute='_compute_manifest_count')
    shipment_count = fields.Integer('shipment Count', compute='_compute_shipment_count')
    road_way_bill_count = fields.Integer('Road Way Bill Count', compute='_compute_road_way_bill_count')
    total_invoiced = fields.Float('Total Invoiced(Receivables', compute='compute_total_amount')
    total_bills = fields.Float('Total Bills(Payables)', compute='compute_total_amount')
    total_customer_claim = fields.Float('Total Customer Claims', compute='compute_total_claims')
    total_vendor_claim = fields.Float('Total Vendor Claims', compute='compute_total_claims')
    all_total_amount = fields.Float('Total', compute='compute_all_total_amount')
    commission = fields.Float()
    commission_user = fields.Many2one('res.users', 'Commission User')
    margin = fields.Float("Margin", compute='compute_total_amount' )
    invoice_residual = fields.Float('Invoice Residual', compute='compute_total_amount')
    bills_residual = fields.Float('Bills Residual', compute='compute_total_amount')
    invoice_paid_amount = fields.Float('Invoice', compute='compute_total_amount')
    bills_paid_amount = fields.Float('Bills', compute='compute_total_amount')
    actual_margin = fields.Float('Actual Margin', compute='compute_total_amount')
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.company)
    with_console = fields.Boolean()
    total_housing = fields.Integer()
    rec_no = fields.Char(string="REC No.")
    flight_no = fields.Char('Flight No')
    way_no = fields.Char(string="Way Bill No")
    booking_no = fields.Char(string="Booking No", copy=False)
    reference = fields.Char('Reference')
    s_id = fields.Char(string="ACID", copy=False)
    s_hbl_id = fields.Char(string="ACID", copy=False)
    notify = fields.Char(string="Notify", copy=False)
    notify_hbl = fields.Char(string="Notify", copy=False)
    master = fields.Many2one('freight.master', copy=False)
    housing = fields.Char(copy=False)
    type_of_mbl = fields.Char(copy=False)
    type_of_hbl = fields.Char(copy=False)
    custom_id = fields.Many2one('crm.customs')
    sales_contract = fields.Boolean(default=False)
    lead_id = fields.Many2one('crm.lead', "Opportunity", readonly=True)
    freight_check = fields.Boolean(string='Freight')
    transport_check = fields.Boolean(string='Transportation')
    clearance_check = fields.Boolean(string="Clearance")
    transit_check = fields.Boolean(string='Transit')
    contract_freight_check = fields.Boolean(string='As Contract')
    contract_transport_check = fields.Boolean(string='As Contract')
    contract_clearance_check = fields.Boolean(string="As Contract")
    contract_transit_check = fields.Boolean(string='As Contract ')
    container_check = fields.Boolean(string='Container')
    package_check = fields.Boolean(string='package')
    handling_check = fields.Boolean(string='Handling')
    documentation_check = fields.Boolean(string='Documentation')
    insurance_check = fields.Boolean(string='Insurance')
    warehousing_check = fields.Boolean(string='Warehousing')
    picking_packing_check = fields.Boolean(string='Picking & Packing')
    insurance_line_ids = fields.One2many('freight.insurance.line', 'shipment_id', copy=True)

    freight_line_ids = fields.One2many('freight.freight.line', 'shipment_id', copy=True)
    transport_line_ids = fields.One2many('freight.transport.line', 'shipment_id', copy=True)
    clearance_line_ids = fields.One2many('freight.clearance.line', 'shipment_id', copy=True)
    transit_line_ids = fields.One2many('freight.transit.line', 'shipment_id', copy=True)
    warehouse_line_ids = fields.One2many('freight.warehouse.line', 'shipment_id', copy=True)
    contract_type = fields.Selection(string='Contract Type', selection=[('spot', 'Spot'), ('cont', 'Contract')])
    customer_service_id = fields.Many2one('res.users', default=lambda self: self.env.user,
                                          readonly=False,
                                          store=True, string='Customer Service', copy=True)
    sale_person = fields.Many2one('res.users',  string='Sale Person', )
    sale_person_changed = fields.Boolean(string="Salesperson Changed", default=False)
    release_type = fields.Selection([
        ('final_import', 'Final Import'),
        ('temporary_permission', 'Temporary Permission'),
        ('drawback', 'Drawback'),
        ('transit', 'Transit'),
        ('exemptions', 'Exemptions')
    ], string='Release system')
    jaffi_no = fields.Char(string="Jaffi NO.")
    def write(self, vals):
        print("Write method called")
        if 'sale_person' in vals:
            for record in self:
                old_sale_person = record.sale_person
                super(FreightOperation, record).write(vals)
                new_sale_person = record.sale_person
                if old_sale_person != new_sale_person and new_sale_person:
                    print(f"Sale person changed from {old_sale_person.name if old_sale_person else 'None'} to {new_sale_person.name}")
                    activity_summary = f"Review required for freight operation {record.name}"
                    res_model_id = self.env['ir.model'].search([('model', '=', 'freight.operation')], limit=1).id
                    print(f"res_model_id: {res_model_id}")
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'summary': activity_summary,
                        'note': f"Freight operation {record.name} requires your review.",
                        'res_id': record.id,
                        'res_model_id': res_model_id,
                        'user_id': new_sale_person.id,
                        'date_deadline': fields.Date.today(),
                    })
                    print(f"Activity created: {activity.id}")
        else:
            super(FreightOperation, self).write(vals)
        return True
    target_price_ids = fields.One2many('target.price.line', 'shipment_id', copy=True)

    freight_operator = fields.Many2one('res.users', domain="[('freight_check','=',True)]")
    transport_operator = fields.Many2one('res.users', domain="[('transport_check','=',True)]")
    clearance_operator = fields.Many2one('res.users', domain="[('clearance_check','=',True)]")
    transit_operator = fields.Many2one('res.users', domain="[('transit_check','=',True)]")
    warehousing_operator = fields.Many2one('res.users', domain="[('warehousing_check','=',True)]")
    operation_type = fields.Selection([('cargo', 'Cargo'), ('coria', 'Courier')], string='Operation Type')

    freight_invisible = fields.Boolean(compute='compute_invisible')
    transport_invisible = fields.Boolean(compute='compute_invisible')
    clearance_invisible = fields.Boolean(compute='compute_invisible')
    transit_invisible = fields.Boolean(compute='compute_invisible')
    warehousing_invisible = fields.Boolean(compute='compute_invisible')
    accounting_invisible = fields.Boolean(compute='compute_invisible')
    shipment_invisible = fields.Boolean(compute='compute_invisible')
    target_price_invisible = fields.Boolean(compute='compute_invisible')
    operator_invisible = fields.Boolean(compute='compute_invisible')
    user_id = fields.Many2one('res.users', string='User', compute='_compute_user_id', required=True)
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    control = fields.Selection(([('con', 'Control'), ('notcon', 'Not Control')]), string='Control')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'land'), ])
                                 , required=True, string='Activity')
    vas_type = fields.Selection(([('package', 'Package'), ('container', 'Container')]), string='Vas Type')
    re_export = fields.Many2one('freight.operation', string='Re-Export')
    certificate_number = fields.Char('Certificate Number', copy=False)
    certificate_date = fields.Date('Certificate Date')
    certificate_end_date = fields.Date('Certificate End Date')
    trans_certificate_number = fields.Char('Transit Certificate Number')
    trans_certificate_date = fields.Date('Transit Certificate Date')
    trans_certificate_end_date = fields.Date('Transit Certificate End Date')
    incoterm_id = fields.Many2one('lead.incoterm', 'Incoterm', )
    # commodity_ids = fields.Many2many('lead.commodity', string='Commodity',)
    commodity_id = fields.Many2one('lead.commodity', 'Commodity')
    # commodity_display_name = fields.Char(string='Commodity Display', compute='_compute_commodity_display_name')
    # commodity_names = fields.Char(string='Commodities', compute='_compute_commodity_names', store=True)

    # @api.depends('commodity_ids')
    # def _compute_commodity_display_name(self):
    #     for record in self:
    #         if record.commodity_ids:
    #             commodity_names = record.commodity_ids.mapped(lambda c: f"{c.name} ({c.sh})")
    #             record.commodity_display_name = ", ".join(commodity_names)
    #         else:
    #             record.commodity_display_name = ""
    #
    # @api.depends('commodity_ids')
    # def _compute_commodity_names(self):
    #     for operation in self:
    #         operation.commodity_names = ", ".join([f"{commodity.name} - {commodity.sh}" for commodity in operation.commodity_ids])


    commodity_origin = fields.Char('Origin of Commodity')
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True)

    stackable = fields.Boolean()
    non_stackable = fields.Boolean()
    none_stackable = fields.Boolean()
    dry = fields.Boolean()
    fresh = fields.Boolean()
    frozen = fields.Boolean()
    Cut_off = fields.Datetime()
    Cutoff_vgm = fields.Datetime('Cut off VGM')
    Cutoff_si = fields.Datetime('Cut off SI')
    Cutoff_gate_in = fields.Datetime('Cut off Gate In')
    estimated_time_departure = fields.Datetime()
    actual_time_departure = fields.Datetime()
    estimated_time_arrival = fields.Datetime()
    actual_time_arrival = fields.Datetime()
    second_agent = fields.Many2one('res.partner')
    state = fields.Selection([('draft', 'draft'), ('close', 'close'), ('done', 'done'), ('delay', 'delay')],
                             compute='compute_state', store=True)

    custom = fields.Char(string="Custom")
    term_of_shipping = fields.Char(string="Term Of Shipping")
    # pickup_shipping = fields.Char(string="Pick-up address")
    # delivery_address = fields.Char(string="Delivery address")

    pickup = fields.Datetime()
    pickup_address = fields.Char()
    delivery_address = fields.Char()
    export_cleared = fields.Datetime()
    export_chick_point = fields.Datetime()
    departed = fields.Datetime()
    freight_term = fields.Selection([('collect', 'Collect'), ('prepaid', 'Prepaid')])
    description = fields.Text()
    romarkes = fields.Char('Remarks')
    total_freight_sale = fields.Float('Total Invoiced(Receivables', compute='compute_total_freight_sale_amount')
    total_freight_cost = fields.Float('Total Invoiced(Receivables')
    total_freight_invoiced_sale = fields.Float('Total Invoiced(Receivables',
                                               compute='compute_total_freight_sale_amount')
    total_freight_invoiced_cost = fields.Float('Total Invoiced(Receivables')
    console_id = fields.Many2one('console.operation', 'Console Operation')
    way_no_bill_count = fields.Float('Way Bills', compute='_compute_way_no_bill_count')
    to_compute_vas = fields.Boolean(compute="_to_compute_vas")
    source_country_id = fields.Many2one('res.country', 'Country',related='source_location_id.country')
    destination_country_id = fields.Many2one('res.country', 'Country',related='destination_location_id.country')
    dry_type = fields.Selection(([('dry', 'Dry'), ('fresh', 'Fresh'), ('frozen', 'Frozen')]))
    temperature = fields.Char(string='Temperature')
    ventilation = fields.Char(string='Ventilation')
    humidity = fields.Char(string='Humidity')
    stackable_type = fields.Selection(([('stackable', 'Stackable'), ('non_stackable', 'Non Stackable')]),
                                      string='Packages stackable')
    service_type = fields.Selection(([('direct_call', 'Direct Call'), ('dirct', 'Direct'), ('transshipment', 'Transshipment')]))

    # _sql_constraints = [
    #     ('master_unique', 'unique(master)', 'Master must be unique!'),
    #     ('booking_no_unique', 'unique(booking_no)', 'Booking No must be unique!'),
    #     ('certificate_number', 'unique(certificate_number)', 'Certificate Number No must be unique!')]

    _sql_constraints = [
        ('master_unique', 'check(1=1)', 'Master must be unique!')
    ]

    @api.depends('freight_check')
    def _to_compute_vas(self):
        for rec in self:
            if not rec.freight_check:
                rec.vas = True
                rec.to_compute_vas = True
            else:
                rec.vas = False
                rec.to_compute_vas = False

    

    def _compute_way_no_bill_count(self):
        task_obj = self.env['way.bill']
        self.way_no_bill_count = task_obj.search_count([('shipment_id', 'in', [a.id for a in self])])

    def action_veiw_way_bill(self):
        way_bill_ids = self.env['way.bill'].search([
            ('shipment_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Way Bill'),
            'res_model': 'way.bill',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', way_bill_ids)],
        }

    @api.onchange('operation_air')
    def onchange_charger_weight(self):
        if self.operation_air != 'carrier':
            self.operation = self.operation_air

    def action_convert(self):
        self.onchang_get_name()
        self.customer_service_id = self.env.user
        if self.lead_id:
            ids = self.env['sale.order'].search([('opportunity_id', '=', self.lead_id.id)])
            for order in ids:
                order.freight_operation_id = self.id
        self.sales_contract = False

    def action_re_export(self):
        transport_code = False
        direction_code = False

        if self.transport == 'air':
            transport_code = 'A'
        if self.transport == 'land':
            transport_code = 'L'
        if self.transport == 'ocean':
            transport_code = 'O'
        if self.transport == 'vas':
            transport_code = 'V'
        if self.direction == 'import':
            direction_code = 'I'
        if self.direction == 'export':
            direction_code = 'E'
        if self.direction == 'local':
            direction_code = 'L'
        seq = (str(self.operation) + ('/') + str(direction_code) + ('/') + str(transport_code))
        generated_seq = self.env['ir.sequence'].next_by_code('operation.seq')
        ctx = self.copy()
        ctx['direction'] = 'export'
        ctx['name'] = seq
        ctx['re_export'] = self.id
        self.re_export = ctx.id

    def onchang_get_name(self):
        transport_code = False
        direction_code = False

        if self.transport == 'air':
            transport_code = 'A'
        if self.transport == 'land':
            transport_code = 'L'
        if self.transport == 'ocean':
            transport_code = 'O'
        if self.transport == 'vas':
            transport_code = 'V'
        if self.direction == 'import':
            direction_code = 'I'
        if self.direction == 'export':
            direction_code = 'E'
        if self.direction == 'local':
            direction_code = 'L'
        seq = (str(self.operation) + ('/') + str(direction_code) + ('/') + str(transport_code))
        generated_seq = self.env['ir.sequence'].next_by_code('operation.seq')

        self.name = seq + ('/') + (generated_seq or _('New'))

    @api.model
    def create(self, values):
        if values.get('transport') == 'air':
            operation = values.get('operation')
        else:
            operation = values.get('operation')
        if values.get('sales_contract') == False:
            transport_code = ''
            direction_code = ''
            if values.get('transport') == 'air':
                transport_code = 'A'
            if values.get('transport') == 'land':
                transport_code = 'L'
            if values.get('transport') == 'ocean':
                transport_code = 'O'
            if values.get('transport')== 'vas':
                transport_code = 'V'
            if values.get('direction') == 'import':
                direction_code = 'I'
            if values.get('direction') == 'export':
                direction_code = 'E'
            if values.get('direction') == 'local':
                direction_code = 'L'
            seq = str(operation) + ('/') + str(direction_code) + ('/') + str(transport_code)
            # seq = str(direction_code) + ('/') + str(transport_code) + self.env['ir.sequence'].next_by_code(
            #     'operation.seq')
            if not values.get('name', False) or values['name'] == _('New'):
                generated_seq = self.env['ir.sequence'].next_by_code('operation.seq')
                values['name'] = seq + ('/')+ (generated_seq or _('New'))
        record = super(FreightOperation, self).create(values)
        return record

    def _compute_way_bill_count(self):
        for order in self:
            order.way_bill_count = self.env['freight.way.bill'].search_count([('operation_id', '=', order.id)])

    def _compute_manifest_count(self):
        for order in self:
            order.manifest_count = self.env['freight.manifest'].search_count([('operation_id', '=', order.id)])

    def _compute_shipment_count(self):
        for order in self:
            order.shipment_count = self.env['freight.shipment'].search_count([('operation_id', '=', order.id)])
    def _compute_road_way_bill_count(self):
        for order in self:
            order.road_way_bill_count = self.env['road.way.bill'].search_count([('operation_id', '=', order.id)])

    @api.onchange('control', 'transport')
    def onchange_control(self):
        if self.transport == 'vas' and self.control == 'notcon':
            self.handling_check = True
        else:
            self.handling_check = False

    @api.depends('freight_line_ids')
    def compute_total_freight_sale_amount(self):
        total_sale = 0.0
        invo_sale = 0.0
        for rec in self.freight_line_ids:
            if rec.sale_id:
                total_sale += rec.sale_id.amount_total
            for i in rec.sale_id.invoice_ids:
                invo_sale += i.amount_total

        self.total_freight_sale = total_sale
        self.total_freight_invoiced_sale = invo_sale

    def action_create_manifest(self):
        if self.transport == "air":
            name = self.env["ir.sequence"].next_by_code("freight.manifest.air")
        elif self.transport == "ocean":
            name = self.env["ir.sequence"].next_by_code("freight.manifest.ocean")
        else:
            name = '',
        vals = {
            'operation_id': self.id,
            'housing': name,
            'master': self.master.id,
            'shipper_id': self.shipper_id.id,
            'consignee_id': self.consignee_id.id,
            'agent_id': self.agent_id.id,
            'customer_id': self.customer_id.id,
            'source_location_id': self.source_location_id.id,
            'destination_location_id': self.destination_location_id.id,
            'pieces': self.pieces,
            'weight': self.weight,
            'net_weight': self.net_weight,
            'weight_type': self.weight_type,
            'net_weight_type': self.net_weight_type,
            'chargeable_weight': self.chargeable_weight,
            'volume': self.volume,
        }
        self.env['freight.manifest'].create(vals)

    def action_shipping_declaration(self):
        if self.transport == "air":
            name = self.env["ir.sequence"].next_by_code("freight.shipment.air")
        elif self.transport == "ocean":
            name = self.env["ir.sequence"].next_by_code("freight.shipment.ocean")
        else:
            name = '',
        vals = {
            'operation_id': self.id,
            'housing': name,
            'master': self.master.id,
            'shipper_id': self.shipper_id.id,
            'consignee_id': self.consignee_id.id,
            'agent_id': self.agent_id.id,
            'customer_id': self.customer_id.id,
            'source_location_id': self.source_location_id.id,
            'destination_location_id': self.destination_location_id.id,
            'notify':self.notify,
            'pieces': self.pieces,
            'weight': self.weight,
            'net_weight': self.net_weight,
            'weight_type': self.weight_type,
            'net_weight_type': self.net_weight_type,
            'chargeable_weight': self.chargeable_weight,
            'volume': self.volume,
            'estimated_time_arrival': self.estimated_time_arrival,
            'actual_time_departure': self.actual_time_departure,
            'voyage_no': self.voyage_no,
            'vessel_id': self.actual_time_departure,
        }
        self.env['freight.shipment'].create(vals)
    def action_road_way_bill(self):
        if self.transport == "air":
            name = self.env["ir.sequence"].next_by_code("freight.shipment.air")
        elif self.transport == "ocean":
            name = self.env["ir.sequence"].next_by_code("freight.shipment.ocean")
        else:
            name = '',
        vals = {
            'operation_id': self.id,
            'housing': name,
            'master': self.master.id,
            'shipper_id': self.shipper_id.id,
            'consignee_id': self.consignee_id.id,
            'agent_id': self.agent_id.id,
            'customer_id': self.customer_id.id,
            'source_location_id': self.source_location_id.id,
            'destination_location_id': self.destination_location_id.id,
            'notify':self.notify,
            'pieces': self.pieces,
            'weight': self.weight,
            'net_weight': self.net_weight,
            'weight_type': self.weight_type,
            'net_weight_type': self.net_weight_type,
            'chargeable_weight': self.chargeable_weight,
            'volume': self.volume,
        }
        self.env['road.way.bill'].create(vals)

    def action_create_master_way_bill(self):
        if self.transport == "air":
            name = self.env["ir.sequence"].next_by_code("freight.way.bill.air")
        elif self.transport == "ocean":
            name = self.env["ir.sequence"].next_by_code("freight.way.bill.ocean")
        else:
            name = self.housing
        vals = {
            'operation_id': self.id,
            'way_bill_type': 'master',
            'housing': name,
            'master': self.master.id,
            'pieces': self.pieces,
            'weight': self.weight,
            'net_weight': self.net_weight,
            'weight_type': self.weight_type,
            'net_weight_type': self.net_weight_type,
            'chargeable_weight': self.chargeable_weight,
            'volume': self.volume,
            'shipper_id': self.shipper_id.id,
            'consignee_id': self.consignee_id.id,
            'agent_id': self.agent_id.id,
            'customer_id': self.customer_id.id,
            'source_location_id': self.source_location_id.id,
            'destination_location_id': self.destination_location_id.id,
            'obl': self.obl,
            'mawb_no': self.mawb_no,
            'airline_id': self.airline_id.id,
            'datetime': self.datetime,
            # 'flight_no': self.airline_id,id,
        }
        self.env['freight.way.bill'].create(vals)

    def action_create_way_bill(self):
        if self.transport == "air":
            name = self.env["ir.sequence"].next_by_code("freight.way.bill.air")
        elif self.transport == "ocean":
            name = self.env["ir.sequence"].next_by_code("freight.way.bill.ocean")
        else:
            name = self.housing
        vals = {
            'operation_id': self.id,
            'way_bill_type': 'house',
            'housing': name,
            'master': self.master.id,
            'pieces': self.pieces,
            'weight': self.weight,
            'net_weight': self.net_weight,
            'weight_type': self.weight_type,
            'net_weight_type': self.net_weight_type,
            'chargeable_weight': self.chargeable_weight,
            'volume': self.volume,
            'shipper_id': self.shipper_id.id,
            'consignee_id': self.consignee_id.id,
            'agent_id': self.agent_id.id,
            'customer_id': self.customer_id.id,
            'source_location_id': self.source_location_id.id,
            'destination_location_id': self.destination_location_id.id,
            'obl': self.obl,
            'mawb_no': self.mawb_no,
            'airline_id': self.airline_id.id,
            'datetime': self.datetime,
            # 'flight_no': self.airline_id,id,
        }
        self.env['freight.way.bill'].create(vals)



    @api.depends('name')
    def compute_bill_domain_ids(self):
        move_ids = []
        for rec in self:
            rec.bill_domain_ids = False
            line_bill_count = self.env['account.move.line'].sudo().search(
                [('shipment_number', '=', rec.id), ('move_type', '=', 'in_invoice')])
            for line in line_bill_count:
                line_id = line.id
                vendor_bill_count = self.env['account.move'].sudo().search(
                    [('move_type', '=', 'in_invoice'),('freight_operation_id', '=', rec.id)])
                rec.bill_domain_ids = vendor_bill_count.ids
                # for part in vendor_bill_count:
                #     move_ids += vendor_bill_count.search(
                #         [('freight_operation_id', '=', rec.id)]).ids
                #     if move_ids:
                #         rec.bill_domain_ids = move_ids
                #     else:
                #         rec.bill_domain_ids = False

    bill_domain_ids = fields.Many2many('account.move', 'res_bill_domain_ids_rel',

                                          string="Allowed Bills")


    @api.depends('freight_orders.volume')
    def compute_total_volume(self):
        for rec in self:
            rec.volume = sum(self.freight_orders.mapped('volume'))

    @api.depends('freight_orders.gross_weight','freight_packages.gross_weight')
    def compute_gross_weight(self):
        for rec in self:
            rec.weight = 0.0
            if rec.transport == 'ocean':
                rec.weight = sum(self.freight_orders.mapped('gross_weight'))
            if rec.transport == 'land':
                rec.weight = sum(self.freight_orders.mapped('gross_weight'))
            if rec.transport == 'air':
                rec.weight = sum(self.freight_packages.mapped('gross_weight'))

    @api.depends('freight_orders.net_weight')
    def compute_net_weight(self):
        for rec in self:
            rec.net_weight = sum(self.freight_orders.mapped('net_weight'))


    @api.depends('freight_packages.charger_weight')
    def compute_chargeable_weight(self):
        for rec in self:
            rec.chargeable_weight = sum(self.freight_packages.mapped('charger_weight'))



    @api.depends()
    def _compute_user_id(self):
        for order in self:
            if not order.user_id:
                order.user_id = self.env.user

    @api.depends('stage_id_import')
    def compute_state(self):
        for rec in self:
            if rec.direction == 'import':
                if rec.stage_id_import.name == 'Draft':
                    rec.state = 'draft'
                elif rec.stage_id_import.name == 'Done':
                    rec.state = 'done'
                elif rec.stage_id_import.name == 'Delay':
                    rec.state = 'delay'
                elif rec.stage_id_import.name == 'Ready To Close':
                    rec.state = 'close'
            elif rec.direction == 'export':
                if rec.stage_id_export.name == 'Draft':
                    rec.state = 'draft'
                elif rec.stage_id_export.name == 'Done':
                    rec.state = 'done'
                elif rec.stage_id_export.name == 'Delay':
                    rec.state = 'delay'
                elif rec.stage_id_export.name == 'Ready To Close':
                    rec.state = 'close'
            elif rec.direction == 'local':
                if rec.stage_id_local.name == 'Draft':
                    rec.state = 'draft'
                elif rec.stage_id_local.name == 'Done':
                    rec.state = 'done'
                elif rec.stage_id_local.name == 'Delay':
                    rec.state = 'delay'
                elif rec.stage_id_local.name == 'Ready To Close':
                    rec.state = 'close'

    @api.depends('user_id', 'customer_service_id')
    def compute_invisible(self):
        for rec in self:
            rec.freight_invisible = True
            rec.transport_invisible = True
            rec.clearance_invisible = True
            rec.transit_invisible = True
            rec.warehousing_invisible = True
            rec.accounting_invisible = True
            rec.shipment_invisible = True
            rec.target_price_invisible = True
            rec.operator_invisible = True
            if rec.user_id.has_group('freight.group_freight_manager'):
                rec.freight_invisible = False
                rec.transport_invisible = False
                rec.clearance_invisible = False
                rec.transit_invisible = False
                rec.warehousing_invisible = False
                rec.accounting_invisible = False
                rec.shipment_invisible = False
                rec.target_price_invisible = False
                rec.operator_invisible = False
            elif rec.user_id.has_group('freight.group_freight_user'):
                if rec.user_id == rec.customer_service_id:
                    rec.freight_invisible = False
                    rec.transport_invisible = False
                    rec.clearance_invisible = False
                    rec.transit_invisible = False
                    rec.warehousing_invisible = False
                    rec.accounting_invisible = False
                    rec.shipment_invisible = False
                    rec.target_price_invisible = False
                    rec.operator_invisible = False
            if rec.user_id.has_group('freight.group_freight_user') and rec.user_id != rec.customer_service_id:
                if rec.user_id == rec.freight_operator:
                    rec.freight_invisible = False
            if rec.user_id.has_group('freight.group_freight_user') and rec.user_id != rec.customer_service_id:
                if rec.user_id == rec.transport_operator:
                    rec.transport_invisible = False
            if rec.user_id.has_group('freight.group_freight_user') and rec.user_id != rec.customer_service_id:
                if rec.user_id == rec.clearance_operator:
                    rec.clearance_invisible = False
            if rec.user_id.has_group('freight.group_freight_user') and rec.user_id != rec.customer_service_id:
                if rec.user_id == rec.transit_operator:
                    rec.transit_invisible = False
            if rec.user_id.has_group('freight.group_freight_user') and rec.user_id != rec.customer_service_id:
                if rec.user_id == rec.warehousing_operator:
                    rec.warehousing_invisible = False

    def select_all(self):
        if self.freight_check == True and self.freight_line_ids:
            for f in self.freight_line_ids:
                f.check = True
        if self.transport_check == True and self.transport_line_ids:
            for f in self.transport_line_ids:
                f.check = True
        if self.clearance_check == True and self.clearance_line_ids:
            for f in self.clearance_line_ids:
                f.check = True
        if self.transit_check == True and self.transit_line_ids:
            for f in self.transit_line_ids:
                f.check = True
        # if self.documentation_check == True and self.documentation_line_ids:
        #     for f in self.documentation_line_ids:
        #         f.check = True
        if self.insurance_check == True and self.insurance_line_ids:
            for f in self.insurance_line_ids:
                f.check = True
        # if self.picking_packing_check == True and self.packing_line_ids:
        #     for f in self.packing_line_ids:
        #         f.check = True
        # if self.storage_check == True and self.storage_line_ids:
        #     for f in self.storage_line_ids:
        #         f.check = True

    def select_all_transit_line_ids(self):
        if self.transit_check == True and self.transit_line_ids:
            for f in self.transit_line_ids:
                f.check = True

    def select_all_freight_line_ids(self):
        if self.freight_check == True and self.freight_line_ids:
            for f in self.freight_line_ids:
                f.check = True

    def select_all_transport_line_ids(self):
        if self.transport_check == True and self.transport_line_ids:
            for f in self.transport_line_ids:
                f.check = True

    def select_all_clearance_line_ids(self):
        if self.clearance_check == True and self.clearance_line_ids:
            for f in self.clearance_line_ids:
                f.check = True

    def select_all_insurance_line_ids(self):
        if self.insurance_check == True and self.insurance_line_ids:
            for f in self.insurance_line_ids:
                f.check = True

    def action_open_create_rfq(self):
        view_id = self.env.ref('freight.view_create_purchase_line').id

        name = _('Create RFQ')
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'create.po.wizard',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_shipment_id': self.id,

            }
        }

    def action_open_create_quotation(self):
        view_id = self.env.ref('freight.view_create_quotation_line').id

        name = _('Create Quotation')
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'quotation.wizard',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_shipment_id': self.id,

            }
        }

    @api.onchange('transit_line_ids')
    def onchange_transit_line_ids(self):
        if self.transit_line_ids and self.transit_line_ids[0].letter_id:
            self.letter_id = self.transit_line_ids[0].letter_id

    @api.onchange('stage_id_import','stage_id_export')
    def onchange_stage_id(self):
        if self.stage_id_import.name == 'Done' and not self.env.user.has_group('freight.group_freight_manager'):
            raise UserError(_("You don't have the rights to convert shipment to state done. Please contact an Administrator."))
        elif self.stage_id_export.name == 'Done' and not self.env.user.has_group('freight.group_freight_manager'):
            raise UserError(_("You don't have the rights to convert shipment to state done. Please contact an Administrator."))


    def action_ready_to_close(self):
        invoices = self.env['account.move'].sudo().search(
            [('freight_operation_id', '=', self.id), ('move_type', '=', 'out_invoice'),('state','!=','post')])
        bels = self.env['account.move'].sudo().search(
            [('freight_operation_id', '=', self.id), ('move_type', '=', 'in_invoice'),('state','!=','post')])
        if not invoices and not bels:
            if self.direction == 'import':
                self.stage_id_import = self.env.ref('freight.ready_freight_import_stage').id
                self.send_activity()
            elif self.direction == 'export':
                self.stage_id_export = self.env.ref('freight.ready_freight_export_stage').id
                self.send_activity()

    def action_shipment_done(self):
        if self.env.user.has_group('freight.group_freight_manager'):
            if self.direction == 'import' :
                self.stage_id_import = self.env.ref('freight.done_freight_import_stage').id
            elif self.direction == 'export':
                self.stage_id_export = self.env.ref('freight.ready_freight_export_stage').id
        raise UserError(
            _("You don't have the rights to convert shipment to state done. Please contact an Administrator."))

    def send_activity(self, user, summary):
        now = fields.datetime.now()
        date_deadline = now.date()
        activ_list = []
        if user and user != 'None':
            activity_id = self.sudo().activity_schedule(
                'mail.mail_activity_data_todo', date_deadline,
                note=_(
                    summary
                ),
                user_id=user.id,
                res_id=self.id,

                summary=summary
            )
            activ_list.append(activity_id.id)
        [(4, 0, rec) for rec in activ_list]

    def send_activity_to_customer_service(self,summary):
        for rec in self:
            if rec.customer_service_id:
                rec.send_activity(rec.customer_service_id, summary)

    def write(self, vals):
        res = super(FreightOperation, self).write(vals)
        if 'freight_operator' in vals:
            self.activity_done()
            self.send_activity_to_operator('You have been assigned to this shipment as operator service')
        if 'customer_service_id' in vals:
            self.send_activity_to_customer_service('You have been assigned to this shipment as customer service')

        return res

    # @api.depends('name')
    # def compute_total_claims(self):
    #     for operation in self:
    #         company_currency = operation.company_id.currency_id
    #
    #         # Fetch customer and vendor claims
    #         customer_claims = self.env['account.move'].sudo().search(
    #             [('freight_operation_id', '=', operation.id), ('move_type', '=', 'out_invoice'),
    #              ('is_claim', '=', True)])
    #         vendor_claims = self.env['account.move'].sudo().search(
    #             [('freight_operation_id', '=', operation.id), ('move_type', '=', 'in_invoice'),
    #              ('is_claim', '=', True)])
    #
    #         # Convert customer claims total to company currency
    #         customer_total_claim = sum(
    #             invoice.currency_id._convert(invoice.amount_total, company_currency, operation.company_id, invoice.invoice_date)
    #             for invoice in customer_claims
    #         )
    #
    #         # Convert vendor claims total to company currency
    #         operation.total_vendor_claim = abs(sum(vendor_claims.mapped('amount_total_in_currency_signed')))
    #
    #         vendor_total_claim = sum(
    #             bill.currency_id._convert(bill.amount_total, company_currency, operation.company_id, bill.invoice_date) for bill
    #             in vendor_claims
    #         )
    #
    #         # Assign the totals to the operation
    #         operation.total_customer_claim = customer_total_claim
    #         operation.total_vendor_claim = vendor_total_claim

    @api.depends('name')
    def compute_total_claims(self):
        for operation in self:
            company_currency = operation.company_id.currency_id

            # Fetch customer and vendor claims
            customer_claims = self.env['account.move'].sudo().search(
                [('freight_operation_id', '=', operation.id), ('move_type', '=', 'out_invoice'),
                 ('is_claim', '=', True)]
            )
            vendor_claims = self.env['account.move'].sudo().search(
                [('freight_operation_id', '=', operation.id), ('move_type', '=', 'in_invoice'),
                 ('is_claim', '=', True)]
            )

            # Convert customer claims total to company currency with a fallback for missing invoice_date
            customer_total_claim = sum(
                invoice.currency_id._convert(
                    invoice.amount_total,
                    company_currency,
                    operation.company_id,
                    invoice.invoice_date or fields.Date.today()  # Fallback to current date if invoice_date is missing
                )
                for invoice in customer_claims
            )

            # Convert vendor claims total to company currency with a fallback for missing invoice_date
            vendor_total_claim = sum(
                bill.currency_id._convert(
                    bill.amount_total,
                    company_currency,
                    operation.company_id,
                    bill.invoice_date or fields.Date.today()  # Fallback to current date if invoice_date is missing
                )
                for bill in vendor_claims
            )

            # Assign the totals to the operation
            operation.total_customer_claim = customer_total_claim
            operation.total_vendor_claim = vendor_total_claim

    @api.depends('total_vendor_claim', 'total_customer_claim', 'total_invoiced', 'total_bills', 'commission')
    def compute_all_total_amount(self):
        for operation in self:
            operation.all_total_amount = 0.0  # Ensure the field is initialized to 0.0

            # Use 'operation' instead of 'self' to reference individual records inside the loop
            if operation.total_customer_claim or operation.total_vendor_claim:
                total_customer = operation.total_customer_claim + operation.total_invoiced
                total_vendor = operation.total_vendor_claim + operation.total_bills + operation.commission
                operation.all_total_amount = total_customer - total_vendor
            else:
                operation.all_total_amount = 0.0

    @api.depends('freight_services')
    def compute_total_amount(self):
        for order in self:
            company_currency = order.company_id.currency_id

            invoices = self.env['account.move'].sudo().search(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'out_invoice'), ('is_claim', '=', False)])
            bills = self.env['account.move'].sudo().search(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'in_invoice'), ('is_claim', '=', False)])

            # Convert invoices total to company currency
            total_invoiced = sum(
                invoice.currency_id._convert(invoice.amount_total, company_currency, order.company_id, invoice.date) for
                invoice in invoices
            )
            invoice_residual = sum(
                invoice.currency_id._convert(invoice.amount_residual, company_currency, order.company_id, invoice.date) for
                invoice in invoices
            )

            # Convert bills total to company currency
            total_bills = sum(
                bill.currency_id._convert(bill.amount_total, company_currency, order.company_id, bill.date) for bill in
                bills
            )
            bills_residual = sum(
                bill.currency_id._convert(bill.amount_residual, company_currency, order.company_id, bill.date) for bill in
                bills
            )
            order.total_invoiced = total_invoiced
            order.total_bills = total_bills
            order.margin = total_invoiced - total_bills
            order.invoice_residual = invoice_residual
            order.bills_residual = bills_residual

            payment_total = 0.0
            for invoice in invoices:
                for payment in invoice.payment_ids:
                    payment_total += payment.amount
            order.invoice_paid_amount = payment_total
            bill_payment_total = 0.0
            for bill_payment in bills:
                for payment in bill_payment.payment_ids:
                    bill_payment_total += payment.amount
            order.bills_paid_amount = bill_payment_total
            order.actual_margin = order.invoice_paid_amount - order.bills_paid_amount

    @api.model
    def _read_group_stage_import_ids(self, stages, domain, order):
        stage_ids = self.env['freight.import.stage'].search([])
        return stage_ids

    @api.model
    def _read_group_stage_export_ids(self, stages, domain, order):
        stage_ids = self.env['freight.export.stage'].search([])
        return stage_ids

    @api.depends('name')
    def _compute_invoice(self):
        for order in self:
            order.service_count = len(order.freight_services)
            order.invoice_count = self.env['account.move'].sudo().search_count(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'out_invoice'), ('is_claim', '=', False)])
            line_bill_count = self.env['account.move.line'].sudo().search_count(
                [('shipment_number', '=', order.id), ('move_type', '=', 'in_invoice'),])
            vendor_bill_count = self.env['account.move'].sudo().search_count(
                [('freight_operation_id', '=', order.id), ('move_type', '=', 'in_invoice'), ('is_claim', '=', False)])
            order.vendor_bill_count = vendor_bill_count

    def button_services(self):
        services = self.mapped('freight_services')
        action = self.env["ir.actions.actions"]._for_xml_id("freight.view_freight_service_action")
        action['context'] = {'default_shipment_id': self.id}
        action['domain'] = [('id', 'in', services.ids)]
        return action

    def button_customer_invoices(self):
        invoices = self.env['account.move'].sudo().search(
            [('freight_operation_id', '=', self.id), ('move_type', '=', 'out_invoice'), ('is_claim', '=', False)])
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['context'] = {'default_freight_operation_id': self.id,
                             'default_partner_id': self.customer_id.id,
                             'default_move_type': 'out_invoice',
                             'default_weight': self.weight,
                             'default_net_weight': self.net_weight,
                             'default_transport': self.transport,
                             'default_ocean_shipment_type': self.ocean_shipment_type,
                             'default_source_location_id': self.source_location_id.id,
                             'default_destination_location_id': self.destination_location_id.id,
                             }
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
            [('freight_operation_id', '=', self.id), ('move_type', '=', 'in_invoice'), ('is_claim', '=', False)])
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        action['context'] = {'default_freight_operation_id': self.id,
                             'default_partner_id': self.customer_id.id,
                             'default_move_type': 'in_invoice',
                             'default_weight': self.weight,
                             'default_net_weight': self.net_weight,
                             'default_transport': self.transport,
                             'default_ocean_shipment_type': self.ocean_shipment_type,
                             'default_source_location_id': self.source_location_id.id,
                             'default_destination_location_id': self.destination_location_id.id,
                             }
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

    def generate_from_the_orders(self):
        for line in self:
            packages = []
            for order in line.freight_orders:
                if not order.package:
                    raise UserError('Please add Package in Containers')
                packages.append((0, 0, {'name': order.name,
                                        'package': order.package.id,
                                        'container_id': order.container_id.id,
                                        'commodity_id': order.commodity_id.id,
                                        'qty': order.qty,
                                        'volume': order.volume,
                                        'gross_weight': order.gross_weight,
                                        'net_weight': order.net_weight,
                                        'shipment_id': line.id}))
            self.freight_packages.unlink()
            self.write({'freight_packages': packages})


    @api.model
    def _vessel_image(self):
        image_path = get_module_resource('freight', 'static/img', 'Vessel.png')
        return base64.b64encode(open(image_path, 'rb').read())

    @api.model
    def _trucking_image(self):
        image_path = get_module_resource('freight', 'static/img', 'Trucking.png')
        return base64.b64encode(open(image_path, 'rb').read())

    @api.model
    def _air_image(self):
        image_path = get_module_resource('freight', 'static/img', 'Airplan.png')
        return base64.b64encode(open(image_path, 'rb').read())

    vessel_image = fields.Binary("Vessel", default=_vessel_image, attachment=True)
    trucking_image = fields.Binary("Truck", default=_trucking_image, attachment=True)
    air_image = fields.Binary("Air", default=_air_image, attachment=True)

    def action_view_bill_off_loading(self):
        ids = self.env['freight.way.bill'].search([('operation_id', '=', self.id)])
        for i in ids:
            i.operation_id = self.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Bill Of Loading'),
            'res_model': 'freight.way.bill',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids.ids)],
            'context': {
                'default_operation_id': self.id,
            }
        }

    def action_view_manifest(self):
        if self.console_id:
            ids = self.env['freight.manifest'].search(['|',('operation_id', '=', self.id),('console_id','=',self.console_id.id)])
        else:
            ids = self.env['freight.manifest'].search([('operation_id', '=', self.id)])
        for rec in ids:
            rec.operation_id = self.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Freight Manifest'),
            'res_model': 'freight.manifest',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids.ids)],
            'context': {
                'default_operation_id': self.id,
            }
        }

    def action_view_shipping_declaration(self):
        if self.console_id:
            ids = self.env['freight.shipment'].search(['|',('operation_id', '=', self.id),('console_id','=',self.console_id.id)])
        else:
            ids = self.env['freight.shipment'].search([('operation_id', '=', self.id)])
        for rec in ids:
            rec.operation_id = self.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Freight Shipping Declraction'),
            'res_model': 'freight.shipment',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids.ids)],
            'context': {
                'default_operation_id': self.id,
            }
        }
    def action_view_road_way_bill(self):
        if self.console_id:
            ids = self.env['road.way.bill'].search(['|',('operation_id', '=', self.id),('console_id','=',self.console_id.id)])
        else:
            ids = self.env['road.way.bill'].search([('operation_id', '=', self.id)])
        for rec in ids:
            rec.operation_id = self.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Freight Road Way Bill'),
            'res_model': 'road.way.bill',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids.ids)],
            'context': {
                'default_operation_id': self.id,
            }
        }



class FreightPackageLine(models.Model):
    _name = 'freight.package.line'


    name = fields.Char(string='Description')
    description = fields.Text(string='Description')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ]),
                                 string='Transport')
    container_no_domain = fields.Char(compute='compute_container_no_domain')
    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    container_id = fields.Many2one('freight.container', 'Container Type',copy=False)
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    container_no_ids = fields.Many2many('freight.container.no', 'container_rel_7900', string='Container No')
    second_container_no_id = fields.Many2one('freight.container.no', 'Container No')
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
    un_number = fields.Char('UN Number',
                            help='UN numbers are four-digit numbers that identify hazardous materials, and articles in the framework of international transport')
    Package_group = fields.Char('Packaging Group:')
    imdg_code = fields.Char('IMDG Code', help='International Maritime Dangerous Goods Code')
    flash_point = fields.Char('Flash Point')
    material_description = fields.Text('Material Description')
    freight_item_lines = fields.One2many('freight.item.line', 'package_line_id')
    route_id = fields.Many2one('freight.route', 'Route')
    charger_weight = fields.Float('Chargeable Weight')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    width = fields.Float('Width (KG)')
    height = fields.Float('Height (KG)')
    size = fields.Float('Length')
    main_measure = fields.Float('FRT',compute='compute_main_measure')
    commodity_id = fields.Many2one('lead.commodity', 'Commodity', )

    @api.onchange('package')
    def onchange_dangerous_goods(self):
        for rec in self:
            rec.dangerous_goods = rec.shipment_id.dangerous_goods

    @api.depends('volume', 'gross_weight')
    def compute_main_measure(self):
        for rec in self:
            if rec.shipment_id.operation_type == 'cargo':
                rec.volume = (rec.width * rec.height * rec.size) / 6000
            if rec.shipment_id.operation_type == 'coria':
                rec.volume = (rec.width * rec.height * rec.size) / 5000
            rec.charger_weight = max(rec.volume, rec.gross_weight)
            rec.main_measure = max(rec.volume, rec.gross_weight)

    @api.onchange('width', 'height', 'size', 'gross_weight')
    def compute_volume(self):
        for rec in self:
            if rec.shipment_id.operation_type == 'cargo':
                rec.volume = (rec.width * rec.height * rec.size) / 6000
            if rec.shipment_id.operation_type == 'coria':
                rec.volume = (rec.width * rec.height * rec.size) / 5000
            rec.charger_weight = max(rec.volume, rec.gross_weight)
    @api.depends('container_id')
    def compute_container_no_domain(self):
        for rec in self:
            if rec.container_id and rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('container_id', '=', rec.container_id.id), ('state', '=', 'available'),
                     ('operation_id', '=', rec.shipment_id.ids[0])]
                )
            elif rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('operation_id', '=', rec.shipment_id.ids[0])])
            else:
                rec.container_no_domain = []

    @api.onchange('container_no_id')
    def onchange_container_no_id(self):
        if self.container_no_id:
            if self.second_container_no_id:
                self.second_container_no_id.state = 'available'
            self.container_no_id.state = 'used'
            self.second_container_no_id = self.container_no_id

    @api.onchange('package')
    def onchange_package_id(self):
        for line in self:
            if line.shipment_id.transport == 'air':
                return {'domain': {'package': [('air', '=', True)]}}
            if line.shipment_id.transport == 'ocean':
                return {'domain': {'package': [('ocean', '=', True)]}}
            if line.shipment_id.transport == 'land':
                return {'domain': {'package': [('land', '=', True)]}}


class FreightItemLine(models.Model):
    _name = 'freight.item.line'

    name = fields.Char(string='Description')
    package_line_id = fields.Many2one('freight.package.line', 'Shipment ID')
    package = fields.Many2one('freight.package', 'Package')
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Operation")
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    qty = fields.Float('Quantity')
    charger_weight = fields.Float('Chargeable Weight')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ]),
                                 string='Transport')

    @api.onchange('package')
    def onchange_package_id(self):
        for line in self:
            line.transport = line.package_line_id.shipment_id.transport
            if line.package_line_id.shipment_id.transport == 'air':
                return {'domain': {'package': [('air', '=', True)]}}
            if line.package_line_id.shipment_id.transport == 'ocean':
                return {'domain': {'package': [('ocean', '=', True)]}}
            if line.package_line_id.shipment_id.transport == 'land':
                return {'domain': {'package': [('land', '=', True)]}}


class FreightOrder(models.Model):
    _name = 'freight.order'

    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ]),
                                 string='Transport')
    name = fields.Char(string='Description')
    container_id = fields.Many2one('freight.container', 'Container Type',copy=False)
    container_no_id = fields.Many2one('freight.container.no', 'Container No',copy=False)
    # second_container_no_id = fields.Many2one('freight.container.no', 'Container No')
    container_no_ids = fields.Many2many('freight.container.no', 'container_rel_76', string='Container No')
    seal_no = fields.Char('Seal No')

    container_no_domain = fields.Char(compute='compute_container_no_domain')
    standard_volume = fields.Float(related='container_id.standard_volume', string='Standard Volume')
    standard_weight = fields.Float(related='container_id.standard_weight', string='Standard Weight')
    package = fields.Many2one('freight.package', 'Package')
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Operation")
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    qty = fields.Float('Quantity')
    dangerous_goods = fields.Boolean('Dangerous Goods')
    class_number = fields.Char('Class Number')
    un_number = fields.Char('UN Number',
                            help='UN numbers are four-digit numbers that identify hazardous materials, and articles in the framework of international transport')
    sale_id = fields.Many2one('sale.order')
    tara_weight = fields.Float('Tara Weight', )
    vgm = fields.Float('VGM', compute='compute_main_measure')
    charger_weight = fields.Float('chargeable Weight (KG)')  # todo how to compute this field
    teu = fields.Float('TEU')
    faw = fields.Float('FEU', )

    # commodity_ids = fields.Many2many('lead.commodity', 'Commodity', )
    commodity_id = fields.Many2one('lead.commodity', 'Commodity', )

    login_of_date = fields.Date(string='Loading of Date')

    @api.depends('gross_weight', 'tara_weight')
    def compute_main_measure(self):
        for rec in self:
            if rec.tara_weight and rec.gross_weight:
                rec.vgm = rec.tara_weight + rec.gross_weight
            else:
                rec.vgm = 0.0

    @api.onchange('container_id')
    def onchange_container_id(self):
        self.teu = self.container_id.teu

    def action_duplicate_line(self):
        view_id = self.env.ref('freight.view_create_container_line').id

        name = _('Add a Line')
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'container.wizard',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_line_id': self.id,
                'default_name': self.name,
                'default_shipment_id': self.shipment_id.id,
                'default_container_id': self.container_id.id,
                'default_package': self.package.id,
                'default_container_no_id': self.container_no_id.id,
                'default_type': self.type,
                'default_teu': self.teu,
                'default_transport': self.transport,
                'default_qty': self.qty,
            }
        }
    @api.onchange('package')
    def onchange_package_id(self):
        for line in self:
            if line.shipment_id.transport == 'air':
                return {'domain': {'package': [('air', '=', True)]}}
            if line.shipment_id.transport == 'ocean':
                return {'domain': {'package': [('ocean', '=', True)]}}
            if line.shipment_id.transport == 'land':
                return {'domain': {'package': [('land', '=', True)]}}

    @api.onchange('transport', 'shipment_id')
    def onchange_transport(self):
        for line in self:
            if line.shipment_id.transport == 'ocean' and line.shipment_id.ocean_shipment_type in ['bulk', 'break']:
                line.volume = line.shipment_id.frt

    def write(self,values):
        res = super(FreightOrder, self).write(values)
        # if 'sale_id' in values:
        #     if self.currency_id == self.sale_id.currency_id:
        #         # self.link_to_order()
        #     else:
        #         raise ValidationError(_('Warning Currency on the line defer from the currency in SO'))
        if 'container_no_id' in values and  self.container_id and self.shipment_id:
            self.container_no_id.operation_id = self.shipment_id
            self.container_no_id.container_id = self.container_id
        return res

    @api.depends('container_id')
    def compute_container_no_domain(self):
        for rec in self:
            if rec.container_id and rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('container_id', '=', rec.container_id.id), ('state', '=', 'available'),
                     ('operation_id', '=', rec.shipment_id.ids[0])]
                )
            elif rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('operation_id', '=', rec.shipment_id.ids[0])])
            else:
                rec.container_no_domain = []


class FreightService(models.Model):
    _name = 'freight.service'

    service_id = fields.Many2one('product.product', 'Service', domain="[('type','=','service')]")
    currency_id = fields.Many2one('res.currency', 'Currency')
    name = fields.Char(string='Description')
    cost = fields.Float('Cost')
    sale = fields.Float('Sale')
    qty = fields.Float('Quantity')
    partner_id = fields.Many2one('res.partner', 'Vendor')
    route_id = fields.Many2one('freight.route', 'Route')
    shipment_id = fields.Many2one('freight.operation', 'Shipment ID', related='route_id.shipment_id')
    customer_invoice = fields.Many2one('account.move')
    vendor_invoice = fields.Many2one('account.move')
    invoiced = fields.Boolean('Invoiced')
    vendor_invoiced = fields.Boolean('Vendor Invoiced')


class FreightRoute(models.Model):
    _name = 'freight.route'

    name = fields.Char('Description', compute='compute_name')
    type = fields.Selection([('pickup', 'Pickup'), ('oncarriage', 'On Carriage'), ('precarriage', 'Pre Carriage'),
                             ('delivery', 'Delivery')], string='Type')
    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ]), string='Transport')
    ocean_shipment_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string='Shipment Type')
    inland_shipment_type = fields.Selection([('ftl', 'FTL'), ('ltl', 'LTL')], string='Shipment Type')
    shipper_id = fields.Many2one('res.partner', 'Shipper')
    consignee_id = fields.Many2one('res.partner', 'Consignee')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading')
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge')
    obl = fields.Char('OBL', help='Original Bill Of Lading')
    shipping_line_id = fields.Many2one('res.partner', 'Shipping Line')
    voyage_no = fields.Char('Voyage No')
    vessel_id = fields.Many2one('freight.vessel', 'Vessel')
    mawb_no = fields.Char('MAWB No')
    airline_id = fields.Many2one('freight.airline', 'Airline')
    flight_no = fields.Char('Flight No')
    datetime = fields.Datetime('Date')
    truck_ref = fields.Char('CMR/RWB#/PRO#:')
    trucker = fields.Many2one('freight.trucker', 'Trucker')
    trucker_number = fields.Many2one('freight.trucker', 'Trucker No')
    etd = fields.Datetime('ETD')
    eta = fields.Datetime('ETA')
    atd = fields.Datetime('ATD')
    ata = fields.Datetime('ATA')
    package_ids = fields.One2many('freight.package.line', 'route_id')
    freight_services = fields.One2many('freight.service', 'route_id')
    main_carriage = fields.Boolean('Main Carriage')

    @api.model
    def create(self, values):
        id = super(FreightRoute, self).create(values)
        id.freight_services.write({'shipment_id': id.shipment_id.id})
        return id

    def write(self, vals):
        res = super(FreightRoute, self).write(vals)
        self.freight_services.write({'shipment_id': self.shipment_id.id})
        return res

    def compute_name(self):
        for line in self:
            if line.main_carriage:
                line.name = 'Main carriage'
            elif line.type:
                line.name = line.type
            else:
                line.name = '/'

    @api.onchange('type')
    def onchange_type(self):
        for line in self:
            if line.type == 'precarriage':
                line.destination_location_id = line.shipment_id.source_location_id
            if line.type == 'oncarriage':
                line.source_location_id = line.shipment_id.destination_location_id


class FreightRouteService(models.Model):
    _name = 'freight.route.service'
    _description = 'Freight Route Service'

    service_id = fields.Many2one('product.product', 'Service', domain="[('type','=','service')]")
    currency_id = fields.Many2one('res.currency', 'Currency')
    name = fields.Char(string='Description')
    cost = fields.Float('Cost')
    sale = fields.Float('Sale')
    partner_id = fields.Many2one('res.partner', 'Vendor')


class CrmFreightLine(models.Model):
    _name = 'freight.freight.line'

    sale_id = fields.Many2one('sale.order')
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')
    name = fields.Char(string='Description')
    check = fields.Boolean()
    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    product_id = fields.Many2one('product.product', string='service')
    container_id = fields.Many2one('freight.container', 'Container Type',copy=False)
    container_no_ids = fields.Many2many('freight.container.no', 'container_rel_6',copy=False, string='Container No')
    second_container_no_ids = fields.Many2many('freight.container.no', 'container_rel_90')
    container_no_domain = fields.Char(compute='compute_container_no_domain')
    currency_id = fields.Many2one('res.currency', 'Currency')
    qty = fields.Float(string='Quantity', default=1.0)
    price_sale = fields.Float(string='Price Sale')
    price_cost = fields.Float(string='Price Cost')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    charger_weight = fields.Float('Chargeable Weight')
    source_location_id = fields.Many2one('freight.port', string='Port of Loading', compute='compute_location_id')
    destination_location_id = fields.Many2one('freight.port', string='Port of Destination', compute='compute_location_id')
    carrier_id = fields.Many2one('res.partner', string="Carrier")
    shipping_line_id = fields.Many2one('res.partner', 'Shipping Line', related='shipment_id.shipping_line_id',readonly=False,store=True)
    agent_id = fields.Many2one('res.partner', 'Agent', related='shipment_id.agent_id',readonly=False,store=True)
    rates_id = fields.Many2one('freight.rate.price', string='Freight Rates')
    expiration_date = fields.Date(string='Expiration Date', related='rates_id.date_to')
    available_fright_rates_id = fields.Many2many('freight.rate.price', string='Freight Rates',
                                                 compute='compute_available_frights_rates')
    available_container_id = fields.Many2many('freight.container', string='Container Type',copy=False,
                                              compute='compute_available_container')
    available_package_id = fields.Many2many('freight.package', string='package Type',
                                              compute='compute_available_package')
    free_in_time = fields.Integer(string="FreeTime (Days)")
    t_time = fields.Integer(string="T.time (Days)")
    vessel_date = fields.Date()
    second_date = fields.Date()
    customer_id = fields.Many2one('res.partner')

    @api.onchange('currency_id', )
    def onchange_currency_id(self):
        for rec in self:
            if not rec.sale_currency_id:
                rec.sale_currency_id = rec.currency_id.id

    @api.depends('shipment_id')
    def compute_available_container(self):
        for rec in self:
            rec.available_container_id = rec.shipment_id.freight_orders.mapped('container_id.id')

    @api.depends('shipment_id')
    def compute_available_package(self):
        for rec in self:
            rec.available_package_id = rec.shipment_id.freight_packages.mapped('package.id')

    package = fields.Many2one('freight.package', 'Package')
    freight_operator = fields.Many2one('res.users', related='shipment_id.freight_operator')
    sale_id = fields.Many2one('sale.order')
    main_measure = fields.Float('FRT')

    total_cost = fields.Float(compute='_onchange_get_tot_cost', store=True)
    total_sale = fields.Float(compute='_onchange_get_tot_cost', store=True)
    price_for_one_container = fields.Float()

    @api.onchange('total_sale', 'qty')
    def get_price_for_one_container(self):
        for rec in self:
            rec.price_for_one_container = 0.0
            if rec.qty > 0:
                rec.price_for_one_container = rec.total_sale / rec.qty

    @api.depends('qty', 'price_cost', 'price_sale')
    def _onchange_get_tot_cost(self):
        for rec in self:
            rec.total_cost = rec.qty * rec.price_cost
            rec.total_sale = rec.qty * rec.price_sale

    @api.onchange('container_no_id')
    def onchange_container_no_id(self):
        if self.container_no_id:
            if self.second_container_no_id:
                self.second_container_no_id.state = 'available'
            self.container_no_id.state = 'used'
            self.second_container_no_id = self.container_no_id

    # @api.depends('volume', 'gross_weight')
    # def compute_main_measure(self):
    #     for rec in self:
    #         if rec.volume and rec.gross_weight:
    #             rec.main_measure = max(rec.volume, rec.gross_weight)
    #         else:
    #             rec.main_measure = 0.0

    @api.depends('container_id', 'shipment_id', 'destination_location_id', 'source_location_id', 'package')
    def compute_available_frights_rates(self):
        for rec in self:
            if rec.container_id:
                rec.available_fright_rates_id = self.env['freight.rate.price'].sudo().search(
                    [('product_id', '=', rec.product_id.id),
                     ('container_id', '=', rec.container_id.id),
                     ('pod_id', '=', rec.destination_location_id.id),
                     ('pol_id', '=', rec.source_location_id.id),
                     ('state', '=', 'run'),
                     ]).ids
                print(self.available_fright_rates_id.ids, 'uuuuu')
            else:
                self.available_fright_rates_id = self.env['freight.rate.price'].sudo().search(
                    [('product_id', '=', rec.product_id.id),
                     ('package', '=', rec.package.id),
                     ('pod_id', '=', rec.destination_location_id.id),
                     ('pol_id', '=', rec.source_location_id.id),
                     ('state', '=', 'run'),
                     ]).ids
                print(self.available_fright_rates_id.ids, 'uuuuu')

    @api.onchange('qty', 'rates_id', 'container_id', 'product_id', 'package')
    def get_cost_price(self):
        for rec in self:
            if rec.shipment_id.transport == 'ocean':
                if rec.shipment_id.ocean_shipment_type == 'fcl':
                    rec.price_cost = rec.qty * rec.rates_id.freight_price
                if rec.shipment_id.ocean_shipment_type == 'lcl':
                    rec.price_cost = rec.main_measure * rec.rates_id.volume
            if rec.shipment_id.transport == 'air':
                rec.price_cost = rec.main_measure * rec.rates_id.air_freight_per_kg
            rec.currency_id = rec.rates_id.currency_id.id
            if rec.rates_id.is_shipping_line == False:
                rec.carrier_id = rec.rates_id.carrier_id.id
                rec.agent_id = rec.rates_id.agent_id.id
                rec.shipping_line_id = False
            if rec.rates_id.is_shipping_line == True:
                rec.shipping_line_id = rec.rates_id.partner_id.id
                rec.carrier_id = False
                rec.agent_id = False

    @api.depends('shipment_id.destination_location_id', 'shipment_id.source_location_id', 'shipment_id', 'product_id')
    def compute_location_id(self):
        for line in self:
            line.destination_location_id = False
            line.source_location_id = False
            if line.shipment_id.freight_check:
                line.destination_location_id = line.shipment_id.destination_location_id.id
                line.source_location_id = line.shipment_id.source_location_id.id

    @api.depends('container_id')
    def compute_container_no_domain(self):
        for rec in self:
            if rec.container_id and rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('container_id', '=', rec.container_id.id), ('state', '=', 'available'),
                     ('operation_id', '=', rec.shipment_id.ids[0])]
                )
            elif rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('operation_id', '=', rec.shipment_id.ids[0])]
                )
            else:
                rec.container_no_domain = []


class CrmTransportLine(models.Model):
    _name = 'freight.transport.line'

    sale_id = fields.Many2one('sale.order')
    name = fields.Char(string='Description',related='product_id.name')
    check = fields.Boolean()
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')
    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    product_id = fields.Many2one('product.product', string='Service')
    container_id = fields.Many2one('freight.container', 'Container Type',copy=False)
    container_no_ids = fields.Many2many('freight.container.no','container_rel_9', string='Container No')
    second_container_no_ids = fields.Many2many('freight.container.no','container_rel_20')
    container_no_domain = fields.Char(compute='compute_container_no_domain')
    currency_id = fields.Many2one('res.currency', 'Currency')
    tracking_agent = fields.Many2one('res.partner', string='Trucking Agent')
    source_location_id = fields.Many2one('freight.port', string='Port of Loading')
    destination_location_id = fields.Many2one('freight.port', string='Port of Destination')
    qty = fields.Float(string='Quantity', default=1.0)
    sale_price = fields.Float(string='Sale Price')
    cost_price = fields.Float(string='Cost Price')
    package = fields.Many2one('freight.package', 'Package')
    transport_operator = fields.Many2one('res.users', related='shipment_id.transport_operator')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    charger_weight = fields.Float('Chargeable Weight')

    available_package_id = fields.Many2many('freight.package', string='package Type',
                                            compute='compute_available_package')
    teu = fields.Float('TEU', related='container_id.teu')
    truck_no = fields.Char('Truck NO.')
    chargeable_weight = fields.Float('chargeable Weight (KG)')
    qty_from = fields.Float(string="From")
    qty_to = fields.Float(string="To")
    total_container_count = fields.Integer(readonly=True)
    residual_container_count = fields.Integer(readonly=True)
    total_qty = fields.Float(string="Total Qty", )
    price_for_one_container = fields.Float()
    total_cost = fields.Float(compute='_onchange_get_tot_cost', store=True)
    total_sale = fields.Float(compute='_onchange_get_tot_cost', store=True)
    available_container_id = fields.Many2many('freight.container', string='Container Type', copy=False,
                                              compute='compute_available_container')
    login_of_date = fields.Date(string='Loading of Date')
    pickup_address = fields.Char()
    delivery_address = fields.Char()
    compass = fields.Boolean()
    compass_address = fields.Char()
    customer_id = fields.Many2one('res.partner')

    @api.onchange('currency_id', )
    def onchange_currency_id(self):
        for rec in self:
            if not rec.sale_currency_id:
                rec.sale_currency_id = rec.currency_id.id
    @api.depends('shipment_id')
    def compute_available_container(self):
        for rec in self:
            rec.available_container_id = rec.shipment_id.freight_orders.mapped('container_id.id')

    @api.depends('qty', 'cost_price', 'sale_price')
    def _onchange_get_tot_cost(self):
        for rec in self:
            rec.total_cost = rec.qty * rec.cost_price
            rec.total_sale = rec.qty * rec.sale_price

    @api.onchange('total_price', 'qty')
    def get_price_for_one_container(self):
        for rec in self:
            rec.price_for_one_container = 0.0
            if rec.total_qty > 0:
                rec.price_for_one_container = rec.total_price / rec.qty

    # @api.onchange('container_id', 'qty', )
    # def get_container_total(self):
    #     for rec in self:
    #         if rec.container_id:
    #             total_container_ids = self.env['freight.order'].search(
    #                 [('container_id', '=', rec.container_id.id), ('shipment_id', '=', rec.shipment_id._origin.id)])
    #             rec.total_container_count = len(total_container_ids)
    #             rec.residual_container_count = rec.total_container_count - rec.shipment_id.transport_qty_count
    #             if rec.container_id and rec.residual_container_count < 0:
    #                 raise UserError(_('Please Check Container Qty'))

    @api.depends('shipment_id')
    def compute_available_package(self):
        for rec in self:
            rec.available_package_id = rec.shipment_id.freight_packages.mapped('package.id')

    @api.depends('qty', 'cost_price', 'sale_price')
    def _onchange_get_tot_cost(self):
        for rec in self:
            rec.total_cost = rec.qty * rec.cost_price
            rec.total_sale = rec.qty * rec.sale_price

    @api.onchange('sale_id')
    def onchange_sale_id(self):
        for rec in self:
            if rec.sale_id:
                rec.sale_id.order_line.create({
                    'product_id': self.product_id.id,
                    'product_uom_qty': self.qty,
                    'price_unit': self.sale_price,
                    'currency_id': self.currency_id.id,
                    'order_id': self.sale_id.id
                })

    @api.depends('container_id')
    def compute_container_no_domain(self):
        for rec in self:
            if rec.container_id and rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('container_id', '=', rec.container_id.id), ('state', '=', 'available'),
                     ('operation_id', '=', rec.shipment_id.ids[0])]
                )
            elif rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('operation_id', '=', rec.shipment_id.ids[0])]
                )
            else:
                rec.container_no_domain = []

    def action_open_create_way_bill(self):
        line_list = []
        view_id = self.env.ref('freight.view_way_bill_form').id
        name = _('Create Way Bill')
        for rec in self:
            line_list.append((0, 0, {
                "product_id": rec.product_id.id,
                "qty": rec.qty,
                "gross_weight": rec.gross_weight,
                "net_weight": rec.net_weight,
                "package": rec.package.id,
                "name": rec.name,
                "volume": rec.volume,
                "source_location_id": rec.source_location_id.id,  # Include source location
                "destination_location_id": rec.destination_location_id.id,  # Include destination location
            }))
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'way.bill',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_transport_line_id': self.id,
                'default_shipment_id': self.shipment_id.id,
                'default_vessel_id': self.shipment_id.vessel_id.id,
                'default_customer_id': self.shipment_id.customer_id.id,
                'default_shipper_id': self.shipment_id.shipper_id.id,
                'default_consignee_id': self.shipment_id.consignee_id.id,
                'default_agent_id': self.shipment_id.agent_id.id,
                'default_source_location_id': self.shipment_id.source_location_id.id,
                'default_destination_location_id': self.shipment_id.destination_location_id.id,
                'default_transport_ids': line_list,
            }
        }



class CrmClearanceLine(models.Model):
    _name = 'freight.clearance.line'

    sale_id = fields.Many2one('sale.order')
    name = fields.Char(string='Description',related='product_id.name')
    check = fields.Boolean()
    clearance_company = fields.Many2one('res.partner')
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')

    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    product_id = fields.Many2one('product.product', string='Service')
    container_id = fields.Many2one('freight.container', 'Container Type',copy=False)
    container_no_ids = fields.Many2many('freight.container.no', 'container_rel_77', string='Container No')
    second_container_no_ids = fields.Many2many('freight.container.no', 'container_rel_27')
    container_no_domain = fields.Char(compute='compute_container_no_domain')
    currency_id = fields.Many2one('res.currency', 'Currency')
    destination_location_id = fields.Many2one('freight.port', string='Port of Destination')
    cost = fields.Float(string='Cost')
    qty = fields.Float(string='Quantity', default=1.0)
    price = fields.Float(string='Price')
    port_id = fields.Many2one('freight.port', string='Port')
    package = fields.Many2one('freight.package', 'Package')
    clearance_operator = fields.Many2one('res.users', related='shipment_id.clearance_operator')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    charger_weight = fields.Float('Chargeable Weight')
    available_package_id = fields.Many2many('freight.package', string='package Type',
                                            compute='compute_available_package')
    available_container_id = fields.Many2many('freight.container', string='Container Type', copy=False,
                                              compute='compute_available_container')
    compass = fields.Boolean()
    compass_address = fields.Char()
    customer_id = fields.Many2one('res.partner')

    @api.onchange('currency_id', )
    def onchange_currency_id(self):
        for rec in self:
            if not rec.sale_currency_id:
                rec.sale_currency_id = rec.currency_id.id

    @api.depends('shipment_id')
    def compute_available_container(self):
        for rec in self:
            rec.available_container_id = rec.shipment_id.freight_orders.mapped('container_id.id')

    @api.depends('shipment_id')
    def compute_available_package(self):
        for rec in self:
            rec.available_package_id = rec.shipment_id.freight_packages.mapped('package.id')

    @api.onchange('sale_id')
    def onchange_sale_id(self):
        for rec in self:
            if rec.sale_id:
                rec.sale_id.order_line.create({
                    'product_id': self.product_id.id,
                    'product_uom_qty': self.qty,
                    'price_unit': self.price,
                    'currency_id': self.currency_id.id,
                    'order_id': self.sale_id.id
                })

    @api.onchange('container_no_id')
    def onchange_container_no_id(self):
        if self.container_no_id:
            if self.second_container_no_id:
                self.second_container_no_id.state = 'available'
            self.container_no_id.state = 'used'
            self.second_container_no_id = self.container_no_id

    @api.depends('container_id')
    def compute_container_no_domain(self):
        for rec in self:
            if rec.container_id and rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('container_id', '=', rec.container_id.id), ('state', '=', 'available'),
                     ('operation_id', '=', rec.shipment_id.ids[0])]
                )
            elif rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('operation_id', '=', rec.shipment_id.ids[0])]
                )
            else:
                rec.container_no_domain = []

 
class CrmTransitLine(models.Model):
    _name = 'freight.transit.line'

    sale_id = fields.Many2one('sale.order')
    name = fields.Char(string='Description',related='product_id.name')
    check = fields.Boolean()
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')
    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    product_id = fields.Many2one('product.product', string='Service')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading', index=True, required=True)
    letter_id = fields.Many2one('letter.guarantee', 'letter', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', index=True, required=True)
    currency_id = fields.Many2one('res.currency', 'Currency')
    custom_fees = fields.Float(string='Custom Fees')
    percentage_id = fields.Many2one('transit.percent', string='Percentage')
    amount = fields.Float(string='Amount')
    minimum_amount = fields.Float(string='Minimum Amount')
    final_amount = fields.Float(string='Final Amount',compute='compute_final_amount')
    container_id = fields.Many2one('freight.container', 'Container Type',copy=False)
    container_no_ids = fields.Many2many('freight.container.no', 'container_rel_88', string='Container No')
    second_container_no_ids = fields.Many2many('freight.container.no', 'container_rel_23')
    container_no_domain = fields.Char(compute='compute_container_no_domain')
    remaining_amount = fields.Float(string='Remaining Amount')
    visible = fields.Boolean(string='Visible', default=False)
    package = fields.Many2one('freight.package', 'Package')
    transit_operator = fields.Many2one('res.users', related='shipment_id.transit_operator')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    charger_weight = fields.Float('Chargeable Weight')
    available_package_id = fields.Many2many('freight.package', string='package Type',
                                            compute='compute_available_package')
    available_container_id = fields.Many2many('freight.container', string='Container Type', copy=False,
                                              compute='compute_available_container')
    customer_id = fields.Many2one('res.partner')

    @api.onchange('currency_id', )
    def onchange_currency_id(self):
        for rec in self:
            if not rec.sale_currency_id:
                rec.sale_currency_id = rec.currency_id.id

    @api.depends('shipment_id')
    def compute_available_container(self):
        for rec in self:
            rec.available_container_id = rec.shipment_id.freight_orders.mapped('container_id.id')

    @api.depends('shipment_id')
    def compute_available_package(self):
        for rec in self:
            rec.available_package_id = rec.shipment_id.freight_packages.mapped('package.id')

    @api.onchange('sale_id')
    def onchange_sale_id(self):
        for rec in self:
            if rec.sale_id:
                rec.sale_id.order_line.create({
                    'product_id': self.product_id.id,
                    'product_uom_qty': self.qty,
                    'price_unit': self.final_amount,
                    'currency_id': self.currency_id.id,
                    'order_id': self.sale_id.id
                })

    @api.onchange('container_no_id')
    def onchange_container_no_id(self):
        if self.container_no_id:
            if self.second_container_no_id:
                self.second_container_no_id.state = 'available'
            self.container_no_id.state = 'used'
            self.second_container_no_id = self.container_no_id

    @api.depends('container_id')
    def compute_container_no_domain(self):
        for rec in self:
            if rec.container_id and rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('container_id', '=', rec.container_id.id), ('state', '=', 'available'),
                     ('operation_id', '=', rec.shipment_id.ids[0])]
                )
            elif rec.shipment_id.ids:
                rec.container_no_domain = json.dumps(
                    [('operation_id', '=', rec.shipment_id.ids[0])]
                )
            else:
                rec.container_no_domain = []

    @api.depends('amount', 'minimum_amount','percentage_id')
    def compute_final_amount(self):
        for rec in self:
            if rec.percentage_id:
                if rec.amount and rec.minimum_amount:
                    rec.final_amount = max(rec.amount, rec.minimum_amount)
                else:
                    rec.final_amount = 0.0
            else:
                rec.final_amount = rec.amount
  

class CrmWarehouseLine(models.Model):
    _name = 'freight.warehouse.line'

    sale_id = fields.Many2one('sale.order')
    name = fields.Char(string='Description')
    check = fields.Boolean()
    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    product_id = fields.Many2one('product.product', string='Service')
    currency_id = fields.Many2one('res.currency', 'Currency')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    package_id = fields.Many2one('freight.package', 'Package')
    warehouse_id = fields.Many2one('stock.warehouse', string='Storage Warehouse')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    amount = fields.Float(string='Amount')
    warehousing_operator = fields.Many2one('res.users', related='shipment_id.warehousing_operator')
    customer_id = fields.Many2one('res.partner')

    @api.onchange('sale_id')
    def onchange_sale_id(self):
        for rec in self:
            if rec.sale_id:
                rec.sale_id.order_line.create({
                    'product_id': self.product_id.id,
                    'product_uom_qty': self.qty,
                    'price_unit': self.amount,
                    'currency_id': self.currency_id.id,
                    'order_id': self.sale_id.id
                })




class TargetPriceLine(models.Model):
    _name = 'target.price.line'

    shipment_id = fields.Many2one('freight.operation', 'Shipment ID')
    lead_id = fields.Many2one('crm.lead', 'Lead ID')
    container_id = fields.Many2one('freight.container', 'Container Type',copy=False)
    description = fields.Char('Description')
    target_price = fields.Float('target Price')
    final_price = fields.Float('Final Price')
    date = fields.Date('Date', default=lambda self: fields.Date.context_today(self))


class TotalContainer(models.Model):
    _name = 'total.container'
    _rec_name = 'container_id'
    operation_id = fields.Many2one('freight.operation')
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_count = fields.Integer('Count')


class CrmTotalContainer(models.Model):
    _name = 'crm.total.container'
    _rec_name = 'container_id'
    lead_id = fields.Many2one('crm.lead')
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_count = fields.Integer('Count')
