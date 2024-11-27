from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from odoo.exceptions import AccessError, UserError, ValidationError

class CrmInsuranceLine(models.Model):
    _name = 'crm.insurance.line'

    name = fields.Char(string='Policy No.')
    check = fields.Boolean()
    lead_id = fields.Many2one('crm.lead', 'Lead ID')
    sale_id = fields.Many2one('sale.order', )
    product_id = fields.Many2one('product.product', string='Service')
    insurance_company = fields.Many2one('res.partner', string='Insurance Company')
    currency_id = fields.Many2one('res.currency', 'Currency')
    destination_location_id = fields.Many2one('freight.port', string='Port of Discharge')
    cost = fields.Float(string='Cost')
    qty = fields.Float(string='Quantity', default=1.0)
    price = fields.Float(string='Sale Price')
    
class Customs(models.Model):
    _name = 'crm.customs'

    #premitive fields
    name = fields.Char()

class Lead(models.Model):
    _inherit = 'crm.lead'

    def _get_pricing_domain(self):
        pricing_group_id = self.env.ref('freight.group_crm_pricing_user').id
        obj_group = self.env['res.groups'].sudo().search([('id', '=', pricing_group_id)])
        obj_group_users = obj_group.users.mapped('id')
        return [('id', 'in', obj_group_users)]

    @api.depends('packages_line_ids.charger_weight')
    def compute_total_chargeable_weight(self):
        for rec in self:
            rec.chargeable_weight = sum(self.packages_line_ids.mapped('charger_weight'))

    @api.depends('packages_line_ids.gross_weight','container_line_ids.gross_weight')
    def compute_gross_weight(self):
        for rec in self:
            if rec.transport == 'air':
                rec.weight = sum(self.packages_line_ids.mapped('gross_weight'))
            else:
                rec.weight = sum(self.container_line_ids.mapped('gross_weight'))

    @api.depends('container_line_ids.net_weight')
    def compute_net_weight(self):
        for rec in self:
            rec.net_weight = sum(self.container_line_ids.mapped('net_weight'))

    @api.depends('container_line_ids.volume', 'packages_line_ids.volume')
    def compute_total_volume(self):
        for rec in self:
            if rec.transport == 'air':
                rec.volume = sum(self.packages_line_ids.mapped('volume'))
            else:
                rec.volume = sum(self.container_line_ids.mapped('volume'))

    @api.onchange('container_line_ids.teu')
    def compute_teu(self):
        for rec in self:
            rec.teu = sum(self.container_line_ids.mapped('teu'))

    @api.depends('container_line_ids')
    def _is_compute_containers(self):
        for record in self:
            container_ids = list(set(record.container_line_ids.mapped('container_id.id')))
            container_count_list = []
            record.total_container_ids = False
            for container in container_ids:
                order_lines = record.container_line_ids.filtered(lambda c: c.container_id.id == container)
                vals = {
                    'container_id': container,
                    'container_count': len(order_lines)
                }
                container_count_list.append((0, 0, vals))
            record.total_container_ids = container_count_list
            record.is_container_computed = True
            
    is_container_computed = fields.Boolean(compute="_is_compute_containers")
    total_container_ids = fields.One2many('crm.total.container', 'lead_id', string='Total Container')
    

    direction = fields.Selection(([('import', 'Import'), ('export', 'Export'), ('local', 'Trans Shipment')]),
                                 default='import',
                                 required=True, string='Direction')
    weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    net_weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    pieces = fields.Float('Pieces')
    weight = fields.Float('Gross Weight', compute='compute_gross_weight')
    net_weight = fields.Float('Net Weight', compute='compute_net_weight')
    chargeable_weight = fields.Float('chargeable Weight',
                                     compute='compute_total_chargeable_weight')
    volume = fields.Float('Volume (CBM)', compute='compute_total_volume',)
    els_call_count = fields.Integer(compute='_compute_els_calls_count', string="Calls")
    operation_type = fields.Selection([('cargo', 'Cargo'), ('coria', 'Courier')], string='Operation Type')

    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land'), ]),
                                 string='Transport')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bulk')]), string='Ocean Shipment Type')
    inland_shipment_type = fields.Selection(([('ftl', 'FTL'), ('ltl', 'LTL')]), string='Inland Shipment Type')
    teu = fields.Float('TEU',)
    faw = fields.Float('FEU',)
    cbm = fields.Float('CBM')
    frt = fields.Float('FRT')
    operation = fields.Selection([('direct', 'Direct'), ('house', 'Back to Back'), ('master', 'Master')], string='Operation')
    shipper_id = fields.Many2one('res.partner', 'Shipper')
    carrier_id = fields.Many2one('res.partner', string="Carrier")
    consignee_id = fields.Many2one('res.partner', 'Consignee')
    shipping_line_id = fields.Many2one('res.partner', 'Shipping Line')
    agent_id = fields.Many2one('res.partner', 'Agent')
    no_employee = fields.Integer('No of Employees')
    container_line_ids = fields.One2many('crm.container.line', 'crm_id', copy=True)
    packages_line_ids = fields.One2many('crm.package.line', 'crm_id', copy=True)
    freight_line_ids = fields.One2many('crm.freight.line', 'crm_id', copy=True)
    transport_line_ids = fields.One2many('crm.transport.line', 'crm_id', copy=True)
    clearance_line_ids = fields.One2many('crm.clearance.line', 'crm_id', copy=True)
    clearance_inspection_line_ids = fields.One2many('inspection.clearance.line', 'crm_id', copy=True)
    transit_line_ids = fields.One2many('crm.transit.line', 'crm_id', copy=True)
    warehouse_line_ids = fields.One2many('crm.warehouse.line', 'crm_id')
    control = fields.Selection(([('con', 'Control'), ('notcon', 'Not Control')]), string='Control')
    freight_check = fields.Boolean(string='Freight')
    is_pricing = fields.Boolean()
    is_ready = fields.Boolean(compute='_compute_last_stage', )
    pricing_user_id = fields.Many2one('res.users', string='Pricing Person', index=True, tracking=True,
                                      domain=_get_pricing_domain)
    transport_check = fields.Boolean(string='Transportation')
    clearance_check = fields.Boolean(string="Clearance")
    transit_check = fields.Boolean(string='Transit')
    container_check = fields.Boolean(string='Container')
    package_check = fields.Boolean(string='package')
    handling_check = fields.Boolean(string='Handling')
    documentation_check = fields.Boolean(string='Documentation')
    insurance_check = fields.Boolean(string='Insurance')
    warehousing_check = fields.Boolean(string='Warehousing')
    picking_packing_check = fields.Boolean(string='Picking & Packing')
    freight_count = fields.Integer(compute='_compute_freight_count')
    transport_qty_count = fields.Integer()
    clearance_qty_count = fields.Integer()
    purchase_count = fields.Integer(compute='_compute_purchase_data', string="Purchase")
    source_location_id = fields.Many2one('freight.port', 'Port of loading', )
    source_country_id = fields.Many2one('res.country', 'Country', )
    destination_country_id = fields.Many2one('res.country', 'Country', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', )
    custom_id = fields.Many2one('crm.customs')
    incoterm_id = fields.Many2one('lead.incoterm', 'Incoterm', )
    up_to_incoterm_id = fields.Many2one('lead.up_to_incoterm', 'Up To Incoterm', )
    period_id = fields.Many2one('lead.period', 'Period', )
    type_id = fields.Many2one('lead.type', 'Type', )
    commodity_id = fields.Many2one('lead.commodity', 'Commodity', )
    commodity_origin = fields.Char('Origin of Commodity')
    name_seq = fields.Char(default='/')
    pickup_address = fields.Char()
    dangerous_goods = fields.Boolean('Dangerous Goods')
    delivery_address = fields.Char()
    contract_type = fields.Selection(string='Oportunity Type', selection=[('spot', 'Spot'), ('cont', 'Contract')])
    assigned = fields.Boolean(compute='_compute_is_assigned', store=True)
    create_id = fields.Many2one(
        'res.users', string='Lead Creator', default=lambda self: self.env.user,
        domain="['&', ('share', '=', False), ('company_ids', 'in', user_company_ids)]",
        check_company=True, index=True, tracking=True)
    freight_term = fields.Selection([('collect', 'Collect'), ('prepaid', 'Prepaid')])
    last_stage_id = fields.Many2one('crm.stage', compute='_compute_last_stage', store=True)
    insurance_line_ids = fields.One2many('crm.insurance.line', 'lead_id', copy=True)
    dry = fields.Boolean()
    fresh = fields.Boolean()
    frozen = fields.Boolean()
    stackable = fields.Boolean()
    non_stackable = fields.Boolean()
    none_stackable = fields.Boolean()
    vas = fields.Boolean()
    dry_type = fields.Selection(([('dry', 'Dry'), ('fresh', 'Fresh'), ('frozen', 'Frozen')]))
    stackable_type = fields.Selection(([('stackable', 'Stackable'), ('non_stackable', 'Non Stackable')]), string='Packages stackable')
    to_compute_vas = fields.Boolean(compute="_to_compute_vas")
    price_air_ids = fields.One2many('clearance.crm.price.air.line', 'lead_id', copy=True)
    price_ocean_ids = fields.One2many('clearance.crm.price.container.line', 'lead_id', copy=True)
    this_ocean_fcl = fields.Boolean()
    this_air_clear = fields.Boolean()
    transpor_ocean_fcl = fields.Boolean()
    transport_air = fields.Boolean()
    release_type = fields.Selection([
        ('final_import', 'Final Import'),
        ('temporary_permission', 'Temporary Permission'),
        ('drawback', 'Drawback'),
        ('transit', 'Transit'),
        ('exemptions', 'Exemptions')
    ], string='Release system')
    jaffi_no = fields.Char(string="Jaffi NO.")

    def generate_from_the_orders(self):
        for line in self:
            packages = []
            for order in line.container_line_ids:
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
                                        'crm_id': line.id}))
            self.packages_line_ids.unlink()
            self.write({'packages_line_ids': packages})

    @api.depends('freight_check')
    def _to_compute_vas(self):
        for rec in self:
            if not rec.freight_check:
                rec.vas = True
                rec.to_compute_vas = True
            else:
                rec.vas = False
                rec.to_compute_vas = False

    @api.depends('stage_id')
    def _compute_last_stage(self):
        for rec in self:
            if rec.stage_id.is_won and not rec.last_stage_id.is_won and rec.user_id != rec.env.user:
                pass
                # raise UserError(_('Only owner opportunity can transport it to won stage '))
            elif rec.stage_id.is_won and not rec.last_stage_id.is_won and rec.user_id == rec.env.user:
                freight_ids = rec.env['freight.operation'].search([('lead_id', '=', rec.id)])
                if not freight_ids:
                    freight_id = rec.create_freight_shipment()
    #                 for line in rec.container_line_ids:
    #                     if line.container_no_id:
    #                         line.container_no_id.operation_id = freight_id
    # #

    @api.depends('user_id')
    def _compute_is_assigned(self):
        for rec in self:
            if rec.user_id:
                rec.assigned = True
            else:
                rec.assigned = False

    def _send_activity(self,user_ids):
        now = fields.datetime.now()
        date_deadline = now.date()
        activ_list = []
        for user_id in user_ids:
            if user_id and user_id != 'None':
                activity_id = self.sudo().activity_schedule(
                    'mail.mail_activity_data_todo', date_deadline,
                    note=_(
                        '<a>New Opportunity  </a> for <a>Need Pricing</a>') % (
                         ),
                    user_id=user_id,
                    res_id=self._origin.id,
                    summary=_("Opportunity Need Pricing %s")
                )
                activ_list.append(activity_id.id)
        [(4, 0, rec) for rec in activ_list]

    @api.onchange('pricing_user_id')
    def _onchange_pricing_user_id(self):
        for rec in self:
            if self.pricing_user_id:
                self._send_activity([rec.pricing_user_id.id])
                self.env['mail.activity'].create({
                    'summary': 'New Opportunity Need Pricing',
                    'activity_type_id': rec.env.ref('mail.mail_activity_data_todo').id,
                    'res_model_id': rec.env['ir.model']._get(rec._name).id,
                    'res_id': self._origin.id,
                    'user_id': rec.pricing_user_id.id
                })

    @api.depends()
    def _compute_freight_count(self):
        for count in self:
            freight = self.env['freight.operation'].search_count([('lead_id', '=', self.id)])
            count.freight_count = freight


    @api.depends()
    def _compute_purchase_data(self):
        for order in self:
            order.purchase_count = self.env['purchase.order'].sudo().search_count(
                [('lead_id', '=', order.id)])

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        if self.stage_id.is_won:
            if self.partner_id and not self.partner_id.vat:
                raise UserError('You must Add Tax Number For this Customer')
        if self._origin:
            # Move All code To this Section
            origin_state = self._origin.stage_id
            self_state = self.stage_id
            if self_state.is_won and not origin_state.is_won and self.user_id != self.env.user:
                raise UserError(_('Only owner opportunity can transport it to won stage '))
            pricing_order = self.stage_id.search([('is_pricing', '=', True)], limit=1).order
            if pricing_order:
                pricing_manager_group_id = self.env.ref('freight.group_crm_pricing_manager').id
                obj_group = self.env['res.groups'].sudo().search([('id', '=', pricing_manager_group_id)])
                obj_group_users = obj_group.users.mapped('id')
                if self_state.name == 'Pricing':
                    if origin_state.order < self_state.order:
                        for rec in self:
                            if obj_group_users:
                                for user in obj_group_users:
                                    # self._send_activity([user])
                                    self.env['mail.activity'].create({
                                        'summary': 'New Opportunity Need Pricing',
                                        'activity_type_id': rec.env.ref('mail.mail_activity_data_todo').id,
                                        'res_model_id': rec.env['ir.model']._get(rec._name).id,
                                        'res_id': self._origin.id,
                                        'user_id': user
                                    })
                    elif origin_state.order > self_state.order:
                        if not self.pricing_user_id:
                            raise UserError('Please add Pricing Person')
                        else:
                            for rec in self:
                                if self.pricing_user_id:
                                    self._send_activity([rec.pricing_user_id.id])
                                    self.env['mail.activity'].create({
                                        'summary': 'New Opportunity Need Pricing',
                                        'activity_type_id': rec.env.ref('mail.mail_activity_data_todo').id,
                                        'res_model_id': rec.env['ir.model']._get(rec._name).id,
                                        'res_id': self._origin.id,
                                        'user_id': rec.pricing_user_id.id
                                    })
                    for rec in self:
                        if origin_state.name == 'Negotiate' and rec.pricing_user_id:
                            rec._activity_done()
                            rec.env['mail.activity'].create({
                                'summary': 'Negotiate Lead Activity',
                                'note': 'Negotiate Lead Activity',
                                'activity_type_id': rec.env.ref('mail.mail_activity_data_email').id,
                                'res_model_id': rec.env['ir.model']._get(rec._name).id,
                                'res_id': self._origin.id,
                                'user_id': rec.user_id.id
                            })
                        if origin_state.name == 'Ready To Quote' and rec.user_id:
                            rec._activity_done()
                            rec.env['mail.activity'].create({
                                'summary': 'Offer Ready',
                                'note': 'Offer Ready',
                                'activity_type_id': rec.env.ref('mail.mail_activity_data_email').id,
                                'res_model_id': rec.env['ir.model']._get(rec._name).id,
                                'res_id': self._origin.id,
                                'user_id': rec.user_id.id
                            })
                            rec.is_pricing = False

    @api.onchange('freight_line_ids')
    def onchange_shipping_line_id(self):
        for line in self.freight_line_ids:
            if line.carrier_id:
                self.carrier_id = line.carrier_id.id
            if line.shipping_line_id:
                self.shipping_line_id = line.shipping_line_id.id
            if line.agent_id:
                self.agent_id = line.agent_id.id
            else:
                self.agent_id = False               
    @api.onchange('transport_line_ids')
    def onchange_transport_line_id(self):
        for line in self.transport_line_ids:
            if line.pickup_address:
                self.pickup_address = line.pickup_address
            if line.delivery_address:
                self.delivery_address = line.delivery_address

    '''function to set letter_id selected in transit lines (note only one letter in one shipment)'''
    def _activity_done(self):
        activity_ids = self.env['mail.activity'].sudo().search([('res_id', '=', self.id)])
        if activity_ids:
            for act in activity_ids:
                act.action_done()
    @api.onchange('transit_line_ids')
    def onchange_transit_line_ids(self):
        if self.transit_line_ids and self.transit_line_ids[0].letter_id:
            self.letter_id = self.transit_line_ids[0].letter_id

    def button_customer_purchase(self):
        orders = self.env['purchase.order'].sudo().search(
            [('lead_id', '=', self.id)])

        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_rfq")
        action['context'] = {'default_lead_id': self.id,
                             'default_partner_id': self.shipper_id.id,
                             }
        if len(orders) == 1:
            form_view = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [view for view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = orders.id
        else:
            action['domain'] = [('id', 'in', orders.ids)]

        return action

    def create_freight_shipment(self):
        vals = {
            'lead_id': self.id,
            'customer_id': self.partner_id.id,
            'custom_id': self.custom_id.id,
            'carrier_id': self.carrier_id.id,
            'control': self.control,
            'freight_check': self.freight_check,
            'transport_check': self.transport_check,
            'clearance_check': self.clearance_check,
            'transit_check': self.transit_check,
            'handling_check': self.handling_check,
            'documentation_check': self.documentation_check,
            'insurance_check': self.insurance_check,
            'warehousing_check': self.warehousing_check,
            'picking_packing_check': self.picking_packing_check,
            'direction': self.direction,
            'weight_type': self.weight_type,
            'pieces': self.pieces,
            'weight': self.weight,
            'volume': self.volume,
            'net_weight': self.net_weight,
            'dangerous_goods': self.dangerous_goods,
            'chargeable_weight': self.chargeable_weight,
            'transport': self.transport,
            # 'e_transport': self.transport,
            'operation': self.operation,
            'ocean_shipment_type': self.ocean_shipment_type,
            'inland_shipment_type': self.inland_shipment_type,
            'teu': self.teu,
            'faw': self.faw,
            'cbm': self.cbm,
            'frt': self.frt,
            'commodity_origin': self.commodity_origin,
            'dry': self.dry,
            'destination_country_id': self.destination_country_id.id,
            'source_country_id': self.source_country_id.id,
            'stackable_type': self.stackable_type,
            'dry_type': self.dry_type,
            'shipper_id': self.shipper_id.id,
            'consignee_id': self.consignee_id.id,
            'shipping_line_id': self.shipping_line_id.id,
            'customer_service_id': self.partner_id.customer_service_id.id,
            'agent_id': self.agent_id.id,
            'source_location_id': self.source_location_id.id,
            'destination_location_id': self.destination_location_id.id,
            'pickup_address': self.pickup_address,
            'delivery_address': self.delivery_address,
            'freight_term': self.freight_term,
            'sales_contract': True,
        }
        list_fright = []
        for re in self.freight_line_ids:
            list_fright.append((0, 0, {'name': re.name,
                                       'product_id': re.product_id.id,
                                       'container_id': re.container_id.id,
                                       'currency_id': re.currency_id.id,
                                       'sale_currency_id': re.sale_currency_id.id,
                                       'qty': re.qty,
                                       'package': re.package.id,
                                       'price_sale': re.price_sale,
                                       'price_cost': re.price_cost,
                                       'volume': re.volume,
                                       'free_in_time': re.free_in_time,
                                       't_time': re.t_time,
                                       'vessel_date': re.vessel_date,
                                       'second_date': re.second_date,
                                       'gross_weight': re.gross_weight,
                                       'net_weight': re.net_weight,
                                       'source_location_id': re.source_location_id.id,
                                       'destination_location_id': re.destination_location_id.id,
                                       'carrier_id': re.carrier_id.id,
                                       'shipping_line_id': re.shipping_line_id.id,
                                       'agent_id': re.agent_id.id,
                                       'sale_id': re.sale_id.id,
                                       }))
        vals['freight_line_ids'] = list_fright
        list_insurance = []
        for re in self.insurance_line_ids:
            list_insurance.append((0, 0, {'name': re.name,
                                          'product_id': re.product_id.id,
                                          'currency_id': re.currency_id.id,

                                          'price': re.price,
                                          'cost': re.cost,
                                          'destination_location_id': re.destination_location_id.id,
                                          'insurance_company': re.insurance_company.id,
                                          'sale_id': re.sale_id.id,
                                          }))
        vals['insurance_line_ids'] = list_insurance
        list_container = []
        for re in self.container_line_ids:
            list_container.append((0, 0, {'name': re.name,
                                          'container_id': re.container_id.id,
                                          'package': re.package.id,
                                          'type': re.type,
                                          'teu': re.teu,
                                          'login_of_date': re.login_of_date,
                                          'volume': re.volume,
                                          'gross_weight': re.gross_weight,
                                          'net_weight': re.net_weight,
                                          'qty': re.qty,
                                          'seal_no': re.seal_no,
                                          }))
        vals['freight_orders'] = list_container

        list_package = []
        for re in self.packages_line_ids:
            list_package.append((0, 0, {'name': re.name,
                                        'container_id': re.container_id.id,
                                        'package': re.package.id,
                                        # 'type': re.type,
                                        'volume': re.volume,
                                        'gross_weight': re.gross_weight,
                                        'charger_weight': re.charger_weight,
                                        'harmonize': re.harmonize,
                                        'temperature': re.temperature,
                                        'vgm': re.vgm,
                                        'qty': re.qty,
                                        'carrier_seal': re.carrier_seal,
                                        'shipper_seal': re.shipper_seal,
                                        'reference': re.reference,
                                        'dangerous_goods': re.dangerous_goods,
                                        'un_number': re.un_number,
                                        'class_number': re.class_number,
                                        'Package_group': re.Package_group,
                                        'imdg_code': re.imdg_code,
                                        'flash_point': re.flash_point,
                                        'material_description': re.material_description,
                                        }))

        vals['freight_packages'] = list_package

        list_transport = []
        for re in self.transport_line_ids:
            list_transport.append((0, 0, {'name': re.name,
                                          'product_id': re.product_id.id,
                                          'package': re.package.id,
                                          'container_id': re.container_id.id,
                                          'volume': re.volume,
                                          'compass': re.compass,
                                          'compass_address': re.compass_address,
                                          'gross_weight': re.gross_weight,
                                          'net_weight': re.net_weight,
                                          'currency_id': re.currency_id.id,
                                          'sale_currency_id': re.sale_currency_id.id,
                                          'tracking_agent': re.tracking_agent.id,
                                          'source_location_id': re.source_location_id.id,
                                          'destination_location_id': re.destination_location_id.id,
                                          'pickup_address': re.pickup_address,
                                          'delivery_address': re.delivery_address,
                                          'qty': re.qty,
                                          'login_of_date': re.login_of_date,
                                          'sale_price': re.sale_price,
                                          'cost_price': re.cost_price,
                                          'sale_id': re.sale_id.id,
                                          }))
        vals['transport_line_ids'] = list_transport
        list_clearance = []
        for re in self.clearance_line_ids:
            list_clearance.append((0, 0, {'name': re.name,
                                          'product_id': re.product_id.id,
                                          'container_id': re.container_id.id,
                                          'currency_id': re.currency_id.id,
                                          'sale_currency_id': re.sale_currency_id.id,
                                          'destination_location_id': re.destination_location_id.id,
                                          'qty': re.qty,
                                          'compass': re.compass,
                                          'compass_address': re.compass_address,
                                          'cost': re.cost,
                                          'clearance_company': re.clearance_company.id,
                                          'price': re.price,
                                          'volume': re.volume,
                                          'gross_weight': re.gross_weight,
                                          'net_weight': re.net_weight,
                                          'sale_id': re.sale_id.id,
                                          }))
        vals['clearance_line_ids'] = list_clearance

        list_transit = []
        for re in self.transit_line_ids:
            list_transit.append((0, 0, {'name': re.name,
                                        'product_id': re.product_id.id,
                                        'currency_id': re.currency_id.id,
                                        'source_location_id': re.source_location_id.id,
                                        'destination_location_id': re.destination_location_id.id,
                                        'letter_id': re.letter_id.id,
                                        'custom_fees': re.custom_fees,
                                        'percentage_id': re.percentage_id.id,
                                        'amount': re.amount,
                                        'volume': re.volume,
                                        'gross_weight': re.gross_weight,
                                        'net_weight': re.net_weight,
                                        'package': re.package.id,
                                        'sale_id': re.sale_id.id,

                                        }))

        vals['transit_line_ids'] = list_transit
        list_warehouse = []
        for re in self.warehouse_line_ids:
            list_warehouse.append((0, 0, {'name': re.name,
                                          'product_id': re.product_id.id,
                                          'currency_id': re.currency_id.id,
                                          'vendor_id': re.vendor_id.id,
                                          'package_id': re.package_id.id,
                                          'warehouse_id': re.warehouse_id.id,
                                          'product_uom': re.product_uom.id,

                                          }))

        vals['warehouse_line_ids'] = list_warehouse
        fright = self.env['freight.operation'].create(vals)
        return fright

    def action_open_freight(self):
        """ Return the list of freight shipment. """
        self.ensure_one()
        freight_ids = self.env['freight.operation'].search([('lead_id', '=', self.id)])
        print("'''''''''", freight_ids)
        action = {
            'name': _('Freight Shipment'),
            'view_type': 'tree',
            'view_mode': 'list,form',
            'res_model': 'freight.operation',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'domain': [('lead_id', 'in', self.ids)],
        }
        return action

    # inherit function that prepaire sale order values to change customer to be the company not the contact and set new val for contact
    def action_new_quotation(self):
        """ Prepares the context for a new quotation (sale.order) by sharing the values of common fields """
        action = super(Lead, self).action_new_quotation()
        action['context']['default_partner_id'] = self.partner_id.parent_id.id
        action['context']['default_contact_id'] = self.partner_id.id
        return action

    @api.model
    def create(self, vals):
        if not vals.get('name_seq', False) or vals['name_seq'] == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('crm.lead')
        res = super(Lead, self).create(vals)
        return res

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


    def action_open_create_quotation(self):
        view_id = self.env.ref('freight.view_create_quotation_lead_line').id

        name = _('Create Quotation')
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'quotation.lead.wizard',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_lead_id': self.id,

            }
        }

    def action_open_create_rfq(self):
        view_id = self.env.ref('freight.view_create_purchase_lead_line').id
        name = _('Create RFQ')
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'create.lead.po.wizard',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
            }
        }

    @api.depends()
    def _compute_els_calls_count(self):
        for count in self:
            calls = self.env['call.call'].search_count([('lead_id', '=', self.id)])
            count.els_call_count = calls

    def action_open_els_calls(self):
        related_call_ids = self.env['call.call'].search([
            ('lead_id', '=', self.id)
        ]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Calls'),
            'res_model': 'call.call',
            'view_type': 'list',
            'view_mode': 'list',
            'context': {
                        "default_origin": self.name,
                        "default_lead_id": self.id,
                        "default_account_id": self.partner_id.parent_id.id,
                        "default_contact_id": self.partner_id.id,
                        "default_employee_id": self.user_id.employee_id.id,
                        "default_phone": self.phone},
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', related_call_ids)],
        }


class CrmContainerLine(models.Model):
    _name = 'crm.container.line'

    sale_id = fields.Many2one('sale.order')
    crm_id = fields.Many2one('crm.lead', ' opportunity')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ]),
                                 string='Activity')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')
    name = fields.Char(string='Description')
    container_id = fields.Many2one('freight.container', 'Container Type')
    currency_id = fields.Many2one('res.currency', 'Currency')
    package = fields.Many2one('freight.package', 'Package')
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Operation")
    volume = fields.Float('Volume (CBM)',)
    teu = fields.Float('TEU')
    cbm = fields.Float('CBM')
    frt = fields.Float('FRT')
    gross_weight = fields.Float('Gross Weight (KG)')
    qty = fields.Float('Quantity', default=1)
    temp = fields.Float('TEMP')
    hum = fields.Float('HUM')
    vent = fields.Float('VENT')
    login_of_date = fields.Date(string='Loading of Date')
    weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    commodity_id = fields.Many2one('lead.commodity', 'Commodity', )
    seal_no = fields.Char('Seal No')

    def action_duplicate_line(self):
        view_id = self.env.ref('freight.view_create_container_lead_line').id

        name = _('Add a Line')
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'container.lead.wizard',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_line_id': self.id,
                'default_lead_id': self.crm_id.id,
                'default_teu': self.teu,
                'default_container_id': self.container_id.id,
                'default_package': self.package.id,
                'default_type': self.type,
                'default_name': self.name,
                'default_teu': self.teu,
                'default_transport': self.transport,
                'default_qty': self.qty,
            }
        }

    @api.depends('crm_id.ocean_shipment_type', 'crm_id.transport')
    def onchange_transport(self):
        for line in self:
            line.transport = line.crm_id.transport
            line.ocean_shipment_type = line.crm_id.ocean_shipment_type

    @api.onchange('container_id')
    def onchange_container_id(self):
        for rec in self:
            rec.teu = rec.container_id.teu

    @api.onchange('package')
    def onchange_package_id(self):
        for line in self:
            if line.crm_id.transport == 'air':
                return {'domain': {'package': [('air', '=', True)]}}
            if line.crm_id.transport == 'ocean':
                return {'domain': {'package': [('ocean', '=', True)]}}
            if line.crm_id.transport == 'land':
                return {'domain': {'package': [('land', '=', True)]}}


class CrmPackageLine(models.Model):
    _name = 'crm.package.line'

    sale_id = fields.Many2one('sale.order')
    container_id = fields.Many2one('freight.container', 'Container Type', copy=False)
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    container_no_ids = fields.Many2many('freight.container.no', 'container_rel_79990', string='Container No')
    second_container_no_id = fields.Many2one('freight.container.no', 'Container No')

    name = fields.Char(string='Description')
    description = fields.Text(string='Description')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ]),
                                 string='Activity')
    crm_id = fields.Many2one('crm.lead', 'op')
    currency_id = fields.Many2one('res.currency', 'Currency')
    package = fields.Many2one('freight.package', 'Package', required=True)
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float(string='Net Weight (KG)')
    weight = fields.Float('Gross Weight (KG)')
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

    charger_weight = fields.Float('Chargeable Weight')
    commodity_id = fields.Many2one('lead.commodity', 'Commodity', )
    width = fields.Float('Width (KG)')
    height = fields.Float('Height (KG)')
    size = fields.Float('Length')
    main_measure = fields.Float('FRT', compute='compute_main_measure')



    @api.onchange('package')
    def onchange_dangerous_goods(self):
        for rec in self:
            rec.dangerous_goods = rec.crm_id.dangerous_goods

    @api.depends('volume', 'gross_weight')
    def compute_main_measure(self):
        for rec in self:
            if rec.crm_id.operation_type == 'cargo':
                rec.volume = (rec.width * rec.height * rec.size) / 6000
            if rec.crm_id.operation_type == 'coria':
                rec.volume = (rec.width * rec.height * rec.size) / 5000
            rec.charger_weight = max(rec.volume, rec.gross_weight)
            rec.main_measure = max(rec.volume, rec.gross_weight)

    @api.onchange('width', 'height', 'size', 'gross_weight')
    def compute_volume(self):
        for rec in self:
            if rec.crm_id.operation_type == 'cargo':
                rec.volume = (rec.width * rec.height * rec.size) / 6000
            if rec.crm_id.operation_type == 'coria':
                rec.volume = (rec.width * rec.height * rec.size) / 5000
            rec.charger_weight = max(rec.volume, rec.gross_weight)

class CrmFreightLine(models.Model):
    _name = 'crm.freight.line'

    sale_id = fields.Many2one('sale.order')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ]),
                                 string='Activity')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')

    name = fields.Char(string='Description')
    check = fields.Boolean()
    crm_id = fields.Many2one('crm.lead', 'opportunity')
    product_id = fields.Many2one('product.product', string='service')
    container_id = fields.Many2one('freight.container', 'Container Type')
    currency_id = fields.Many2one('res.currency', 'Currency')
    rates_id = fields.Many2one('freight.rate.price', string='Freight Rates')
    available_fright_rates_id = fields.Many2many('freight.rate.price', string='Freight Rates',)
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    free_in_time = fields.Integer(string="FreeTime (Days)")
    t_time = fields.Integer(string="T.time (Days)")
    vessel_date = fields.Date()
    second_date = fields.Date()
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')

    qty = fields.Float('Quantity', required=True)
    price_sale = fields.Float(string='Price Sale')
    price_cost = fields.Float(string='Price Cost')
    volume = fields.Float(string='Volume (CBM)')
    gross_weight = fields.Float(string='Gross Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    weight = fields.Float(string='Gross Weight (KG)')
    source_location_id = fields.Many2one('freight.port',  string='Port of Loading')
    destination_location_id = fields.Many2one('freight.port',  string='Port of Destination')
    carrier_id = fields.Many2one('res.partner', string="Carrier")
    shipping_line_id = fields.Many2one('res.partner', 'Shipping Line')
    agent_id = fields.Many2one('res.partner', 'Agent')
    package = fields.Many2one('freight.package', 'Package')
    target_price = fields.Float(string='target Price')
    expiration_date = fields.Date(string='Expiration Date', related='rates_id.date_to')
    charger_weight = fields.Float('Chargeable Weight')

    available_package_id = fields.Many2many('freight.package', string='package Type',
                                           compute='compute_available_package')

    available_container_id = fields.Many2many('freight.container', string='Container Type',
                                              compute='compute_available_container')

    total_cost = fields.Float(compute='_onchange_get_tot_cost', store=True)
    total_sale = fields.Float(compute='_onchange_get_tot_cost', store=True)
    customer_id = fields.Many2one('res.partner')

    @api.onchange('currency_id', )
    def onchange_currency_id(self):
        for rec in self:
            if not rec.sale_currency_id:
                rec.sale_currency_id = rec.currency_id.id

    @api.depends('crm_id')
    def compute_available_package(self):
        for rec in self:
            rec.available_package_id = rec.crm_id.packages_line_ids.mapped('package.id')

    @api.depends('qty', 'price_cost', 'price_sale')
    def _onchange_get_tot_cost(self):
        for rec in self:
            rec.total_cost = rec.qty * rec.price_cost
            rec.total_sale = rec.qty * rec.price_sale

    # @api.depends('container_id', 'crm_id', 'destination_location_id', 'source_location_id', 'package')
    # def compute_available_frights_rates(self):
    #     for rec in self:
    #         rec.available_fright_rates_id = False
    #         if rec.container_id:
    #             available_fright_rates_id = self.env['freight.rate.price'].sudo().search(
    #                 [('product_id', '=', rec.product_id.id),
    #                  ('container_id', '=', rec.container_id.id),
    #                  ('transport', '=', rec.crm_id.transport),
    #                  ('ocean_shipment_type', '=', rec.crm_id.ocean_shipment_type),
    #                  ('pod_id', '=', rec.destination_location_id.id),
    #                  ('pol_id', '=', rec.source_location_id.id),
    #                  ('state', '=', 'run'),
    #                  ])
    #             # print(available_fright_rates_id, 'uuuuu')
    #             if available_fright_rates_id:
    #                 rec.available_fright_rates_id = available_fright_rates_id.ids
    #         if rec.package:
    #             rec.available_fright_rates_id = self.env['freight.rate.price'].sudo().search(
    #                 [('product_id', '=', rec.product_id.id),
    #                  ('package', '=', rec.package.id),
    #                  ('transport', '=', rec.crm_id.transport),
    #                  ('ocean_shipment_type', '=', rec.crm_id.ocean_shipment_type),
    #                  ('pod_id', '=', rec.destination_location_id.id),
    #                  ('pol_id', '=', rec.source_location_id.id),
    #                  ('state', '=', 'run'),
    #                  ]).ids
                # print(self.available_fright_rates_id.ids,'uuuuu')

    @api.depends('crm_id')
    def compute_available_container(self):
        for rec in self:
            rec.available_container_id = rec.crm_id.container_line_ids.mapped('container_id.id')


    @api.onchange('crm_id', 'product_id')
    def compute_location_id(self):
        for line in self:
            line.destination_location_id = False
            line.source_location_id = False
            if line.crm_id.freight_check:
                line.destination_location_id = line.crm_id.destination_location_id.id
                line.source_location_id = line.crm_id.source_location_id.id




class CrmTransportLine(models.Model):
    _name = 'crm.transport.line'

    sale_id = fields.Many2one('sale.order')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation')]),
                                 string='Activity', default='ocean')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')

    name = fields.Char(string='Description')
    check = fields.Boolean()
    compass = fields.Boolean()
    compass_address = fields.Char()
    crm_id = fields.Many2one('crm.lead', ' opportunity')
    product_id = fields.Many2one('product.product', string='Service')
    container_id = fields.Many2one('freight.container', 'Container Type')
    currency_id = fields.Many2one('res.currency', 'Currency')
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')
    tracking_agent = fields.Many2one('res.partner', string='Trucking Agent')
    source_location_id = fields.Many2one('freight.port', string='Port of Loading')
    destination_location_id = fields.Many2one('freight.port', string='Port of Destination')
    qty = fields.Float('Quantity', required=True, default=1)
    sale_price = fields.Float(string='Sale Price')
    cost_price = fields.Float(string='Cost Price')
    package = fields.Many2one('freight.package', 'Package')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    chargeable_weight = fields.Float('chargeable Weight (KG)')
    amount_from = fields.Float(string="From")
    amount_to = fields.Float(string="To")
    qty_trans_from = fields.Integer(string="From")
    qty_trans_to = fields.Integer(string="To")
    total_container_count = fields.Integer(readonly=True)
    residual_container_count = fields.Integer(readonly=True)
    direction = fields.Selection(([('import', 'Import'), ('export', 'Export'), ('local', 'Trans Shipment')]),
                                 default='import',
                                 string='Direction')

    pickup_address = fields.Char()
    delivery_address = fields.Char()

    charger_weight = fields.Float('Chargeable Weight')

    available_package_id = fields.Many2many('freight.package', string='package Type',
                                            compute='compute_available_package')
    total_cost = fields.Float()
    total_sale = fields.Float(compute='_onchange_get_tot_cost', store=True)
    price_for_one_container = fields.Float(compute='_onchange_get_tot_cost', store=True)
    available_container_id = fields.Many2many('freight.container', string='Container Type',
                                              compute='compute_available_container')
    login_of_date = fields.Date(string='Loading of Date')
    customer_id = fields.Many2one('res.partner')

    @api.onchange('tracking_agent', 'product_id',  'container_id', 'destination_location_id','chargeable_weight')
    def get_sale_price(self):
        if not self.env.user.has_group('freight.group_crm_use_pricing_user'):
            return
        for rec in self:
            rec.sale_price = 0.0
            if rec.crm_id.transport == 'ocean':
                clearance = self.env['transport.rate.price'].sudo().search(
                    [('product_id', '=', rec.product_id.id),
                     ('transport', '=', rec.crm_id.transport),
                     ('agent_id', '=', rec.tracking_agent.id),
                     ('direction', '=', rec.crm_id.direction),
                     ('destination_location_id', '=', rec.destination_location_id.id),
                     ('state', '=', 'run'),
                     ], limit=1)
                if clearance:
                    rec.sale_price = clearance.amount_sale
                    rec.cost_price = clearance.amount_cost
                    rec.currency_id = clearance.currency_id.id
            if rec.crm_id.transport == 'air' and rec.chargeable_weight:
                clearance = self.env['transport.rate.price'].sudo().search(
                    [('product_id', '=', rec.product_id.id),
                     ('transport', '=', rec.crm_id.transport),
                     ('direction', '=', rec.crm_id.direction),
                     ('destination_location_id', '=', rec.destination_location_id.id),
                     ('source_location_id', '=', rec.source_location_id.id),
                     ('agent_id', '=', rec.tracking_agent.id),
                     ('state', '=', 'run'),
                     ], limit=1)
                if clearance:
                    last_id = clearance.price_air_ids.search([])[-1]
                    for clear in clearance.price_air_ids:
                        amount_sale = clear.amount_sale
                        if clear.amount_from <= rec.chargeable_weight <= clear.amount_to:
                            rec.sale_price = amount_sale
                            rec.cost_price = clear.amount_cost
                            rec.currency_id = clearance.currency_id.id
                        if last_id.amount_to < rec.chargeable_weight:
                            remain_gross = rec.chargeable_weight - last_id.amount_to
                            if remain_gross % clearance.other_kg < clearance.other_kg:
                                remaining_gross = remain_gross - remain_gross % clearance.other_kg + clearance.other_kg
                            if remain_gross % clearance.other_kg == 0:
                                remaining_gross = remain_gross
                            new = remaining_gross / clearance.other_kg
                            rec.sale_price = last_id.amount_sale + (new * clearance.other_air_sale)
                            rec.cost_price = clearance.amount_cost
                            rec.currency_id = clearance.currency_id.id


    @api.onchange('currency_id', )
    def onchange_currency_id(self):
        for rec in self:
            if not rec.sale_currency_id:
                rec.sale_currency_id = rec.currency_id.id

    @api.depends('crm_id')
    def compute_available_container(self):
        for rec in self:
            rec.available_container_id = rec.crm_id.container_line_ids.mapped('container_id.id')



    @api.onchange('total_sale', 'qty')
    def get_price_for_one_container(self):
        for rec in self:
            rec.price_for_one_container = 0.0
            if rec.qty > 0:
                rec.price_for_one_container = rec.total_sale / rec.qty

    @api.depends('qty', 'cost_price', 'sale_price')
    def _onchange_get_tot_cost(self):
        for rec in self:
            rec.total_cost = rec.qty * rec.cost_price
            rec.total_sale = rec.qty * rec.sale_price

    @api.depends('crm_id')
    def compute_available_package(self):
        for rec in self:
            rec.available_package_id = rec.crm_id.packages_line_ids.mapped('package.id')

    @api.onchange('crm_id', 'crm_id.pickup_address')
    def compute_pickup_address(self):
        for line in self:
            line.pickup_address = False
            line.delivery_address = False
            if line.crm_id.freight_check:
                line.pickup_address = line.crm_id.pickup_address
                line.delivery_address = line.crm_id.delivery_address


class CrmClearanceLine(models.Model):
    _name = 'crm.clearance.line'

    sale_id = fields.Many2one('sale.order')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ]),
                                 string='Activity', default='ocean')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')

    name = fields.Char(string='Description')
    check = fields.Boolean()
    crm_id = fields.Many2one('crm.lead', 'opportunity')
    product_id = fields.Many2one('product.product', string='Service')
    container_id = fields.Many2one('freight.container', 'Container Type')
    clearance_company = fields.Many2one('res.partner')
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    currency_id = fields.Many2one('res.currency', 'Currency')
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')
    destination_location_id = fields.Many2one('freight.port', string='Port of Destination')
    cost = fields.Float(string='Cost')
    qty = fields.Float('Quantity', required=True, default=1.0)
    price = fields.Float(string='Price')
    package = fields.Many2one('freight.package', 'Package')
    target_price = fields.Float(string='target Price')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    chargeable_weight = fields.Float('chargeable Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    direction = fields.Selection(([('import', 'Import'), ('export', 'Export'), ('local', 'Trans Shipment')]),
                                 default='import',
                                 string='Direction')
    price_for_one_container = fields.Float()
    customer_id = fields.Many2one('res.partner', )
    vendor_id = fields.Many2one('res.partner', )
    available_package_id = fields.Many2many('freight.package', string='package Type',
                                            compute='compute_available_package')

    available_container_id = fields.Many2many('freight.container', string='Container Type',
                                              compute='compute_available_container')
    charger_weight = fields.Float('Chargeable Weight')
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)
    compass = fields.Boolean()
    compass_address = fields.Char()
    amount_from = fields.Float(string="From")
    amount_to = fields.Float(string="To")
    qty_from = fields.Float(string="From")
    qty_to = fields.Float(string="To")
    total_qty = fields.Float(string="Total Qty", )

    @api.onchange('qty_from', 'qty_to')
    def get_qty(self):
        for rec in self:
            if rec.qty_to:
                if rec.qty_from == 0.0:
                    rec.total_qty = rec.qty_to - rec.qty_from
                else:
                    rec.total_qty = rec.qty_to - rec.qty_from + 1

    @api.onchange('currency_id', )
    def onchange_currency_id(self):
        for rec in self:
            if not rec.sale_currency_id:
                rec.sale_currency_id = rec.currency_id.id

    @api.depends('crm_id')
    def compute_available_container(self):
        for rec in self:
            rec.available_container_id = rec.crm_id.container_line_ids.mapped('container_id.id')

    @api.depends('crm_id')
    def compute_available_package(self):
        for rec in self:
            rec.available_package_id = rec.crm_id.packages_line_ids.mapped('package.id')

    @api.onchange('crm_id', 'transport', 'product_id', 'container_id', 'qty_to', 'destination_location_id','chargeable_weight')
    def get_sale_price(self):
        if not self.env.user.has_group('freight.group_crm_use_pricing_user'):
            return
        for rec in self:
            rec.price = 0.0
            if rec.crm_id.transport == 'ocean' and rec.crm_id.ocean_shipment_type == 'lcl':
                clearance = self.env['clearance.rate.price'].sudo().search(
                    [('product_id', '=', rec.product_id.id),
                     ('transport', '=', rec.crm_id.transport),
                     ('direction', '=', rec.crm_id.direction),
                     ('port_id', '=', rec.destination_location_id.id),
                     ('state', '=', 'run'),
                     ], limit=1)
                if clearance:
                    rec.price = clearance.amount_sale
                    rec.cost = clearance.amount_cost
                    rec.currency_id = clearance.currency_id.id
            if rec.crm_id.transport == 'ocean' and rec.crm_id.ocean_shipment_type == 'fcl' and rec.qty_to:
                clearance = self.env['clearance.rate.price'].sudo().search(
                    [('product_id', '=', rec.product_id.id),
                     ('direction', '=', rec.crm_id.direction),
                     ('transport', '=', rec.crm_id.transport),
                     ('port_id', '=', rec.destination_location_id.id),
                     ('state', '=', 'run'),
                     ], limit=1)
                if clearance:
                    last_id = clearance[0].price_ocean_ids.search([('price_id', '=', clearance.id)])[-1]

                    for clear in clearance.price_ocean_ids:
                        if (rec.qty_from == 0.0) or (rec.qty_from == rec.qty_to):
                            if clear.amount_to >= rec.qty_to >= clear.amount_from:
                                rec.price = clear.amount_sale
                                rec.cost = clear.amount_cost
                                rec.currency_id = clearance.currency_id.id
                        elif (rec.qty_to > rec.qty_from) and (
                                rec.qty_from == clear.amount_from and rec.qty_to <= clear.amount_to):
                            qty = rec.qty_to - rec.qty_from + 1
                            rec.price = qty * clear.amount_sale
                            rec.cost = clearance.amount_cost
                            rec.currency_id = clearance.currency_id.id
                    if rec.qty_to > last_id.amount_to:
                        remain_gross = rec.qty_to - last_id.amount_to
                        if remain_gross % clearance.other_container < clearance.other_container:
                            remaining_gross = remain_gross - remain_gross % clearance.other_container + clearance.other_container
                        if remain_gross % clearance.other_container == 0:
                            remaining_gross = remain_gross
                        new = remaining_gross / clearance.other_container
                        rec.price = last_id.amount_to + (new * clearance.other_container_sale)
                        rec.cost = clearance.amount_cost
                        rec.currency_id = clearance.currency_id.id

            if rec.crm_id.transport == 'air' and rec.chargeable_weight:
                clearance = self.env['clearance.rate.price'].sudo().search(
                    [('product_id', '=', rec.product_id.id),
                     ('direction', '=', rec.crm_id.direction),
                     ('transport', '=', rec.crm_id.transport),
                     ('port_id', '=', rec.destination_location_id.id),
                     ('state', '=', 'run'),
                     ], limit=1)
                if clearance:
                    last_id = clearance.price_air_ids.search([])[-1]
                    for clear in clearance.price_air_ids:
                        amount_sale = clear.amount_sale
                        if clear.amount_from <= rec.chargeable_weight <= clear.amount_to:
                            rec.price = amount_sale
                            rec.cost = clear.amount_cost
                            rec.currency_id = clearance.currency_id.id
                        if last_id.amount_to < rec.chargeable_weight:
                            remain_gross = rec.chargeable_weight - last_id.amount_to
                            if remain_gross % clearance.other_kg < clearance.other_kg:
                                remaining_gross = remain_gross - remain_gross % clearance.other_kg + clearance.other_kg
                            if remain_gross % clearance.other_kg == 0:
                                remaining_gross = remain_gross
                            new = remaining_gross / clearance.other_kg
                            rec.price = last_id.amount_sale + (new * clearance.other_air_sale)
                            rec.currency_id = clearance.currency_id.id


class CrmTransitLine(models.Model):
    _name = 'crm.transit.line'

    sale_id = fields.Many2one('sale.order')
    name = fields.Char(string='Description')
    check = fields.Boolean()
    crm_id = fields.Many2one('crm.lead', ' opportunity')
    product_id = fields.Many2one('product.product', string='Service')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading', index=True, required=True)
    letter_id = fields.Many2one('letter.guarantee', 'letter', )
    vendor_id = fields.Many2one('res.partner', 'Vendor', )
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', index=True, required=True)
    currency_id = fields.Many2one('res.currency', 'Currency')
    sale_currency_id = fields.Many2one('res.currency', 'Sale Currency')
    custom_fees = fields.Float(string='Custom Fees')
    percentage_id = fields.Many2one('transit.percent', string='Percentage')
    amount = fields.Float()
    remaining_amount = fields.Float()
    visible = fields.Boolean(string='Visible', default=False)
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_no_id = fields.Many2one('freight.container.no', 'Container No')
    package = fields.Many2one('freight.package', 'Package')
    target_price = fields.Float(string='target Price')
    main_measure = fields.Float('FRT')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ]),
                                 string='Activity')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    available_package_id = fields.Many2many('freight.package', string='package Type',
                                            compute='compute_available_package')
    available_container_id = fields.Many2many('freight.container', string='Container Type',
                                              compute='compute_available_container')
    customer_id = fields.Many2one('res.partner', )
    vendor_id = fields.Many2one('res.partner', )

    @api.depends('crm_id')
    def compute_available_container(self):
        for rec in self:
            rec.available_container_id = rec.crm_id.container_line_ids.mapped('container_id.id')

    @api.depends('crm_id')
    def compute_available_package(self):
        for rec in self:
            rec.available_package_id = rec.crm_id.packages_line_ids.mapped('package.id')

    def letter_amount_confirm(self):
        for rec in self:
            letter = self.env['letter.guarantee'].sudo().search(
                [('name', '=', rec.letter_id.name)])
            if letter.letter_amount and rec.amount:
                new_amount = (letter.letter_amount - rec.amount)
                letter.update({'letter_amount': new_amount})
                rec.visible = True

    @api.onchange('percentage_id', 'custom_fees', 'letter_id')
    def compute_amount(self):
        for rec in self:
            if rec.percentage_id and rec.custom_fees and rec.letter_id:
                rec.remaining_amount = rec.letter_id.letter_remaining_amount + rec.amount
                rec.amount = rec.custom_fees * (rec.percentage_id.percentage_amount / 100)
                if rec.amount != 0:
                    rec.remaining_amount = rec.remaining_amount - rec.amount
                    rec.letter_id.letter_remaining_amount = rec.remaining_amount


class CrmWarehouseLine(models.Model):
    _name = 'crm.warehouse.line'

    sale_id = fields.Many2one('sale.order')
    name = fields.Char(string='Description')
    check = fields.Boolean()
    crm_id = fields.Many2one('crm.lead', ' opportunity')
    product_id = fields.Many2one('product.product', string='Service')
    currency_id = fields.Many2one('res.currency', 'Currency')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    package_id = fields.Many2one('freight.package', 'Package')
    warehouse_id = fields.Many2one('stock.warehouse', string='Storage Warehouse')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    customer_id = fields.Many2one('res.partner')


class CrmClearanceInspectionLine(models.Model):
    _name = 'inspection.clearance.line'

    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')]),
                                 string='Activity', default='ocean')
    sale_id = fields.Many2one('sale.order')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'FCL'), ('lcl', 'LCL'), ('bulk', 'Bulk'), ('break', 'Break Bilk')]), string='Ocean Shipment Type')
    name = fields.Char(string='Description')
    check = fields.Boolean()
    crm_id = fields.Many2one('crm.lead', 'opportunity')
    product_id = fields.Many2one('product.product', string='Service')
    currency_id = fields.Many2one('res.currency', 'Currency')
    destination_location_id = fields.Many2one('freight.port', string='Port of Discharge',)
    cost = fields.Float(string='Cost')
    qty = fields.Float('Quantity', required=True, default=1.0)
    price = fields.Float(string='Price')
    package = fields.Many2one('freight.package', 'Package')
    target_price = fields.Float(string='target Price')
    main_measure = fields.Float('FRT')
    truck_type_id = fields.Many2one('truck.type')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float('Net Weight (KG)')
    branch_id = fields.Many2one('res.branch', string='Branch')
    amount_from = fields.Float(string="From")
    amount_to = fields.Float(string="To")
    qty_from = fields.Float(string="From")
    qty_to = fields.Float(string="To")
    total_qty = fields.Float(string="Total Qty",)
    total_container_count = fields.Integer(readonly=True)
    residual_container_count = fields.Integer(readonly=True)
    direction = fields.Selection(([('import', 'Import'), ('export', 'Export'), ('local', 'Trans Shipment')]),
                                 default='import',
                                 string='Direction')
    price_for_one_container = fields.Float()
    customer_id = fields.Many2one('res.partner', )
    vendor_id = fields.Many2one('res.partner', )
