import json

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class Event(models.Model):
    _name = 'els.events'
    # _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']
    _description = "Events"
    _order = "date desc, id desc"
    _check_company_auto = True

    @api.model
    def _default_user_id(self):
        user = self.env.user
        return user

    name = fields.Char()
    date = fields.Date(default=fields.Date.today())
    user_id = fields.Many2one('res.users',string="User",default=lambda self:self.env.user,check_company=True)

    company_id = fields.Many2one('res.company',default=lambda self:self.env.company)
    state = fields.Selection([('draft', 'Draft'),('submit', 'Submitted'),('close', 'Closed')],
                             string='Status', copy=False, readonly=True, store=True, default='draft',tracking=True)

    freight_id_domain = fields.Char(compute="_compute_freight_id_domain", readonly=True, store=False)
    # console_id_domain = fields.Char(compute="_compute_console_id_domain", readonly=True, store=False)

    branch_id = fields.Many2one('res.branch', string='Branch')
    freight_operation_id = fields.Many2one('freight.operation')
    state_id = fields.Many2one('els.event.state')
    comment = fields.Char()
    operator_service = fields.Selection([('freight', 'Freight'), ('clearance', 'Clearance'), ('transportation', 'Transportation')
                                            , ('transit', 'Transit'), ('warehousing', 'Warehousing')], string='Service')
    operator_service_domain = fields.Char(compute='compute_operator_service_domain',readonly=True,store=False,)
    is_console = fields.Boolean()
    @api.model
    def default_get(self, flds):
        """ Override to get default branch from user """
        result = super(Event, self).default_get(flds)

        user_id = self.env.user
        if user_id:
            if user_id.branch_id:
                result['branch_id'] = user_id.branch_id.id
        return result

    @api.depends('user_id','company_id')
    def _compute_freight_id_domain(self):
        for rec in self:
            if rec.user_id.employee_id:
                rec.freight_id_domain = json.dumps(
                    [('company_id', '=', rec.company_id.id), ('employee_ids', 'in', [rec.user_id.employee_id.id])]
                )
            else:
                rec.freight_id_domain = json.dumps([])



    @api.onchange('user_id')
    def onchange_user_id(self):
        if self.user_id.operator:
            if self.user_id.freight_check:
                self.operator_service = 'freight'
            elif self.user_id.transport_check:
                self.operator_service = 'transportation'
            elif self.user_id.clearance_check:
                self.operator_service = 'clearance'
            elif self.user_id.transit_check:
                self.operator_service = 'transit'
            elif self.user_id.warehousing_check:
                self.operator_service = 'warehousing'
    def action_submit(self):
        self.state = 'submit'
        if self.freight_operation_id:
            if self.operator_service == 'freight':
                self.freight_operation_id.freight_check = True
                self.freight_operation_id.freight_event_state = self.state_id
                self.freight_operation_id.freight_event_date = self.date
                self.freight_operation_id.send_activity_customer_service()
            elif self.operator_service == 'transportation':
                self.freight_operation_id.transport_check = True
                self.freight_operation_id.transport_event_state = self.state_id
                self.freight_operation_id.transport_event_date = self.date
                self.freight_operation_id.send_activity_customer_service()
            elif self.operator_service == 'clearance':
                self.freight_operation_id.clearance_check = True
                if self.state_id.id == self.env.ref('custom_hr_expense.els_event_state_receive').id:
                    done_state = self.env.ref('custom_hr_expense.els_event_state_done').id
                    event = self.create({'state_id': done_state,'freight_operation_id':self.freight_operation_id.id,
                                 'operator_service':'clearance'})

                    event.freight_operation_id.clearance_event_state = event.state_id
                    event.freight_operation_id.clearance_event_date = event.date
                    event.state = 'submit'
                else:
                    self.freight_operation_id.clearance_event_state = self.state_id
                    self.freight_operation_id.clearance_event_date = self.date
                self.freight_operation_id.send_activity_customer_service()


            elif self.operator_service == 'transit':
                self.freight_operation_id.transit_check = True
                self.freight_operation_id.transit_event_state = self.state_id
                self.freight_operation_id.transit_event_date = self.date
                self.freight_operation_id.send_activity_customer_service()
            elif self.operator_service == 'warehousing':
                self.freight_operation_id.warehousing_check = True
                self.freight_operation_id.warehousing_event_state = self.state_id
                self.freight_operation_id.warehousing_event_date = self.date
                self.freight_operation_id.send_activity_customer_service()
            else:
                raise ValidationError('You must select service before submit')


    def action_close(self):
        self.state = 'close'

    @api.depends('operator_service')
    def compute_operator_service_domain(self):
        for rec in self:
            rec.operator_service_domain = json.dumps(
                [('operator_service','=',rec.operator_service)]
            )
