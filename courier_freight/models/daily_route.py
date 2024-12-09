from odoo import fields, models, api
from datetime import date


class DailyRoute(models.Model):
    _name = 'daily.route'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add this line
    _description = 'Daily Route'

    name = fields.Char(string='Route Name', required=False, copy=False, readonly=True, index=True, default=lambda self: self.env['ir.sequence'].next_by_code('daily.route.serial') or 'New')
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    customer_line_ids = fields.One2many('daily.route.line', 'route_id', string='Customers')
    description = fields.Text(string='Description')
    representative_id = fields.Many2one('res.users', string='Representative', required=True)
    log_ids = fields.One2many('daily.route.log', 'route_id', string='Logs')
    grouped_log_ids = fields.One2many('daily.route.log.group', 'route_id', string='Grouped Logs')

    @api.depends('log_ids')
    def _compute_grouped_logs(self):
        for route in self:
            grouped_logs = {}
            for log in route.log_ids:
                if log.log_date not in grouped_logs:
                    grouped_logs[log.log_date] = []
                grouped_logs[log.log_date].append(log)

            # Create or update the grouped log entries
            route.grouped_log_ids = [(0, 0, {
                'log_date': log_date,
                'log_ids': [(6, 0, logs.ids)]
            }) for log_date, logs in grouped_logs.items()]
            # Create new groups
            for log_date, logs in grouped_logs.items():
                self.env['daily.route.log.group'].create({
                    'route_id': route.id,
                    'log_date': log_date,
                    'log_ids': [(6, 0, [log.id for log in logs])]
                })

    # Add this computed field for today's logs
    today_log_ids = fields.One2many('daily.route.log', 'route_id', string="Today's Logs", compute='_compute_today_logs')

    @api.depends('log_ids')
    def _compute_today_logs(self):
        today = date.today()  # Get today's date
        for route in self:
            route.today_log_ids = route.log_ids.filtered(lambda log: log.log_date == today)

    def button_send(self):
        today = date.today()  # Get today's date
        for route in self:
            if route.representative_id:
                # Create an activity for the representative
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'daily.route')], limit=1).id,
                    'res_id': route.id,  # Related to the DailyRoute record
                    'user_id': route.representative_id.id,  # Assign the activity to the representative
                    'summary': f'Activity for Route {route.name}',
                    'note': route.description or 'No description provided.',
                    'date_deadline': today,  # Set the deadline to today's date
                })
    def button_open_daily_log_wizard(self):
        """Open the wizard to log daily receipts."""
        today = date.today()
        return {
            'name': 'Daily Log Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'daily.route.log.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_route_id': self.id,
                'default_log_date': today,
            }
        }


class DailyRouteCustomerLine(models.Model):
    _name = 'daily.route.line'
    _description = 'Daily Route Customer Line'

    route_id = fields.Many2one('daily.route', string='Daily Route', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    description = fields.Text(string='Description')
    daily_log_ids = fields.One2many('daily.route.log', 'route_line_id', string='Daily Logs')

class DailyRouteLog(models.Model):
    _name = 'daily.route.log'
    _description = 'Daily Route Log'

    route_id = fields.Many2one('daily.route', string='Daily Route', required=True)  # Relate the log to the route
    route_line_id = fields.Many2one('daily.route.line', string='Route Line', required=True)  # Existing relation to the route line
    customer_id = fields.Many2one('res.partner', string='Customer', related='route_line_id.customer_id', store=True, readonly=True)
    log_date = fields.Date(string='Date', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('not_received', 'Not Received')
    ], string='Status', default='pending', required=True)
    log_date_id = fields.Many2one('daily.route.log.group', string='Log Group', required=False)

    @api.model
    def create(self, vals):
        res = super(DailyRouteLog, self).create(vals)
        print("Created log: %s", res)
        return res

    def write(self, vals):
        res = super(DailyRouteLog, self).write(vals)
        print("Updated log: %s", vals)
        return res

    @api.model
    def create(self, vals):
        res = super(DailyRouteLog, self).create(vals)
        # Add logging or print statements to check if this is hit
        print(f"Created log: {res.id} for route: {res.route_id.name}")
        return res
class DailyRouteLogGroup(models.Model):
    _name = 'daily.route.log.group'
    _description = 'Grouped Daily Route Logs'

    route_id = fields.Many2one('daily.route', string='Daily Route', required=True)
    log_date = fields.Date(string='Log Date', required=True)
    log_ids = fields.One2many('daily.route.log', 'log_date_id', string='Logs')