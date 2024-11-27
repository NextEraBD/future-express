from odoo import api, fields, models,_,_lt
import datetime
from dateutil.relativedelta import relativedelta
from math import copysign
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, formatLang, end_of
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, UserError, ValidationError


class FreightProfitabilityWizard(models.TransientModel):
    _name = 'freight.profitability.report'
    _description = 'Activity Profitability'

    date_start = fields.Date(string="From")
    date_end = fields.Date(string="To")
    # stage_ids = fields.Many2many('freight.export.stage')
    customer_ids = fields.Many2many('res.partner')
    branch_ids = fields.Many2many('res.branch')
    details = fields.Boolean()
    max_operation = fields.Integer()
    official = fields.Boolean(string="Include Official")
    import_stage_ids = fields.Many2many('freight.import.stage', string="Stages")
    export_stage_ids = fields.Many2many('freight.export.stage', string="Export Stages")
    direction = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('local', 'Trans Shipment')
    ], string='Direction')
    claim_created_filter = fields.Boolean(string="Show Only Invoiced Opreation", default=False)
    official_receipt = fields.Boolean(string="Official Receipt")
    official_expenses = fields.Boolean(string="Official Expenses")

    # Method to trigger the report generation
    def generate_report(self):
        self.ensure_one()

        # Get selected direction and stage IDs
        selected_direction = self.direction
        import_stages = self.import_stage_ids.ids
        export_stages = self.export_stage_ids.ids

        # Build the domain for filtering
        domain = [
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('customer_id', 'in', self.customer_ids.ids),
        ]

        if selected_direction == 'import':
            domain.append(('stage_id_import', 'in', import_stages))
        elif selected_direction == 'export':
            domain.append(('stage_id_export', 'in', export_stages))
        else:
            domain.append(('stage_id_import', 'in', import_stages))
            domain.append(('stage_id_export', 'in', export_stages))

        data = {
            'model_id': self.id,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'max_operation': self.max_operation,
            'customer_ids': ','.join(str(x) for x in self.customer_ids.ids),
            'stage_id_import': ','.join(str(x) for x in import_stages),
            'stage_id_export': ','.join(str(x) for x in export_stages),
            'direction': selected_direction,
            'claim_created_filter': self.claim_created_filter
        }
        return self.env.ref('freight.action_freight_trx_report_xlsx').report_action(self, data=data)

    def generate_report_expenses(self):
        self.ensure_one()

        # Get selected direction and stage IDs
        selected_direction = self.direction
        import_stages = self.import_stage_ids.ids
        export_stages = self.export_stage_ids.ids

        # Build the domain for filtering
        domain = [
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('customer_id', 'in', self.customer_ids.ids),
        ]

        if selected_direction == 'import':
            domain.append(('stage_id_import', 'in', import_stages))
        elif selected_direction == 'export':
            domain.append(('stage_id_export', 'in', export_stages))
        else:
            domain.append(('stage_id_import', 'in', import_stages))
            domain.append(('stage_id_export', 'in', export_stages))

        data = {
            'model_id': self.id,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'max_operation': self.max_operation,
            'customer_ids': ','.join(str(x) for x in self.customer_ids.ids),
            'stage_id_import': ','.join(str(x) for x in import_stages),
            'stage_id_export': ','.join(str(x) for x in export_stages),
            'direction': selected_direction,
            'claim_created_filter': self.claim_created_filter
        }
        return self.env.ref('freight.action_freight_trx_report_expenses_xlsx').report_action(self, data=data)

    def action_print_excel(self):
        self.ensure_one()

        # Get selected direction and stage IDs
        selected_direction = self.direction
        import_stages = self.import_stage_ids.ids
        export_stages = self.export_stage_ids.ids

        # Build the domain for filtering
        domain = [
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('customer_id', 'in', self.customer_ids.ids),
        ]

        if selected_direction == 'import':
            domain.append(('stage_id_import', 'in', import_stages))
        elif selected_direction == 'export':
            domain.append(('stage_id_export', 'in', export_stages))
        else:
            domain.append(('stage_id_import', 'in', import_stages))
            domain.append(('stage_id_export', 'in', export_stages))

        data = {
            'model_id': self.id,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'max_operation': self.max_operation,
            'customer_ids': ','.join(str(x) for x in self.customer_ids.ids),
            'stage_id_import': ','.join(str(x) for x in import_stages),
            'stage_id_export': ','.join(str(x) for x in export_stages),
            'direction': selected_direction,
            'claim_created_filter': self.claim_created_filter
        }

        return self.env.ref('freight.action_freight_profitability_report_xlx').report_action(None, data=data)

    def action_print_trx_excel(self):
        self.ensure_one()

        # Get selected direction
        selected_direction = self.direction
        import_stages = self.import_stage_ids.ids
        export_stages = self.export_stage_ids.ids
        # Build the domain for filtering the freight operations
        domain = [
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('customer_id', 'in', self.customer_ids.ids),
        ]

        if selected_direction == 'import':
            domain.append(('stage_id_import', 'in', self.import_stage_ids.ids))
        elif selected_direction == 'export':
            domain.append(('stage_id_export', 'in', self.export_stage_ids.ids))
        else:
            domain.append(('stage_id_import', 'in', self.import_stage_ids.ids))
            domain.append(('stage_id_export', 'in', self.export_stage_ids.ids))

        # Pass the data to the report
        data = {
            'model_id': self.id,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'max_operation': self.max_operation,
            'customer_ids': ','.join(str(x) for x in self.customer_ids.ids),
            'stage_id_import': ','.join(str(x) for x in self.import_stage_ids.ids),
            'stage_id_export': ','.join(str(x) for x in self.export_stage_ids.ids),
            'direction': selected_direction,
            'claim_created_filter': self.claim_created_filter

        }

        return self.env.ref('freight.action_freight_trx_report_xlx').report_action(None, data=data)


class FreightTrxExcelReport(models.AbstractModel):
    _name = 'report.freight.action_freight_trx_report_xlx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'EGY Activity Trx Report'

    def generate_xlsx_report(self, workbook, data, objs):
        # Extract parameters from the wizard
        direction = data.get('direction', '')
        customer_ids = [int(x) for x in data.get('customer_ids', '').split(',')] if data.get('customer_ids') else []
        stage_id_import = [int(x) for x in data.get('stage_id_import', '').split(',')] if data.get(
            'stage_id_import') else []
        stage_id_export = [int(x) for x in data.get('stage_id_export', '').split(',')] if data.get(
            'stage_id_export') else []

        claim_created_filter = data.get('claim_created_filter', False)  # Get the checkbox value
        max_operation = data.get('max_operation', None)
        date_start = datetime.strptime(data['date_start'], '%Y-%m-%d') if data['date_start'] else None
        date_end = datetime.strptime(data['date_end'], '%Y-%m-%d') if data['date_end'] else None

        # Build domain for filtering based on date, customer, direction, stages, and claim_created_filter
        domain = []
        if date_start:
            domain.append(('create_date', '>=', date_start))
        if date_end:
            domain.append(('create_date', '<=', date_end))
        if customer_ids:
            domain.append(('customer_id', 'in', customer_ids))

        # Apply direction-specific filters
        if direction == 'import':
            domain.append(('direction', '=', 'import'))
            domain.append(('stage_id_import', 'in', stage_id_import))  # Import stages
        elif direction == 'export':
            domain.append(('direction', '=', 'export'))
            domain.append(('stage_id_export', 'in', stage_id_export))  # Export stages
        elif direction == 'local':
            domain.append(('direction', '=', 'local'))

        # If the claim_created_filter checkbox is checked, filter by either claim_created = True or invised_created = True
        if claim_created_filter:
            domain.append('|')
            domain.append(('claim_created', '=', True))
            domain.append(('invised_created', '=', True))

        limit = max_operation
        operations = self.env['freight.operation'].search(domain, limit=limit)
        current_user = self.env.user.name
        current_date = fields.Date.today()
        # Create the Excel worksheet
        sheet = workbook.add_worksheet()

        # Formatting for the Excel report
        format_header = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'bg_color': '#C0C0C0'})
        bold_center_format = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'bold': True})
        format_title = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'bold': True, 'border': True, 'bg_color': '#C0C0C0'})
        format_field = workbook.add_format({'font_size': 10, 'align': 'left'})
        format_date = workbook.add_format({'font_size': 10, 'align': 'left', 'num_format': 'yyyy-mm-dd'})

        # Set column widths
        sheet.set_column(0, 11, 20)
        date_start_str = data['date_start']
        date_end_str = data['date_end']
        date_start = datetime.strptime(date_start_str, '%Y-%m-%d') if date_start_str else None
        date_end = datetime.strptime(date_end_str, '%Y-%m-%d') if date_end_str else None
        date_range_str = f"{date_start.strftime('%Y-%m-%d') if date_start else ''} To {date_end.strftime('%Y-%m-%d') if date_end else ''}"
        # Header
        # Define format for bold and centered text

        combined_text_header = (
            "Egyptian Transport & Commercial Services CO. S.A.E.\n"
            "AP/AR مصروفات وإرادات العمليات\n")
        combined_text = (

            f"Issued By:                          {current_user}    \tIssued on:                                      {current_date}\n"
            f"Date From:                          {date_end_str}      \tTo:                                              {date_end_str}\n"
            "Operations From:                     ALL              \tTo:                                              ALL\n"
            "Branch:                              ALL Branches     \tStatus:                                          Exclude Official Receipts & under processing\n"
            "Project:                                                   Sales:\n"
            "Customer:                                                   GL Posting Status:                                   ALL\n"
            "OPR Status:                           OPEN\n\n"
            "                                     Note: This report display the details of max 250 operations.              "
        )

        # Merge cells and write the combined text
        sheet.merge_range('A1:L2', combined_text_header, bold_center_format)
        sheet.merge_range('A3:L11', combined_text, format_field)

        # Write the column titles
        sheet.write(11, 0, 'Operation', format_title)
        sheet.write(11, 1, 'Client No.', format_title)
        sheet.write(11, 2, 'Client Name', format_title)
        sheet.write(11, 3, 'Notes', format_title)
        sheet.write(11, 4, 'Start Date', format_title)
        sheet.write(11, 5, 'End Date', format_title)
        sheet.write(11, 6, 'Total Expenses (EGP)', format_title)
        sheet.write(11, 7, 'Total Revenue (EGP)', format_title)
        sheet.write(11, 8, 'Total (EGP)', format_title)
        sheet.write(11, 9, 'Direction', format_title)
        sheet.write(11, 10, 'Stage', format_title)
        sheet.write(11, 11, 'Invoiced', format_title)  # Add the "Claim Created" column

        serial_number = 1
        row = 12

        # Loop through the filtered operations and write to the report
        for operation in operations:
            # Get the stage name based on the direction
            stage_name = ''
            if operation.direction == 'import':
                stage_name = operation.stage_id_import.name if operation.stage_id_import else ''
            elif operation.direction == 'export':
                stage_name = operation.stage_id_export.name if operation.stage_id_export else ''
            elif operation.direction == 'local':
                stage_name = 'N/A'  # Trans Shipment doesn't have a specific stage

            # Write operation details
            sheet.write(row, 0, operation.name or '', format_field)
            sheet.write(row, 1, operation.customer_id.name or '', format_field)
            sheet.write(row, 2, operation.customer_id.name or '', format_field)
            sheet.write(row, 3, operation.description or '', format_field)
            sheet.write(row, 4, operation.date_from or '', format_field)
            sheet.write(row, 5, operation.date_end or '', format_field)
            sheet.write(row, 6, operation.total_invoiced or '', format_field)
            sheet.write(row, 7, operation.total_bills or '', format_field)
            sheet.write(row, 8, operation.control or '', format_field)

            # Write direction (Import, Export, or Trans Shipment)
            sheet.write(row, 9, operation.direction, format_field)
            # Write stage (Import Stage, Export Stage, or N/A for Trans Shipment)
            sheet.write(row, 10, stage_name, format_field)

            # Write Claim Created status
            claim_status = 'Created' if operation.claim_created or operation.invised_created else 'Not Created'
            sheet.write(row, 11, claim_status, format_field)

            row += 1
            serial_number += 1

class FreightProfitabilityExcelReport(models.AbstractModel):
    _name = 'report.freight.action_freight_profitability_report_xlx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'EGY Activity Profitability Report'

    def generate_xlsx_report(self, workbook, data, objs):
        max_operation = data.get('max_operation', None)
        date_start = False
        date_end = False
        if data['date_start']:
            date_start = datetime.strptime(data['date_start'], '%Y-%m-%d')
        if data['date_end']:
            date_end = datetime.strptime(data['date_end'], '%Y-%m-%d')
        domain = []
        if date_start:
            domain.append(('create_date', '>=', date_start))
        if date_end:
            domain.append(('create_date', '<=', date_end))
        # if business_unit_ids:
        #     domain.append(('business_unit_id', 'in', business_unit_ids))

        limit = max_operation if max_operation is not None else None
        operations = self.env['freight.operation'].search(domain, limit=limit)
        current_user = self.env.user.name
        current_date = fields.Date.today()
        sheet = workbook.add_worksheet()
        format_header = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'bold': True, 'bg_color': '#C0C0C0'})
        format_title = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'bold': True, 'border': True, 'bg_color': '#C0C0C0'})
        format_field = workbook.add_format({'font_size': 10, 'align': 'left'})
        format_date = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'num_format': 'yyyy-mm-dd'})

        sheet.set_column(0, 11, 20)  # Adjusting column widths
        date_start_str = data['date_start']
        date_end_str = data['date_end']
        date_start = datetime.strptime(date_start_str, '%Y-%m-%d') if date_start_str else None
        date_end = datetime.strptime(date_end_str, '%Y-%m-%d') if date_end_str else None
        date_range_str = f"{date_start.strftime('%Y-%m-%d') if date_start else ''} To {date_end.strftime('%Y-%m-%d') if date_end else ''}"
        # Header
        # header_row = 1

        # Merge cells and write header text
        sheet.merge_range('A1:B3',
                          f"Egyptian Transport & Commercial Services CO. S.A.E.\nEGY Activity Profitability\nIssued By: {current_user}\tIssued on: {current_date}",
                          format_field)
        sheet.merge_range('A4:B7',
                          f'Order Date From: {date_start_str}\tOrder Date To: {date_end_str}\nBusiness Unit: NOTPROJECTS',
                          format_field)
        # Start with the initial value

        sheet.write(8, 0, 'File Number', format_title)
        sheet.write(8, 1, 'Branch', format_title)
        sheet.write(8, 2, 'Business Unit', format_title)
        sheet.write(8, 3, 'Sales Person Name', format_title)
        sheet.write(8, 4, 'Activity', format_title)
        sheet.write(8, 5, 'Master Service', format_title)
        sheet.write(8, 6, 'Commodity Type', format_title)
        sheet.write(8, 7, 'Status', format_title)
        sheet.write(8, 8, 'Order Type', format_title)
        sheet.write(8, 9, 'Deal Number', format_title)
        sheet.write(8, 10, 'Customer Name', format_title)
        sheet.write(8, 11, 'Agent', format_title)
        sheet.write(8, 12, 'Carrier', format_title)
        sheet.write(8, 13, 'Parent Entity', format_title)
        sheet.write(8, 14, 'Starting Date', format_title)
        sheet.write(8, 15, 'Ending Date', format_title)
        sheet.write(8, 16, 'Operator Name', format_title)
        sheet.write(8, 17, 'Inco Terms', format_title)
        sheet.write(8, 18, 'TEUS', format_title)
        sheet.write(8, 19, 'CNT20', format_title)
        sheet.write(8, 20, 'CNT40', format_title)
        sheet.write(8, 21, 'FRTONS', format_title)
        sheet.write(8, 22, 'KGS', format_title)
        sheet.write(8, 23, 'CBM', format_title)
        sheet.write(8, 24, 'Port of load', format_title)
        sheet.write(8, 25, 'Port of discharge', format_title)
        sheet.write(8, 26, 'Revenue', format_title)
        sheet.write(8, 27, 'Expense', format_title)
        sheet.write(8, 28, 'CM without official receipts', format_title)
        sheet.write(8, 29, 'Pass-thru', format_title)
        sheet.write(8, 30, 'Performa', format_title)
        sheet.write(8, 31, 'Expense Under Processing', format_title)
        sheet.write(8, 32, 'Estimate buy EGP', format_title)
        sheet.write(8, 33, 'Estimate sell EGP', format_title)
        sheet.write(8, 34, 'Estimate pass-throughs EGP', format_title)
        sheet.write(8, 35, 'Estimate CM', format_title)
        sheet.write(8, 36, 'GEF % of completion', format_title)
        sheet.write(8, 37, 'Accrued Rev', format_title)
        sheet.write(8, 38, 'Accrued Exp', format_title)
        sheet.write(8, 39, 'Accrued CM', format_title)


        serial_number = 1
        row = 9
        for operation in operations:
            expense_ids = self.env['hr.cover.letter.expense'].search([('shipment_number', '=', operation.id), ('line_state', 'in', ('draft','approved_operator'))])
            expense_under_progress = sum(expense_ids.mapped('amount_sale'))
            official_ids = self.env['hr.cover.letter.official'].search([('shipment_number', '=', operation.id), ('line_state', 'in', ('draft','approved_operator'))])
            official_under_progress = sum(official_ids.mapped('amount_sale'))
            claims = self.env['account.move'].sudo().search(
                [('freight_operation_id', '=', operation.id), ('move_type', '=', 'out_invoice'), ('is_claim', '=', True)])
            total_claim = 0.0
            for invoice in claims:
                total_claim += invoice.amount_total
            claims_total = operation.total_invoiced - total_claim
            # Write operation details
            sheet.write(row, 0, operation.name if operation.name else '', format_field)
            sheet.write(row, 1, operation.branch_id.name if operation.branch_id else '', format_field)
            sheet.write(row, 2, operation.business_unit_id.name if operation.business_unit_id else '', format_field)
            sheet.write(row, 3, operation.customer_service_id.name if operation.customer_service_id else '', format_field)
            sheet.write(row, 4, operation.transport if operation.transport else '', format_field)
            sheet.write(row, 5, operation.master.name if operation.master else '', format_field)
            sheet.write(row, 6, operation.commodity_id.name if operation.commodity_id else '', format_field)
            sheet.write(row, 7, operation.state if operation.state else '', format_field)
            sheet.write(row, 8, operation.control if operation.control else '', format_field)
            sheet.write(row, 9, operation.housing if operation.housing else '', format_field)
            sheet.write(row, 10, operation.customer_id.name if operation.customer_id else '', format_field)
            sheet.write(row, 11, operation.agent_id.name if operation.agent_id else '', format_field)
            sheet.write(row, 12, operation.carrier_id.name if operation.carrier_id else '', format_field)
            sheet.write(row, 13, operation.name if operation.name else '', format_field)
            sheet.write(row, 14, operation.date_from if operation.date_from else '', format_date)
            sheet.write(row, 15, operation.date_end if operation.date_end else '', format_date)
            sheet.write(row, 16, operation.clearance_operator.name if operation.clearance_operator else '', format_field)
            sheet.write(row, 17, operation.incoterm_id.name if operation.incoterm_id else '', format_field)
            sheet.write(row, 18, operation.teu if operation.teu else '', format_field)
            sheet.write(row, 19, operation.teu if operation.teu else '', format_field)
            sheet.write(row, 20, operation.teu if operation.teu else '', format_field)
            sheet.write(row, 21, operation.frt if operation.frt else '', format_field)
            sheet.write(row, 22, operation.frt if operation.frt else '', format_field)
            sheet.write(row, 23, operation.cbm if operation.cbm else '', format_field)
            sheet.write(row, 24, operation.source_location_id.name if operation.source_location_id else '', format_field)
            sheet.write(row, 25, operation.destination_location_id.name if operation.destination_location_id else '', format_field)
            sheet.write(row, 26, operation.total_invoiced if operation.total_invoiced else '', format_field)
            sheet.write(row, 27, operation.total_bills if operation.total_bills else '', format_field)
            sheet.write(row, 28, claims_total if claims_total else '', format_field)
            sheet.write(row, 29, operation.pass_thru if operation.pass_thru else '', format_field)
            sheet.write(row, 30, expense_under_progress if expense_under_progress else '', format_field)
            sheet.write(row, 31, operation.total_bills if operation.total_bills else '', format_field)
            sheet.write(row, 32, operation.total_invoiced if operation.total_invoiced else '', format_field)
            sheet.write(row, 33,operation.pass_thru if operation.pass_thru else '', format_field)
            sheet.write(row, 34,  '', format_field)
            sheet.write(row, 35,  '', format_field)
            sheet.write(row, 36,  '', format_field)
            sheet.write(row, 37,  '', format_field)
            sheet.write(row, 38, '', format_field)
            sheet.write(row, 39,  '', format_field)

            row += 1
            serial_number += 1

        workbook.close()

class FreightTrxExcelReport(models.AbstractModel):
    _name = 'report.freight.action_freight_trx_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Freight Transaction Excel Report'

    def generate_xlsx_report(self, workbook, data, objs):
        # Extract parameters from the wizard
        direction = data.get('direction', '')
        customer_ids = [int(x) for x in data.get('customer_ids', '').split(',')] if data.get('customer_ids') else []
        stage_id_import = [int(x) for x in data.get('stage_id_import', '').split(',')] if data.get(
            'stage_id_import') else []
        stage_id_export = [int(x) for x in data.get('stage_id_export', '').split(',')] if data.get(
            'stage_id_export') else []

        claim_created_filter = data.get('claim_created_filter', False)  # Get the checkbox value
        max_operation = data.get('max_operation', None)
        date_start = datetime.strptime(data['date_start'], '%Y-%m-%d') if data['date_start'] else None
        date_end = datetime.strptime(data['date_end'], '%Y-%m-%d') if data['date_end'] else None

        # Build domain for filtering based on date, customer, direction, stages, and claim_created_filter
        domain = []
        if date_start:
            domain.append(('create_date', '>=', date_start))
        if date_end:
            domain.append(('create_date', '<=', date_end))
        if customer_ids:
            domain.append(('customer_id', 'in', customer_ids))

        # Apply direction-specific filters
        if direction == 'import':
            domain.append(('direction', '=', 'import'))
            domain.append(('stage_id_import', 'in', stage_id_import))  # Import stages
        elif direction == 'export':
            domain.append(('direction', '=', 'export'))
            domain.append(('stage_id_export', 'in', stage_id_export))  # Export stages
        elif direction == 'local':
            domain.append(('direction', '=', 'local'))

        # If the claim_created_filter checkbox is checked, filter by either claim_created = True or invised_created = True
        if claim_created_filter:
            domain.append('|')
            domain.append(('claim_created', '=', True))
            domain.append(('invised_created', '=', True))

        limit = max_operation
        operations = self.env['freight.operation'].search(domain, limit=limit)
        current_user = self.env.user.name
        current_date = fields.Date.today()
        # Create the Excel worksheet
        sheet = workbook.add_worksheet()

        # Formatting for the Excel report
        format_header = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'bg_color': '#C0C0C0'})
        bold_center_format = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'bold': True})
        format_title = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'bold': True, 'border': True, 'bg_color': '#C0C0C0'})
        format_field = workbook.add_format({'font_size': 10, 'align': 'left'})
        format_date = workbook.add_format({'font_size': 10, 'align': 'left', 'num_format': 'yyyy-mm-dd'})

        # Set column widths
        sheet.set_column(0, 11, 20)
        date_start_str = data['date_start']
        date_end_str = data['date_end']
        date_start = datetime.strptime(date_start_str, '%Y-%m-%d') if date_start_str else None
        date_end = datetime.strptime(date_end_str, '%Y-%m-%d') if date_end_str else None
        date_range_str = f"{date_start.strftime('%Y-%m-%d') if date_start else ''} To {date_end.strftime('%Y-%m-%d') if date_end else ''}"
        # Header
        # Define format for bold and centered text

        combined_text_header = (
            "Egyptian Transport & Commercial Services CO. S.A.E.\n"
            "AP/AR مصروفات وإرادات العمليات\n")
        combined_text = (

            f"Issued By:                          {current_user}    \tIssued on:                                      {current_date}\n"
            f"Date From:                          {date_end_str}      \tTo:                                              {date_end_str}\n"
            "Operations From:                     ALL              \tTo:                                              ALL\n"
            "Branch:                              ALL Branches     \tStatus:                                          Exclude Official Receipts & under processing\n"
            "Project:                                                   Sales:\n"
            "Customer:                                                   GL Posting Status:                                   ALL\n"
            "OPR Status:                           OPEN\n\n"
            "                                     Note: This report display the details of max 250 operations.              "
        )

        # Merge cells and write the combined text
        sheet.merge_range('A1:L2', combined_text_header, bold_center_format)
        sheet.merge_range('A3:L11', combined_text, format_field)

        # Write the column titles
        sheet.write(11, 0, 'Operation', format_title)
        sheet.write(11, 1, 'Client No.', format_title)
        sheet.write(11, 2, 'Client Name', format_title)
        sheet.write(11, 3, 'Notes', format_title)
        sheet.write(11, 4, 'Start Date', format_title)
        sheet.write(11, 5, 'End Date', format_title)
        sheet.write(11, 6, 'Total Sale Amount', format_title)
        sheet.write(11, 7, 'Total Cost Amount', format_title)
        sheet.write(11, 8, 'Total Profit Amount', format_title)
        sheet.write(11, 9, 'Direction', format_title)
        sheet.write(11, 10, 'Stage', format_title)
        sheet.write(11, 11, 'Invoiced', format_title)  # Add the "Claim Created" column

        serial_number = 1
        row = 12

        # Loop through the filtered operations and write to the report
        for operation in operations:
            # Get the stage name based on the direction
            stage_name = ''
            if operation.direction == 'import':
                stage_name = operation.stage_id_import.name if operation.stage_id_import else ''
            elif operation.direction == 'export':
                stage_name = operation.stage_id_export.name if operation.stage_id_export else ''
            elif operation.direction == 'local':
                stage_name = 'N/A'  # Trans Shipment doesn't have a specific stage

            # Write operation details
            sheet.write(row, 0, operation.name or '', format_field)
            sheet.write(row, 1, operation.customer_id.name or '', format_field)
            sheet.write(row, 2, operation.customer_id.name or '', format_field)
            sheet.write(row, 3, operation.description or '', format_field)
            sheet.write(row, 4, operation.date_from or '', format_field)
            sheet.write(row, 5, operation.date_end or '', format_field)
            sheet.write(row, 6, operation.total_sale_amount or '', format_field)
            sheet.write(row, 7, operation.total_cost_amount or '', format_field)
            sheet.write(row, 8, operation.total_profit_amount or '', format_field)

            # Write direction (Import, Export, or Trans Shipment)
            sheet.write(row, 9, operation.direction, format_field)
            # Write stage (Import Stage, Export Stage, or N/A for Trans Shipment)
            sheet.write(row, 10, stage_name, format_field)

            # Write Claim Created status
            claim_status = 'Created' if operation.claim_created or operation.invised_created else 'Not Created'
            sheet.write(row, 11, claim_status, format_field)

            row += 1
            serial_number += 1

class FreightTrxExcelExpensesReport(models.AbstractModel):
    _name = 'report.freight.action_freight_trx_report_expenses_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Freight Transaction Excel Report Expenses'

    def generate_xlsx_report(self, workbook, data, objs):
        # Extract parameters from the wizard
        direction = data.get('direction', '')
        customer_ids = [int(x) for x in data.get('customer_ids', '').split(',')] if data.get('customer_ids') else []
        stage_id_import = [int(x) for x in data.get('stage_id_import', '').split(',')] if data.get(
            'stage_id_import') else []
        stage_id_export = [int(x) for x in data.get('stage_id_export', '').split(',')] if data.get(
            'stage_id_export') else []

        claim_created_filter = data.get('claim_created_filter', False)  # Get the checkbox value
        max_operation = data.get('max_operation', None)
        date_start = datetime.strptime(data['date_start'], '%Y-%m-%d') if data['date_start'] else None
        date_end = datetime.strptime(data['date_end'], '%Y-%m-%d') if data['date_end'] else None

        # Build domain for filtering based on date, customer, direction, stages, and claim_created_filter
        domain = []
        if date_start:
            domain.append(('create_date', '>=', date_start))
        if date_end:
            domain.append(('create_date', '<=', date_end))
        if customer_ids:
            domain.append(('customer_id', 'in', customer_ids))

        # Apply direction-specific filters
        if direction == 'import':
            domain.append(('direction', '=', 'import'))
            domain.append(('stage_id_import', 'in', stage_id_import))  # Import stages
        elif direction == 'export':
            domain.append(('direction', '=', 'export'))
            domain.append(('stage_id_export', 'in', stage_id_export))  # Export stages
        elif direction == 'local':
            domain.append(('direction', '=', 'local'))

        # If the claim_created_filter checkbox is checked, filter by either claim_created = True or invised_created = True
        if claim_created_filter:
            domain.append('|')
            domain.append(('claim_created', '=', True))
            domain.append(('invised_created', '=', True))

        limit = max_operation
        operations = self.env['freight.operation'].search(domain, limit=limit)
        current_user = self.env.user.name
        current_date = fields.Date.today()
        # Create the Excel worksheet
        sheet = workbook.add_worksheet()

        # Formatting for the Excel report
        format_header = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'bg_color': '#C0C0C0'})
        bold_center_format = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'bold': True})
        format_title = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'bold': True, 'border': True, 'bg_color': '#C0C0C0'})
        format_field = workbook.add_format({'font_size': 10, 'align': 'left'})
        format_date = workbook.add_format({'font_size': 10, 'align': 'left', 'num_format': 'yyyy-mm-dd'})

        # Set column widths
        sheet.set_column(0, 11, 20)
        date_start_str = data['date_start']
        date_end_str = data['date_end']
        date_start = datetime.strptime(date_start_str, '%Y-%m-%d') if date_start_str else None
        date_end = datetime.strptime(date_end_str, '%Y-%m-%d') if date_end_str else None
        date_range_str = f"{date_start.strftime('%Y-%m-%d') if date_start else ''} To {date_end.strftime('%Y-%m-%d') if date_end else ''}"
        # Header
        # Define format for bold and centered text

        combined_text_header = (
            "Egyptian Transport & Commercial Services CO. S.A.E.\n"
            "AP/AR مصروفات وإرادات العمليات\n")
        combined_text = (

            f"Issued By:                          {current_user}    \tIssued on:                                      {current_date}\n"
            f"Date From:                          {date_end_str}      \tTo:                                              {date_end_str}\n"
            "Operations From:                     ALL              \tTo:                                              ALL\n"
            "Branch:                              ALL Branches     \tStatus:                                          Exclude Official Receipts & under processing\n"
            "Project:                                                   Sales:\n"
            "Customer:                                                   GL Posting Status:                                   ALL\n"
            "OPR Status:                           OPEN\n\n"
            "                                     Note: This report display the details of max 250 operations.              "
        )

        # Merge cells and write the combined text
        sheet.merge_range('A1:L2', combined_text_header, bold_center_format)
        sheet.merge_range('A3:L11', combined_text, format_field)

        # Write the column titles
        sheet.write(11, 0, 'Operation', format_title)
        sheet.write(11, 1, 'Client No.', format_title)
        sheet.write(11, 2, 'Client Name', format_title)
        sheet.write(11, 3, 'Notes', format_title)
        sheet.write(11, 4, 'Start Date', format_title)
        sheet.write(11, 5, 'End Date', format_title)
        sheet.write(11, 6, 'Total Sale Amount', format_title)
        sheet.write(11, 7, 'Total Cost Amount', format_title)
        sheet.write(11, 8, 'Total Profit Amount', format_title)
        sheet.write(11, 9, 'Direction', format_title)
        sheet.write(11, 10, 'Stage', format_title)
        sheet.write(11, 11, 'Invoiced', format_title)  # Add the "Claim Created" column

        serial_number = 1
        row = 12

        # Loop through the filtered operations and write to the report
        for operation in operations:
            # Get the stage name based on the direction
            stage_name = ''
            if operation.direction == 'import':
                stage_name = operation.stage_id_import.name if operation.stage_id_import else ''
            elif operation.direction == 'export':
                stage_name = operation.stage_id_export.name if operation.stage_id_export else ''
            elif operation.direction == 'local':
                stage_name = 'N/A'  # Trans Shipment doesn't have a specific stage

            # Write operation details
            sheet.write(row, 0, operation.name or '', format_field)
            sheet.write(row, 1, operation.customer_id.name or '', format_field)
            sheet.write(row, 2, operation.customer_id.name or '', format_field)
            sheet.write(row, 3, operation.description or '', format_field)
            sheet.write(row, 4, operation.date_from or '', format_field)
            sheet.write(row, 5, operation.date_end or '', format_field)
            sheet.write(row, 6, operation.total_expense_sale_amount or '', format_field)
            sheet.write(row, 7, operation.total_expense_cost_amount or '', format_field)
            sheet.write(row, 8, operation.total_expense_profit_amount or '', format_field)

            # Write direction (Import, Export, or Trans Shipment)
            sheet.write(row, 9, operation.direction, format_field)
            # Write stage (Import Stage, Export Stage, or N/A for Trans Shipment)
            sheet.write(row, 10, stage_name, format_field)

            # Write Claim Created status
            claim_status = 'Created' if operation.claim_created or operation.invised_created else 'Not Created'
            sheet.write(row, 11, claim_status, format_field)

            row += 1
            serial_number += 1
