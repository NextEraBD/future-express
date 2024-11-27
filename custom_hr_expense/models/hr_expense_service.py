from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class HrExpenseService(models.Model):
    _name = 'hr.expense.service'

    name = fields.Char()

