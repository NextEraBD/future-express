from odoo import fields, models, api


class DailyRouteLogWizard(models.TransientModel):
    _name = 'daily.route.log.wizard'
    _description = 'Daily Route Log Wizard'

    route_id = fields.Many2one('daily.route', string='Daily Route', required=True)
    log_date = fields.Date(string='Log Date', required=True)

    daily_log_line_ids = fields.One2many('daily.route.log.wizard.line', 'wizard_id', string='Daily Log Lines')

    @api.model
    def default_get(self, fields):
        """Prepopulate the log lines for the current day and customers."""
        res = super(DailyRouteLogWizard, self).default_get(fields)
        route_id = self.env.context.get('default_route_id')
        log_date = self.env.context.get('default_log_date')

        if route_id and log_date:
            # Find the route
            route = self.env['daily.route'].browse(route_id)
            log_lines = []

            for line in route.customer_line_ids:
                # Find existing log for the route line and log date
                existing_log = self.env['daily.route.log'].search([
                    ('route_line_id', '=', line.id),
                    ('log_date', '=', log_date)
                ], limit=1)

                if not existing_log:
                    # Create a log if it doesn't exist for this date and route line
                    existing_log = self.env['daily.route.log'].create({
                        'route_line_id': line.id,
                        'log_date': log_date,
                        'status': 'pending',
                    })

                # Add log line with log_id
                log_lines.append((0, 0, {
                    'customer_id': line.customer_id.id,
                    'status': existing_log.status,
                    'log_id': existing_log.id  # Link to the log entry
                }))

            # Update the result with the generated log lines
            res.update({
                'daily_log_line_ids': log_lines,
            })
        return res

    def action_save_logs(self):
        """Save the updated logs."""
        for line in self.daily_log_line_ids:
            log = self.env['daily.route.log'].browse(line.log_id.id)
            log.status = line.status  # Update status of each log



class DailyRouteLogWizardLine(models.TransientModel):
    _name = 'daily.route.log.wizard.line'
    _description = 'Daily Route Log Wizard Line'

    wizard_id = fields.Many2one('daily.route.log.wizard', string='Wizard', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('not_received', 'Not Received')
    ], string='Status', required=True)
    log_id = fields.Many2one('daily.route.log', string='Daily Route Log', required=False)  # The required log link
