{
    'name': 'Freight Management',
    'version': '16.0',
    'category': 'freight',
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'author': 'NextEra',
    'summary': 'Freight Management By NextEra',
    'description': '',

    'depends': ['base', 'base_setup', 'sales_team', 'sale_management', 'product','hr_expense',
                'contacts', 'calendar', 'mail', 'fleet', 'account','web', 'website', 'board', 'stock',
                'purchase', 'crm', 'hr', 'sale','report_xlsx'],

    'data': [
        'data/freight_seq.xml',
        'data/freight_manifest_seq.xml',
        'data/freight_shipment_seq.xml',
        'data/freight_data.xml',
        'data/crm_stage_data.xml',
        'data/lead_seq.xml',
        'data/way_bill_seq.xml',
        'data/console_operation_sequence.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/freight_view.xml',
        'views/container_view.xml',
        'views/crm_leads.xml',
        'views/crm_stage.xml',
        'views/freight_manifest.xml',
        'views/freight_shipment.xml',
        'views/road_way_bill.xml',
        'views/airline_view.xml',
        'views/package_veiw.xml',
        'views/port_view.xml',
        'views/account_move.xml',
        'views/res_partner.xml',
        'views/service_view.xml',
        'views/freight_stage.xml',
        'views/vessel_view.xml',
        'views/rate_price.xml',
        'views/transit_view.xml',
        'views/transit_config.xml',
        'views/crm_config.xml',
        'views/clearance_rate_price.xml',
        'views/transport_rate_price.xml',
        'views/freight_way_bill.xml',
        'views/console_operation.xml',
        'views/cals_view.xml',
        'views/meeting_view.xml',
        'views/visits.xml',
        'views/customs.xml',
        'views/res_users_view.xml',
        'views/way_bill.xml',
        'views/purchase_views.xml',
        'wizard/container_duplicate.xml',
        'wizard/register_invoice_freight_view.xml',
        'wizard/crm_lead_to_opportunity_views.xml',
        'wizard/freight_rfq_wizard.xml',
        'wizard/purchase_lead.xml',
        'wizard/quotation.xml',
        'wizard/quotation_lead.xml',
        'wizard/purchase.xml',
        'wizard/transport_rfq_wizard.xml',
        'wizard/clearance_rfq_wizard.xml',
        'wizard/freight_report.xml',
        'report/delivery_order.xml',
        'report/bill_of_lading.xml',
        'report/mawb_report.xml',
        'report/quotation_report.xml',
        'report/airway_bill.xml',
        'report/freight_report.xml',
        'report/guarantee_report.xml',
        'report/journal_entries.xml',
        'report/air_manifest_report.xml',
        'report/freight_manifest.xml',
        'report/freight_shipment.xml',
        'report/road_way_bill.xml',
        'report/vgm_template.xml',
        'report/way_bill_report.xml',
        'report/delivery_letter_report.xml',
        'report/shipping_declaration_report.xml',
        'report/pre_alert.xml',
        'report/report_invoice_template_inherit.xml',

    ],
    'web.assets_backend': [

        'freight/static/src/css/freight.css',],
    'application': True,
    'installable': True,
    'auto_install': False,
}