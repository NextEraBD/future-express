from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class HrExpense(models.Model):
    _name = 'hr.expense.type'

    name = fields.Char()