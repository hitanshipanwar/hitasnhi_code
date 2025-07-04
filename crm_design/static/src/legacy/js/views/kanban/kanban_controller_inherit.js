odoo.define('crm_design.KanbanControllerExtend', function (require) {
"use strict";

/**
 * The KanbanController is the class that coordinates the kanban model and the
 * kanban renderer.  It also makes sure that update from the search view are
 * properly interpreted.
 */

var BasicController = require('web.BasicController');
var Context = require('web.Context');
var core = require('web.core');
var Dialog = require('web.Dialog');
var Domain = require('web.Domain');
var view_dialogs = require('web.view_dialogs');
var viewUtils = require('web.viewUtils');

var _t = core._t;
var qweb = core.qweb;

const MyKanbanController = require('web.KanbanController');
var BasicControllerExtend = require('web.BasicController');

MyKanbanController.include({
	_onQuickCreateRecord: function (ev) {
		var self = this;
		var values = ev.data.values;
		var column = ev.target;
		var onFailure = ev.data.onFailure || function () {};

		// function that updates the kanban view once the record has been added
		// it receives the local id of the created record in arguments
		var update = function (db_id) {

			var columnState = self.model.getColumn(db_id);
			var state = self.model.get(self.handle);
			return self.renderer
				.updateColumn(columnState.id, columnState, {openQuickCreate: true, state: state})
				.then(function () {
					if (ev.data.openRecord) {
						self.trigger_up('open_record', {id: db_id, mode: 'edit'});
					}
				});
		};

		this.model.createRecordInGroup(column.db_id, values)
			.then(update)
			.guardedCatch(function (reason) {
				reason.event.preventDefault();
				var columnState = self.model.get(column.db_id, {raw: true});
				var context = columnState.getContext();
				var state = self.model.get(self.handle, {raw: true});
				var groupByField = viewUtils.getGroupByField(state.groupedBy[0]);
				context['default_' + groupByField] = viewUtils.getGroupValue(columnState, state.groupedBy[0]);

				// Passing Default Value to Form
				var context_new = {
					default_partner_id: values.partner_id,
					default_priority: values.priority,
					default_expected_revenue: values.expected_revenue,
					default_email_from: values.email_from,
					default_phone: values.phone
				}
				context = _.extend(context,context_new)

				new view_dialogs.FormViewDialog(self, {
					res_model: state.model,
					context: _.extend({default_name: values.name || values.display_name}, context),
					title: _t("Create"),
					disable_multiple_selection: true,
					on_saved: function (record) {
						self.model.addRecordToGroup(column.db_id, record.res_id)
							.then(update);
					},
				}).open().opened(onFailure);
			});
	},
});

});