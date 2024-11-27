from odoo import api, fields, models


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    freight_operation_id = fields.Many2one('freight.operation', string='Freight operation')
    console_id = fields.Many2one('console.operation', 'Console Operation')
