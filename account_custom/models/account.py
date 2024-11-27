from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_external_journal = fields.Boolean(string='External Journal')


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def create(self, values):
        if 'journal_id' in values:
            journal = self.env['account.journal'].browse(values['journal_id'])
            if journal.is_external_journal:
                for line_vals in values.get('invoice_line_ids', []):
                    # Update account_id for invoice line
                    line_vals[2]['account_id'] = journal.default_account_id.id
        return super(AccountMove, self).create(values)

    def write(self, values):
        if 'journal_id' in values:
            journal = self.env['account.journal'].browse(values['journal_id'])
            if journal.is_external_journal:
                for line in values.get('invoice_line_ids', []):
                    # Update account_id for invoice line
                    line[2]['account_id'] = journal.default_account_id.id
        return super(AccountMove, self).write(values)

