odoo.define('airbid_master.signup', function (require) {
'use strict';

  // ++++++++++++++++++++++++CheckBox ID ++++++++++++++++++++++++++++
   $(function(){ 

          $('.compare_bid_ss').attr('disabled','disabled');
        $('#customers :checkbox').change(function () {
          var list_project_ids = []
          $('#customers input:checked').each(function(index, item){
                list_project_ids.push(item.value)
          });
          
          if (list_project_ids.length == 0){
            $('.compare_bid_ss').attr('disabled','disabled');
            
          }else{
            $('.compare_bid_ss').removeAttr('disabled');

          }
             $('#supplier_data').val(list_project_ids)
             var project_id = $('#project_id').val()
             $('#pro_id').val(project_id)
        });
    });

// +++++++++++++++++++++++++++++++++++romove compare page ++++++++++++++++++++

    $( ".remove_from_compate_list" ).on("click", function() {
        $('#supplier_bid_data').remove();
    });

// +++++++++++++++++++++++++++++++++++romove compare page end ++++++++++++++++
    // Code By Webdevtrick ( https://webdevtrick.com )
    const items = document.querySelectorAll(".accordion a");
     
    function toggleAccordion(){
      this.classList.toggle('active');
      this.nextElementSibling.classList.toggle('active');
    }
     
    items.forEach(item => item.addEventListener('click', toggleAccordion));

    // ++++++++++++++ INPROGRESS PART +++++++++++++++++++++++++
      var inprogress_trs = $("#supplier_recent_bid_view tr#supplier_review_inprogress_border");
      var btnmore_inprogress = $("#supplier_inprogress_show_more");
      var btnlessinprogress = $("#supplier_inprogress_show_less");
      var inprogress_trsLength = inprogress_trs.length;
      var currentindexinprogress = 5;

      inprogress_trs.hide();
      inprogress_trs.slice(0, 5).show(); 
      var start_inprogress = 0; 
      var end_inprogress = currentindexinprogress;

      btnmore_inprogress.click(function (e) { 
          e.preventDefault();

          $("#supplier_recent_bid_view tr#supplier_review_inprogress_border").slice(start_inprogress, end_inprogress).hide();
          $("#supplier_recent_bid_view tr#supplier_review_inprogress_border").slice(currentindexinprogress, currentindexinprogress + 5).show();
          start_inprogress = end_inprogress
          end_inprogress = currentindexinprogress += 5
      });

      btnlessinprogress.click(function (e) {
          e.preventDefault();
              inprogress_trs.slice(0,inprogress_trsLength).hide();
              $("#supplier_recent_bid_view tr#supplier_review_inprogress_border").slice(inprogress_trsLength - 5, inprogress_trsLength).show()
              $("#supplier_recent_bid_view tr#supplier_review_inprogress_border").slice(inprogress_trsLength + 5, inprogress_trsLength).hide()
              
          });

        // ++++++++++++++ INPROGRESS PART END +++++++++++++++++++++++++

        // ++++++++++++++ VIEW ALL PAGE ++++++++++++++++++++++++++=
        var bid = $("#supplier_recent_bid_view tr.supplier_review_border");
        var view_all = $("#recent_view_dash_project");
        var view_less = $("#recent_view_dash_project_less");
        var bidLength = bid.length;
        var currentIndexbid = bidLength;

        bid.hide();
        bid.slice(0, 5).show(); 
        view_less.hide()
        view_all.click(function (e) { 
          e.preventDefault();
          $("#supplier_recent_bid_view tr.supplier_review_border").slice(0,currentIndexbid).show();
            view_all.hide()
            view_less.show()
        });

        view_less.click(function (e) { 
          e.preventDefault();
          $("#supplier_recent_bid_view tr.supplier_review_border").slice(0,bidLength).hide();
          bid.slice(0,bidLength).hide();
          bid.slice(0, 5).show()
          view_less.hide()
          view_all.show()
        });

        // ++++++++++++++ VIEW ALL END ++++++++++++++++++++++++++=

        // ++++++++++++++++ SUPPLIER RESENT BID +++++++++++++++
        var sup_bid = $(".project_recent_bids #supplier_project_name_recent_bid");
        var view_all_supplier = $("#view_all_supplier");
        var view_less_supplier = $("#view_less_supplier");
        var bidLength_supplier = sup_bid.length;
        var currentIndexsupbid = bidLength_supplier;

        sup_bid.hide();
        sup_bid.slice(0, 5).show(); 
        view_less_supplier.hide()
        view_all_supplier.click(function (e) { 
          e.preventDefault();
          $(".project_recent_bids #supplier_project_name_recent_bid").slice(0,currentIndexsupbid).show();
            view_all_supplier.hide()
            view_less_supplier.show()
        });

        view_less_supplier.click(function (e) { 
          e.preventDefault();
          $(".project_recent_bids #supplier_project_name_recent_bid").slice(0,bidLength_supplier).hide();
          sup_bid.slice(0,bidLength_supplier).hide();
          sup_bid.slice(0, 5).show()
          view_less_supplier.hide()
          view_all_supplier.show()
        });
        // ++++++++++++++++ SUPPLIER RESENT BID END +++++++++++++++

        // =================== INSTALLER OPEN STATE ++++++++++++++++++
        var bid_open = $(".supplier_recent_bid_view_open tr.supplier_review_open_border");
        var view_all_open = $("#recent_view_dash_project_open");
        var view_less_open = $("#recent_view_dash_project_less_open");
        var bidLength = bid_open.length;
        var currentIndexbid = bidLength;

        bid_open.hide();
        bid_open.slice(0, 5).show(); 
        view_less_open.hide()
        view_all_open.click(function (e) { 
          e.preventDefault();
          $(".supplier_recent_bid_view_open tr.supplier_review_open_border").slice(0,currentIndexbid).show();
            view_all_open.hide()
            view_less_open.show()
        });

        view_less_open.click(function (e) { 
          e.preventDefault();
          $(".supplier_recent_bid_view_open tr.supplier_review_open_border").slice(0,bidLength).hide();
          bid_open.slice(0,bidLength).hide();
          bid_open.slice(0, 5).show()
          view_less_open.hide()
          view_all_open.show()
        });
        // =================== INSTALLER OPEN STATE end ++++++++++++++++++

        // =============  INSTALLER INPROGRESS +++++++++++++++

        var bid_inprogress = $(".supplier_recent_bid_view_inprogres tr.supplier_review_inprogress_border");
        var view_all_inprogress = $("#recent_view_dash_project_open_inp");
        var view_less_inprogress = $("#recent_view_dash_project_less_inp");
        var bidLength = bid_inprogress.length;
        var currentIndexbid = bidLength;

        bid_inprogress.hide();
        bid_inprogress.slice(0, 5).show(); 
        view_less_inprogress.hide()
        view_all_inprogress.click(function (e) { 
          e.preventDefault();
          $(".supplier_recent_bid_view_inprogres tr.supplier_review_inprogress_border").slice(0,currentIndexbid).show();
            view_all_inprogress.hide()
            view_less_inprogress.show()
        });

        view_less_inprogress.click(function (e) { 
          e.preventDefault();
          $(".supplier_recent_bid_view_inprogres tr.supplier_review_inprogress_border").slice(0,bidLength).hide();
          bid_inprogress.slice(0,bidLength).hide();
          bid_inprogress.slice(0, 5).show()
          view_less_inprogress.hide()
          view_all_inprogress.show()
        });
        // =============  INSTALLER INPROGRESS END +++++++++++++++

    $("#login_sign").on('input', function() {
      // alert( "Handler for .change() called." );
      var txt_len = $(this).val().length;

      var email = document.getElementById('login_sign');
      var filter = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/;

      if (!filter.test(email.value))
      // if(txt_len == 0)
      {
        $('#email_verify').prop('disabled', true);
        
      }else{
        $('#email_verify').prop('disabled', false);
      }
  
    });
    
    $('input[name="current_paswd"]').on('change',function(e){
       var val=$(this).val()
       var old=$(this).data('current')
       
       if(val != old){
         $('#current_paswd_id').css('display','')
         $('#update_paswd').prop('disabled', true);
       }else{
         $('#current_paswd_id').css('display','none')
          $('#update_paswd').prop('disabled', false);
       }
    })
    $("#phone_no_sign").on('input', function() {
      // alert( "Handler for .change() called." );
      var mobile_len = $(this).val().length;
      if(mobile_len == 10)
      {
        $('#mobile_no_verify').prop('disabled', false);
      }else{
        $('#mobile_no_verify').prop('disabled', true);
      }
  
    });


    const passwordField = document.querySelector("#password_sign");
    const eyeIcon= document.querySelector("#eye");

    eyeIcon.addEventListener("click", function(){
      this.classList.toggle("fa-eye-slash");
      const type = passwordField.getAttribute("type") === "password" ? "text" : "password";
      passwordField.setAttribute("type", type);
    
    });
    
    const confirmpasswordField = document.querySelector("#confirm_password");
    const eyeIconc= document.querySelector("#eyec");

    eyeIconc.addEventListener("click", function(){
      this.classList.toggle("fa-eye-slash");
      const type = confirmpasswordField.getAttribute("type") === "password" ? "text" : "password";
      confirmpasswordField.setAttribute("type", type);
      
    });

});