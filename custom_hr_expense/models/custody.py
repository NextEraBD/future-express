from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class CustodyCustody(models.Model):
    _name = 'custody.custody'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']
    _order = "date desc, id desc"
    _check_company_auto = True
    _rec_name = 'name'

    @api.model
    def default_get(self, fields):
        res = super(CustodyCustody, self).default_get(fields)
        branch_id = False
        if self.env.user.branch_id:
            branch_id = self.env.user.branch_id.id
        res.update({
            'branch_id': branch_id
        })
        return res

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        return employee

    name = fields.Char(default='/')
    date = fields.Date(default=fields.Date.today(), readonly=True)
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", store=True, required=True, readonly=True, tracking=True,
                                  default=_default_employee_id,
                                  check_company=True)

    amount = fields.Float()
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('submitted', 'Submitted'),
        # ('approved', 'Management Approve'),
        # ('branch_approve', 'Branch Manager Approved'),
        # ('account_approve', 'Account Approved'),
        ('done', 'Confirmed'),
        ('refused', 'Refused')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft')
    refuse_user_id = fields.Many2one('res.users')
    refuse_reason = fields.Char()
    refuse_date = fields.Date()
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company)
    move_id = fields.Many2one('account.move',check_company=True)
    currency_id = fields.Many2one('res.currency',default=lambda self: self.env.company.currency_id)
    branch_id = fields.Many2one('res.branch', string='Branch', default=lambda self: self.env.user.branch_id, readonly=True)
    total_gl = fields.Float(compute='compute_remaining_balance')
    remaining_balance = fields.Float(compute='compute_remaining_balance')
    description = fields.Text()
    cheaf_clearance = fields.Many2one('res.users', required=False, string='Chef Clearance')
    user_domain_ids = fields.Many2many('res.users', 'res_user_chef_domain_rel',
                                          string="Allowed Checf")

    # @api.depends('branch_id')
    # def compute_chef_domain_ids(self):
    #     users_ids = []
    #     users = self.env['res.users'].search([])
    #     for user in users:
    #         users_ids += users.search(
    #             [('id', 'in', (self.branch_id.cheaf_clearance.ids
    #                            ))]).ids
    #         if users_ids:
    #             self.user_domain_ids = users_ids
    #         else:
    #             self.user_domain_ids = False
    def action_change_branch(self):
        view_id = self.env.ref('custom_hr_expense.view_create_treasury_manager_wizard').id
        name = _('Change Custody Branch')
        if self.env.user in self.branch_id.treasury_manager:
            return {
                'name': name,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'treasury.manager.wizard',
                'view_id': view_id,
                'views': [(view_id, 'form')],
                'target': 'new',
                'context': {
                    'default_custody_id': self.id,

                }
            }
        else:
            raise ValidationError(_("You are not authorised to approve this request only Branch Treasury Manager"))

    def get_employee_balance(self):
        for rec in self:
            partner = rec.employee_id.custody_manager_id.partner_id
            if partner:
                lines_opj = rec.env['account.move.line'].sudo()
                move_lines = lines_opj.search(
                    [('partner_id', '=', partner.id),
                     ('account_id', '=', rec.employee_id.employee_account_id.id),
                     ('parent_state', '=', 'posted'),
                     ]
                )
                print('mommmmmmmmmmm',move_lines)
                debit, credit = 0.0, 0.0
                for line in move_lines:
                    credit += line.credit
                    debit += line.debit
                balance = debit - credit
                return balance
            else:
                return 0

    @api.depends('amount', 'employee_id')
    def compute_remaining_balance(self):
        for rec in self:
            rec.total_gl = rec.get_employee_balance()
            rec.remaining_balance = rec.total_gl - rec.amount



    # @api.onchange('employee_id')
    # def get_branch(self):
    #     if self.employee_id:
    #         if self.employee_id.branch_id:
    #             self.update({'branch_id': self.employee_id.branch_id})
    #         else:
    #             self.update({'branch_id': False})

   #####################################################################################################################
   #...........................................CRUD METHODS.............................................................
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('custody.custody')
        res = super(CustodyCustody, self).create(vals)
        return res
    ####################################################################################################################


    #####################################################################################################################
    #..........................................ACTION METHODS...........................................................

    def action_submit(self):
        self.state = 'submitted'
        self._send_activity([self.employee_id.expense_manager_id.id])

    # def action_manager_approve(self):
    #     if self.cheaf_clearance == self.env.user:
    #         self.state = 'approved'
    #         self._activity_done()
    #         self._send_activity([self.branch_id.manager_id.id])
    #     else:
    #         raise ValidationError(_("You are not authorised to approve this request only Chef Clearance Manager"))
    def action_manager_approve(self):
        self.state = 'approved'
        self._activity_done()
        # self._send_activity([self.manager_id.id])

    # def action_branch_approve(self):
    #     if self.branch_id.manager_id == self.env.user:
    #         self.state = 'branch_approve'
    #         self._activity_done()
    #         for i in self.branch_id.account_manager_ids:
    #             self._send_activity([i.id])
    #     else:
    #         raise ValidationError(_("You are not authorised to approve this request only Branch Manager"))
    def action_branch_approve(self):
        self.state = 'branch_approve'
        self._activity_done()
        # for i in self.branch_id.account_manager_ids:
        #     self._send_activity([i.id])

    # def action_account_approve(self):
    #     if self.env.user in self.branch_id.account_manager_ids:
    #         self.state = 'account_approve'
    #         self._activity_done()
    #         for i in self.branch_id.treasury_manager:
    #             self._send_activity([i.id])
    #     else:
    #         raise ValidationError(_("You are not authorised to approve this request only Branch account manager"))
    def action_account_approve(self):
        # Assuming you don't need to check account managers
        self.state = 'account_approve'
        self._activity_done()
        # for i in self.branch_id.treasury_manager:
        #     self._send_activity([i.id])

    # def action_done(self):
    #     if self.env.user in self.branch_id.treasury_manager:
    #         return {
    #             'name': _('Custody Entry'),
    #             'view_mode': 'form',
    #             'view_id': self.env.ref('custom_hr_expense.custody_custody_wizard_view_form').id,
    #             'res_model': 'custody.custody.wizard',
    #             'context': {
    #                 'default_custody_id': self.id,
    #                 'default_branch_id': self.branch_id.id,
    #                         },
    #             'type': 'ir.actions.act_window',
    #             'target': 'new',
    #
    #         }
    #
    #     else:
    #         raise ValidationError(_("You are not authorised to approve this request only Branch Treasury Manager"))
    def action_done(self):
        return {
            'name': _('Custody Entry'),
            'view_mode': 'form',
            'view_id': self.env.ref('custom_hr_expense.custody_custody_wizard_view_form').id,
            'res_model': 'custody.custody.wizard',
            'context': {
                'default_custody_id': self.id,
                'default_branch_id': self.branch_id.id,
            },
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
    def action_refuse(self):
        self.state = 'refused'
        self.refuse_user_id = self.env.user
        self.refuse_date = fields.Date.today()
        self._activity_done()

    def _send_activity(self,user_ids):
        date_deadline = fields.Date.today()
        activ_list = []
        for user_id in user_ids:
            if user_id and user_id != 'None':
                activity_id = self.sudo().activity_schedule(
                    'mail.mail_activity_data_todo', date_deadline,
                    note=_(
                        '<a>Task </a> for <a>Approve</a>') % (
                         ),
                    user_id=user_id,
                    res_id=self.id,

                    summary=_("PLZ Approve this cover letter for the employee %s")% self.employee_id.name
                )
                activ_list.append(activity_id.id)
        [(4, 0, rec) for rec in activ_list]

    def _activity_done(self):
        activity_ids = self.env['mail.activity'].sudo().search([('res_id', '=', self.id)])
        if activity_ids:
            for act in activity_ids:
                act.action_done()

    #todo create configuration custody account and cash account

    ####################################################################################################################

