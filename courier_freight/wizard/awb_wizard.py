from odoo import models, fields, api


class AWBSearchWizard(models.TransientModel):
    _name = 'awb.search.wizard'
    _description = 'AWB Search Wizard'

    awb_numbers = fields.Text(string="AWB Numbers", help="Enter AWB numbers separated by commas or spaces.")
    found_awbs = fields.Text(readonly=True)
    missing_awbs = fields.Text(readonly=True)
    found_rec_ids = fields.Many2many('sale.order', string="Found Sale Orders")
    search = fields.Boolean(string="Search", default=False)

    @api.onchange('search')
    def search_awbs(self):
        if self.search and self.awb_numbers:
            input_awbs = set(awb.strip() for awb in self.awb_numbers.split('\n'))
            self.found_rec_ids = self.env['sale.order'].search([('account_number_wb', 'in', list(input_awbs))])
            found_awbs = {rec.account_number_wb for rec in self.found_rec_ids}
            missing_awbs = input_awbs - found_awbs
            self.found_awbs = ', '.join(found_awbs)
            self.missing_awbs = ', '.join(missing_awbs)

    def open_sale_order(self):
        domain = [('id', 'in', self.found_rec_ids.ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Orders with AWBs',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': domain,
            'target': 'current',
        }
