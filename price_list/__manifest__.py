# -*- coding: utf-8 -*-
{
    'name': 'Price List',
    'version': '1.0',
    'summary': 'Manage Price List',
    'author': 'Banan',
    'depends': ['base', 'mail','crm'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/import_price_list_line_view.xml',
        'views/custom_price_list_views.xml',
        'views/res_partner.xml',

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
