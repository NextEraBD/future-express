from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    cover_letter_manager_id = fields.Many2one('res.users',string='Accounting Cover Letter')
    custody_manager_id = fields.Many2one('res.users',string='Accounting Custody Manager')
    journal_id = fields.Many2one('account.journal')
    custody_journal_id = fields.Many2one('account.journal')
    employee_account_id = fields.Many2one('account.account')

