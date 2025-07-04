odoo.define('airbid_master.area_operates', function (require) {
  'use strict';
    
    var ajax = require('web.ajax');
  
    $(document).ready(function () {
      $("#add_area_operates").on( "click", function() {
        var count = $("#area_operates_counter").val()
        count = parseInt(count)+1
        var area_operates_city = "area_operates_city"+String(count)
        var redius_profile = "redius_profile"+String(count)
        var zip_code_no = "zip_code_no"+String(count)
        var delete_icon = "delete_icon"+String(count)
        var area_operates_remove = "area_operates_remove"+String(count)
        var button_data  = String(count)
        $(this).before("<div class='area_operates_remove'><div id='field_2' class='column col-sm-3'><label id='user_detail_labels'>City<span style='color: red; padding-left: 6px;'>*</span></label><input type='text' id='" +area_operates_city+"' name='" +area_operates_city+"' class='form-control form-control-md profile_detail_supplier' t-att-value='request.env.user.city_area' required='required' /></div><div id='field_2' class='column col-sm-3'><label id='user_detail_labels'>Postcode<span style='color: red; padding-left: 6px;'>*</span></label><input type='text' id='"+zip_code_no+"' name='"+zip_code_no+"' class='form-control form-control-md profile_detail_supplier number_input_only' t-att-value='rec.zip_code' required='required' minlength='4' maxlength='4' /></div><div id='field_2' class='column col-sm-3'><label id='user_detail_labels'>Radius<span style='color: red; padding-left: 6px;'>*</span></label><input type='text' id='" +redius_profile+"' name='" +redius_profile+"' class='form-control form-control-md profile_detail_supplier' t-att-value='request.env.user.radius' required='required' /><span class='km'>KM<span style='font-size: 10px;'>S</span></span></div><div id='field_2' class='column col-sm-3'><img src='/airbid_master/static/src/image/delete.png' class='delete_icon' id='delete_icon' name='" +delete_icon+"'></img></div><input type='checkbox' id='is_saved"+count+"' t-attf-name='is_saved"+count+"' hidden='hidden'/></div>")
        $("#area_operates_counter").val(count)

        $('.area_operates_remove').on('click', '#delete_icon', function()
        {
           $(this).closest('div.area_operates_remove').remove();
           var count = $("#area_operates_counter").val()
        });
      })

      $('.area_operates_remove').on('click', '#delete_icon_area', function()
        {
           $(this).closest('div.area_operates_remove').remove();
           var count = $("#area_operates_counter").val()
          //  count -= 1
        });

      $(".remove_area_operates").on("click",function(){
        $('.area_operates_remove:last').remove()
        var count = $("#area_operates_counter").val()
        count = parseInt(count)-1
        var button_data  = String(count)
        $("#area_operates_counter").val(count)
      }); 
    })

     $("#myBtn").click(function(){
         $('#myModal').modal('show');
    });

     $(".publishpro").click(function(){
         $('#publishModal').modal('show');
         $('.modal-backdrop').removeClass('show');
      });
     
     $('#publishModal').on('click', '.close', function(){
          $('#publishModal').modal('hide');
      });
     
     $('.bid_btn').click(function(){
        $('#bidModal').modal('show');
        $('.modal-backdrop').removeClass('show');
     })

     $('#bidModal').on('click', '.close', function(){
          $('#bidModal').modal('hide');
        });
     $('img[class="house_images"]').click(function(e){
         $('#ImgModal').modal('show');
         var modalImg = document.getElementById("img01");
         modalImg.src = this.src;
         $('#ImgModal .modal-title').text(this.alt)
         $('.modal-backdrop').removeClass('show');
         var panzoom = Panzoom(document.querySelector(".image--zoom"), {
          maxScale: 6
        });
        document.querySelector(".image--zoom").addEventListener("wheel", panzoom.zoomWithWheel);
         
      });
      $('#ImgModal').on('click', '.close', function(){
          $('#ImgModal').modal('hide');
      });
  });