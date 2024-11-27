# -*- coding: utf-8 -*-
{
    'name': "Freight Expense",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Amna Yousif",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_expense','freight',],

    # always loaded
    'data': [
        'data/journal_data.xml',
        'security/groups.xml',
        # 'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/expense.xml',
        'views/product_product.xml',
        'views/account_move.xml',
        # 'views/hr_employee.xml',
        'views/freight_operation.xml',
        'views/register_payment_views.xml',
        'views/console_operation.xml',
        # 'views/menue_xml.xml',
        'views/distribute.xml',
        'views/purchase_views.xml',
        'views/sale_order.xml',
        'wizard/expense_invoice_wizard.xml',
        'wizard/quotation_wizard.xml',
        'wizard/offical_invoice_wizard.xml',
        # 'data/data.xml',
        'data/sequence.xml',
        # 'report/expense_report.xml',
        # 'report/official_receipt_report.xml',
        # 'report/custody_receipt.xml',
        # 'report/cover_letter.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
