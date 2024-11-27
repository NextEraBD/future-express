# -*- coding: utf-8 -*-
{
    'name': "ELS Custom HR Expense",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mohamed Eldeeb",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HR',
    'version': '16.1',

    # any module necessary for this one to work correctly
    'depends': ['custom_hr_expense'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/coverage_letter.xml',
        'views/account_move.xml',
        # 'views/console_operation.xml',
        'views/els_event.xml',

        'data/sequence.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
