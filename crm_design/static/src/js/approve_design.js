odoo.define('crm_design.approve_designs', function (require) {
'use strict';

var concurrency = require('web.concurrency');
var core = require('web.core');
var utils = require('web.utils');
var ajax = require('web.ajax');
var _t = core._t;
var qweb = core.qweb;

	$(document).ready(function(){

		// Approve Functionality
		$('.approve').on('click',function (){

			var $input = $(this.parentNode);
			var tr = $(this).closest('tr');
			var comment = tr.find('textarea').val()
            var sale_order_id = parseInt($input.data('sale-order-id'), 10);
            var design_id = parseInt($input.data('design-id'), 10);

			var modal = $('#myModalDesignApprove')
			$('#myModalDesignApprove').show();
			
			var close_btn = $('#close_modal_approve')
			close_btn.on('click', function () {
					$('#myModalDesignApprove').hide();
			});

			var approve_btn = $('#approve_btn_modal')
			approve_btn.on('click', function () {
					approveDesign(sale_order_id,design_id,comment)
					$('#myModalDesignApprove').hide();
			});

		});
		function approveDesign(sale_order_id,design_id,comment){
		
			ajax.jsonRpc('/approve/design','call',{
				sale_order_id:sale_order_id,
				design_id:design_id,
				comment:comment,
			}).then(function (result){
				location.reload(); 
			});
		}

		// Reject Functionality
		$('.reject').on('click',function (){

			var $input = $(this.parentNode);
			var tr = $(this).closest('tr');
			var comment = tr.find('textarea').val()
            var sale_order_id = parseInt($input.data('sale-order-id'), 10);
            var design_id = parseInt($input.data('design-id'), 10);

			var modal = $('#myModalDesignReject')
			$('#myModalDesignReject').show();
			
			var close_btn = $('#close_modal_reject')
			close_btn.on('click', function () {
					$('#myModalDesignReject').hide();
			});

			var reject_btn = $('#reject_btn_modal')
			reject_btn.on('click', function () {
				rejectDesign(sale_order_id,design_id,comment)
					$('#myModalDesignReject').hide();
			});
			
		});

		function rejectDesign(sale_order_id,design_id,comment){
		
			ajax.jsonRpc('/reject/design','call',{
				sale_order_id:sale_order_id,
				design_id:design_id,
				comment:comment,
			}).then(function (result){
				location.reload(); 
			});
		}
		
	});

});