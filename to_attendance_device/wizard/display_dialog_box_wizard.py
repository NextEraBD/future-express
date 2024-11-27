from odoo import models, fields, api

class DialogBox(models.TransientModel):
    _name = 'display.dialog.box'
    _description = 'Show information in a message box'

    text = fields.Text(string='Write your custom message here to show in dialog box', required=True)
