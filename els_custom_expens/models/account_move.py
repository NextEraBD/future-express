import json

from odoo import models,fields,api,_

class AccountMove(models.Model):
    _inherit = 'account.move'



    console_id = fields.Many2one('console.operation')

