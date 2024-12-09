from multiprocessing.connection import default_family

from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from datetime import date


class FreightOperation(models.Model):
    _inherit = 'freight.operation'

    def _get_default_import_cruise_stage_id(self):
        return self.env['freight.import.stage.courier'].search([], order='sequence', limit=1)

    def _get_default_export_cruise_stage_id(self):
        return self.env['freight.export.stage.courier'].search([], order='sequence', limit=1)

    def _get_default_local_cruise_stage_id(self):
        return self.env['freight.local.stage.courier'].search([], order='sequence', limit=1)

    @api.model
    def _read_group_stage_local_cruise_ids(self, stages, domain, order):
        stage_ids = self.env['freight.local.stage.courier'].search([])
        return stage_ids

    @api.model
    def _read_group_stage_import_courier_ids(self, stages, domain, order):
        stage_ids = self.env['freight.import.stage.courier'].search([])
        return stage_ids

    @api.model
    def _read_group_stage_export_courier_ids(self, stages, domain, order):
        stage_ids = self.env['freight.export.stage.courier'].search([])
        return stage_ids

    stage_id_local_cruise = fields.Many2one('freight.local.stage.courier', 'Stage local courier ',
                                            default=_get_default_local_cruise_stage_id,
                                            group_expand='_read_group_stage_local_cruise_ids')
    stage_id_import_cruise = fields.Many2one('freight.import.stage.courier', 'Stage import courier',
                                             default=_get_default_import_cruise_stage_id,
                                             group_expand='_read_group_stage_import_courier_ids')
    stage_id_export_cruise = fields.Many2one('freight.export.stage.courier', 'Stage export courier',
                                             default=_get_default_export_cruise_stage_id,
                                             group_expand='_read_group_stage_export_courier_ids')
    operation_type = fields.Selection([('cruise', 'Courier'), ('cargo', 'Cargo')],
                                      string='Type of Comduty', readonly=False)

    shipment_order_name = fields.Char(string='Order Reference')
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=False)
    address = fields.Text(string='Address',)
    tax_id = fields.Char(string='Tax ID',related="customer_id.vat")
    account_number = fields.Char(string='Account Number')
    phone = fields.Char(string='Phone',related="customer_id.phone")
    email = fields.Char(string='Email',related="customer_id.email")
    account_number_wb = fields.Char(string='AWB')
    received_date = fields.Date(string='Received Date')
    sale_order_date = fields.Date(string='Sale Order Date')
    competitors = fields.Char(string='Competitors')
    sale_order_type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase')], string='Sale Order Type')
    shipment_type = fields.Selection([('doc', 'Doc'), ('nondoc', 'Non Doc')], string='Shipment Type')
    courier = fields.Char(string='Courier')
    price_list_id = fields.Many2one(
        'custom.price.list',
        string='Price List',
        domain=[],  # Empty domain initially; will be set dynamically
        store=True
    )
    payment_terms = fields.Many2one('account.payment.term', string='Payment Terms',
                                    related='customer_id.property_payment_term_id')
    sender_name = fields.Char(string='Sender Name')
    sender_mobile = fields.Char(string='Sender Mobile')
    sender_address = fields.Text(string='Address From')
    sender_country_id = fields.Many2one('res.country', string='Country From', compute='_compute_sender_country_id',
                                        store=True)
    sender_town = fields.Many2one('res.branch.town', string='Sender Town')
    receiver_town = fields.Many2one('res.branch.town', string='Receiver Town')
    sender_state_id = fields.Many2one('res.country.state', string='State From',
                                      domain="[('country_id', '=', sender_country_id)]")
    receiver_name = fields.Char(string='Receiver Name')
    receiver_mobile = fields.Char(string='Receiver Mobile')
    receiver_address = fields.Text(string='Address To')
    receiver_country_id = fields.Many2one('res.country', string='Country To', compute='_compute_receiver_country_id',
                                          store=True)
    receiver_state_id = fields.Many2one('res.country.state', string='State To',
                                        domain="[('country_id', '=', receiver_country_id)]")

    shipment_order_line_ids = fields.One2many('shipment.order.line', 'freight_operation_id',
                                              string='Shipment Order Lines', readonly=False)

    compliment_count = fields.Integer('Compliment Count', compute='_compute_compliment_count')
    cruise_type = fields.Selection([('local', 'Local'), ('international', 'International')],
                                   string='Courier Type',
                                   store=True
                                   )
    local_type = fields.Selection(
        [('online', 'Online'), ('not_online', 'Not Online')],
        string='Local Type',
        readonly=False
    )
    collection_amount = fields.Float(string="Collection amount")

    pricelist_id = fields.Many2one('product.pricelist', string="Price List", compute='_compute_pricelist_id')
    currency_id = fields.Many2one('res.currency', string="Currency", compute='_compute_currency_id', readonly=1)
    shipment_order_count = fields.Integer(string='Shipment Orders Count', compute='_compute_shipment_order_count')

    untaxed_amount = fields.Float(string="Untaxed Amount", compute='_compute_totals')
    services = fields.Float(string="Services", compute='_compute_totals')
    local_taxes = fields.Float(string="Local Tax", compute='_compute_totals')
    international_taxes = fields.Float(string="International Tax",compute='_compute_totals')
    vat = fields.Float(string="Vat", compute='_compute_totals')
    total_usd = fields.Float(string="Total USD", compute='_compute_totals')
    total_egp = fields.Float(string="Total EGP", compute='_compute_totals')

    assigned_to = fields.Many2one('res.users', string='Assigned to Pick')
    assigned_to_deliver = fields.Many2one('res.users', string='Assigned to Deliver')
    branch_id = fields.Many2one('res.branch', string='Branch', ondelete='set null',
                                default=lambda self: self._get_default_branch())
    issue_count = fields.Integer(string='Issue Count', compute='_compute_issue_count')
    ks_global_discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')],
                                               string='Universal Discount Type',
                                               readonly=False,
                                               default='percent')
    ks_global_discount_rate = fields.Float('Universal Discount',
                                           readonly=False, )
    ks_amount_discount = fields.Monetary(string='Universal Discount', readonly=True, store=True,
                                         compute='_amount_all',
                                         track_visibility='always')
    ks_enable_discount = fields.Boolean()
    task_number = fields.Integer(compute='task_count', string='Tasks', tracking=True)
    dead_line = fields.Date('Deadline')
    date_assign = fields.Date(string='Creation Date', default=fields.Date.context_today)
    cash = fields.Selection([
        ('cash', 'Cash'),
        ('invoice', 'Invoice')
    ], string="Payment Type",required=False)

    @api.onchange('customer_id', 'direction')
    def _onchange_partner_info(self):
        if self.customer_id:
            if self.direction == 'export':
                # Fill sender fields for export
                self.sender_name = self.customer_id.name
                self.sender_mobile = self.customer_id.mobile
                self.sender_address = self.customer_id.contact_address
            elif self.direction == 'import':
                # Fill receiver fields for import
                self.receiver_name = self.customer_id.name
                self.receiver_mobile = self.customer_id.mobile
                self.receiver_address = self.customer_id.contact_address
            elif self.cruise_type == 'local':
                # Fill sender fields for export
                self.sender_name = self.customer_id.name
                self.sender_mobile = self.customer_id.mobile
                self.sender_address = self.customer_id.contact_address

    @api.model
    def _cron_check_deadlines_and_create_activity(self):
        """
        This method is triggered by a cron job to check for freight operations with deadlines matching today.
        It creates an activity for the customer service team for each matching record.
        """
        today = date.today()
        operations = self.search([('dead_line', '=', today)])

        customer_service_group = self.customer_service_id
        if not customer_service_group:
            return

        for operation in operations:
            for user in customer_service_group.users:
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,  # To-Do activity type
                    'res_id': operation.id,  # ID of the current freight operation record
                    'res_model_id': self.env['ir.model']._get('freight.operation').id,  # Model freight.operation
                    'user_id': user.id,  # Assign to each customer service member
                    'summary': 'Follow-up on freight operation deadline',
                    'note': 'The deadline for this operation is today: {}'.format(operation.dead_line),
                    'date_deadline': fields.Date.today()  # Deadline for the activity (today)
                })

    def task_count(self):
        task_obj = self.env['project.task']
        self.task_number = task_obj.search_count([('operation_id', 'in', [a.id for a in self])])


    @api.constrains('account_number_wb')
    def _check_unique_account_number(self):
        for record in self:
            if record.account_number_wb:
                existing_records = self.search(
                    [('account_number_wb', '=', record.account_number_wb), ('id', '!=', record.id)])
                if existing_records:
                    raise ValidationError(f"The Account Number WB '{record.account_number_wb}' already exists.")

    @api.depends('company_id.ks_enable_discount')
    def ks_verify_discount(self):
        for rec in self:
            rec.ks_enable_discount = rec.company_id.ks_enable_discount

    @api.depends('total_egp', 'ks_global_discount_rate', 'ks_global_discount_type')
    def _amount_all(self):
        for rec in self:
            rec.ks_calculate_discount()

    #
    def ks_calculate_discount(self):
        for rec in self:
            if rec.ks_global_discount_type == "amount":
                rec.ks_amount_discount = rec.ks_global_discount_rate if rec.untaxed_amount > 0 else 0

            elif rec.ks_global_discount_type == "percent":
                if rec.ks_global_discount_rate != 0.0:
                    rec.ks_amount_discount = (rec.untaxed_amount + rec.vat) * rec.ks_global_discount_rate / 100
                else:
                    rec.ks_amount_discount = 0
            elif not rec.ks_global_discount_type:
                rec.ks_amount_discount = 0
                rec.ks_global_discount_rate = 0
            # rec.amount_total = rec.amount_untaxed + rec.amount_tax - rec.ks_amount_discount

    @api.model
    def _get_default_branch(self):
        # Access the current user's record
        user = self.env.user

        # Fetch the branch associated with the current user
        branch = user.branch_id

        return branch

    @api.onchange('sender_town')
    def _onchange_sender_town(self):
        for record in self:
            record.sender_state_id = record.sender_town.state_id.id if record.sender_town else False

    @api.onchange('receiver_town')
    def _onchange_receiver_town(self):
        for record in self:
            record.receiver_state_id = record.receiver_town.state_id.id if record.receiver_town else False

    def action_assign_to_pick(self):
        if not self.assigned_to:
            raise UserError('Please assign a user before proceeding.')

        # Proceed with the action if assigned_to is set
        assigned_stage = self.env.ref(
            'courier_freight.ready_freight_local_stage_courier')  # Adjust the reference based on the operation type
        self.stage_id_local_cruise = assigned_stage

        # Post a message to the assigned user
        self.message_post(
            body=f'Operation assigned to {self.assigned_to.name}.',
            partner_ids=[self.assigned_to.partner_id.id]
        )

        # Create an activity for the assigned user
        activity_type = self.env.ref('mail.mail_activity_data_todo')  # Adjust activity type if needed
        activity_date_deadline = fields.Datetime.to_string(datetime.now())  # Set deadline to today's date
        self.env['mail.activity'].create({
            'activity_type_id': activity_type.id,
            'note': 'Follow up on assigned operation.',
            'date_deadline': activity_date_deadline,
            'user_id': self.assigned_to.id,
            'res_model_id': self.env.ref('freight.model_freight_operation').id,
            'res_id': self.id,
        })

    def action_pick(self):
        # Change the state to "Picked"
        picked_stage = self.env.ref(
            'courier_freight.delay_freight_local_stage_courier')  # Adjust the reference based on your stage
        self.write({'stage_id_local_cruise': picked_stage.id})

        # Find and mark the existing activity for the assigned user as done
        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', self.env.ref('freight.model_freight_operation').id),
            ('res_id', '=', self.id),
            ('user_id', '=', self.assigned_to.id),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('state', '=', 'pending')  # Ensure we're dealing with pending activities
        ], limit=1)

        if activity:
            # Use the `action_done` method to mark the activity as done
            activity.action_done()

        # Find users in the Admin group
        admin_group = self.env.ref('courier_freight.group_freight_admin')
        admin_users = self.env['res.users'].search([('groups_id', '=', admin_group.id)])

        # Post a message to admin users
        for user in admin_users:
            self.message_post(
                body=f'Operation {self.name} has been picked.',
                partner_ids=[user.partner_id.id]
            )

            # Create a new activity for admin users
            activity_type = self.env.ref('mail.mail_activity_data_todo')
            activity_date_deadline = activity_date_deadline = fields.Datetime.to_string(datetime.now())# Set deadline to 1 day from now
            self.env['mail.activity'].sudo().create({
                'activity_type_id': activity_type.id,
                'note': 'Follow up on picked operation.',
                'date_deadline': activity_date_deadline,
                'user_id': user.id,
                'res_model_id': self.env.ref('freight.model_freight_operation').id,
                'res_id': self.id,
            })

    def action_send_to_sort(self):
        # Get the admin group
        admin_group = self.env.ref('courier_freight.group_freight_admin')
        # Search for users in the admin group
        admin_users = self.env['res.users'].search([('groups_id', '=', admin_group.id)])

        # Ensure there are admin users before proceeding
        if not admin_users:
            raise UserError("No admin users found in the freight admin group.")

        # Search for pending activities related to this freight operation
        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', self.env.ref('freight.model_freight_operation').id),
            ('res_id', '=', self.id),
            ('user_id', 'in', admin_users.ids),  # Use 'in' to handle multiple users
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('state', '=', 'pending')
        ], limit=1)

        if activity:
            # Use the `action_done` method to mark the activity as done
            activity.action_done()

        # Set the stage to "Sort"
        sort_stage = self.env.ref('courier_freight.done_freight_import_stage_courier')  # Adjust XML ID as needed
        self.write({'stage_id_local_cruise': sort_stage.id})

        # Find users in the Sort group
        sort_group = self.env.ref('courier_freight.group_freight_sort')  # Adjust XML ID as needed
        sort_users = self.env['res.users'].search([('groups_id', '=', sort_group.id)])

        # Post a message to sort users
        for user in sort_users:
            self.message_post(
                body=f'Operation {self.name} has been sent to sort.',
                partner_ids=[user.partner_id.id]
            )

            # Create an activity for sort users
            activity_type = self.env.ref('mail.mail_activity_data_todo')
            activity_date_deadline = fields.Datetime.to_string(datetime.now())  # Set deadline to 1 day from now
            self.env['mail.activity'].create({
                'activity_type_id': activity_type.id,
                'note': 'Follow up on sorting operation.',
                'date_deadline': activity_date_deadline,
                'user_id': user.id,
                'res_model_id': self.env.ref('freight.model_freight_operation').id,
                'res_id': self.id,
            })

    def action_open_operation_wizard(self):
        operation_orders = self.env["freight.operation"].browse(self._context.get("active_ids", []))

        operation_lines = [(0, 0, {'operation_id': op.id}) for op in operation_orders]

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'operation.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('courier_freight.view_operation_wizard_form').id,
            'target': 'new',
            # 'context': {
            #     'default_operation_line_ids': operation_lines,  # Pre-fills the operation lines in the wizard
            # }
        }

    def action_open_assign_pick_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'assign.operation.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('courier_freight.view_assign_pick_wizard_form').id,
            'target': 'new',
            'context': {
                'default_operation_ids': self._context.get("active_ids", []),  # Pre-fills the operation lines in the wizard
            }
        }

    def action_open_assign_delivered_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'assign.delivered.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('courier_freight.view_assign_delivered_wizard_form').id,
            'target': 'new',
            'context': {
                'default_operation_ids': self._context.get("active_ids", []),  # Pre-fills the operation lines in the wizard
            }
        }

    def action_open_delivered_wizard(self):
        for operation in self._context.get("active_ids", []):
            operation_id = self.env["freight.operation"].browse(operation)
            operation_id.action_delivered()

    def action_assign_to_delivered(self):
        if not self.assigned_to_deliver:
            raise UserError('Please assign a user before proceeding.')

        # Proceed with the action if assigned_to is set
        assigned_stage = self.env.ref(
            'courier_freight.assigned_deliver_freight_local_stage_courier')  # Adjust the reference based on the operation type
        self.stage_id_local_cruise = assigned_stage

        # Post a message to the assigned user
        self.message_post(
            body=f'Operation assigned to {self.assigned_to.name}.',
            partner_ids=[self.assigned_to_deliver.partner_id.id]
        )

        # Create an activity for the assigned user
        activity_type = self.env.ref('mail.mail_activity_data_todo')  # Adjust activity type if needed
        activity_date_deadline = fields.Datetime.to_string(datetime.now())  # Set deadline to 1 day from now
        self.env['mail.activity'].create({
            'activity_type_id': activity_type.id,
            'note': 'Follow up on assigned operation.',
            'date_deadline': activity_date_deadline,
            'user_id': self.assigned_to.id,
            'res_model_id': self.env.ref('freight.model_freight_operation').id,
            'res_id': self.id,
        })

    def action_delivered(self):
        # Change the state to "Delivered"
        picked_stage = self.env.ref(
            'courier_freight.delivered_freight_local_stage_courier')  # Adjust the reference based on your stage
        self.write({'stage_id_local_cruise': picked_stage.id})

        # Find and mark the existing activity for the assigned user as done
        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', self.env.ref('freight.model_freight_operation').id),
            ('res_id', '=', self.id),
            ('user_id', '=', self.assigned_to_deliver.id),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('state', '=', 'pending')  # Ensure we're dealing with pending activities
        ], limit=1)

        if activity:
            # Use the `action_done` method to mark the activity as done
            activity.action_done()

    @api.depends('shipment_order_line_ids.net_rate',
                 'shipment_order_line_ids.services_amount',
                 'shipment_order_line_ids.international_tax','shipment_order_line_ids.local_tax')
    def _compute_totals(self):
        for order in self:
            untaxed_amount = 0.0
            services = 0.0
            local_taxes = 0.0
            international_taxes = 0.0
            vat = 0.0
            rate = 1.0

            # Retrieve the latest rate for the currency based on the most recent date
            usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
            if usd_currency:
                # Get the latest rate for USD
                latest_rate = usd_currency.rate_ids.sorted('name', reverse=True)[:1]
                if latest_rate:
                    rate = latest_rate.company_rate
                    print(f"Latest USD Rate: {rate}")  # Debugging purpose

            for line in order.shipment_order_line_ids:
                untaxed_amount += line.net_rate
                services += line.services_amount
                # local_taxes += line.international_tax.amount/100 *(line.net_rate)
                if order.cruise_type == 'local':
                    # Calculate local taxes for local cruise type
                    if line.local_tax:
                        for tax in line.local_tax:
                            local_taxes = (tax.amount / 100.0) * (untaxed_amount + services)
                elif order.cruise_type == 'international':
                    # Calculate international taxes for international cruise type
                    if line.international_tax:
                        for tax in line.international_tax:
                            international_taxes = (tax.amount / 100.0) * (untaxed_amount + services)
                # if line.international_tax:
                #     for tax in line.international_tax:
                #         local_taxes = (tax.amount / 100.0) * (untaxed_amount + services)
                if line.tax_id:
                    for tax in line.tax_id:
                        vat = (tax.amount / 100.0) * (untaxed_amount + services + local_taxes)

            total_usd = untaxed_amount + services + local_taxes + vat

            order.untaxed_amount = untaxed_amount
            order.services = services
            order.local_taxes = local_taxes
            order.international_taxes = international_taxes
            order.vat = vat
            order.total_usd = total_usd
            order.total_egp = total_usd * rate

    def _compute_shipment_order_count(self):
        # Example computation method
        for order in self:
            order.shipment_order_count = self.env['shipment.order.payment'].sudo().search_count(
                [('lead_id', '=', order.id)])

    @api.depends('customer_id', 'cruise_type')
    def _compute_pricelist_id(self):
        for record in self:
            if record.customer_id:
                if record.cruise_type == 'local':
                    # Check and assign only if the customer has a local price list
                    record.pricelist_id = record.customer_id.local_currency_id or False
                elif record.cruise_type == 'international':
                    # Check and assign only if the customer has an international price list
                    record.pricelist_id = record.customer_id.international_currency_id or False
                else:
                    record.pricelist_id = False
            else:
                record.pricelist_id = False

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            # Determine the initial domain based on the customer
            if self.cruise_type == 'local':
                return {
                    'domain': {
                        'price_list_id': [('id', 'in', self.customer_id.local_price_list_id.ids)]
                    }
                }
            elif self.cruise_type == 'international':
                return {
                    'domain': {
                        'price_list_id': [('id', 'in', self.customer_id.international_price_list_id.ids)]
                    }
                }
            else:
                return {
                    'domain': {
                        'price_list_id': []
                    }
                }
        else:
            return {
                'domain': {
                    'price_list_id': []
                }
            }

    @api.onchange('cruise_type', 'customer_id')
    def _onchange_cruise_type(self):
        if self.customer_id:
            # Update price_list_id based on current customer and cruise_type
            if self.cruise_type == 'local':
                # Get local price lists for the customer
                local_price_lists = self.customer_id.local_price_list_id
                self.price_list_id = local_price_lists and local_price_lists[0] or False
                return {
                    'domain': {
                        'price_list_id': [('id', 'in', local_price_lists.ids)]
                    }
                }
            elif self.cruise_type == 'international':
                # Get international price lists for the customer
                international_price_lists = self.customer_id.international_price_list_id
                self.price_list_id = international_price_lists and international_price_lists[0] or False
                return {
                    'domain': {
                        'price_list_id': [('id', 'in', international_price_lists.ids)]
                    }
                }
            else:
                self.price_list_id = False
        else:
            self.price_list_id = False  # Reset if no customer is selected

    # Trigger recomputation of pricelist_id whenever cruise_type or customer_id changes
    @api.onchange('customer_id', 'cruise_type')
    def _onchange_pricelist(self):
        # Call the compute method explicitly to update pricelist
        self._compute_pricelist_id()

    @api.depends('pricelist_id')
    def _compute_currency_id(self):
        for record in self:
            if record.pricelist_id:
                record.currency_id = record.pricelist_id.currency_id or False
            else:
                record.currency_id = False

    @api.depends('cruise_type', 'direction', 'sender_country_id', 'receiver_country_id')
    def _compute_sender_country_id(self):
        for record in self:
            if not record.sender_country_id:  # Check if sender_country_id is not already set
                if record.cruise_type == 'local':
                    record.sender_country_id = self.env.ref(
                        'base.eg').id  # Replace 'base.eg' with the actual XML ID for Egypt
                elif record.cruise_type == 'international' and record.direction == 'export':
                    record.sender_country_id = self.env.ref(
                        'base.eg').id  # Replace 'base.eg' with the actual XML ID for Egypt
                else:
                    record.sender_country_id = False

    @api.depends('cruise_type', 'direction', 'sender_country_id', 'receiver_country_id')
    def _compute_receiver_country_id(self):
        for record in self:
            if not record.receiver_country_id:  # Check if receiver_country_id is not already set
                if record.cruise_type == 'local':
                    record.receiver_country_id = self.env.ref(
                        'base.eg').id  # Replace 'base.eg' with the actual XML ID for Egypt
                elif record.cruise_type == 'international' and record.direction == 'import':
                    record.receiver_country_id = self.env.ref(
                        'base.eg').id  # Replace 'base.eg' with the actual XML ID for Egypt
                else:
                    record.receiver_country_id = False

    @api.onchange('customer_id', 'cruise_type')
    def _compute_price_list_id(self):
        for record in self:
            if record.customer_id and not record.price_list_id:
                if record.cruise_type == 'local':
                    price_lists = record.customer_id.local_price_list_id
                elif record.cruise_type == 'international':
                    price_lists = record.customer_id.international_price_list_id
                else:
                    price_lists = False

                # Select the first price list if any are available
                if price_lists:
                    record.price_list_id = price_lists[0]
                else:
                    record.price_list_id = False

    def action_view_online_payments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Online Payments',
            'view_mode': 'tree,form',
            'res_model': 'online.payment',
            'domain': [('freight_operation_id', '=', self.id)],
            'context': {'default_freight_operation_id': self.id,'default_amount': self.collection_amount,'default_customer_id': self.customer_id.id},
        }

    def action_view_shipment_orders(self):
        current_record_id = self.id
        return {
            'name': 'Shipment Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'shipment.order.payment',
            'view_mode': 'tree,form',
            'target': 'current',  # or 'new' if you want to open it in a new windowcontext
            'domain': [('lead_id', '=', current_record_id)],
            # Replace `related_model_id` with the actual field linking to `shipment.order`
            'context': {
                'default_lead_id': self.id
                # Replace `default_freight_shipment_id` with the actual field name you want to filter on
            }
        }

    @api.model
    def _read_group_stage_import_courier_ids(self, stages, domain, order):
        stage_ids = self.env['freight.import.stage.courier'].search([])
        return stage_ids

    @api.model
    def _read_group_stage_export_courier_ids(self, stages, domain, order):
        stage_ids = self.env['freight.export.stage.courier'].search([])
        return stage_ids

    @api.depends('customer_compliment_ids')
    def _compute_compliment_count(self):
        for operation in self:
            operation.compliment_count = len(operation.customer_compliment_ids)

    customer_compliment_ids = fields.One2many('customer.compliment', 'number_of_operations',
                                              string='Customer Compliments')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = ['|', ('name', operator, name), ('master', operator, name)]
        operations = self.search(domain + args, limit=limit)
        return operations.name_get()

    def action_view_compliments(self):
        action = self.env.ref('courier_freight.action_complaint').read()[
            0]  # Replace 'your_module_name' with your actual module name
        action['domain'] = [('number_of_operations', '=', self.id)]
        return action

    def _prepare_shipment_order_vals(self):
        # Common method to prepare ShipmentOrder values from FreightOperation
        return {
            'name': self.name,
            'customer_id': self.customer_id.id,
            'account_number_wb': self.account_number_wb,
            'received_date': self.received_date,
            'sale_order_date': self.sale_order_date,
            'competitors': self.competitors,
            'sale_order_type': self.sale_order_type,
            'shipment_type': self.shipment_type,
            'courier': self.courier,
            'price_list_id': self.price_list_id.id,
            'payment_terms': self.payment_terms.id,
            'sender_name': self.sender_name,
            'sender_mobile': self.sender_mobile,
            'sender_address': self.sender_address,
            'sender_country_id': self.sender_country_id.id,
            'sender_state_id': self.sender_state_id.id,
            'receiver_name': self.receiver_name,
            'receiver_mobile': self.receiver_mobile,
            'receiver_address': self.receiver_address,
            'receiver_country_id': self.receiver_country_id.id,
            'receiver_state_id': self.receiver_state_id.id,
            'cruise_type': self.cruise_type,
            'operation_type': self.operation_type,
            'direction': self.direction,
            'order_lines': [(0, 0, {
                'product': line.product.id,
                'weight': line.weight,
                'vendor': line.vendor.id,
                'customer': line.customer.id,
                'source': line.source,
                'destination': line.destination,
                'services': [(6, 0, [service.id for service in line.services])],
                'services_amount': line.services_amount,
                'departial_date': line.departial_date,
                'description': line.description,
                'no_of_item': line.no_of_item,
                'analytic_tag': line.analytic_tag,
                'international_tax': [(6, 0, [tax.id for tax in line.international_tax])],
                'taxes': line.taxes,
                'net_rate': line.net_rate,
                'sale_price': line.sale_price,
                'cost_price': line.cost_price,
                'total_price': line.total_price,
                'discount': line.discount,
            }) for line in self.shipment_order_line_ids]
        }

    def action_convert(self):
        # Call the original method first if needed
        super(FreightOperation, self).action_convert()
        for operation in self:
            # Prepare ShipmentOrder values
            shipment_order_vals = operation._prepare_shipment_order_vals()

            # Include fields specific to the "cruise" operation type
            if operation.operation_type == 'cruise':
                shipment_order_vals.update({
                    'name': self.name,
                    'customer_id': self.customer_id.id,
                    'account_number_wb': self.account_number_wb,
                    'received_date': self.received_date,
                    'sale_order_date': self.sale_order_date,
                    'competitors': self.competitors,
                    'sale_order_type': self.sale_order_type,
                    'shipment_type': self.shipment_type,
                    'courier': self.courier,
                    'local_type': self.local_type,
                    'price_list_id': self.price_list_id.id,
                    'payment_terms': self.payment_terms.id,
                    'sender_name': self.sender_name,
                    'sender_mobile': self.sender_mobile,
                    'sender_address': self.sender_address,
                    'sender_country_id': self.sender_country_id.id,
                    'sender_state_id': self.sender_state_id.id,
                    'receiver_name': self.receiver_name,
                    'receiver_mobile': self.receiver_mobile,
                    'receiver_address': self.receiver_address,
                    'receiver_country_id': self.receiver_country_id.id,
                    'receiver_state_id': self.receiver_state_id.id,
                    'cruise_type': self.cruise_type,
                    'operation_type': self.operation_type,
                    'direction': self.direction,
                    'lead_id': self.lead_id.id,
                    'order_lines': shipment_order_vals['order_lines'],
                })

    def select_all(self):
        res = super(FreightOperation, self).select_all()
        for line in self.shipment_order_line_ids:
            if not line.processed_so:
                line.check = True
            if not line.processed_po:
                line.check = True
        return res

    def action_open_delivered_issue_wizard(self):
        """Open the delivered issue wizard for this operation."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Delivered Issue',
            'res_model': 'freight.operation.delivered.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_operation_id': self.id,
            }
        }

    def action_open_issue_wizard(self):
        """Opens the wizard for updating the operation's stage."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Issue',
            'res_model': 'freight.operation.delivered.wizard',
            'view_mode': 'tree',
            'target': 'new',
            'context': {
                'default_operation_id': self.id,
            }
        }

    def _compute_issue_count(self):
        for operation in self:
            operation.issue_count = self.env['freight.operation.delivered.wizard'].search_count([('operation_id', '=', operation.id)])

    def action_open_create_rfq_courier(self):
        rate = 1.0

        # Retrieve the latest rate for the currency based on the most recent date
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if usd_currency:
            # Get the latest rate for USD
            latest_rate = usd_currency.rate_ids.sorted('name', reverse=True)[:1]
            if latest_rate:
                rate = latest_rate.company_rate
                print(f"Latest USD Rate: {rate}")  # Debugging purpose

        selected_lines = self.shipment_order_line_ids.filtered(lambda line: line.check and not line.processed_po)

        if not selected_lines:
            raise UserError('No lines selected or all selected lines have already been processed.')

        rfq_ids = []
        for line in selected_lines:
            if not line.vendor:
                raise UserError(f'No vendor selected for product {line.product.name}.')

            # Determine the unit price based on currency and cruise type
            if self.cruise_type == 'international':
                if self.currency_id.name == 'EGP':
                    unit_price = line.cost_price * rate   # Use the total_price_currency field
                else:
                    unit_price = line.cost_price  # Use another price field or conversion logic as needed
            else:
                unit_price = line.cost_price  # Use total_price for local cruise type or other conditions

            # Create RFQ for each selected line
            rfq_vals = {
                'partner_id': line.vendor.id,
                'currency_id': self.currency_id.id,
                'origin': self.name,
                'date_order': fields.Datetime.now(),
                'account_number_wb': self.account_number_wb,
                'lead_id': self.lead_id.id,
                'freight_operation_id': self.id,
                'order_line': [(0, 0, {
                    'product_id': line.product.id,
                    'services_amount': line.services_amount,
                    'chargeable_weight': line.weight,
                    'gross_weight': line.gross_weight,
                    'source': line.source,
                    'destination': line.destination,
                    'account_number_wb': self.account_number_wb,
                    'sender_name': self.sender_name,
                    'receiver_name': self.receiver_name,
                    'services': [(6, 0, [service.id for service in line.services])],
                    'taxes_id': [(6, 0, [tax.id for tax in line.international_tax] + [tax_id.id for tax_id in line.tax_id])],
                    'product_qty': 1,  # Adjust quantity as needed
                    'price_unit': unit_price,  # Set the unit price based on the conditions
                    'name': line.product.name,  # Adjust according to your RFQ line model

                })]
            }

            rfq = self.env['purchase.order'].create(rfq_vals)
            rfq_ids.append(rfq.id)

            # Mark the line as processed and uncheck it
            line.processed_po = True
            line.check = False
            # rfq.action_confirm()
            self.set_order_state()

        # Optional: Open RFQ views for the created RFQs
        if rfq_ids:
            action = self.env.ref('purchase.purchase_rfq').read()[0]
            action['domain'] = [('id', 'in', rfq_ids)]
            return action

    def action_create_rfq_for_multiple(self):
        rate = 1.0
        # Retrieve the latest rate for the currency based on the most recent date
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if usd_currency:
            # Get the latest rate for USD
            latest_rate = usd_currency.rate_ids.sorted('name', reverse=True)[:1]
            if latest_rate:
                rate = latest_rate.company_rate
                print(f"Latest USD Rate: {rate}")  # Debugging purpose

        selected_lines = self.shipment_order_line_ids.filtered(lambda line: not line.processed_po)

        for line in selected_lines:
            if not line.vendor:
                continue
            # Determine the unit price based on currency and cruise type
            if self.cruise_type == 'international':
                if self.currency_id.name == 'EGP':
                    unit_price = line.cost_price * rate   # Use the total_price_currency field
                else:
                    unit_price = line.cost_price  # Use another price field or conversion logic as needed
            else:
                unit_price = line.cost_price  # Use total_price for local cruise type or other conditions

            # Create RFQ for each selected line
            rfq_vals = {
                'partner_id': line.vendor.id,
                'currency_id': self.currency_id.id,
                'origin': self.name,
                'date_order': fields.Datetime.now(),
                'account_number_wb': self.account_number_wb,
                'lead_id': self.lead_id.id,
                'freight_operation_id': self.id,
                'order_line': [(0, 0, {
                    'product_id': line.product.id,
                    'services_amount': line.services_amount,
                    'chargeable_weight': line.weight,
                    'gross_weight': line.gross_weight,
                    'source': line.source,
                    'destination': line.destination,
                    'account_number_wb': self.account_number_wb,
                    'sender_name': self.sender_name,
                    'receiver_name': self.receiver_name,
                    'services': [(6, 0, [service.id for service in line.services])],
                    'taxes_id': [(6, 0, [tax.id for tax in line.international_tax] + [tax_id.id for tax_id in line.tax_id])],
                    'product_qty': 1,  # Adjust quantity as needed
                    'price_unit': unit_price,  # Set the unit price based on the conditions
                    'name': line.product.name,  # Adjust according to your RFQ line model

                })]
            }

            self.env['purchase.order'].create(rfq_vals)
            # Mark the line as processed and uncheck it
            line.processed_po = True
            line.check = False
            self.set_order_state()

    def action_create_multiple_rfq(self):
        selected_ids = self._context.get('active_ids')
        freight_ids = self.browse(selected_ids)
        for freight in freight_ids:
            freight.action_create_rfq_for_multiple()

    def action_open_create_quotation_courier(self):
        selected_lines = self.shipment_order_line_ids.filtered(lambda line: line.check and not line.processed_so)

        if not selected_lines:
            raise UserError('No lines selected or all selected lines have already been processed.')

        quotation_ids = []
        for line in selected_lines:
            if self.cruise_type == 'international' and not line.vendor:
                raise UserError(f'No vendor selected for product {line.product.name}.')
            if self.cruise_type == 'local' and not self.customer_id:
                raise UserError(f'No customer selected ')

            # Determine the partner_id based on the cruise_type
            partner_id = self.customer_id.id

            # Determine the unit price based on currency and cruise type
            if self.cruise_type == 'international':
                if self.currency_id.name == 'EGP':
                    unit_price = line.total_price_currency  # Use the total_price_currency field
                else:
                    unit_price = line.total_price  # Use another price field or conversion logic as needed
            else:
                unit_price = line.total_price_currency  # Use total_price_currency for local cruise

            # Create quotation for each selected line
            quotation_vals = {
                'opportunity_id': self.lead_id.id,
                'freight_operation_id': self.id,
                'account_number_wb': self.account_number_wb,
                'partner_id': partner_id,
                'payment_term_id': self.payment_terms.id,
                'cash': self.cash,
                'order_line': [(0, 0, {
                    'product_id': line.product.id,
                    'services_amount': line.services_amount,
                    'source': line.source,
                    'chargeable_weight': line.weight,
                    'gross_weight': line.gross_weight,
                    'net_rate': line.net_rate,
                    'account_number_wb': self.account_number_wb,
                    'sender_name': self.sender_name,
                    'receiver_name': self.receiver_name,
                    'destination': line.destination,
                    'services': [(6, 0, [service.id for service in line.services])],
                    'local_tax': [(6, 0, [local_tax.id for local_tax in line.local_tax])],
                    'tax_id': [(6, 0, [tax.id for tax in line.international_tax] + [tax_id.id for tax_id in line.tax_id])],
                    'product_uom_qty': 1,  # Adjust quantity as needed
                    'price_unit': unit_price,  # Set the unit price based on the conditions
                    'name': line.product.name,  # Adjust according to your quotation line model
                })]
            }

            quotation = self.env['sale.order'].create(quotation_vals)
            quotation_ids.append(quotation.id)

            # Mark the line as processed and uncheck it
            line.processed_so = True
            line.check = False
            quotation.action_confirm()
            self.set_order_state()

        # Optional: Open quotation views for the created quotations
        if quotation_ids:
            action = self.env.ref('sale.action_quotations').read()[0]
            action['domain'] = [('id', 'in', quotation_ids)]
            return action

    def action_create_so_for_multiple(self):
        selected_lines = self.shipment_order_line_ids.filtered(lambda line: not line.processed_so)

        for line in selected_lines:
            if self.cruise_type == 'international' and not line.vendor:
                raise UserError(f'No vendor selected for product {line.product.name}.')
            if self.cruise_type == 'local' and not self.customer_id:
                raise UserError(f'No customer selected ')

            # Determine the partner_id based on the cruise_type
            partner_id = self.customer_id.id

            # Determine the unit price based on currency and cruise type
            if self.cruise_type == 'international':
                if self.currency_id.name == 'EGP':
                    unit_price = line.total_price_currency  # Use the total_price_currency field
                else:
                    unit_price = line.total_price  # Use another price field or conversion logic as needed
            else:
                unit_price = line.total_price_currency  # Use total_price_currency for local cruise

            # Create quotation for each selected line
            quotation_vals = {
                'opportunity_id': self.lead_id.id,
                'freight_operation_id': self.id,
                'account_number_wb': self.account_number_wb,
                'partner_id': partner_id,
                'payment_term_id': self.payment_terms.id,
                'cash': self.cash,
                'order_line': [(0, 0, {
                    'product_id': line.product.id,
                    'services_amount': line.services_amount,
                    'source': line.source,
                    'chargeable_weight': line.weight,
                    'gross_weight': line.gross_weight,
                    'net_rate': line.net_rate,
                    'account_number_wb': self.account_number_wb,
                    'sender_name': self.sender_name,
                    'receiver_name': self.receiver_name,
                    'destination': line.destination,
                    'services': [(6, 0, [service.id for service in line.services])],
                    'tax_id': [
                        (6, 0, [tax.id for tax in line.international_tax] + [tax_id.id for tax_id in line.tax_id])],
                    'product_uom_qty': 1,  # Adjust quantity as needed
                    'price_unit': unit_price,  # Set the unit price based on the conditions
                    'name': line.product.name,  # Adjust according to your quotation line model
                })]
            }

            quotation = self.env['sale.order'].create(quotation_vals)
            # Mark the line as processed and uncheck it
            line.processed_so = True
            line.check = False
            quotation.action_confirm()
            self.set_order_state()

    def action_create_multiple_so(self):
        selected_ids = self._context.get('active_ids')
        freight_ids = self.browse(selected_ids)
        for freight in freight_ids:
            freight.action_create_so_for_multiple()