from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.employee'

    #
    suspended = fields.Boolean(string='Suspended')