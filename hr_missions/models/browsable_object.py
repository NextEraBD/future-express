# -*- coding:utf-8 -*-

from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips


class Payslips(Payslips):
    """a class that will be used into the python code, mainly for usability purposes"""

    @property
    def employee_mission_amount(self):
        print("------------")
        return self.dict._get_employee_mission_amount()

    # @property
    # def paid_amount(self):
    #     return self.dict._get_employee_mission_amount()
