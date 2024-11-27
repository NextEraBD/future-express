import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AttendanceWizard(models.TransientModel):
    _name = 'attendance.wizard'
    _description = 'Attendance Wizard'

    @api.model
    def _default_get_all_device_ids(self):
        all_devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
        if all_devices:
            return all_devices.ids
        else:
            return []

    device_ids = fields.Many2many('attendance.device', string='Devices', default=_default_get_all_device_ids, domain=[('state', '=', 'confirmed')])

    def action_download_attendance(self):
        if not self.device_ids:
            raise UserError(_('You must confirm at least one device to continue!'))
        self.device_ids.action_attendance_download()

    def cron_download_device_attendance(self):
        devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
        devices.action_attendance_download()

    def cron_sync_attendance(self):
        self.env['user.attendance']._cron_synch_hr_attendance()

    def sync_attendance(self):
        # TODO: rename me into `action_sync_attendance` in master/14+
        """
        This method will synchronize all downloaded attendance data with Odoo attendance data.
        It do not download attendance data from the devices.
        """
        self.env['user.attendance']._cron_synch_hr_attendance()

    def clear_attendance(self):
        # TODO: rename me into `action_clear_attendance` in master/14+
        if not self.device_ids:
            raise UserError(_('You must confirm at least one device to continue!'))
        if not self.env.user.has_group('hr_attendance.group_hr_attendance_manager'):
            raise UserError(_('Only HR Attendance Managers can manually clear device attendance data'))
        
        message = ''
        for device in self.device_ids:
            if device.clearAttendance():
                message += '%s; ' % device.display_name
        message += ''
        if message != '':
            return self.device_ids.message_box_show(_('Clear attendance data in these devices: %s successfully!') % message)
