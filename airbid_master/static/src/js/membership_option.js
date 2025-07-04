odoo.define('airbid_master.membership_plan', function (require) {
'use strict';

	var ajax = require('web.ajax');
	
	// membership plan selection fileds....................................
	$(document).ready(function(){
		$('select[name="value_select"]').click(function() {

			if ($(this).val() == "select_bids") {
				$('#bid_product_select').attr('disabled','disabled');
			};


			if ($(this).val() == "10_bids") {
				$('div #bid_selection span .currency').html("<span>190</span>")
				var value = $("#value_10bid").val()
				$('form[name="bid_ppb"] input[type="submit"]').before("<input name='product_id' value='"+value+"' type='hidden'/>")
				if($(this).data('approve')){
					$('#bid_product_select'). removeAttr('disabled');
				}

			};

			if ($(this).val() == "20_bids") {
				$('div #bid_selection span .currency').html("<span>360</span>")
				var value = $("#value_20bid").val()
				$('form[name="bid_ppb"] input[type="submit"]').before("<input name='product_id' value='"+value+"' type='hidden'/>")
				if($(this).data('approve')){
					$('#bid_product_select'). removeAttr('disabled');
				}
			};

			if ($(this).val() == "30_bids") {
				$('div #bid_selection span .currency').html("<span>525</span>")
				var value = $("#value_30bid").val()
				$('form[name="bid_ppb"] input[type="submit"]').before("<input name='product_id' value='"+value+"' type='hidden'/>")
				if($(this).data('approve')){
					$('#bid_product_select'). removeAttr('disabled');
				}
			};
		});

	});

// +++++++++++++++++++++++++++++++++Intrested checkbox click evevt+++++++++++++++++++++++++++++++
	
	$(document).ready(function() {
		$("input[type='checkbox']").on('click',function (){
                var $input = $(this.parentNode);
               
                var project_id = parseInt($input.data('project-id'), 10);

                removeCourseAttendee(project_id);
        });
		function removeCourseAttendee(project_id)
		{
			ajax.jsonRpc('/intrested', 'call', {
				project_id: project_id,
            }).then(function (val){
             	});
		}
	});

	// +++++++++++++++++++++++++++++Restriction in supplier bid page++++++++++++++++++++++
	$(document).ready(function() {
		// Number Input Value +++++++++++++
		$('.number_input_only').keypress(function (e) {    
			var charCode = (e.which) ? e.which : event.keyCode    
			if (String.fromCharCode(charCode).match(/[^0-9]/g))   
				return false;
		});

		// Float Number value++++++++++++++
		$('.float_number_input_only').keypress(function(event) {
		    if (event.which != 46 && (event.which < 47 || event.which > 59))
		    {
		        event.preventDefault();
		        if ((event.which == 46) && ($(this).indexOf('.') != -1)) {
		            event.preventDefault();
		        }
		    }
		});


		// TEXT INPUT VALUE  ++++++++++++++
		$('.text_input_only').keypress(function (e) {
			var charCode = (e.which) ? e.which : event.keyCode
			if (String.fromCharCode(charCode).match(/[^0-9]/g)){
				return true;
			}else{
				return false;
			}
		});

	});
	// ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

});