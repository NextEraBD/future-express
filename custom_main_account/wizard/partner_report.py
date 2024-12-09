# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PartnerMoveReportWizard(models.TransientModel):
    _name = 'partner.move.report.wizard'
    _description = 'Partner Move Report Wizard'

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To", )
    company_id = fields.Many2one('res.company', string="Branch", default=lambda s: s.env.company, required=True)
    customer_ids = fields.Many2many('res.partner', string="Customers")
    move_type = fields.Selection(
        [('invoice', 'Invoice'), ('bill', 'Bill')],
        string="Move Type",
        required=True,
        default='invoice'
    )
    is_claim = fields.Boolean(string="Claims")

    def action_generate_report(self):
        self.ensure_one()
        data = {
            'customer_ids': self.customer_ids.ids,
            'move_type': self.move_type,
            'company_id': self.company_id.id,
            'is_claim': self.is_claim,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return self.env.ref('custom_main_account.action_partner_move_report_xlsx').report_action(self, data=data)


class PartnerMoveReportXlsx(models.AbstractModel):
    _name = 'report.custom_main_account.partner_move_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        # Fetch company and filters from the input data
        company_id = self.env['res.company'].browse(int(data['company_id']))
        date_start = data.get('date_from')
        date_end = data.get('date_to')
        is_claim = data.get('is_claim')
        move_type = data.get('move_type')

        # Define worksheet and formats
        sheet = workbook.add_worksheet("Sales Report")
        format_header = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#C0C0C0'})
        format_field = workbook.add_format({'align': 'left'})
        format_currency = workbook.add_format({'align': 'right', 'num_format': '#,##0.00'})
        format_date = workbook.add_format({'num_format': 'yyyy-mm-dd'})

        # Set column widths
        column_headers = ['Reference', 'Date', 'Partner', 'Currency', 'Total Amount', 'Unpaid Amount', 'Paid Amount',
                          'Status']
        column_widths = [20, 15, 25, 10, 15, 15, 15, 10]
        for i, width in enumerate(column_widths):
            sheet.set_column(i, i, width)

        # Header Section
        sheet.merge_range('A1:H1', f"Sales Report for {company_id.name}", format_header)
        for col, header in enumerate(column_headers):
            sheet.write(1, col, header, format_header)

        # Fetch Invoice Data
        invoice_domain = [('company_id', '=', company_id.id)]
        if date_start:
            invoice_domain.append(('date', '>=', date_start))
        if date_end:
            invoice_domain.append(('date', '<=', date_end))
        if move_type:
            invoice_domain.append(('move_type', '=', 'out_invoice' if move_type == 'invoice' else 'in_invoice'))
            invoice_domain.append(('is_claim', '=', False))
        claim_domain = [('company_id', '=', company_id.id)]
        if date_start:
            claim_domain.append(('date', '>=', date_start))
        if date_end:
            claim_domain.append(('date', '<=', date_end))
        if move_type:
            claim_domain.append(('move_type', '=', 'out_invoice' if move_type == 'invoice' else 'in_invoice'))


        # Write Invoice Data
        row = 2
        invoices = self.env['account.move'].search(invoice_domain)
        if invoices:
            sum_total_amount = sum(invoices.mapped('amount_total'))
            sum_unpaid_amount = sum(invoices.mapped('amount_residual'))
            sum_paid_amount = sum(invoices.mapped(lambda inv: inv.amount_total - inv.amount_residual))

            for invoice in invoices:
                sheet.write(row, 0, invoice.name, format_field)
                sheet.write(row, 1, invoice.date, format_date)
                sheet.write(row, 2, invoice.partner_id.name, format_field)
                sheet.write(row, 3, invoice.currency_id.name, format_field)
                sheet.write(row, 4, invoice.amount_total, format_currency)
                sheet.write(row, 5, invoice.amount_residual, format_currency)
                sheet.write(row, 6, invoice.amount_total - invoice.amount_residual, format_currency)
                sheet.write(row, 7, invoice.payment_state, format_field)
                row += 1

            # Write totals at the end of the columns
            sheet.write(row, 3, "Total", format_header)
            sheet.write(row, 4, sum_total_amount, format_currency)
            sheet.write(row, 5, sum_unpaid_amount, format_currency)
            sheet.write(row, 6, sum_paid_amount, format_currency)
            row += 2

        # Claims Section
        if is_claim :
            claims = self.env['account.move'].search(claim_domain + [('is_claim', '=', True)])
            if claims:
                sheet.merge_range(row, 0, row, 7, "Claims", format_header)
                row += 1
                for col, header in enumerate(column_headers):
                    sheet.write(row, col, header, format_header)
                row += 1

                sum_claim_total_amount = sum(claims.mapped('amount_total'))
                sum_claim_unpaid_amount = sum(claims.mapped('amount_residual'))
                sum_claim_paid_amount = sum(claims.mapped(lambda claim: claim.amount_total - claim.amount_residual))

                for claim in claims:
                    sheet.write(row, 0, claim.name, format_field)
                    sheet.write(row, 1, claim.date, format_date)
                    sheet.write(row, 2, claim.partner_id.name, format_field)
                    sheet.write(row, 3, claim.currency_id.name, format_field)
                    sheet.write(row, 4, claim.amount_total, format_currency)
                    sheet.write(row, 5, claim.amount_residual, format_currency)
                    sheet.write(row, 6, claim.amount_total - claim.amount_residual, format_currency)
                    sheet.write(row, 7, claim.payment_state, format_field)
                    row += 1

                # Write totals for claims
                sheet.write(row, 3, "Total", format_header)
                sheet.write(row, 4, sum_claim_total_amount, format_currency)
                sheet.write(row, 5, sum_claim_unpaid_amount, format_currency)
                sheet.write(row, 6, sum_claim_paid_amount, format_currency)
