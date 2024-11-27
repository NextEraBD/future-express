from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _sql_constraints = [
        ('vat_uniq', 'unique (vat)', 'This Tax ID already exists!'),
    ]

    ar_name = fields.Char(string='Arabic Name')
    shipper = fields.Boolean('Shipper')
    consignee = fields.Boolean('Consignee')
    agent = fields.Boolean('Agent')

    is_shipping_line = fields.Boolean(string="Is Shipping Line", default=False)
    is_tracking_agent = fields.Boolean(string="Is Trucking Agent", default=False)
    is_driver = fields.Boolean(string="Is Trucking Agent", default=False)
    tracking_agent_serial = fields.Char(string="Truck Agent Serial")
    serial_seq = fields.Integer(string="Sequence")
    customer_service_id = fields.Many2one('res.users', string='Customer Service',
                                          domain="[('customer_service','=',True)]")

    freight_count = fields.Integer(compute='_compute_freight_count')

    @api.depends()
    def _compute_freight_count(self):
        for count in self:
            freight = self.env['freight.operation'].search_count([('customer_id', '=', self.id)])
            count.freight_count = freight

    def action_open_freight(self):
        """ Return the list of freight shipment. """
        self.ensure_one()
        freight_ids = self.env['freight.operation'].search([('customer_id', '=', self.id)])
        print("'''''''''", freight_ids)
        action = {
            'name': _('Freight Shipment'),
            'view_type': 'tree',
            'view_mode': 'list,form',
            'res_model': 'freight.operation',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'domain': [('customer_id', 'in', self.ids)],
        }
        return action






