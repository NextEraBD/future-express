from odoo import api, fields, models


class Container(models.Model):
    _name = 'freight.container'
    _description = 'Freight Container'

    name = fields.Char()
    standard_volume = fields.Float('Maximum Volume')
    standard_weight = fields.Float('Maximum Weight')
    volume_type = fields.Selection(([('m2', 'M2'), ('m3', 'M3')]), string='Weight Type')
    weight_type = fields.Selection(([('kg', 'KG'), ('ton', 'Ton')]), string='Weight Type')
    container_no_ids = fields.One2many('freight.container.no', 'container_id')
    teu = fields.Float('TEU')

class ContainerNo(models.Model):
    _name = 'freight.container.no'
    _description = 'Freight Container No'

    name = fields.Char()
    container_id = fields.Many2one('freight.container', 'Container Type')
    operation_id = fields.Many2one('freight.operation')
    state = fields.Selection([('available','Available'),('used','Used')],default='available')


class TotalContainer(models.Model):
    _name = 'total.container'
    _rec_name = 'container_id'
    operation_id = fields.Many2one('freight.operation')
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_count = fields.Integer('Count')


class CrmTotalContainer(models.Model):
    _name = 'crm.total.container'
    _rec_name = 'container_id'
    lead_id = fields.Many2one('crm.lead')
    container_id = fields.Many2one('freight.container', 'Container Type')
    container_count = fields.Integer('Count')