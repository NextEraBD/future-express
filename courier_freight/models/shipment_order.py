from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from odoo.exceptions import AccessError, UserError, ValidationError

class ShipmentOrderLine(models.Model):
    _name = 'shipment.order.line'
    _description = 'Shipment Order Line'

    # def _get_default_product(self):
    #     # Replace 'YOUR_PRODUCT_ID' with the ID of the product you want as default
    #     product = self.env['product.product'].search([('name', '=', 'Import Service')], limit=1)
    #     return product.id if product else False

    @api.model
    def default_get(self, fields_list):
        result = super(ShipmentOrderLine, self).default_get(fields_list)
        result['product'] = self.env['product.product'].search([('name', '=', 'Import Service')], limit=1)
        if self.shipment_order_crm_id.operation_type == 'cruise' and self.shipment_order_crm_id.cruise_type == 'local':
            result['product'] = self.env['product.product'].search([('name', '=', 'Local Service')], limit=1)
        elif self.shipment_order_crm_id.direction == 'local':
            result['product'] = self.env['product.product'].search([('name', '=', 'Local Service')], limit=1)
        elif self.shipment_order_crm_id.direction == 'export':
            result['product'] = self.env['product.product'].search([('name', '=', 'Export Service')], limit=1)
        return result

    shipment_order_crm_id = fields.Many2one('crm.lead', string='Shipment Order', inverse_name='shipment_order_lines',
                                            help="Related CRM Lead")
    freight_operation_id = fields.Many2one('freight.operation', string='Freight Operation',
                                           inverse_name='shipment_order_lines', )  # New field
    check = fields.Boolean()
    product = fields.Many2one(
        'product.product', string='Product', required=True,
    )
    weight = fields.Float(string='Charger Weight')
    gross_weight = fields.Float(string='Gross Weight')
    cbm = fields.Float('CBM',compute='compute_main_measure')
    source = fields.Char(string='Source', compute='_compute_source_destination', store=True)
    destination = fields.Char(string='Destination', compute='_compute_source_destination', store=True)
    services_amount = fields.Integer(string='Services Amount', compute="_compute_services_amount")
    departial_date = fields.Date(string='Departial Date')
    description = fields.Text(string='Description')
    no_of_item = fields.Integer(string='No. of Item')
    analytic_tag = fields.Char(string='Analytic Tag')
    taxes = fields.Integer(string='Taxes', compute="_compute_international_tax")
    net_rate = fields.Float(string='Net Rate', store=True)
    unit_price = fields.Integer(string='Unit Price')
    discount = fields.Float(string='Discount', default=0.0)
    sale_price = fields.Float(string='Sale Price', compute='_compute_sale_price', store=True)
    cost_price = fields.Float(string='Cost Price', compute='_compute_sale_price', store=True)
    vendor = fields.Many2one('res.partner', string='Vendor')
    customer = fields.Many2one('res.partner', string='Customer')
    currency_id = fields.Many2one('res.currency', string='Currency', related='shipment_order_crm_id.currency_id')
    processed_so = fields.Boolean('Processed SO', default=False)
    processed_po = fields.Boolean('Processed PO', default=False)
    total_price = fields.Float(string='Total Price', compute='_compute_total_price', store=True)
    total_price_currency = fields.Float(string='Currency Total Price', compute='_compute_total_price')
    services = fields.Many2many(
        'product.template',
        'shipment_order_line_service_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='Additional Services',
    )
    international_tax = fields.Many2many(
        'account.tax',
        'shipment_order_line_international_tax_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='International Tax'
    )
    local_tax = fields.Many2many(
        'account.tax',
        'shipment_order_line_local_tax_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='Local Tax'
    )
    tax_id = fields.Many2many(
        'account.tax',
        'shipment_order_line_tax_id_rel',  # Relation table name
        'line_ids',  # Column for this model
        'product_id',  # Column for the related model
        string='Taxes'
    )
    width = fields.Float('Width (KG)')
    height = fields.Float('Height (KG)')
    size = fields.Float('Length')
    main_measure = fields.Float('FRT')

    # @api.model
    # def create(self, vals):
    #     # Set default product based on direction
    #     direction = self.env['freight.operation'].browse(vals.get('freight_operation_id')).direction
    #     cruise_type = self.env['freight.operation'].browse(vals.get('freight_operation_id')).cruise_type
    #     if direction == 'import':
    #         vals['product'] = self.env['product.product'].search([('name', '=', 'Import Service')], limit=1).id
    #     elif direction == 'export':
    #         vals['product'] = self.env['product.product'].search([('name', '=', 'Export Service')], limit=1).id
    #     elif cruise_type == 'local':
    #         vals['product'] = self.env['product.product'].search([('name', '=', 'Local Service')], limit=1).id
    #
    #     return super(ShipmentOrderLine, self).create(vals)
    #
    @api.onchange('shipment_order_crm_id','product','freight_operation_id')
    def _onchange_shipment_order_crm_id(self):
        # Update the product based on the selected freight operation
        if self.shipment_order_crm_id:
            direction = self.shipment_order_crm_id.direction
            cruise_type = self.shipment_order_crm_id.cruise_type
            if cruise_type == 'local':
                self.product = self.env['product.product'].search([('name', '=', 'Local Service')], limit=1)
            elif direction == 'import':
                self.product = self.env['product.product'].search([('name', '=', 'Import Service')], limit=1)
            elif direction == 'export':
                self.product = self.env['product.product'].search([('name', '=', 'Export Service')], limit=1)
            elif direction == 'local':
                self.product = self.env['product.product'].search([('name', '=', 'Local Service')], limit=1)

        elif self.freight_operation_id:
            direction = self.freight_operation_id.direction
            cruise_type = self.freight_operation_id.cruise_type
            if cruise_type == 'local':
                self.product = self.env['product.product'].search([('name', '=', 'Local Service')], limit=1)
            elif direction == 'import':
                self.product = self.env['product.product'].search([('name', '=', 'Import Service')], limit=1)
            elif direction == 'export':
                self.product = self.env['product.product'].search([('name', '=', 'Export Service')], limit=1)
            elif direction == 'local':
                self.product = self.env['product.product'].search([('name', '=', 'Local Service')], limit=1)

    # @api.model
    # def _get_default_product(self):
    #     # Define default product based on the direction of the freight operation
    #     default_product = self.env['product.product']
    #     if self._context.get('default_freight_operation_id'):
    #         freight_operation = self.env['freight.operation'].browse(self._context['default_freight_operation_id'])
    #         direction = freight_operation.direction
    #         cruise_type = self.freight_operation_id.cruise_type
    #         if direction == 'import':
    #             default_product = self.env['product.product'].search([('name', '=', 'Import Service')], limit=1)
    #         elif direction == 'export':
    #             default_product = self.env['product.product'].search([('name', '=', 'Export Service')], limit=1)
    #         elif cruise_type == 'local':
    #             default_product = self.env['product.product'].search([('name', '=', 'Local Service')], limit=1)
    #     return default_product

    @api.depends('width', 'height', 'size', 'gross_weight', 'shipment_order_crm_id', 'freight_operation_id')
    def compute_main_measure(self):
        for rec in self:
            # Default to None if fields are not set
            operation_type = cruise_type = None

            # Get the values from CRM lead if present
            if rec.shipment_order_crm_id:
                operation_type = rec.shipment_order_crm_id.operation_type
                cruise_type = rec.shipment_order_crm_id.cruise_type

            # Otherwise, get the values from Freight operation
            if not operation_type and rec.freight_operation_id:
                operation_type = rec.freight_operation_id.operation_type
                cruise_type = rec.freight_operation_id.cruise_type

            # Calculate CBM based on operation and cruise type
            if operation_type == 'cruise':
                if cruise_type == 'local':
                    rec.cbm = (rec.width * rec.height * rec.size) / 7000
                elif cruise_type == 'international':
                    rec.cbm = (rec.width * rec.height * rec.size) / 5000

            # Set weight to the maximum of CBM and gross weight
            weight = max(rec.cbm, rec.gross_weight)
            # Round up to the nearest multiple of 500
            # rounded_value = ((weight + 499) // 500) * 500
            rec.weight = weight

           

    # @api.depends('currency_id')
    # def _compute_net_rate(self):
    #     for line in self:
    #         if line.currency_id:
    #             # Get the rate for the selected currency
    #             currency_rate = line.currency_id.rate
    #             line.net_rate = currency_rate
    #         else:
    #             line.net_rate = 0.0

    @api.depends('services')
    def _compute_services_amount(self):
        for line in self:
            total_amount = sum(service.list_price for service in line.services)
            line.services_amount = total_amount

    @api.depends('international_tax')
    def _compute_international_tax(self):
        for line in self:
            total_tax = sum(international_taxs.amount for international_taxs in line.international_tax)
            line.taxes = total_tax

    @api.depends('unit_price', 'taxes', 'services_amount')
    def _compute_total_price(self):
        for line in self:
            rate = 1.0
            # Calculate total price and the Currency Total Price
            if line.currency_id:
                latest_rate = line.currency_id.rate_ids.sorted('name', reverse=True)[:1]
                if latest_rate:
                    rate = latest_rate.company_rate
            line.total_price = line.net_rate + line.services_amount or 0.0
            line.total_price_currency = (line.total_price or 0.0) * rate

    @api.depends('freight_operation_id.cruise_type', 'shipment_order_crm_id.cruise_type',
                 'freight_operation_id.direction', 'shipment_order_crm_id.direction',
                 'freight_operation_id.sender_state_id', 'freight_operation_id.receiver_state_id',
                 'freight_operation_id.sender_country_id', 'freight_operation_id.receiver_country_id',
                 'shipment_order_crm_id.sender_state_id', 'shipment_order_crm_id.receiver_state_id',
                 'shipment_order_crm_id.sender_country_id', 'shipment_order_crm_id.receiver_country_id')
    def _compute_source_destination(self):
        egypt_id = self.env.ref('base.eg').name  # Replace 'base.eg' with the actual XML ID for Egypt

        for line in self:
            # Initialize source and destination
            source = destination = False

            # Check cruise_type and direction
            cruise_type = line.freight_operation_id.cruise_type or line.shipment_order_crm_id.cruise_type
            direction = line.freight_operation_id.direction or line.shipment_order_crm_id.direction

            if cruise_type == 'local':
                source = line.freight_operation_id.sender_state_id.name or line.shipment_order_crm_id.sender_state_id.name
                destination = line.freight_operation_id.receiver_state_id.name or line.shipment_order_crm_id.receiver_state_id.name

            elif cruise_type == 'international':
                if direction == 'export':
                    source = egypt_id
                    destination = line.freight_operation_id.receiver_country_id.name or line.shipment_order_crm_id.receiver_country_id.name

                elif direction == 'import':
                    source = line.freight_operation_id.sender_country_id.name or line.shipment_order_crm_id.sender_country_id.name
                    destination = egypt_id

            # Assign computed values to the fields
            line.source = source
            line.destination = destination
            print(f"Source: {line.source}, Destination: {line.destination}")

    @api.depends('shipment_order_crm_id.direction', 'shipment_order_crm_id.sender_country_id',
                 'shipment_order_crm_id.receiver_country_id', 'shipment_order_crm_id.receiver_state_id',
                 'product', 'weight', 'vendor', 'shipment_order_crm_id.partner_id',
                 'freight_operation_id.direction', 'freight_operation_id.sender_country_id',
                 'freight_operation_id.receiver_country_id', 'freight_operation_id.receiver_state_id')
    def _compute_sale_price(self):
        for line in self:
            sale_price = cost_price = 0.0000
            new_sale_price = new_cost_price = 0.0000
            extra_weight_sale_price = extra_weight_cost_price = 0.0000
            cruise_type = ''
            international_tax_export = []
            international_tax_import = []
            local_tax = []
            tax_id = []
            services = []
            currency_id = None

            if line.product and line.weight:
                price_list_line_sale = False
                price_list_line_cost = False

                # Determine the price list based on cruise_type and direction
                price_list_id = False

                # Determine cruise_type
                cruise_type = line.freight_operation_id.cruise_type if line.freight_operation_id else (
                    line.shipment_order_crm_id.cruise_type if line.shipment_order_crm_id else '')

                if cruise_type == 'international':
                    if line.freight_operation_id:
                        price_list_id = line.freight_operation_id.price_list_id.id

                    elif line.shipment_order_crm_id:
                        price_list_id = line.shipment_order_crm_id.price_list_id.id
                    else:
                        price_list_id = False

                    # Search for sale and cost prices based on the price_list_id
                    if line.shipment_order_crm_id.direction == 'import' or line.freight_operation_id.direction == 'import':
                        if (
                                line.shipment_order_crm_id.sender_country_id or line.freight_operation_id.sender_country_id) and line.product and line.weight and line.vendor:

                            if line.freight_operation_id:
                                country_id = line.freight_operation_id.sender_country_id.id
                                zone = line.freight_operation_id.sender_country_id.zone

                            elif line.shipment_order_crm_id:
                                zone = line.shipment_order_crm_id.sender_country_id.zone
                                country_id = line.shipment_order_crm_id.sender_country_id.id
                            else:
                                zone = False
                                country_id = False
                            price_list_line_sale = self.env['custom.price.list.international.import.line'].search([
                                ('zone', '=',zone),
                                ('product', '=', line.product.id),
                                ('price_list_id', '=', price_list_id),
                                ('country_id', '=', country_id),
                                ('weight', '<=', line.weight),
                                ('price_list_id.vendor', '=', line.vendor.id)
                            ], order='weight desc', limit=1)

                            if price_list_line_sale:
                                price_list_line_sale = price_list_line_sale[0]
                                last_weight = price_list_line_sale.weight
                                print("jjjjjjjjjj import last_weight", last_weight)
                                # Calculate extra weight sale price
                                if line.weight > last_weight:
                                    print("hi ")
                                    extra_weight = line.weight - last_weight
                                    print("jjjjjjjjjj import extra_weight", extra_weight)
                                    extra_weight_sale_price = (extra_weight * price_list_line_sale.extra_weight_sale_price)
                                    extra_weight_cost_price = (extra_weight * price_list_line_sale.extra_weight_cost_price)

                    if line.freight_operation_id.direction == 'export' or line.shipment_order_crm_id.direction == 'export':
                        if (
                                line.shipment_order_crm_id.receiver_country_id or line.freight_operation_id.receiver_country_id) and line.product and line.weight and line.vendor:
                            if line.freight_operation_id:
                                country_id = line.freight_operation_id.receiver_country_id.id
                                zone = line.freight_operation_id.receiver_country_id.zone

                            elif line.shipment_order_crm_id:
                                zone = line.shipment_order_crm_id.receiver_country_id.zone
                                country_id = line.shipment_order_crm_id.receiver_country_id.id
                            else:
                                zone = False
                                country_id = False


                            price_list_line_sale = self.env['custom.price.list.international.export.line'].search([
                                ('zone', '=',zone),
                                ('product', '=', line.product.id),
                                ('price_list_id', '=', price_list_id),
                                ('country_id', '=', country_id),
                                ('weight', '<=', line.weight),
                                ('price_list_id.vendor', '=', line.vendor.id)
                            ], order='weight desc', limit=1)
                            if price_list_line_sale:
                                price_list_line_sale = price_list_line_sale[0]
                                last_weight = price_list_line_sale.weight
                                print("yyydf export", last_weight)
                                # Calculate extra weight sale price
                                if line.weight > last_weight:
                                    extra_weight = line.weight - last_weight
                                    print("yyyyyy export", extra_weight)
                                    extra_weight_sale_price = (extra_weight * price_list_line_sale.extra_weight_sale_price)
                                    extra_weight_cost_price = ( extra_weight * price_list_line_sale.extra_weight_cost_price)
                elif cruise_type == 'local':
                    # Determine the price list ID based on existing records
                    if line.freight_operation_id:
                        price_list_id = line.freight_operation_id.price_list_id.id
                        state_id = line.freight_operation_id.receiver_state_id.id
                    elif line.shipment_order_crm_id:
                        price_list_id = line.shipment_order_crm_id.price_list_id.id
                        state_id = line.shipment_order_crm_id.receiver_state_id.id
                    else:
                        price_list_id = False  # Handle case when no price list is available
                        state_id = False
                    # Retrieve the receiver zone
                    receiver_zone = line.shipment_order_crm_id.receiver_state_id.zone or line.freight_operation_id.receiver_state_id.zone
                    if receiver_zone and line.product and line.weight:
                        print("Receiver Zone:", receiver_zone)

                        # Search for the best matching price list line
                        price_list_lines = self.env['custom.price.list.local.line'].search([
                            ('zone', '=', receiver_zone),
                            ('product', '=', line.product.id),
                            ('weight', '<=', line.weight),
                            ('state_id','=',state_id),
                            ('price_list_id', '=', price_list_id),
                        ], order='weight desc', limit=1)

                        # Initialize total sale price
                        total_sale_price = 0.000

                        # Process the best matching price list line
                        if price_list_lines:
                            price_list_line_sale = price_list_lines[0]
                            last_weight = price_list_line_sale.weight
                            print("LAST_WEIGHT", last_weight)

                            # Calculate extra weight if current weight exceeds the weight in the price list
                            extra_weight_sale_price = 0.000
                            if line.weight > last_weight:
                                extra_weight = line.weight - last_weight
                                print("extra_weight", extra_weight)
                                extra_weight_sale_price = extra_weight * price_list_line_sale.extra_weight_sale_price
                                print("extra_weight_sale_price", extra_weight_sale_price)

                            # Base sale price from the price list line
                            sale_price = price_list_line_sale.sale_price
                            print("sale_price", sale_price)

                            # Calculate the total sale price by adding base and extra weight sale prices
                            total_sale_price = sale_price + extra_weight_sale_price

                        # Set the total sale price on the shipment line
                        line.sale_price = total_sale_price
                        print("total_sale_price", total_sale_price)

                # Set sale and cost prices if available
                if price_list_line_sale:
                    # sale_price = price_list_line_sale.sale_price
                    # print("sale_price", sale_price)
                    services = price_list_line_sale.additional_services
                    tax_id = price_list_line_sale.taxes
                    currency_id = price_list_line_sale.price_list_id.currency_id.id
                    if cruise_type == 'international' and line.shipment_order_crm_id.direction == 'import' or line.freight_operation_id.direction == 'import' :
                        sale_price = price_list_line_sale.sale_price
                        cost_price = price_list_line_sale.cost_price
                        international_tax_import = price_list_line_sale.international_tax_import
                    if cruise_type == 'international' and line.shipment_order_crm_id.direction == 'export' or line.freight_operation_id.direction == 'export' :
                        sale_price = price_list_line_sale.sale_price
                        cost_price = price_list_line_sale.cost_price
                        international_tax_export = price_list_line_sale.international_tax_export
                    if cruise_type == 'local':
                        local_tax = price_list_line_sale.local_tax

                #
                # if price_list_line_cost:
                #     cost_price = price_list_line_cost.cost_price

            print("extra cost ", extra_weight_cost_price)
            print("extra sale ", extra_weight_sale_price)

            if extra_weight_sale_price != 0.000 :
                new_sale_price = sale_price + extra_weight_sale_price
            else:
                new_sale_price = sale_price

            if extra_weight_cost_price != 0.000:

                new_cost_price = cost_price + extra_weight_cost_price
            else:
                new_cost_price = cost_price

            line.sale_price = new_sale_price
            line.cost_price = new_cost_price
            if line.services.ids == []:
                line.services = [(6, 0, [service.id for service in services])]
            if line.tax_id.ids == []:
                line.tax_id = [(6, 0, [tax.id for tax in tax_id])]
            line.currency_id = currency_id

            # Set unit_price based on cruise_type
            if cruise_type == 'international' and line.shipment_order_crm_id.direction == 'import' or line.freight_operation_id.direction == 'import':
                line.net_rate = new_sale_price
                if line.international_tax.ids == []:
                    line.international_tax = [(6, 0, [tax.id for tax in international_tax_import])]
            elif cruise_type == 'international' and line.shipment_order_crm_id.direction == 'export' or line.freight_operation_id.direction == 'export':
                line.net_rate = new_sale_price
                if line.international_tax.ids == []:
                    line.international_tax = [(6, 0, [tax.id for tax in international_tax_export])]
            elif cruise_type == 'local':
                line.net_rate = new_sale_price
                if line.local_tax.ids == []:
                    line.local_tax = [(6, 0, [tax.id for tax in local_tax])]
            else:
                line.net_rate = 0.000
