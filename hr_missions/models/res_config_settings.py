from odoo import fields, models, api


class ResBranch(models.Model):
    _inherit = 'res.branch'
    _description = 'Branch'

    account_mission_ids = fields.Many2many('res.users', string='Mission Account Managers')
    administrative_affairs_ids = fields.Many2many('res.users','administrative_branch_rel', string='Administrative affairs Managers')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    config_mission_rate_overtime = fields.Float(string='Mission Overtime Rate', related='company_id.config_mission_rate_overtime', readonly=False)
    config_mission_rate_weekend = fields.Float(string='Mission Weekend Rate',
                                                related='company_id.config_mission_rate_weekend', readonly=False)
    mission_journal_id = fields.Many2one(related='company_id.mission_journal_id', readonly=False)


class ResCompany(models.Model):
    _inherit = 'res.company'

    config_mission_rate_overtime = fields.Float(string='Mission Overtime Rate')
    config_mission_rate_weekend = fields.Float(string='Mission Weekend Rate')
    mission_journal_id = fields.Many2one(comodel_name='account.journal', readonly=False)


class HRContract(models.Model):
    _inherit = 'hr.contract'

    config_mission_rate_overtime = fields.Float(string='Mission Overtime Rate')
    config_mission_rate_weekend = fields.Float(string='Mission Weekend Rate')
    mission_per_day_amount = fields.Float(compute='_onchange_emp_job_ids',store=True)
    mission_travel_allowance = fields.Float()
    mission_per_multi_day_amount = fields.Float()
    mission_with_accommodation_amount = fields.Float(compute='_onchange_emp_job_ids',store=True)

    @api.depends("employee_id")
    def _onchange_emp_job_ids(self):
        # print('BBBBBBBBBBBBBBBBBBBBBB',)
        for rec in self:
            rec.mission_per_day_amount = 0.0
            rec.mission_with_accommodation_amount = 0.0
            rec.mission_travel_allowance = 0.0
            if rec.employee_id.job_id:
                rec.mission_per_day_amount = rec.employee_id.job_id.mission_per_day_amount
                rec.mission_with_accommodation_amount = rec.employee_id.job_id.mission_with_accommodation_amount
                rec.mission_travel_allowance = rec.employee_id.job_id.mission_travel_allowance


class HRJob(models.Model):
    _inherit = 'hr.job'

    mission_per_day_amount = fields.Float()
    mission_with_accommodation_amount = fields.Float()
    mission_travel_allowance = fields.Float()


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    mission_manager_id = fields.Many2one(
        'hr.employee', string='Mission Manager')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_mission = fields.Boolean()
    can_be_mission = fields.Boolean()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_mission = fields.Boolean()
    can_be_mission = fields.Boolean()


class AccountMove(models.Model):
    _inherit = 'account.move'

    mission_id = fields.Many2one('hr.missions')

