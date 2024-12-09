# -*- coding: utf-8 -*-
# from odoo import http


# class CustomMainAccount(http.Controller):
#     @http.route('/custom_main_account/custom_main_account', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_main_account/custom_main_account/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_main_account.listing', {
#             'root': '/custom_main_account/custom_main_account',
#             'objects': http.request.env['custom_main_account.custom_main_account'].search([]),
#         })

#     @http.route('/custom_main_account/custom_main_account/objects/<model("custom_main_account.custom_main_account"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_main_account.object', {
#             'object': obj
#         })
