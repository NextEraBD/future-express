from odoo import models, fields, api,_
from odoo.exceptions import ValidationError



class ResPartnerIn(models.Model):
    _inherit = 'res.partner'

    tax_exempt = fields.Boolean()
    approved_tax_exempt = fields.Boolean()
    code = fields.Char(string="Partner Code")
    tax_type = fields.Selection([
        ('business', 'Business'),
        ('individual', 'Individual'),
        ('foreign', 'Foreign')
    ], string='Tax Type')

    @api.model
    def create(self, vals):
        if not vals.get('code', False):
            vals['code'] = self.env['ir.sequence'].get('res.partner.seq') or ''
        res = super(ResPartnerIn, self).create(vals)
        return res

    @api.constrains('vat')
    def _check_vat_uniqueness(self):
        for partner in self:
            if partner.tax_type in ['business', 'individual']:
                if partner.vat:
                    partners = self.env['res.partner'].search(
                        [('vat', '=', partner.vat), ('tax_type', 'in', ['business', 'individual']),
                         ('id', '!=', partner.id)])
                    if partners:
                        raise ValidationError("VAT number must be unique for Business or Individual tax types.")

    def action_taxing_approve(self):
        self.approved_tax_exempt = True
