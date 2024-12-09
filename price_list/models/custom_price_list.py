from datetime import date

from odoo import fields, models, api, _

import logging

_logger = logging.getLogger(__name__)

from odoo import fields, models, api


class CustomPriceList(models.Model):
    _name = 'custom.price.list'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Custom Price List'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('custom.price.list.sequence') or 'New')
    validation_date_from = fields.Date(string='Validation Date From', required=True)
    validation_date_to = fields.Date(string='Validation Date To', required=True)
    price_list_type = fields.Selection(
        [('international', 'International'), ('local', 'Local')],
        string='Price List Type',
        required=True,
        default='international'
    )
    vendor = fields.Many2one('res.partner', string='Vendor')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    seleclocal_line_idst_customer = fields.Boolean(string='Select Customer')
    customer_id = fields.Many2one('res.partner', string='Customer', domain=[('customer_rank', '>', 0)])
    local_line_ids = fields.One2many('custom.price.list.local.line', 'price_list_id', string='Price List Local Lines')
    international_import_line_ids = fields.One2many('custom.price.list.international.import.line', 'price_list_id',
                                                    string='Price List International Import Lines')
    international_export_line_ids = fields.One2many('custom.price.list.international.export.line', 'price_list_id',
                                                    string='Price List International Export Lines')
    message_main_attachment_id = fields.Many2one('ir.attachment', string='Main Attachment', index=True)
    activity_ids = fields.One2many('mail.activity', 'res_id', domain=lambda self: [('res_model', '=', self._name)],
                                   auto_join=True)
    message_ids = fields.One2many('mail.message', 'res_id', domain=lambda self: [('model', '=', self._name)],
                                  auto_join=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('expired', 'Expired')
    ], string="Status", compute='_compute_status', store=True, readonly=False, default='draft')
    extra_weight = fields.Float(string='Extra Weight')
    extra_weight_sale_price = fields.Float(string='Extra Weight Sale Price')
    extra_weight_cost_price = fields.Float(string='Extra Weight Cost Price')

    @api.depends('validation_date_from', 'validation_date_to')
    def _compute_status(self):
        today = fields.Date.today()
        for record in self:
            if not record.validation_date_from or not record.validation_date_to:
                record.status = 'draft'
            elif record.validation_date_from <= today <= record.validation_date_to:
                record.status = 'running'
            else:
                record.status = 'expired'

    @api.model
    def _update_status_cron(self):
        # You don't need to search for records again, as _compute_status will handle it.
        self.search([])._compute_status()


    def copy(self, default=None):
        if default is None:
            default = {}
        # Create a new record with default values
        new_record = super(CustomPriceList, self).copy(default)

        # Copy local lines
        for line in self.local_line_ids:
            line.copy(default={'price_list_id': new_record.id})

        # Copy international import lines
        for line in self.international_import_line_ids:
            line.copy(default={'price_list_id': new_record.id})

        # Copy international export lines
        for line in self.international_export_line_ids:
            line.copy(default={'price_list_id': new_record.id})

        return new_record


class CustomPriceListLocalLine(models.Model):
    _name = 'custom.price.list.local.line'
    _description = 'Custom Price List Line'

    product = fields.Many2one('product.template', string='Product', required=True)
    weight = fields.Float(string='Charger Weight')
    country_id = fields.Many2one('res.country', string='Country', required=False)
    state_id = fields.Many2one('res.country.state', string='State', required=True)
    zone = fields.Char(string='Zone', compute='_compute_zone',)
    extra_weight = fields.Float(string='Extra Weight')
    extra_weight_sale_price = fields.Float(string='Extra Weight Sale Price')
    cost_price = fields.Float()

    @api.depends('state_id')
    def _compute_zone(self):
        for record in self:
            if record.state_id:
                record.zone = record.state_id.zone or 'Default Zone'
            else:
                record.zone = 'No State Selected'

    sale_price = fields.Float(string='Sale Price')
    additional_services = fields.Many2many(
        'product.template',
        'price_list_local_line_additional_services_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='Additional Services',
    )
    taxes = fields.Many2many(
        'account.tax',
        'price_list_local_line_taxes_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='Taxes',
    )
    local_tax = fields.Many2many(
        'account.tax',
        'shipment_order_line_local_tax_local_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='Local Tax'
    )
    price_list_id = fields.Many2one('custom.price.list', string='Price List', required=False)
    international_tax_export = fields.Many2many(
        'account.tax',
        'shipment_order_line_international_tax_local_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='International Tax'
    )

class CustomPriceListInternationalImportLine(models.Model):
    _name = 'custom.price.list.international.import.line'
    _description = 'Custom Price List Line'

    product = fields.Many2one('product.template', string='Product', required=True)
    direction = fields.Char(string='Direction', default='import')
    weight = fields.Float(string='Charger Weight')
    country_id = fields.Many2one('res.country', string='Country', required=True)
    zone = fields.Char(string='Zone', compute='_compute_zone',)
    custom_zone = fields.Char(string='Custom Zone')  # Field for customer to enter a custom zone
    final_zone = fields.Char(string='Final Zone', compute='_compute_final_zone', store=True)  # Final zone to use
    extra_weight = fields.Float(string='Extra Weight')
    extra_weight_sale_price = fields.Float(string='Extra Weight Sale Price')
    extra_weight_cost_price = fields.Float(string='Extra Weight Cost Price')

    @api.depends('country_id', 'custom_zone')
    def _compute_final_zone(self):
        for record in self:
            # Use custom_zone if set, otherwise fall back to the country's zone
            record.final_zone = record.custom_zone if record.custom_zone else record.zone

    @api.depends('country_id')
    def _compute_zone(self):
        for record in self:
            if record.country_id:
                record.zone = record.country_id.zone or 'Default Zone'
            else:
                record.zone = 'No Country Selected'

    sale_price = fields.Float(string='Sale Price')
    cost_price = fields.Float(string='Cost Price')
    additional_services = fields.Many2many(
        'product.template',
        'price_list_international_import_line_additional_services_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='Additional Services',
    )
    taxes = fields.Many2many(
        'account.tax',
        'price_list_international_import_line_taxes_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='Taxes',
    )
    international_tax_import = fields.Many2many(
        'account.tax',
        'shipment_order_line_international_tax_import_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='International Tax'
    )
    price_list_id = fields.Many2one('custom.price.list', string='Price List', required=False)

class CustomPriceListInternationalExportLine(models.Model):
    _name = 'custom.price.list.international.export.line'
    _description = 'Custom Price List Line'

    product = fields.Many2one('product.template', string='Product', required=True)
    direction = fields.Char(string='Direction', default='export')
    weight = fields.Float(string='Charger Weight')
    country_id = fields.Many2one('res.country', string='Country')
    zone = fields.Char(string='Zone', compute='_compute_zone', store=True)
    custom_zone = fields.Char(string='Custom Zone')  # Field for customer to enter a custom zone
    final_zone = fields.Char(string='Final Zone', compute='_compute_final_zone', store=True)  # Final zone to use
    extra_weight = fields.Float(string='Extra Weight')
    extra_weight_sale_price = fields.Float(string='Extra Weight Sale Price')
    extra_weight_cost_price = fields.Float(string='Extra Weight Cost Price')

    @api.depends('country_id', 'custom_zone')
    def _compute_final_zone(self):
        for record in self:
            # Use custom_zone if set, otherwise fall back to the country's zone
            record.final_zone = record.custom_zone if record.custom_zone else record.zone

    @api.depends('country_id')
    def _compute_zone(self):
        for record in self:
            if record.country_id:
                record.zone = record.country_id.zone or 'Default Zone'
            else:
                record.zone = 'No Country Selected'

    sale_price = fields.Float(string='Sale Price')
    cost_price = fields.Float(string='Cost Price')
    additional_services = fields.Many2many(
        'product.template',
        'price_list_international_export_line_additional_services_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='Additional Services',
    )
    taxes = fields.Many2many(
        'account.tax',
        'price_list_international_export_line_taxes_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='Taxes',
    )
    international_tax_export = fields.Many2many(
        'account.tax',
        'shipment_order_line_international_tax_export_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='International Tax'
    )
    price_list_id = fields.Many2one('custom.price.list', string='Price List', required=False)