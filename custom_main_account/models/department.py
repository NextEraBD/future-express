from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class Department(models.Model):
    _inherit = 'hr.department'

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
