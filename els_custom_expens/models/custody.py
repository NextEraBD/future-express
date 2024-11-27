from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class CustodyCustody(models.Model):
    _inherit = 'custody.custody'



   #####################################################################################################################
   #...........................................CRUD METHODS.............................................................
    @api.model
    def create(self, vals):
        if 'company_id' in vals and vals['company_id'] == 1:
            cov_name = self.env['ir.sequence'].get('custody.custody.els')
            vals['name'] = cov_name or '/'
        else:
            cov_name = self.env['ir.sequence'].next_by_code('custody.custody')
            vals['name'] = cov_name or '/'

        res = super(CustodyCustody, self).create(vals)
        return res

    ####################################################################################################################


