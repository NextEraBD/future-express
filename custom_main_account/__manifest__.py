# -*- coding: utf-8 -*-
{
    'name': "Custom Main Account",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Nexterad",
    'developer': "DeeB",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base_companies', 'hr', 'sale', 'purchase', 'account', 'branch', 'account_accountant',
                'product_analytic_account','account_asset'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        'data/data.xml',
        'views/account_account_views.xml',
        'views/product_categ_views.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/menue_xml.xml',
        'views/branch.xml',
        'views/partner.xml',
        'wizard/partner_report.xml',
        'views/debit_credit_memo.xml',
        'views/distribution_set.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
