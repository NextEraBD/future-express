from odoo import models,fields,api
from odoo.exceptions import UserError


class Cals(models.Model):
    _name = 'call.call'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'call_subject'

    #premitive fields
    call_type = fields.Selection([('outgoing','Outgoing'),('ingoing','Ingoing'),('missed','Missed')])
    date_from = fields.Datetime()
    duration = fields.Float()
    call_subject = fields.Char(required=1)
    description = fields.Text()
    state = fields.Selection([('scheduled', 'Scheduled'), ('finished', 'Finished')], required=1)
    phone = fields.Char()
    origin = fields.Char()


    #relational fields
    lead_id = fields.Many2one('crm.lead')
    employee_id = fields.Many2one('hr.employee', default=lambda self: self.lead_id.user_id.employee_id)
    contact_id = fields.Many2one('res.partner', domain="[('is_company','=',False)]")
    contact_name = fields.Char('Contact')
    account_id = fields.Many2one('res.partner', domain="[('is_company','=',True)]")
    call_purpose = fields.Many2one('call.purpose')
    call_result = fields.Many2one('call.result')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def convert_to_finished(self):
        self.state = 'finished'




