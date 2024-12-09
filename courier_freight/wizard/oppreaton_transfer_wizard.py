from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class OperationWizard(models.TransientModel):
    _name = 'operation.wizard'
    _description = 'Operation Wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add this line


    wb_number = fields.Char(string="WB Number")
    operation_line_ids = fields.One2many('operation.wizard.line', 'wizard_id', string="Operations")
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    show_vendor = fields.Boolean(string='Show Vendor', compute='_compute_show_vendor')

    def print_report(self):
        data = {
            'freight_ids': self.operation_line_ids.ids,
        }
        return self.env.ref('courier_freight.report_freight_operation_action').report_action(self, data=data)

    @api.depends('operation_line_ids')
    def _compute_show_vendor(self):
        """Compute if vendor field should be shown based on cruise_type"""
        for wizard in self:
            wizard.show_vendor = any(line.operation_id.cruise_type == 'international' for line in wizard.operation_line_ids)


    @api.onchange('wb_number')
    def _onchange_wb_number(self):
        if self.wb_number:
            # Search for the operation with the given WB number
            operation = self.env['freight.operation'].search([('account_number_wb', '=', self.wb_number)], limit=1)

            if operation:
                # Check if the operation is already in the operation_line_ids
                existing_line = self.operation_line_ids.filtered(lambda line: line.operation_id == operation)

                if existing_line:
                    # Raise an error if the operation is already added
                    raise ValidationError(f"The operation '{operation.name}' is already added.")
                else:
                    # Add the operation to the operation line
                    self.update({
                        'operation_line_ids': [(0, 0, {'operation_id': operation.id})]
                    })

                    # Clear the WB number field after adding
                    self.wb_number = ''
            else:
                # Raise an error if no operation is found with the given WB number
                raise ValidationError(f"No operation found for WB Number '{self.wb_number}'")

    def action_process_operations(self):
        admin_group = self.env.ref('courier_freight.group_freight_sort')
        sort_users = self.env['res.users'].search([('groups_id', '=', admin_group.id)])

        for line in self.operation_line_ids:
            for order_line in line.operation_id.shipment_order_line_ids:
                order_line.write({'vendor': self.vendor_id.id})
            operation = line.operation_id
            delivered_stage = self.env.ref('courier_freight.choose_freight_local_stage_courier')

            if operation:
                operation.write({'stage_id_local_cruise': delivered_stage.id})

            town = operation.receiver_town
            if town:
                branch = self.env['res.branch'].search([('town_ids', 'in', town.id)], limit=1)
                if branch:
                    operation.branch_id = branch.id
            elif operation.receiver_state_id:
                branch = self.env['res.branch'].search([('state_id', '=', operation.receiver_state_id.id)], limit=1)
                if branch:
                    operation.branch_id = branch.id

            if operation.branch_id and operation.branch_id.branch_manager_id:
                manager_id = operation.branch_id.branch_manager_id.id
                res_model_id = self.env['ir.model'].search([('model', '=', 'freight.operation')], limit=1).id

                if res_model_id:
                    self.env['mail.activity'].create({
                        'res_model_id': res_model_id,
                        'res_id': operation.id,
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'summary': _('New Operation Assigned to Your Branch'),
                        'note': _(
                            'A new operation has been assigned to your branch: %s.\n\nPlease choose and assign a delivery user to this operation.') % operation.name,
                        'user_id': manager_id,
                        'date_deadline': fields.Date.today(),
                    })

class OperationWizardLine(models.TransientModel):
    _name = 'operation.wizard.line'
    _description = 'Operation Wizard Line'

    wizard_id = fields.Many2one('operation.wizard', string="Wizard")
    operation_id = fields.Many2one('freight.operation', string="Operation")
    _sql_constraints = [
        ('unique_operation_per_wizard', 'unique(wizard_id, operation_id)',
         'You cannot add the same operation more than once.')
    ]
    account_number_wb = fields.Char(string="WB Number", related="operation_id.account_number_wb")
    sender_name = fields.Char(string="Sender Name", related="operation_id.sender_name")
    sender_mobile = fields.Char(string="Sender Mobile", related="operation_id.sender_mobile")
    # sender_address = fields.Char(string="Sender Address", related="operation_id.sender_address")

    receiver_name = fields.Char(string="Receiver Name", related="operation_id.receiver_name")
    receiver_country_id = fields.Many2one('res.country', string="Receiver Country", related="operation_id.receiver_country_id")
    receiver_state_id = fields.Many2one('res.country.state', string="Receiver State", related="operation_id.receiver_state_id")
    receiver_town = fields.Many2one('res.branch.town', string="Receiver Town", related="operation_id.receiver_town")
    chargeable_weight = fields.Float(string="Chargeable Weight", related="operation_id.chargeable_weight")
    branch_id = fields.Many2one('res.branch', string="Branch", related="operation_id.branch_id")
class FreightOperationExcelReport(models.AbstractModel):
    _name = 'report.shipment_order.report_freight_operation_action'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Operation Report'

    def generate_xlsx_report(self, workbook, data, objs):
        freight_ids = data.get('freight_ids') or []

        sheet = workbook.add_worksheet()
        current_user = self.env.user.name
        current_date = fields.Date.today()

        # Define formats
        format_header = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'bg_color': '#C0C0C0'})
        format_title = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True, 'border': True, 'bg_color': '#C0C0C0'})
        format_field = workbook.add_format({'font_size': 10, 'align': 'left'})
        format_date = workbook.add_format({'font_size': 10, 'align': 'left', 'num_format': 'yyyy-mm-dd'})

        # Set column widths
        sheet.set_column(0, 8, 20)

        # Merge cells for the report header
        sheet.merge_range('A1:B3', f"Freight Report\nIssued By: {current_user}\tIssued on: {current_date}", format_field)

        # Write table headers
        headers = ['Operation', 'Operation Type', 'Product', 'Charger Weight', 'Gross Weight', 'Services Amount', 'Sale Price', 'Cost Price', 'Vendor']
        for col, header in enumerate(headers):
            sheet.write(8, col, header, format_title)

        # Populate rows
        row = 9
        wizard_line = self.env['operation.wizard.line'].search([('id', 'in', freight_ids)])
        for op in wizard_line:
            operation_id = op.operation_id
            freight_operations = self.env['freight.operation'].search([('id', '=', operation_id.id)])  # Correct search
            for freight in freight_operations:
                for operation in freight.shipment_order_line_ids:
                    sheet.write(row, 0, operation.freight_operation_id.name or '', format_field)
                    sheet.write(row, 1, operation.freight_operation_id.operation_type or '', format_field)
                    sheet.write(row, 2, operation.product.name or '', format_field)
                    sheet.write(row, 3, operation.weight or 0.0, format_field)
                    sheet.write(row, 4, operation.gross_weight or 0.0, format_field)
                    sheet.write(row, 5, operation.services_amount or 0.0, format_field)
                    sheet.write(row, 6, operation.sale_price or 0.0, format_field)
                    sheet.write(row, 7, operation.cost_price or 0.0, format_field)
                    sheet.write(row, 8, operation.vendor.name or '', format_field)
                    row += 1

        workbook.close()