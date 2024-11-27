# -*- coding:utf-8 -*-

from odoo import api, fields, models, _


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.model
    def _get_default_rule_ids(self):
        res = super(HrPayrollStructure, self)._get_default_rule_ids()
        res.append((0, 0, {
                'name': 'Mission Overtime',
                'sequence': 1,
                'code': 'MISS_OVR',
                'category_id': self.env.ref('hr_missions.mission_salary_rule_categ').id,
                'condition_select': 'none',
                'amount_select': 'code',
                'is_mission_rule': True,
                'amount_python_compute': 'result = employee_mission_amount(payslip)',
            }))
        return res

    rule_ids = fields.One2many(
        'hr.salary.rule', 'struct_id',
        string='Salary Rules', default=_get_default_rule_ids)
