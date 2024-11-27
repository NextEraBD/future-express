from odoo import models,fields,api
from odoo.exceptions import UserError


class CalsPurpose(models.Model):
    _name = 'call.purpose'
    _rec_name = 'name'

    name = fields.Char()


class MeetingPurpose(models.Model):
    _name = 'meeting.purpose'
    _rec_name = 'name'

    name = fields.Char()

