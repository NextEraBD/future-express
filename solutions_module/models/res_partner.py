from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    @api.model
    def create(self, vals):
        # Check if the company is being created or updated
        if vals.get('is_company', False):
            # Check if a VAT number is provided for the company
            if 'vat' in vals and vals['vat']:
                # Ensure no duplicate VAT number for companies
                existing_company = self.search([('vat', '=', vals['vat']), ('is_company', '=', True)], limit=1)
                if existing_company:
                    raise UserError('This VAT number is already assigned to another company.')

        # Proceed with normal record creation
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        # If the VAT number is being updated and the partner is a company
        if vals.get('vat') and self.is_company:
            existing_company = self.search([('vat', '=', vals['vat']), ('is_company', '=', True)], limit=1)
            if existing_company:
                raise UserError('This VAT number is already assigned to another company.')

        # Proceed with normal record update
        return super(ResPartner, self).write(vals)



