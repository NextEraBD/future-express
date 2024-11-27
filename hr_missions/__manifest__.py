# -*- coding: utf-8 -*-
{
    'name': "HR Missions",

    'summary': """
        This enhancement for HR Module Hanimex""",

    'description': """
        1- add field in contract for receive wage
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',

    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_expense','hr_contract',"base_address_extended", 'hr_holidays','hr_attendance','branch'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/mission_security.xml',
        'views/hr_mission_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/mission_journal.xml',
        # 'views/hr_dept_inh.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
