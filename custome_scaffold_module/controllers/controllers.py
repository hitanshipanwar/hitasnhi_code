# -*- coding: utf-8 -*-
# from odoo import http


# class CustomeScaffoldModule(http.Controller):
#     @http.route('/custome_scaffold_module/custome_scaffold_module', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custome_scaffold_module/custome_scaffold_module/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custome_scaffold_module.listing', {
#             'root': '/custome_scaffold_module/custome_scaffold_module',
#             'objects': http.request.env['custome_scaffold_module.custome_scaffold_module'].search([]),
#         })

#     @http.route('/custome_scaffold_module/custome_scaffold_module/objects/<model("custome_scaffold_module.custome_scaffold_module"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custome_scaffold_module.object', {
#             'object': obj
#         })
