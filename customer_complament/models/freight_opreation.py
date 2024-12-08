from odoo import fields, models, api


class FreightOperation(models.Model):
    _inherit = 'freight.operation'

    customer_compliment_ids = fields.One2many('customer.compliment', 'number_of_operations',
                                              string='Customer Compliments')
    compliment_count = fields.Integer('Compliment Count', compute='_compute_compliment_count')

    @api.depends('customer_compliment_ids')
    def _compute_compliment_count(self):
        for operation in self:
            operation.compliment_count = len(operation.customer_compliment_ids)

    def action_view_compliments(self):
        action = self.env.ref('customer_complament.action_complaint').read()[0]
        action['domain'] = [('number_of_operations', '=', self.id)]
        return action