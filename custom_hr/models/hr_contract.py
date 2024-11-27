from odoo import models, fields, api

class HrContract(models.Model):
    _inherit = 'hr.contract'

    insurance_salary = fields.Float(string="Insurance Salary")
    company_insurance_percentage = fields.Float(string="Company's Percentage of Insurance", compute='_compute_insurance_percentages', store=True)
    employee_insurance_percentage = fields.Float(string="Employee's Percentage of Insurance", compute='_compute_insurance_percentages', store=True)
    health_insurance = fields.Float(string="Health Insurance")
    martyrs_fund = fields.Float(string="Martyrs Fund")
    mobile_deduction = fields.Float(string="Mobile Deduction")

    @api.depends('insurance_salary')
    def _compute_insurance_percentages(self):
        for contract in self:
            contract.company_insurance_percentage = contract.insurance_salary * 0.1875 if contract.insurance_salary else 0.0
            contract.employee_insurance_percentage = contract.insurance_salary * 0.1125 if contract.insurance_salary else 0.0

