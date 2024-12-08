# -*- coding: utf-8 -*-
{
    'name': 'Customer Complement',
    'version': '1.0',
    'summary': 'journal_statment',
    'author': 'Banan',
    'depends': ['base','freight',],
    'data': [
        'security/ir.model.access.csv',
        'wizard/ticket_payment_view_wizard.xml',
        'wizard/task_view_wizard.xml',
        'views/complaint_type.xml',
        'views/customer_compliment.xml',
        'views/customer_ticket_view.xml',
        'views/fright_operation_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
