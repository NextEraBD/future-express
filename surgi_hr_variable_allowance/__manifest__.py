# -*- coding: utf-8 -*-
{
    'name': "Surgi Hr Variable Allowance",

    'summary': """
    """,

    'description': """
    """,

    'author': "Surgitech",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr', 'hr_payroll_community', 'branch'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_variable_allowance_request.xml',
        'views/hr_variable_allowance_rule.xml',
        'views/hr_variable_allowance_type.xml',
        'views/hr_employee.xml',
        'data/hr_salary_structure.xml',


    ]
}
