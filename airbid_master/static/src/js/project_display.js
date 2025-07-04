odoo.define('airbid_master.display_form', function (require) {
'use strict';

var ajax = require('web.ajax');
$(document).ready(function(){

	$('[data-toggle="tooltip"]').tooltip({
        placement : 'top'
    });

	$('#supplied_sepretly_brand_lable').hide();
	$('#supplied_sepretly_brand').hide();
	$('#supplied_sepretly_size_lable').hide();
	$('#supplied_sepretly_size').hide();
	$('#supplied_sepretly_made_in').hide();
	$('#supplied_sepretly_made_lable').hide();
	$('#supplied_sepretly_inverter_warranty_lable').hide();
	$('#supplied_sepretly_inverter_warranty').hide();
	$('#supplied_sepretly_attchment_photo_multi_lable').hide();
	$('#supplied_sepretly_attchment_photo_multi').hide();
	$('#supplied_sepretly_battery_brand').hide();
	$('#supplied_sepretly_battery_brand_lable').hide();
	$('#supplied_sepretly_battery_model').hide();
	$('#supplied_sepretly_battery_model_lable').hide();
	$('#supplied_sepretly_battery_model_lable_kw').hide();
	$('#supplied_sepretly_battery_warranty').hide();
	$('#supplied_sepretly_battery_warranty_lable').hide();
	$('#supplied_sepretly_battery_datasheet').hide();
	$('#supplied_sepretly_battery_datasheet_lable').hide();

	$('#supplied_sepretly_battery_made_in_lable').hide();
	$('#supplied_sepretly_battery_made_in').hide();
	$('#supplied_sepretly_size_lable_kw').hide();
	$('#supplied_sepretly_hide').hide();
	$('#battery_inverter_product_add').hide();
	$('#supplied_sepretly_select_hide').hide();
	$('#supplied_sepretly_select_bat_hide').hide();
	$('#sup_battery_information_hide_show').hide();
	$('#del_sup_bat_img').hide();
	$('#del_sup_inv_img').hide();
	
	// selection +++++++++++++++++
    $("#battary_select").change(function() {
	    if ($(this).val() == "inbuilt_in_box") {
			$('#inbuilt_product_brand').show();
			$('#inbuilt_product_model_no').show();
			$('#inbuilt_made_in').show();
			$('#inbuilt_product_warranty').show();
			$('#inbuilt_attchment_photo_multi').show();
			$('#Inbuilt_in_box_hide').show();

			$('#inbuilt_product_warranty_lable').show();
			$('#inbuilt_made_in_lable').show();
			$('#inbuilt_made_in_model_mo').show();
			$('#inbuilt_made_in_brand').show();
			$('#inbuilt_attchment_photo_multi_lable').show();
			$('#inbuilt_made_in_model_mo_kw').show();
			$('#inbuilt_in_box_hide').show();
			$('#del_inbuilt_img').show();

			// $('#house_attachment').prop("required", false);

			$('#supplied_sepretly_brand_lable').hide();
			$('#supplied_sepretly_brand').hide();
			$('#supplied_sepretly_size_lable').hide();
			$('#supplied_sepretly_size_lable_kw').hide();
			$('#supplied_sepretly_size').hide();
			$('#supplied_sepretly_made_in').hide();
			$('#supplied_sepretly_made_lable').hide();
			$('#supplied_sepretly_inverter_warranty_lable').hide();
			$('#supplied_sepretly_inverter_warranty').hide();
			$('#supplied_sepretly_attchment_photo_multi_lable').hide();
			$('#supplied_sepretly_attchment_photo_multi').hide();
			$('#supplied_sepretly_battery_brand').hide();
			$('#supplied_sepretly_battery_brand_lable').hide();
			$('#supplied_sepretly_battery_model').hide();
			$('#supplied_sepretly_battery_model_lable').hide();
			$('#supplied_sepretly_battery_model_lable_kw').hide();
			$('#supplied_sepretly_battery_warranty').hide();
			$('#supplied_sepretly_battery_warranty_lable').hide();
			$('#supplied_sepretly_battery_datasheet').hide();
			$('#supplied_sepretly_battery_datasheet_lable').hide();
			$('#supplied_sepretly_battery_made_in_lable').hide();
			$('#supplied_sepretly_battery_made_in').hide();
			$('#supplied_sepretly_hide').hide();
			$('#battery_inverter_product_add').hide();
			$('#supplied_sepretly_select_hide').hide();
			$('#supplied_sepretly_select_bat_hide').hide();
			$('#sup_battery_information_hide_show').hide();
			$('#del_sup_bat_img').hide();
			$('#del_sup_inv_img').hide();
		}else{
			$('#inbuilt_product_brand').hide();
			$('#inbuilt_product_model_no').hide();
			$('#inbuilt_made_in').hide();
			$('#inbuilt_product_warranty').hide();
			$('#Inbuilt_in_box_hide').hide();
			$('#inbuilt_attchment_photo_multi').hide();

			$('#inbuilt_product_warranty_lable').hide();
			$('#inbuilt_made_in_lable').hide();
			$('#inbuilt_made_in_model_mo').hide();
			$('#inbuilt_made_in_model_mo_kw').hide();
			$('#inbuilt_made_in_brand').hide();
			$('#inbuilt_attchment_photo_multi_lable').hide();
			$('#inbuilt_in_box_hide').hide();
			$('#del_inbuilt_img').hide();

			$('#supplied_sepretly_brand_lable').show();
			$('#supplied_sepretly_brand').show();
			$('#supplied_sepretly_size_lable').show();
			$('#supplied_sepretly_size_lable_kw').show();
			$('#supplied_sepretly_size').show();
			$('#supplied_sepretly_made_in').show();
			$('#supplied_sepretly_made_lable').show();
			$('#supplied_sepretly_inverter_warranty_lable').show();
			$('#supplied_sepretly_inverter_warranty').show();
			$('#supplied_sepretly_attchment_photo_multi_lable').show();
			$('#supplied_sepretly_attchment_photo_multi').show();
			$('#supplied_sepretly_battery_brand').show();
			$('#supplied_sepretly_battery_brand_lable').show();
			$('#supplied_sepretly_battery_model').show();
			$('#supplied_sepretly_battery_model_lable').show();
			$('#supplied_sepretly_battery_model_lable_kw').show();
			$('#supplied_sepretly_battery_warranty').show();
			$('#supplied_sepretly_battery_warranty_lable').show();
			$('#supplied_sepretly_battery_datasheet').show();
			$('#supplied_sepretly_battery_datasheet_lable').show();
			$('#supplied_sepretly_battery_made_in_lable').show();
			$('#supplied_sepretly_battery_made_in').show();
			$('#supplied_sepretly_hide').show();
			$('#battery_inverter_product_add').show();
			$('#supplied_sepretly_select_hide').show();
			$('#supplied_sepretly_select_bat_hide').show();
			$('#sup_battery_information_hide_show').show();
			$('#del_sup_bat_img').show();
			$('#del_sup_inv_img').show();
		}
	});

    // Add button click Battary
	// $('#battery_information_hide_show').hide();
	// $( "#battery_information_add" ).click(function() {
	//   $( "#battery_information_hide_show" ).toggle( "hide", function() {
	//   });
	// });

      $("#battery_information_add").on( "click", function() {
        var count_no = $("#battery_information_count").val()
        var count = parseInt(count_no)+1
        var battery_information_brand = "battery_information_brand"+String(count)
        var battery_information_model = "battery_information_model"+String(count)
        var battery_information_made_in = "battery_information_made_in"+String(count)
        var battery_information_product_warranty = "battery_information_product_warranty"+String(count)
        var battery_information_product_datasheet_img = "battery_information_product_datasheet_img"+String(count)

        var btn_example_file_reset = "btn_example_file_reset"+String(count)
        var delete_icon = "delete_icon"+String(count)
        var battery_information_hide_show = "battery_information_hide_show"+String(count)
        var button_data  = String(count)
        $(this).before("<div id='battery_information_hide_show' class='battery_information_hide_show'><div class='row'><div class='col-md-4 form-group'><label for=' class='col-form-label suppler_disp_name' id='battery_information_brand_lable'>product Brand</label><input type='text' class='form-control suppler_disp_name_input text_input_only' name='"+battery_information_brand+"' id='"+battery_information_brand+"' required='required'/></div><div class='col-md-4 form-group'><label for=' class='col-form-label suppler_disp_name' id='battery_information_model_lable'>product model no</label><input type='text' class='form-control suppler_disp_name_input float_number_input_only' name='"+battery_information_model+"' id='"+battery_information_model+"' required='required'/></div><div class='col-md-4 form-group'><label for=' class='col-form-label suppler_disp_name' id='battery_information_made_in_lable'>Made in</label><input type='text' class='form-control suppler_disp_name_input text_input_only' name='"+ battery_information_made_in +"' id='"+battery_information_made_in+"' required='required'/></div></div><div class='row'><div class='col-md-4 form-group'><label for=' class='col-form-label suppler_disp_name' id='battery_information_product_warranty_lable'>product warranty</label><input type='text' class='form-control suppler_disp_name_input float_number_input_only' name='"+battery_information_product_warranty+"' id='"+battery_information_product_warranty+"' required='required'/></div><div class='col-md-4 form-group'><label for=' class='col-form-label suppler_disp_name' id='battery_information_product_datasheet_lable'>upload datasheet</label><input type='file' accept='.jpg,.png,.jpeg' name='"+battery_information_product_datasheet_img+"' id='"+battery_information_product_datasheet_img+"'/><button type='button' id='"+btn_example_file_reset+"' class='del_clear_file_view'><img src='/airbid_master/static/src/image/delete.png' class='clear_data' id='clear_data'></img></button></div><div id='field_2' class='column col-sm-3'><img src='/airbid_master/static/src/image/delete.png' class='delete_icon_pro' id='delete_icon_pro' name='" +delete_icon+"' data-toggle='tooltip' data-original-title='Delete'></img></div></div><input type='checkbox' id='is_saved"+count+"' t-attf-name='is_saved"+count+"' hidden='hidden'/></div>")
        $("#battery_information_count").val(count)

        $('.battery_information_hide_show').on('click', '#delete_icon_pro', function(){
           $(this).closest('div.battery_information_hide_show').remove();
           var count = $("#battery_information_count").val()
        });

    	 $('#btn_example_file_reset'+String(count)).on('click', function() {   
		      $('#battery_information_product_datasheet_img'+String(count)).val('');
		   });
    	 	$('[data-toggle="tooltip"]').tooltip();
      })

      $('.battery_information_hide_show').on('click', '#delete_icon_pro', function(){
         $(this).closest('div.battery_information_hide_show').remove();
         $('#myModal_delete').hide();
      });

			var c_no = $("#battery_information_count").val()
			for (let i = 1; i <= parseInt(c_no); i++) {
				$('#btn_example_file_reset'+String(i)).on('click', function() {
		      $('#battery_information_product_datasheet_img'+String(i)).val('');
		   });
			}

			// removing image from web Inb
			var inb_count = $("#inb_count").val()
		  var inb_removed_list = $('#inb_removed_list');
			for (let i = 1; i <= parseInt(inb_count); i++) {

				$('#del_inb_img'+String(i)).on('click', function() {
		  		// make list of delete image line id
		      var line_id = $('#inb_line_id'+String(i)).val();
		      var ids = inb_removed_list.val()
		      inb_removed_list.val(ids+','+line_id)

		      $('#inb_line_id'+String(i)).remove();
		      $('#inb_doc_att_img'+String(i)).remove();
		      $('#del_inb_img'+String(i)).remove();
		   	});
			// removing image from web Inb
			}

			// INVENTER SUPPLIER CODE
			var inv_count = $("#inv_count").val()
		  var inv_removed_list = $('#inv_removed_list');
			for (let i = 1; i <= parseInt(inv_count); i++) {

				$('#del_inv_img'+String(i)).on('click', function() {
		  		// make list of delete image line id
		      var line_id = $('#inv_line_id'+String(i)).val();
		      var ids = inv_removed_list.val()
		      inv_removed_list.val(ids+','+line_id)

		      $('#inv_line_id'+String(i)).remove();
		      $('#sup_inv_doc_att_img'+String(i)).remove();
		      $('#del_inv_img'+String(i)).remove();
		   	});
			// removing image from web Inv
			}			
			// INVENTER SUPPLIER CODE END
  		
  		// BATTERY SUPPLIER CODE
			var bat_count = $("#bat_count").val()
		  var bat_removed_list = $('#bat_removed_list');
			for (let i = 1; i <= parseInt(bat_count); i++) {

				$('#del_bat_img'+String(i)).on('click', function() {
		  		// make list of delete image line id
		      var line_id = $('#bat_line_id'+String(i)).val();
		      var ids = bat_removed_list.val()
		      bat_removed_list.val(ids+','+line_id)

		      $('#bat_line_id'+String(i)).remove();
		      $('#sup_bat_doc_att_img'+String(i)).remove();
		      $('#del_bat_img'+String(i)).remove();
		   	});
			// removing image from web Inv
			}			
			// BATTERY SUPPLIER CODE END

			// :LOOK BATTERY SUPPLIER CODE
			var look_count = $("#look_count").val()
		  var look_removed_list = $('#look_removed_list');
			for (let i = 1; i <= parseInt(look_count); i++) {

				$('#look_bat_img'+String(i)).on('click', function() {
		  		// make list of delete image line id
		      var line_id = $('#look_line_id'+String(i)).val();
		      var ids = look_removed_list.val()
		      look_removed_list.val(ids+','+line_id)

		      $('#look_line_id'+String(i)).remove();
		      $('#sup_look_doc_att_img'+String(i)).remove();
		      $('#look_bat_img'+String(i)).remove();
		   	});
			// removing image from web Inv
			}			
			// LOOK BATTERY SUPPLIER CODE END

			// how look like val none
			$('#del_how_it_img').on('click', function() {   
	      $('#how_it_look_attchment_photo_multi').val('');
	    });
			$('#del_inbuilt_img').on('click', function() {   
		    $('#inbuilt_attchment_photo_multi').val('');
		  });

		  $('#del_sup_inv_img').on('click', function() {   
		    $('#supplied_sepretly_attchment_photo_multi').val('');
		  });

		  $('#del_sup_bat_img').on('click', function() {   
		    $('#supplied_sepretly_battery_datasheet').val('');
		  });

      $("#battery_inverter_product_add").on( "click", function() {
        var count_no = $("#inventor_area_operates_counter").val()
        var count = parseInt(count_no)+1
        var supllier_inverter_brand = "supllier_inverter_brand"+String(count)
        var supllier_inverter_size = "supllier_inverter_size"+String(count)
        var made_in_sup = "made_in_sup"+String(count)
        var supllier_inverter_warranty = "supllier_inverter_warranty"+String(count)
        var attchment_photo_multi_inverter = "attchment_photo_multi_inverter"+String(count)
        var btn_file_reset = "btn_file_reset"+String(count)
        var delete_icon = "delete_icon"+String(count)
        var battery_inverter_hide_show_product_add = "battery_inverter_hide_show_product_add"+String(count)
        var button_data  = String(count)
        $(this).before('<div id="battery_inverter_hide_show_product_add" class="battery_inverter_hide_show_product_add"><div class="row"><div class="col-md-4 form-group"><label for="" class="col-form-label suppler_disp_name">product Brand</label><input type="text" class="form-control suppler_disp_name_input text_input_only" name="'+supllier_inverter_brand+'" id="'+supllier_inverter_brand+'" t-if="not bid_data"/></div><div class="col-md-4 form-group"><label for="" class="col-form-label suppler_disp_name">product model no</label><input type="text" class="form-control suppler_disp_name_input float_number_input_only" name="'+supllier_inverter_size+'" id="'+supllier_inverter_size+'" t-if="not bid_data"/></div><div class="col-md-4 form-group"><label for="" class="col-form-label suppler_disp_name">Made in</label><input type="text" class="form-control suppler_disp_name_input text_input_only" name="'+made_in_sup+'" id="'+made_in_sup+'"  t-if="not bid_data"/></div></div><div class="row"><div class="col-md-4 form-group"><label for="" class="col-form-label suppler_disp_name">product warranty </label><input type="text" class="form-control suppler_disp_name_input float_number_input_only" name="'+supllier_inverter_warranty+'" id="'+supllier_inverter_warranty+'" t-if="not bid_data"/></div><div class="col-md-4 form-group"><label for="" class="col-form-label suppler_disp_name">upload datasheet</label><input type="file" accept=".jpg,.png,.jpeg" name="'+attchment_photo_multi_inverter+'" id="'+attchment_photo_multi_inverter+'" /><button type="button" id="'+btn_file_reset+'" class="del_clear_file_view"><img src="/airbid_master/static/src/image/delete.png" class="clear_data" id="clear_data"></img></button></div><div id="field_2" class="column col-sm-3"><img src="/airbid_master/static/src/image/delete.png" class="delete_icon_pro" id="delete_icon_pro" name="'+delete_icon+'"  data-toggle="tooltip" data-original-title="Delete"></img></div></div></div><input type="checkbox" id="is_saved'+count+'" t-attf-name="is_saved'+count+'" hidden="hidden"/></div>') 
        
        $("#inventor_area_operates_counter").val(count)
        $('.battery_inverter_hide_show_product_add').on('click', '#delete_icon_pro', function(){
           $(this).closest('div.battery_inverter_hide_show_product_add').remove();
           var count = $("#inventor_area_operates_counter").val()
        });

        $('#btn_file_reset'+String(count)).on('click', function() {     
		      $('#attchment_photo_multi_inverter'+String(count)).val('');
		  	});
        $('[data-toggle="tooltip"]').tooltip();
      })

      $('.battery_inverter_hide_show_product_add').on('click', '#delete_icon_pro', function(){
        $(this).closest('div.battery_inverter_hide_show_product_add').remove();
      });

      var i_no = $("#inventor_area_operates_counter").val()
			for (let i = 1; i <= parseInt(i_no); i++) {
				$('#btn_sup_file_reset'+String(i)).on('click', function() {
		      $('#attchment_photo_multi_inverter'+String(i)).val('');
		   });
			}
      // INVENTOR ++++++++++++++++++

	// $('#battery_inverter_hide_show_product_add').hide();
	// $( "#battery_inverter_product_add" ).click(function() {
	//   $( "#battery_inverter_hide_show_product_add" ).toggle( "hide", function() {
	//   });
	// });


// EMAIL CHANGES
$( "#email_changes" ).click(function() {
  	$('#login_sign').val('');
  	if ($('#login_sign').val('')) {
		$('#email_verify').show();
		$('#email_changes').hide();
		$('#validate_email').hide();
	}
});

// PHONE NUMBER 
$( "#mobile_changes" ).click(function() {
  	$('#phone_no_sign').val('');
  	if ($('#phone_no_sign').val('')) {
		$('#mobile_no_verify').show();
		$('#mobile_changes').hide();
		$('#validate').hide();
	}
});
	
$('input[name="property"]').click(function() {
	if ($(this).val() == "yes") {
		$('#next_1'). removeAttr('disabled');
			 
	}else{
		$('#next_1').attr('disabled','disabled');
		}
});
$('input[name="question3"]').click(function(){
	if ($(this).val() == "yes") {
		$('#next_3'). removeAttr('disabled');
				
	}else{
		$('#next_3'). removeAttr('disabled');
			
		}
});
$('input[name="remove_panels"]').click(function(){
	if ($(this).val() == "yes") {
		$('#next_removeexisting'). removeAttr('disabled');
						
	}else{
		$('#next_removeexisting'). removeAttr('disabled');
		
	}
});

$('input[name="add_panels"]').click(function(){
	if ($(this).val() == "yes") {
		$('#next_addpanels'). removeAttr('disabled');
			
	}else{
		$('#next_addpanels'). removeAttr('disabled');
		
		
	}
});  
$('input[name="add_battery"]').click(function(){
	if ($(this).val() == ""){
		$('#text_box').hide();
	}
	if ($(this).val() == "yes") {
		$('#next_battery'). removeAttr('disabled');
		$('#text_box').show();
		$('#que_type').show();
		$('#que_inverter').show();
		$('#que_backup').show();
		$('#que_property').show();
		$('#que_story').show();
		$('#que_roof').show();
		$('#que_electricity').show();
		$('#que_looking').show();
		$('#que_finance').show();
		$('#que_comment').show();
		$('#que_submit').show();
	}else{
		$('#next_battery').attr('disabled','disabled');
		$('#text_box').hide();
	}
});

$('input[name="solar_panels"]').click(function(){
	if ($(this).val() == "select") {
		$('#specify_panels').show();
	}else{
		$('#specify_panels').hide();
	}
});

$('input[name="inverter_type"]').click(function(){
	if ($(this).val() == "select") {
		$('#specify_inverter').show();
	}else{
		$('#specify_inverter').hide();
	}
});


$('input[name="system_size"]').click(function(){
	if ($(this).val() == "specify") {
		$('#systemsize').show();
	}else{
		$('#systemsize').hide();
	}
});

$('input[name="upgrade_system"]').click(function(){
	if ($(this).val() == "yes") {
		$('#que4_new').show();
		$('#que_type').show();
		$('#que_inverter').show();
		$('#que_backup').show();
		$('#que_property').show();
		$('#que_story').show();
		$('#que_roof').show();
		$('#que_electricity').show();
		$('#que_looking').show();
		$('#que_finance').show();
		$('#que_comment').show();
		$('#que_submit').show();
 }else{
	$('#que_storage_new').show();
	$('#que4_new').hide();
	$('#que_type').hide();
	$('#que_inverter').hide();
	$('#que_backup').hide();
	$('#que_property').hide();
	$('#que_story').hide();
	$('#que_roof').hide();
	$('#que_electricity').hide();
	$('#que_looking').hide();
	$('#que_finance').hide();
	$('#que_comment').hide();
	$('#que_submit').hide();
 }  
});

$('input[name="battery_backup"]').click(function(){
	if ($(this).val() == "yes") {
		$('#specify_size').show();
		$('#specify_size_box').show();
	
	}else{
		$('#specify_size').hide();
		$('#specify_size_box').hide();
		
	}
});

$('a[id="enter_manually"]').click(function(){
	$('#field_line1').show();
	$('#field_line2').show();
	$('#city_state').show();
	$('#fatch_address').hide();
	$('#manual_address').hide();
});

// +++++++++++++++++++++++++++++++Previous button+++++++++++++++++++++++
$("#previous").on("click", function() {
	window.history.back();
	// Sunen
	// location.replace(document.referrer);
	// location.reload(); 

});
// ++++++++++++++++Popup window++++++++++++++++++++++++
	$(".social_share_link").on("click", function() {
		window.open("/mobile/verify", "Google", "width=500,height=500");
	});

// +++++++++++++++++++++++++menu popup+++++++++++++++++++++++++++++++

// Get the modal
var modal = $('#myModal')
var modal = $('#myModalemail')

// Get the button that opens the modal
var btn = $('.myBtn')
var btnEmail = $('.myBtnEmail')

// Get the <span> element that closes the modal
var span = $('.close')

// When the user clicks the button, open the modal 
btn.on('click', function () {	
	$('#image_preview').attr('src',this.src);
	$('#myModal').show();
});


// ++++++++++  REQUEST EDIT +++++++++++
var req_btn = $('.request_btn')
// Get the <span> element that closes the modal
var close_model = $('.close_req_model')
// When the user clicks the button, open the modal 
req_btn.on('click', function () {	
	$('#req_myModal').show();
});
close_model.on('click', function () {
	$('#req_myModal').hide();
});
// ++++++++++  REQUEST EDIT +++++++++++

// DELETE +++++++++++++++++++++
// var delete_req_btn = $('.delete_icon_pro')
// // Get the <span> element that closes the modal
// var delete_close_model = $('.close_req_model_delete')
// // When the user clicks the button, open the modal 
// delete_req_btn.on('click', function () {	
// 	$('#myModal_delete').show();
// });
// delete_close_model.on('click', function () {
// 	$('#myModal_delete').hide();
// });
// DELETE END +++++++++++++++++++++




btnEmail.on('click', function () {	
	$('#image_preview').attr('src',this.src);
	$('#myModalemail').show();
});

// When the user clicks on <span> (x), close the modal
span.on('click', function () {
	$('#myModal').hide();

});

span.on('click', function () {
	$('#myModalemail').hide();
});
// Roof type text box hide and show
$('.column_images').on('click',function(){
	console.log("2222222222222222222222222222222")
    var name = $('input[type="radio"]').attr('name');
    console.log("55555555555555555555555555555",name)
if (document.querySelector('input[name="roof"]:checked') != null){
	var value = document.querySelector('input[name="roof"]:checked').value;
	if(value){
	    if (value == 'other') {
			$('#rood_div').show();
				 
		}else{
			$('#rood_div').hide();
			}
	}else{
		return false
	}
}
});

// +++ REQUEST EDIT ++++++++
// $('#request_return_btn').click(function(ev) {
// 	var project_name = $("#project_name").val();
// 	var customer_project_name = $("#customer_project_name").val();
// 	var login_sign_email = $("#login_sign_email").val();
// 	var phone_no_sign_customer = $("#phone_no_sign_customer").val();
// 	var about_the_project_comment = $("#about_the_project_comment").val();
// 	var attchment_photo_multi = document.getElementById('attchment_photo_multi').files;
	// var attchment_photo_multi = $('#attchment_photo_multi').files
	// var attchment_photo_multi = $('#attchment_photo_multi')[0].files[0];
	// console.log('ssssssssssssssssssssssssssssssssssssss',attchment_photo_multi)

	// var attachment_list_view_file = document.querySelector('#attchment_photo_multi')
	// attchment_photo_multi.files = attachment_list_view_file.files
	// console.log('444444444444444444444444444444444444444444444',attchment_photo_multi.files)

	// let list_index = []
	// if (attchment_photo_multi) {
	// 	reader.onload = function(evt) { 
	// 	    const contents = evt.target.result;
	// 	    // const metadata = `name: ${attchment_photo_multi.name}, type: ${attchment_photo_multi.type}, size: ${attchment_photo_multi.size}, contents:`;
	// 	    var images = {
	// 	    	'name': attchment_photo_multi.name,
	// 	    	'contents':contents
	// 	    }
	// 	    // console.log(metadata);
	// 	    // console.log('22222222222222222',contents);
	// 	    list_index.push(images)
	// 	}
	//   	reader.readAsDataURL(attchment_photo_multi);
	// }
	// console.log('dddddddddddddddddddddddddddddddddddddddddddddd',attchment_photo_multi)

	// var data ={'jsonrpc': "2.0", 'method': "call", 
	// 			"params": {project_name: project_name,
 //        	customer_project_name: customer_project_name,
 //        	login_sign_email: login_sign_email,
 //        	phone_no_sign_customer: phone_no_sign_customer,
 //        	about_the_project_comment: about_the_project_comment,
 //        	list_index: attchment_photo_multi
 //        }}

	// console.log('data ----------------',data)
	// ajax.jsonRpc('/request/project','call',{ 
	// 	project_name : project_name,
	// 	customer_project_name : customer_project_name,
	// 	login_sign_email : login_sign_email,
	// 	phone_no_sign_customer : phone_no_sign_customer,
	// 	about_the_project_comment : about_the_project_comment,
	// 	list_index: attchment_photo_multi
	// }).then(function (result){
	// 	console.log('result ----- ',result)
	// 	$('#req_myModal').hide();
	// 	$("#project_name").val('');
	// 	$("#customer_project_name").val('');
	// 	$("#login_sign_email").val('');
	// 	$("#phone_no_sign_customer").val('');
	// 	$("#about_the_project_comment").val('');
	// 	$("#attchment_photo_multi").val('');
	// });
	// $.ajax({
 //        type: "POST",
 //        dataType: 'json',
 //        url: '/request/project',
 //        contentType: "application/json; charset=utf-8",
 //      //   data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'project_name': project_name,
 //      //   	'customer_project_name': customer_project_name,
 //      //   	'login_sign_email': login_sign_email,
 //      //   	'phone_no_sign_customer': phone_no_sign_customer,
 //      //   	'about_the_project_comment': about_the_project_comment,
 //      //   	'list_index': attchment_photo_multi
 //     	// }}),
 //     	data:data,
 //        success: function () {
 //            // widget.html($('<div class="alert alert-info" role="alert"><strong>Thank you!</strong> Mail has been sent.</div>'));
 //        },
 //        error: function (data) {
 //            // console.error("ERROR ", data);
 //        },
 //    });
    // console.log('9999999999999999999999999',data)
 //    .then(function (result){
	// 	$('#req_myModal').hide();
	// 	$("#project_name").val('');
	// 	$("#customer_project_name").val('');
	// 	$("#login_sign_email").val('');
	// 	$("#phone_no_sign_customer").val('');
	// 	$("#about_the_project_comment").val('');
	// 	$("#attchment_photo_multi").val('');
	// });

	// ajax.jsonRpc('/request/project','call',{
	// 	project_name : project_name,
	// 	customer_project_name : customer_project_name,
	// 	login_sign_email : login_sign_email,
	// 	phone_no_sign_customer : phone_no_sign_customer,
	// 	about_the_project_comment : about_the_project_comment,
	// 	attchment_photo_multi : list_index
	// })
	
// })
// Roof type text box hide and show End

// +++++++++++++++++++++++++++++verify email otp button+++++++++++++++++++++

$('button[id="email_verify"]').click(function() {
	$('#notification_email').hide();
	var value = $("#login_sign").val();
	console.log('5555555555555555',value)
	$("#test_id").append("<input type='hidden' name='email_val' t-att-value='"+value+"'/>");
	$("#user_email").html(value);
	ajax.jsonRpc('/email/verify','call',{
		email_id : value,
	}).then(function (result){
	});

});

// sign up verify link display+++++++++++++++++++++++++++++
$('button[id="email_no_verify_hidden"]').click(function() {
	$('#notification_email').hide();
	var value = $("#login_sign").val();
	$("#test_id").append("<input type='hidden' name='email_val' t-att-value='"+value+"'/>");
	$("#user_email").html(value);
	ajax.jsonRpc('/email/verify','call',{
		email_id : value,
	}).then(function (result){
	});

});
// +++++++++++++++++++++++++++++verify otp button+++++++++++++++++++++

$('button[id="mobile_no_verify"]').click(function() {
	$('#notification').hide();
	var value = $("#phone_no_sign").val();
	$("#test_id").append("<input type='hidden' name='mobile_val' t-att-value='"+value+"'/>");
	$("#user_number").html(value);
	ajax.jsonRpc('/mobile/verify','call',{
		mobile_num : value,
	}).then(function (result){
	});

});
// +++++++++++++++sign up verify link display ++++++++++++++
$('a[id="mobile_no_verify_hidden"]').click(function() {
	$('#notification').hide();
	var value = $("#phone_no_sign").val();
	$("#test_id").append("<input type='hidden' name='mobile_val' t-att-value='"+value+"'/>");
	$("#user_number").html(value);
	ajax.jsonRpc('/mobile/verify','call',{
		mobile_num : value,
	}).then(function (result){
	});


});

// +++++++++++++++++++++++Resend otp again++++++++++++++++++++
$('a[id="resend_otp"]').click(function() {
	$('#notification').hide();
	$('#notification_email').hide();
	var value = $("#phone_no_sign").val();
	$("#test_id").append("<input type='hidden' name='mobile_val' t-att-value='"+value+"'/>");
	$("#user_number").html(value);
	ajax.jsonRpc('/mobile/verify','call',{
		mobile_num : value,
	}).then(function (result){
	});


});

$('a[id="confirm_no"]').click(function() {
	var otp = $("#code").val();
	var mobile_num = $("#user_number").text();
	ajax.jsonRpc('/verifyOTP','call',{
		otp : otp,
		mobile_num : mobile_num,
	}).then(function (result){
		if(result){
			$('#notification').hide();
			$('#mobile_no_verify').hide();
			$('#new_mobile_no_verify').hide();
			$('#mobile_no_verify_hidden').hide();
			$('#new_mobile_no_verify_res').hide();
			$('#myModal').hide();
			$("#phone_no_sign").prop("readonly", true);
			$("#user_phone_no").prop("readonly", true);
			$('#validate').show();
			$('#sign_up_btn').show();
			$('#mobile_changes').show();
		}else{
			$('#notification').show();
			$("#code").val('');
			$('#validate').hide();
		}
		
	});


});

$('a[id="confirm_email"]').click(function() {
	var otp = $("#emailcode").val();
	var email_id = $("#user_email").text();
	ajax.jsonRpc('/verifyemailOTP','call',{
		otp : otp,
		email_id : email_id,
	}).then(function (result){
		if(result){
			$('#notification_email').hide();
			$('#email_verify').hide();
			$('#myModalemail').hide();
			$("#login_sign").prop("readonly", true);
			$('#validate_email').show();
			$('#sign_up_btn').show();
			$('#email_changes').show();
			
		}else{
			$('#notification_email').show();
			$("#emailcode").val('');
			$('#validate_email').hide();
		}
		
	});


});

$("#condition").change(function() {
    if ( $(this).is(':checked') && $('#validate').is(':visible')){
       	$('#sign_up_btn').removeAttr('disabled');
    }
    else{
    	$('#sign_up_btn').attr('disabled','disabled');
    }
});

$('button[id="new_mobile_no_verify"]').click(function() {
	$('#notification').hide();
	var value = $("#user_phone_no").val();
	$("#test_id").append("<input type='hidden' name='mobile_val' t-att-value='"+value+"'/>");
	$("#user_number").html(value);

	ajax.jsonRpc('/mobile/verify','call',{
		mobile_num : value,
	}).then(function (result){
	});


});

if($('input[name="pv_system"]:checked').val() == 'no'){
	 $('#upload_img_supplier_customer_pv_image').show();
	 $('input[name="ins_house_attachment"]').prop('required','required')
	 $('input[name="ins_image_of_roof"]').prop('required','required')
	 $('input[name="ins_image_of_meter_box"]').prop('required','required')
	 
	 
}else{
	$('#upload_img_supplier_customer_pv_image').hide();
	$('input[name="ins_house_attachment"]').prop("required", false);
	$('input[name="ins_image_of_roof"]').prop("required", false);
	$('input[name="ins_image_of_meter_box"]').prop("required", false);
}

$('input[name="pv_system"]').click(function(){
	if ($(this).val() == "no") {
		$('#upload_img_supplier_customer_pv_image').show();
	 	$('input[name="ins_house_attachment"]').prop('required','required')
	 	$('input[name="ins_image_of_roof"]').prop('required','required')
	 	$('input[name="ins_image_of_meter_box"]').prop('required','required')
	}else{
		$('#upload_img_supplier_customer_pv_image').hide();
		$('input[name="ins_house_attachment"]').prop("required", false);
		$('input[name="ins_image_of_roof"]').prop("required", false);
		$('input[name="ins_image_of_meter_box"]').prop("required", false);
	}
});

if($('input[name="batteryback_up"]:checked').val() == 'no'){
	 $('#batteryback_up_upload_img_supplier_customer').show();
	  /*$('input[name="house_attachment"]').prop('required','required');
	  $('input[name="image_of_roof"]').prop('required','required');
	  $('input[name="image_of_meter_box"]').prop('required','required');
	  $('input[name="meter_zoomin"]').prop('required','required');
	  $('input[name="meter_zoomout"]').prop('required','required');
	  $('input[name="meter_box_wall_pic"]').prop('required','required');*/
}else{
	$('#batteryback_up_upload_img_supplier_customer').hide();
	$('input[name="house_attachment"]').prop('required',false);
	$('input[name="image_of_roof"]').prop('required',false);
	$('input[name="image_of_meter_box"]').prop('required',false);
	$('input[name="meter_zoomin"]').prop('required',false);
	$('input[name="meter_zoomout"]').prop('required',false);
	$('input[name="meter_box_wall_pic"]').prop('required',false);

}

$('input[name="batteryback_up"]').click(function(){
	if ($(this).val() == "no") {
		$('#batteryback_up_upload_img_supplier_customer').show();
		$('input[name="house_attachment"]').prop('required','required');
	  	$('input[name="image_of_roof"]').prop('required','required');
	  	$('input[name="image_of_meter_box"]').prop('required','required');
	  	$('input[name="meter_zoomin"]').prop('required','required');
	  	$('input[name="meter_zoomout"]').prop('required','required');
	  	$('input[name="meter_box_wall_pic"]').prop('required','required');
	}else{
		$('#batteryback_up_upload_img_supplier_customer').hide();
		$('input[name="house_attachment"]').prop('required',false);
		$('input[name="image_of_roof"]').prop('required',false);
		$('input[name="image_of_meter_box"]').prop('required',false);
		$('input[name="meter_zoomin"]').prop('required',false);
		$('input[name="meter_zoomout"]').prop('required',false);
		$('input[name="meter_box_wall_pic"]').prop('required',false);
	}
});

if($('input[name="panels_tilts"]:checked').val() == 'yes'){
	 $('#que_existing_remove_panels_tile').show();
	 $('input[name="panels_tile_need"]').prop('required','required');
}else{
	$('#que_existing_remove_panels_tile').hide();
	$('input[name="panels_tile_need"]').prop('required',false);
}

$('input[name="panels_tilts"]').click(function(){
	if ($(this).val() == "yes") {
		$('#que_existing_remove_panels_tile').show();
		$('input[name="panels_tile_need"]').prop('required','required');
	}else{
		$('#que_existing_remove_panels_tile').hide();
		$('input[name="panels_tile_need"]').prop('required',false);
	}
});

if($('input[name="clip_locks"]:checked').val() == 'yes'){
	 	$('#que_existing_clip_locks').show();
	 	$('input[name="clip_locks_need"]').prop('required','required');
	 	
}else{
	$('#que_existing_clip_locks').hide();
	$('input[name="clip_locks_need"]').prop('required',false);
}

$('input[name="clip_locks"]').click(function(){
	if ($(this).val() == "yes") {
		$('#que_existing_clip_locks').show();
		$('input[name="clip_locks_need"]').prop('required','required');
	}else{
		$('#que_existing_clip_locks').hide();
		$('input[name="clip_locks_need"]').prop('required',false);
	}
});

if($('input[name="battery_sup_backup"]:checked').val() == 'yes'){
	 	$('#pv_battery_backupsection').show();
	 	$('#pv_battery_backupsection_btn').show();
	 	/*if($('input[name="battery_sup_backup"]:checked').data('is_next')== 'yes'){
			$('#pv_battery_backupsection_btn').show();
		}else{
			$('#pv_battery_backupsection_btn').hide();
		}*/
	
}else{
		$('#pv_battery_backupsection').hide();
		if($('input[name="battery_sup_backup"]:checked').data('is_next')== 'yes'){
			$('#pv_battery_backupsection_btn').show();
		}else{
			$('#pv_battery_backupsection_btn').hide();
			$('#pv_battery_backupsection_img').hide();
		}
		
}

$('input[name="battery_sup_backup"]').click(function(){
	if ($(this).val() == "yes") {
		$('#pv_battery_backupsection').show();
		$('#pv_battery_backupsection_btn').show();
		$('#pv_battery_backupsection_img').show();
		$('.seven_img').show()
		/*if($(this).data('is_next')== 'yes'){
			$('#pv_battery_backupsection_btn').show();
		}else{
			
			$('#pv_battery_backupsection_btn').hide();
		}*/
	}else{
		$('#pv_battery_backupsection').hide();
		if($(this).data('is_next')== 'yes'){
			$('input[name="ins_battery_size"]').prop('required',false);
			$('input[name="ins_battery_model_no"]').prop('required',false);
			$('input[name="ins_battery_brand"]').prop('required',false);
			$('#pv_battery_backupsection_btn').show();
			$('.seven_img').hide()
		}else{
			console.log("23333333333333333333333")
			$('#pv_battery_backupsection_btn').hide();
			$('#pv_battery_backupsection_img').hide();
			$('#batteryModal').modal('show');
			$('.modal-backdrop').removeClass('show');
		}
		
		
	}
});

$('#batteryModal').on('click', '.close', function(){
          $('#batteryModal').modal('hide');
      });

if($('input[name="pv_system_property"]:checked').val() == 'yes'){
	 	$('#pv_system_installation').show();
		$('input[name="size_of_solar_system"]').prop('required','required')
		$('input[name="pv_system_need"]').prop('required','required')
		$('input[name="panel_power_class"]').prop('required','required')
		$('input[name="inventer_pv_size"]').prop('required','required')
		$('input[name="single_ph_three"]').prop('required','required')
		$('input[name="export_device"]').prop('required','required')
		$('input[name="panels_tilts"]').prop('required','required')
		$('input[name="single_storey"]').prop('required','required')
		$('input[name="roof"]').prop('required','required')
		$('input[name="batteryback_up"]').prop('required','required')
}else{
		$('#pv_system_installation').hide();
		$('input[name="size_of_solar_system"]').prop('required',false)
		$('input[name="pv_system_need"]').prop('required',false)
		$('input[name="panel_power_class"]').prop('required',false)
		$('input[name="inventer_pv_size"]').prop('required',false)
		$('input[name="single_ph_three"]').prop('required',false)
		$('input[name="export_device"]').prop('required',false)
		$('input[name="panels_tilts"]').prop('required',false)
		$('input[name="single_storey"]').prop('required',false)
		$('input[name="roof"]').prop('required',false)
		$('input[name="batteryback_up"]').prop('required',false)
}

$('input[name="pv_system_property"]').click(function(){
	if ($(this).val() == "yes") {
		$('#pv_system_installation').show();
		$('input[name="size_of_solar_system"]').prop('required','required')
		$('input[name="pv_system_need"]').prop('required','required')
		$('input[name="panel_power_class"]').prop('required','required')
		$('input[name="inventer_pv_size"]').prop('required','required')
		$('input[name="single_ph_three"]').prop('required','required')
		$('input[name="export_device"]').prop('required','required')
		$('input[name="panels_tilts"]').prop('required','required')
		$('input[name="single_storey"]').prop('required','required')
		$('input[name="roof"]').prop('required','required')
		$('input[name="batteryback_up"]').prop('required','required')
	}else{
		$('#pv_system_installation').hide();
		$('input[name="size_of_solar_system"]').prop('required',false)
		$('input[name="pv_system_need"]').prop('required',false)
		$('input[name="panel_power_class"]').prop('required',false)
		$('input[name="inventer_pv_size"]').prop('required',false)
		$('input[name="single_ph_three"]').prop('required',false)
		$('input[name="export_device"]').prop('required',false)
		$('input[name="panels_tilts"]').prop('required',false)
		$('input[name="single_storey"]').prop('required',false)
		$('input[name="roof"]').prop('required',false)
		$('input[name="batteryback_up"]').prop('required',false)
	}
});


});

});