from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    customer_service = fields.Boolean()
    operator = fields.Boolean()

    freight_check = fields.Boolean(string='Freight')
    transport_check = fields.Boolean(string='Transportation')
    clearance_check = fields.Boolean(string="Clearance")
    transit_check = fields.Boolean(string='Transit')
    warehousing_check = fields.Boolean(string='Warehousing')

    # @api.onchange('customer_service', 'operator')
    # def customer_service_operator_visible(self):
    #     if self.customer_service == True:
    #         self.operator = False
    #         self.freight_check = False
    #         self.transport_check = False
    #         self.clearance_check = False
    #         self.transit_check = False
    #         self.warehousing_check = False
    #     elif self.operator == True:
    #         self.customer_service = False
