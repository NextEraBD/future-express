from odoo import models, fields, api, _


class ResBranch(models.Model):
    _inherit = 'res.branch'
    _description = 'Branch'

    account_manager_ids = fields.Many2many('res.users','rel_els_account_branch_manager', string='Account Managers')
    cheaf_clearance = fields.Many2many('res.users','rel_clearance_branch_manager', string='Chef Clearance')
    it_manager = fields.Many2many('res.users','rel_it_branch_manager', string='IT Branch Managers')
    treasury_manager = fields.Many2many('res.users','rel_tiger_branch_manager', string='Treasury Managers')
    hr_person_id = fields.Many2one('hr.employee')
    recruiter_id = fields.Many2one('hr.employee')
    lawyer_manager_id = fields.Many2one('res.users', string='Lawyer Manager')
