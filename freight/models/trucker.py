from odoo import api, fields, models


class FreightTrucker(models.Model):
    _name = 'freight.trucker'

    name = fields.Char(string='Name')



class FreightMaster(models.Model):
    _name = 'freight.master'
    _rec_name = 'name'

    name = fields.Char(string='Name')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'A MBL already exists with this value !'),
    ]