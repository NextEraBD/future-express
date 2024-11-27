# -*- coding: utf-8 -*-
{
    'name': "Custom HR Expense",
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
    'category': 'Uncategorized',
    'version': '16.1',

    # any module necessary for this one to work correctly
    'depends': ['freight','hr_missions'],

    # always loaded
    'data': [
        'data/journal_data.xml',
        'security/groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/expense.xml',
        'views/coverage_letter.xml',
        'views/coverage_letter_line.xml',
        'views/product_product.xml',
        'views/account_move.xml',
        'views/hr_employee.xml',
        'views/custody.xml',
        'views/freight_operation.xml',
        'views/register_payment_views.xml',
        'views/sale_order.xml',
        'views/els_event_state.xml',
        'views/els_event.xml',
        'views/purchase_order.xml',
        'views/menue_xml.xml',

        'wizard/custody_journal.xml',
        'wizard/treasury_manager.xml',
        'data/data.xml',

        'data/sequence.xml',
        'report/expense_report.xml',
        'report/official_receipt_report.xml',
        'report/custody_receipt.xml',
        'report/cover_letter.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
