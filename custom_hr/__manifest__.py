# -*- coding: utf-8 -*-
{
    'name': 'Custom HR Contract',

    'summary': """
        Custom HR Contract""",

    'description': """
        Custom HR Contract
    """,

    'author': "Banan Babiker",
    'website': "http://www.nextrabd.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_contract',],

    # always loaded
    'data': [
        'data/salary_rule_insurance_custom.xml',
        'views/hr_contract_view_inherit.xml',
        ],
    'installable': True,
    'application': False,
}


