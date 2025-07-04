# -*- coding: utf-8 -*-
# from odoo import http


# class SoltQuarryDocumentsSpecs(http.Controller):
#     @http.route('/solt_quarry_documents_specs/solt_quarry_documents_specs', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/solt_quarry_documents_specs/solt_quarry_documents_specs/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('solt_quarry_documents_specs.listing', {
#             'root': '/solt_quarry_documents_specs/solt_quarry_documents_specs',
#             'objects': http.request.env['solt_quarry_documents_specs.solt_quarry_documents_specs'].search([]),
#         })

#     @http.route('/solt_quarry_documents_specs/solt_quarry_documents_specs/objects/<model("solt_quarry_documents_specs.solt_quarry_documents_specs"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('solt_quarry_documents_specs.object', {
#             'object': obj
#         })

