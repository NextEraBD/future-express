from odoo import api, fields, models


class FreightPort(models.Model):
    _name = 'freight.port'
    _description = 'Freight Port'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    country = fields.Many2one('res.country', 'Country')
    state = fields.Many2one('res.country.state', 'Fed. State', domain="[('country_id', '=', country)]")
    air = fields.Boolean(string='Air')
    ocean = fields.Boolean(string='Ocean')
    land = fields.Boolean(string='Land')
    active = fields.Boolean(default=True, string='Active')

    def name_get(self):
        # print("Hello context")
        if self._context.get('port_by_code_ref'):
            # print("Entered if context")
            res = []
            for port in self:
                name = port.name
                if port.code:
                    name = '%s' % port.code
                res.append((port.id, name))
            return res
        return super(FreightPort, self).name_get()

