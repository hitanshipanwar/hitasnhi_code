# -*- coding: utf-8 -*-
# from odoo import http


# class SoltQuarryDoorMpr(http.Controller):
#     @http.route('/solt_quarry_door_mpr/solt_quarry_door_mpr', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/solt_quarry_door_mpr/solt_quarry_door_mpr/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('solt_quarry_door_mpr.listing', {
#             'root': '/solt_quarry_door_mpr/solt_quarry_door_mpr',
#             'objects': http.request.env['solt_quarry_door_mpr.solt_quarry_door_mpr'].search([]),
#         })

#     @http.route('/solt_quarry_door_mpr/solt_quarry_door_mpr/objects/<model("solt_quarry_door_mpr.solt_quarry_door_mpr"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('solt_quarry_door_mpr.object', {
#             'object': obj
#         })

