from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_local = fields.Boolean(string='Local')
    is_international = fields.Boolean(string='International')
    # local_price_list_id = fields.Many2one(
    #     'custom.price.list',
    #     string='Local Price List',
    #     domain=[('price_list_type', '=', 'local')]
    # )
    # international_price_list_id = fields.Many2one(
    #     'custom.price.list',
    #     string='International Price List',
    #     domain=[('price_list_type', '=', 'international')]
    # )

    local_price_list_id = fields.Many2many(
        'custom.price.list', 'local_price_list_id_rel',
        string='Local Price Lists',
        domain=[('price_list_type', '=', 'local')]
    )

    international_price_list_id = fields.Many2many(
        'custom.price.list', 'international_price_list_id_rel',
        string='International Price Lists',
        domain=[('price_list_type', '=', 'international')]
    )

    # # New fields for local and international currency
    local_currency_id = fields.Many2one(
        'product.pricelist',
        string='Local Currency',
        help='Select the local currency for this partner.'
    )

    international_currency_id = fields.Many2one(
        'product.pricelist',
        string='International Currency',
        help='Select the international currency for this partner.'
    )