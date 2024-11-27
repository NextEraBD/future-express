from odoo import models, fields, api

from odoo import models, fields, api


class HrVariableAllowanceTypeRule(models.Model):
    _name = 'hr.variable.allowance.type.rule'

    sequence = fields.Integer()
    rate = fields.Float()
    name = fields.Char()
    description = fields.Char()
    amount = fields.Float()
    type_id = fields.Many2one('hr.variable.allowance.type')


class HrVariableAllowanceType(models.Model):
    _name = 'hr.variable.allowance.type'

    name = fields.Char()
    description = fields.Char()
    leave_type = fields.Selection([('leave', 'Leave'), ('permission', 'Permission')], default="leave")

    type = fields.Selection([('fixed', 'Fixed'), ('rule', 'Rule')], default="fixed")
    period = fields.Selection([('day', 'Daily'), ('month', 'Monthly')], default="day")
    rule_ids = fields.One2many('hr.variable.allowance.type.rule', 'type_id', string="Rules")