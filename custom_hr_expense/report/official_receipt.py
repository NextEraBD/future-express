from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError

class OfficialReceiptReport(models.AbstractModel):
    _name = 'report.custom_hr_expense.report_operation_official_templates'
    _description = 'Official Receipt'

    @api.model
    def _get_report_values(self, docids, data=None):
        # if not data.get('id') or not self.env.context.get('active_model') or not self.env.context.get('active_ids'):
        #     raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids'))
        return {
            'doc_ids': docs.ids,
            'doc_model': model,
            'data': data,
            'docs': docs
        }