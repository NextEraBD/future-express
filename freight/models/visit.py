from odoo import api, fields, models
import requests


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    @api.model
    def _get_current_user_partner(self):
        return self.in_user_id.partner_id.id

    e_type = fields.Selection([('event', 'Event'), ('visit', 'Visit'),('meeting', 'Meeting')])
    in_longitude = fields.Float()
    in_latitude = fields.Float()

    out_longitude = fields.Float()
    out_latitude = fields.Float()
    # relational fields
    meeting_purpose = fields.Many2one('meeting.purpose',string='Purpose')
    meeting_result = fields.Many2one('meeting.result', string='Result')
    in_user_id = fields.Many2one('res.users',string='Check IN User')
    out_user_id = fields.Many2one('res.users',string='Check OUT User')
    date_out = fields.Datetime(string="Check Out Date")
    date_in = fields.Datetime(string="Check IN Date")
    sa_name = fields.Many2one('res.partner', string="User Partner Name", default=_get_current_user_partner)

    def get_location(self):
        # Make a request to the Geolocation API to get the current location
        response = requests.get('https://ipinfo.io/json')
        data = response.json()

        # Extract the latitude and longitude from the response
        lat, lon = data['loc'].split(',')

        return float(lat), float(lon)

    def action_checkin(self):
        self.date_in = fields.Datetime.now()
        self.in_user_id = self.env.user
        self.in_latitude,self.in_longitude = self.get_location()

    def action_checkout(self):
        self.date_out = fields.Datetime.now()
        self.out_user_id = self.env.user
        self.out_latitude,self.out_longitude = self.get_location()
