# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import json


class TransitLetter(models.Model):
    _name = 'letter.guarantee'
    _description = 'Letter Guarantee'
    _order = 'name'

    @api.model
    def _get_letter_guarantee_body(self):
        return """
              <p>We are pleased to offer you the [full-time, part-time, etc.] position of [job title] at [company name] 
              with a start date of [start date], contingent upon [background check, I-9 form, etc.]. You will be 
              reporting directly to [manager/supervisor name] at [workplace location]. We believe your skills and 
              experience are an excellent match for our company.</p>
              <br/>
              <p>In this role, you will be required to [briefly mention relevant job duties and responsibilities].</p>
              <br/>
              <p>The annual starting salary for this position is [dollar amount] to be paid on a [monthly, semi-
              monthly, weekly, etc.] basis by [direct deposit, check, etc.], starting on [first pay period]. In 
              addition to this starting salary, we’re offering you [discuss stock options, bonuses, commission 
              structures, etc.].</p>
              <br/>
              <p>Your employment with [company name] will be on an at-will basis, which means you and the company 
              are free to terminate the employment relationship at any time for any reason. This letter is not a 
              contract or guarantee of employment for a definite amount of time.</p>
              <br/>
              <p>As an employee of [company name], you are also eligible for our benefits program, which includes 
              [medical insurance, 401(k), vacation time, etc.], and other benefits which will be described in more 
              detail in the [employee handbook, orientation package, etc.].</p>
              <br/>
              <p>Please confirm your acceptance of this offer by signing and returning this letter by [offer expiration 
              date].</p>
              <br/>
              <p>We are excited to have you join our team! If you have any questions, please feel free to reach out at any time.</p>
              <br/>
              <p>Sincerely,</p>
              <p>[Your Signature]</p>
              <br/>
              <p>[Your Printed Name]</p>
              <p>[Your Job Title]</p>
              <br/>
              <p>Signature: ______________________________</p>
              <p>Printed Name: ___________________________</p>
              <p>Date: __________________________________</p>
         """

    name = fields.Char(
        string="Letter Name",
        default=lambda self: _('New'),
        readonly=True,
        copy=False,
    )
    note = fields.Html(string="Body", default=_get_letter_guarantee_body,)

    letter_no = fields.Char('Letter No',)
    bank = fields.Char()
    letter_amount = fields.Integer('Letter Amount', default=10)
    letter_remaining_amount = fields.Integer('Remaining', default=10)
    freight_ids = fields.Many2many('freight.operation', compute="compute_freight_ids")
    lead_ids = fields.Many2many('crm.lead', compute="compute_lead_ids")
    expiration_date = fields.Date(string='Expiration Date')

    def compute_lead_ids(self):
        for letter in self:
            letter.lead_ids = False
            fids = self.env['crm.lead'].search([('letter_id', '=', letter.id)])
            for lead_id in fids:
                letter.lead_ids = [(4, lead_id.id)]

    @api.onchange('letter_amount')
    def onchanfe_letter_amount(self):
        self.letter_remaining_amount = self.letter_amount
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('letter.guarantee')
        return super(TransitLetter, self).create(vals)

    def compute_freight_ids(self):
        for letter in self:
            letter.freight_ids = False
            fids = self.env['freight.operation'].search([('letter_id','=',letter.id)])
            for freight_id in fids:
                letter.freight_ids = [(4, freight_id.id)]
                print(letter.freight_ids)


class TransitStageImport(models.Model):
    _name = 'transit.import.stage'
    _description = 'Transit Import Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)


class TransitStageExport(models.Model):
    _name = 'transit.export.stage'
    _description = 'Transit Export Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)


class FreightTransit(models.Model):
    _name = 'freight.transit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Freight Transit'

    @api.model
    def _transit_office_users(self):
        self.ensure_one()
        return [('id', 'in', self.clear_office_id.user_ids.ids)] if self.clear_office_id.user_ids else []

    def _get_default_import_stage_id(self):
        return self.env['transit.import.stage'].search([], order='sequence', limit=1)

    def _get_default_export_stage_id(self):
        return self.env['transit.export.stage'].search([], order='sequence', limit=1)

    color = fields.Integer('Color')
    stage_id_import = fields.Many2one('transit.import.stage', 'Stage', default=_get_default_import_stage_id,
                                      group_expand='_read_group_stage_import_ids')
    stage_id_export = fields.Many2one('transit.export.stage', 'Stage', default=_get_default_export_stage_id,
                                      group_expand='_read_group_stage_export_ids')
    name = fields.Char(string="Transit Serial")

    direction = fields.Selection(([('import', 'Import'), ('export', 'Export')]), string='Direction')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'International transportation'), ('vas', 'Vas')]),
                                 string='Transport')
    operation = fields.Selection([('direct', 'Direct'), ('house', 'House'), ('master', 'Master')], string='Operation')
    ocean_shipment_type = fields.Selection(([('fcl', 'FCL'), ('lcl', 'LCL')]), string='Ocean Shipment Type')
    inland_shipment_type = fields.Selection(([('ftl', 'FTL'), ('ltl', 'LTL')]), string='Inland Shipment Type')
    shipper_id = fields.Many2one('res.partner', 'Shipper')
    consignee_id = fields.Many2one('res.partner', 'Consignee')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading', index=True, required=True)
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', index=True, required=True)
    obl = fields.Char('OBL', help='Original Bill Of Landing')
    shipping_line_id = fields.Many2one('res.partner', 'Shipping Line')
    voyage_no = fields.Char('Voyage No')
    vessel_id = fields.Many2one('freight.vessel', 'Vessel')
    mawb_no = fields.Char('MAWB No')
    airline_id = fields.Many2one('freight.airline', 'Airline')
    datetime = fields.Datetime('Date')
    truck_ref = fields.Char('CMR/RWB#/PRO#:')
    trucker = fields.Many2one('freight.trucker', 'Trucker')
    trucker_number = fields.Char('Trucker No')
    agent_id = fields.Many2one('res.partner', 'Agent')
    operator_id = fields.Many2one('res.users', 'User')
    freight_pc = fields.Selection(([('collect', 'Collect'), ('prepaid', 'Prepaid')]), string="Freight PC")
    other_pc = fields.Selection(([('collect', 'Collect'), ('prepaid', 'Prepaid')]), string="Other PC")
    notes = fields.Text('Notes')
    dangerous_goods = fields.Boolean('Dangerous Goods')
    dangerous_goods_notes = fields.Text('Dangerous Goods Info')
    tracking_number = fields.Char('Tracking Number')
    declaration_number = fields.Char('Declaration Number')
    declaration_date = fields.Date('Declaration Date')
    trans_line_ids = fields.One2many('transit.transit.line', 'transit_id')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('freight.transit')
        return super(FreightTransit, self).create(vals)

    @api.model
    def _read_group_stage_import_ids(self, stages, domain, order):
        stage_ids = self.env['transit.import.stage'].search([])
        return stage_ids

    @api.model
    def _read_group_stage_export_ids(self, stages, domain, order):
        stage_ids = self.env['transit.export.stage'].search([])
        return stage_ids

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


class TransitLine(models.Model):
    _name = 'transit.transit.line'

    name = fields.Char(string='Description')
    transit_id = fields.Many2one('freight.transit', string='Transit ID')
    product_id = fields.Many2one('product.product', string='Transit Product')
    source_location_id = fields.Many2one('freight.port', 'Port of Loading', index=True, required=True)
    destination_location_id = fields.Many2one('freight.port', 'Port of Discharge', index=True, required=True)
    custom_fees = fields.Float(string='Custom Fees')
    percentage_id = fields.Many2one('transit.percent', string='Percentage')
    amount = fields.Float(string='Amount')


class TransitPercent(models.Model):
    _name = 'transit.percent'

    name = fields.Char(string='Percentage Name')
    percentage_amount = fields.Integer(string='Percentage Amount')
