from odoo import models,fields,api
from odoo.exceptions import UserError


class CalsResult(models.Model):
    _name = 'call.result'
    _rec_name = 'name'

    name = fields.Char()


class MeetingResult(models.Model):
    _name = 'meeting.result'
    _rec_name = 'name'

    name = fields.Char()
