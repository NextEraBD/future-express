from odoo import fields, models, api


class operation_task_wizard(models.TransientModel):
    _name = 'operation.task.wizard'
    _description = "Operation Task Wizard"

    def get_name(self):
        ctx = dict(self._context or {})
        active_id = ctx.get('active_id')
        operation_brw = self.env['freight.operation'].browse(active_id)
        name = operation_brw.name
        return name

    dead_line = fields.Date('Deadline')
    date_assign = fields.Date(string='Assigning Date', default=fields.Date.context_today)
    description = fields.Html()
    name = fields.Char('Task Name', default=get_name)
    user_ids = fields.Many2many('res.users', relation='operation_task_assignee_rel', string='Assignees',index=True)
    create_id = fields.Many2one(
        'res.users', string='Task Creator', default=lambda self: self.env.user,)
    branch_id = fields.Many2one('res.branch', string='Branch', ondelete='set null',
                                default=lambda self: self._get_default_branch())
    @api.model
    def _get_default_branch(self):
        # Access the current user's record
        user = self.env.user

        # Fetch the branch associated with the current user
        branch = user.branch_id

        return branch

    def create_task(self):
        ctx = dict(self._context or {})
        active_id = ctx.get('active_id')
        operation_brw = self.env['freight.operation'].browse(active_id)
        user = []
        for users in self.user_ids:
            user.append(users.id)
        vals = {'name': self.name,
                # 'date_assigned': self.date_assign,
                'description': self.description,
                'user_ids': user or False,
                'date_deadline': self.dead_line or False,
                'partner_id': operation_brw.customer_id.id or False,
                'operation_id': operation_brw.id or False,
                'create_id': self.create_id.id or False
                }

        task=self.env['project.task'].create(vals)
        self.env['mail.activity'].create({
            'summary': 'Operation Task Activity',
            'activity_type_id': task.env.ref('mail.mail_activity_data_email').id,
            'res_model_id': task.env['ir.model']._get(task._name).id,
            'res_id': task.id,
            'user_id': users.id
        })





class project_Task(models.Model):
    _inherit = 'project.task'

    operation_id = fields.Many2one('freight.operation', 'Operation')
    create_id = fields.Many2one(
        'res.users', string='Task Creator', default=lambda self: self.env.user, )
    branch_id = fields.Many2one('res.branch', string='Branch', ondelete='set null')
