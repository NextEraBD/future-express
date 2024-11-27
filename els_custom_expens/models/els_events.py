import json

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class Event(models.Model):
    _inherit = 'els.events'


    console_id_domain = fields.Char(compute="_compute_console_id_domain", readonly=True, store=False)
    console_id = fields.Many2one('console.operation', check_company=True)
    is_console = fields.Boolean()


    @api.depends('company_id', 'user_id')
    def _compute_console_id_domain(self):
        for rec in self:
            if rec.user_id.employee_id:
                rec.console_id_domain = json.dumps(
                    [('company_id', '=', rec.company_id.id), ('employee_ids', 'in', [rec.user_id.employee_id.id])]
                )

