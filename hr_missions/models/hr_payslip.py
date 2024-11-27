# -*- coding:utf-8 -*-
from odoo import api, fields, models, _


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_mission_rule = fields.Boolean(default=False, readonly=True, copy=False)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'employee_mission_amount': employee_mission_amount,
        })
        return res

    # def _get_payslip_lines(self):
    #     result = super(HrPayslip, self)._get_payslip_lines()
    #     for line in result:
    #         description = ''
    #         used_type_ids = []
    #         salary_rule = self.env['hr.salary.rule'].browse(line['salary_rule_id'])
    #         if salary_rule.is_mission_rule:
    #             for bonus_line in self.env['hr.missions'].search([
    #                     '|',
    #                     ('employee_id', '=', self.employee_id.id),
    #                     '&',
    #                     ('state', '=', 'confirmed'),
    #                     ('date_from', '<=', self.date_to),
    #                     ('date_from', '>=', self.date_from)
    #                 ]):
    #                 if bonus_line.comments and bonus_line.comments not in used_type_ids:
    #                     description += description == '' and bonus_line.comments or (', ' + bonus_line.comments)
    #                     used_type_ids.append(bonus_line.comments)
    #             line['description'] = description
    #         print("949999999", salary_rule, description)
    #     return result

    def _get_employee_mission_amount(self):
        employee_bonus = self.env['hr.missions'].search([
                        '|',
                        ('employee_id', '=', self.employee_id.id),
                        '&',
                        ('state', '=', 'confirmed'),
                        ('date_from', '<=', self.date_to),
                        ('date_from', '>=', self.date_from)
                    ])
        return sum(b.amount for b in employee_bonus)


def employee_mission_amount(payslip):
    return payslip.dict._get_employee_mission_amount()