(function ($) {
  $(document).ready(function () {

    function readURL() {
        var $input = $(this);
        var $newinput =  $(this).parent().parent().parent().find('.portimg');
        if (this.files && this.files[0]) {
            var reader = new FileReader();
            reader.onload = function (e) {
                // reset($newinput.next('.delbtn'), true);
                $newinput.attr('src', e.target.result).show();
                // $newinput.after('<input type="button" class="delbtn removebtn" id="delete_btn" value="remove"/>');
                $('#profile_img_default').hide();
                $('#profile_img').hide();
                $('input[name="is_detele"]').val(false)
                // reset($newinput.next('.delbtn'), false);
                // $newinput.after('<i id="clean" class="fa fa-trash delbtn removebtn" value="remove"/>');
            }
            reader.readAsDataURL(this.files[0]);
        }
    }
    $(".fileUpload").change(readURL);

    $("form").on('click', '#clean', function (e) {
        $('.portimg').attr('src', '').hide();
        $('.portimg').attr('src', '').remove();
        $('#profile_img').attr('src', '').hide();
        $('#profile_img').attr('src', '').remove();
        $('#delete_btn').hide();
        $('#profile_img_default').removeClass('hidden')
        $('#profile_img_default').css('display','inherit')
        $('#profile_img').hide();
        $('input.fileUpload').val("");
        $('#profile_edit_view').val("");
        $('input[name="is_detele"]').val(true)
    });

    if($('#house_visible').is(":visible")){
      $('#house_attachment').prop("required", false);
    }

    if($('#inverter_wall_visible').is(":visible")){
      $('#inverter_wall').prop("required", false);
    }

    if($('#roof_visible').is(":visible")){
      $('#image_of_roof').prop("required", false);
    }
    
    if($('#meter_box_visible').is(":visible")){
      $('#image_of_meter_box').prop("required", false);
    }
    
    if($('#electricity_bill_visible').is(":visible")){
      $('#image_of_electricity_bill').prop("required", false);
    }
    
    if($('#meter_box_2_visible').is(":visible")){
      $('#meter_box_2').prop("required", false);
    }
    
    // ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    updateList = function(e) {
      var input = document.getElementById('cec_retailer');
      var output = document.getElementById('fileList');
      document.getElementById("fileList").style.display = "none";
      output.innerHTML = '<ul id="input_name_ul">';
      for (var i = 0; i < input.files.length; ++i) {
        output.innerHTML += '<li id="input_name">' + input.files.item(i).name + '</li>';
        output.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" class="delete_certificate" id="delete_certificate"></img>'
        $( "#input_name_value" ).val(input.files.item(i).name);  
      }
      output.innerHTML += '</ul>';
      document.getElementById("fileList").style.display = "block";

      $("#delete_certificate").click(function() {
        document.getElementById("input_name").style.display = "none";
        document.getElementById("input_name_ul").style.display = "none";
        document.getElementById("delete_certificate").style.display = "none";
        document.getElementById("cec_retailer").value = "";
        document.getElementById("input_name_value").value = "";
        document.getElementById("input_name").value = "";
        document.getElementById("fileList").style.display = "none";
        // $("#fileList").append('<input type="text" placeholder="Certificate1.pdf" class="attchment_photo" id="attchment_photo" readonly="readonly"/>');
      });
    }


    cecmemberteList = function() {
      var redius_profile = document.getElementById('cec_member');
      var redius_profile_list = document.getElementById('redius_profile_list');
      document.getElementById("redius_profile_list").style.display = "none";
      redius_profile_list.innerHTML = '<ul id="input_name_ul_1">';
      for (var i = 0; i < redius_profile.files.length; ++i) {
        redius_profile_list.innerHTML += '<li id="input_name_1">' + redius_profile.files.item(i).name + '</li>';
        redius_profile_list.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" id="delete_certificate_1" class="delete_certificate"></img>'
        $( "#member_name" ).val(redius_profile.files.item(i).name);
      }
      redius_profile_list.innerHTML += '</ul>';
      document.getElementById("redius_profile_list").style.display = "block";

      $("#delete_certificate_1").click(function() {
        document.getElementById("input_name_1").style.display = "none";
        document.getElementById("input_name_ul_1").style.display = "none";
        document.getElementById("delete_certificate_1").style.display = "none";
        document.getElementById("cec_member").value = "";
        document.getElementById("member_name").value = "";
        document.getElementById("input_name_1").value = "";
        document.getElementById("redius_profile_list").style.display = "none";

        // $("#redius_profile_list").append('<input type="text" placeholder="Certificate1.pdf" class="attchment_photo" id="attchment_photo" readonly="readonly"/>');
      });
    }

    ios_certificationList = function() {
      var ios_certification = document.getElementById('ios_certification');
      var ios_certification_list = document.getElementById('ios_certification_list');
      document.getElementById("ios_certification_list").style.display = "none";
      ios_certification_list.innerHTML = '<ul id="input_name_ul_2">';
      for (var i = 0; i < ios_certification.files.length; ++i) {
        ios_certification_list.innerHTML += '<li id="input_name_2">' + ios_certification.files.item(i).name + '</li>';
        ios_certification_list.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" id="delete_certificate_2" class="delete_certificate"></img>'
        $( "#iso_name" ).val(ios_certification.files.item(i).name);
      }
      ios_certification_list.innerHTML += '</ul>';
      document.getElementById("ios_certification_list").style.display = "block";

      $("#delete_certificate_2").click(function() {
        document.getElementById("input_name_2").style.display = "none";
        document.getElementById("input_name_ul_2").style.display = "none";
        document.getElementById("delete_certificate_2").style.display = "none";
        document.getElementById("ios_certification").value = "";
        document.getElementById("iso_name").value = "";
        document.getElementById("input_name_2").value = "";
        document.getElementById("ios_certification_list").style.display = "none";
        // $("#ios_certification_list").append('<input type="text" placeholder="Certificate1.pdf" class="attchment_photo" id="attchment_photo" readonly="readonly"/>');
      });
    }

    other_certificationList = function() {
      var other_certification = document.getElementById('other_certification');
      var other_certification_list = document.getElementById('other_certification_list');
      document.getElementById("other_certification_list").style.display = "none";
      other_certification_list.innerHTML = '<ul id="input_name_ul_3">';
      for (var i = 0; i < other_certification.files.length; ++i) {
        other_certification_list.innerHTML += '<li id="input_name_3">' + other_certification.files.item(i).name + '</li>';
        other_certification_list.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" id="delete_certificate_3" class="delete_certificate"></img>'
        $( "#document_name" ).val(other_certification.files.item(i).name);
      }
      document.getElementById("other_certification_list").style.display = "block";
      $("#delete_certificate_3").click(function() {
        document.getElementById("input_name_3").style.display = "none";
        document.getElementById("input_name_ul_3").style.display = "none";
        document.getElementById("delete_certificate_3").style.display = "none";
        document.getElementById("other_certification").value = "";
        document.getElementById("document_name").value = "";
        document.getElementById("input_name_3").value = "";
        document.getElementById("other_certification_list").style.display = "none";
        // $("#other_certification_list").append('<input type="text" placeholder="Certificate1.pdf" class="attchment_photo" id="attchment_photo" readonly="readonly"/>');
      });
    }


    company_logo = function() {
      console.log("44444444444444444444444444444")
      var comapany_logo = document.getElementById('comapany_logo');
      var profile_company = document.getElementById('profile_company');

      profile_company.innerHTML = '<ul id="company_logo_attchment_ul">';
      for (var i = 0; i < comapany_logo.files.length; ++i) {
        profile_company.innerHTML += '<li id="company_logo_attchment">' + comapany_logo.files.item(i).name + '</li>';
        profile_company.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" id="delete_company_logo" class="delete_certificate"></img>'
        $( "#company_logo_name" ).val(comapany_logo.files.item(i).name);
      }
      // document.getElementById("company_logo_hide").style.display = "none";
      document.getElementById("attchment_company_name").style.display = "none";
      document.getElementById("profile_company").style.display = "block";                                        
      $("#delete_company_logo").click(function() {
        document.getElementById("company_logo_hide").style.display = "block";
        document.getElementById("profile_company").style.display = "none";
        document.getElementById("comapany_logo").value = "";
        document.getElementById("company_logo_name").value = "";
      });
    }

    company_photo_logo = function() {
      console.log("3333333333333333")
      var directors_photo = document.getElementById('directors_photo');
      var profile_company_photo = document.getElementById('profile_company_photo');

      profile_company_photo.innerHTML = '<ul id="company_photo_attchment_ul">';
      for (var i = 0; i < directors_photo.files.length; ++i) {
        profile_company_photo.innerHTML += '<li id="company_photo_attchment">' + directors_photo.files.item(i).name + '</li>';
        profile_company_photo.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" id="delete_company_photo" class="delete_certificate"></img>'
        $( "#company_photo_name" ).val(directors_photo.files.item(i).name);
      }
      document.getElementById("attchment_photo_name").style.display = "none";
      document.getElementById("profile_company_photo").style.display = "block";
      $("#delete_company_photo").click(function() {
        document.getElementById("company_photo_hide").style.display = "block";
        document.getElementById("profile_company_photo").style.display = "none";
        document.getElementById("directors_photo").value = "";
        document.getElementById("company_photo_name").value = "";
      });
    }

    // ++++++++++++ NEW HOUSE CODE +++++++++++++++++

    uploadimagehouse = function(e) {
      console.log("22222222222222222222222222222222======>",e)
      var house_attachment = document.getElementById('house_attachment');
      var house_attachment_file = document.getElementById('house_attachment_file');

      house_attachment_file.innerHTML = '<ul id="house_name_ul">';
      for (var i = 0; i < house_attachment.files.length; ++i) {
        house_attachment_file.innerHTML += '<img id="house_att_img" src="#" />';
        house_attachment_file.innerHTML += '<li id="house_input_name">' + house_attachment.files.item(i).name + '</li>';
        house_attachment_file.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" class="delete_certificate_house" id="house_delete_certificate"></img>'
        $( "#house_name" ).val(house_attachment.files.item(i).name);
      }
      house_attachment_file.innerHTML += '</ul>';  
      
      document.getElementById("house_attachment_file").style.border = "1px solid #D1D9E3;";
      var house_attachment = document.getElementById("house_attachment")

      if (house_attachment.files && house_attachment.files[0]) {
          var reader = new FileReader();
          reader.onload = function (e) {
              $('#house_att_img').attr('src', e.target.result);
          };
          reader.readAsDataURL(house_attachment.files[0]);
      }

      if (document.getElementById("house_image_name") != undefined){ 
        document.getElementById("house_image_name").style.display = "none";
        document.getElementById("house_image").style.display = "none";
      }

      $("#house_delete_certificate").click(function() {
        document.getElementById("house_att_img").style.display = "none";
        document.getElementById("house_input_name").style.display = "none";
        document.getElementById("house_name_ul").style.display = "none";
        document.getElementById("house_delete_certificate").style.display = "none";
        document.getElementById("house_attachment").value = "";
        document.getElementById("house_name").value = "";
        // $("#house_attachment_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });
    }
    $("#house_delete_certificate").click(function() {
        document.getElementById("house_image_name").style.display = "none";
        document.getElementById("house_image").style.display = "none";
        document.getElementById("house_delete_certificate").style.display = "none";
       
        // $("#house_attachment_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });

    // ++++ ROOF +++++++++++
    uploadimageroof = function(e) {
      var image_of_roof = document.getElementById('image_of_roof');
      var roof_attachment_file = document.getElementById('roof_attachment_file');

      roof_attachment_file.innerHTML = '<ul id="roof_house_name_ul">';
      for (var i = 0; i < image_of_roof.files.length; ++i) {
        roof_attachment_file.innerHTML += '<img id="roof_att_img" src="#" />';
        roof_attachment_file.innerHTML += '<li id="roof_house_input_name">' + image_of_roof.files.item(i).name + '</li>';
        roof_attachment_file.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" class="delete_certificate_house" id="roof_delete_certificate"></img>'
        $( "#roof_name" ).val(image_of_roof.files.item(i).name);
      }
      roof_attachment_file.innerHTML += '</ul>';  
      
      // document.getElementById("roof_house_name_ul").style.display = "none";
      var image_of_roof = document.getElementById("image_of_roof")

      if (image_of_roof.files && image_of_roof.files[0]) {
          var reader = new FileReader();
          reader.onload = function (e) {
              $('#roof_att_img').attr('src', e.target.result);
          };
          reader.readAsDataURL(image_of_roof.files[0]);
      }
      if (document.getElementById("roof_img") != undefined){ 
        document.getElementById("roof_img").style.display = "none";
        document.getElementById("roof_img_name").style.display = "none";
      }
      $("#roof_delete_certificate").click(function() {
        document.getElementById("roof_att_img").style.display = "none";
        document.getElementById("roof_house_input_name").style.display = "none";
        document.getElementById("roof_house_name_ul").style.display = "none";
        document.getElementById("roof_delete_certificate").style.display = "none";
        document.getElementById("image_of_roof").value = "";
        document.getElementById("roof_name").value = "";
        // $("#roof_attachment_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });
    }
    $("#roof_delete_certificate").click(function() {
        document.getElementById("roof_img").style.display = "none";
        document.getElementById("roof_img_name").style.display = "none";
        document.getElementById("roof_delete_certificate").style.display = "none";
        // $("#roof_attachment_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });

    uploadimageinverter = function(e) {
      var inverter_wall = document.getElementById('inverter_wall');
      var inverter_attachment_file = document.getElementById('inverter_attachment_file');

      inverter_attachment_file.innerHTML = '<ul id="inverter_house_name_ul">';
      for (var i = 0; i < inverter_wall.files.length; ++i) {
        inverter_attachment_file.innerHTML += '<img id="inverter_att_img" src="#" />';
        inverter_attachment_file.innerHTML += '<li id="inverter_house_input_name">' + inverter_wall.files.item(i).name + '</li>';
        inverter_attachment_file.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" class="delete_certificate_house" id="inverter_delete_certificate"></img>'
        $( "#inverter_wall_name" ).val(inverter_wall.files.item(i).name);
      }
      inverter_attachment_file.innerHTML += '</ul>';  
      
      var inverter_wall = document.getElementById("inverter_wall")

      if (inverter_wall.files && inverter_wall.files[0]) {
          var reader = new FileReader();
          reader.onload = function (e) {
              $('#inverter_att_img').attr('src', e.target.result);
          };
          reader.readAsDataURL(inverter_wall.files[0]);
      }

      if (document.getElementById("inverter_img") != undefined){
        document.getElementById("inverter_img").style.display = "none";
        document.getElementById("inverter_img_name").style.display = "none";
      }
      $("#inverter_delete_certificate").click(function() {
        document.getElementById("inverter_att_img").style.display = "none";
        document.getElementById("inverter_house_input_name").style.display = "none";
        document.getElementById("inverter_house_name_ul").style.display = "none";
        document.getElementById("inverter_delete_certificate").style.display = "none";
        document.getElementById("inverter_wall").value = "";
        document.getElementById("inverter_wall_name").value = "";
      });
    }

    image_of_meter_box_filelist = function(e) {
      var image_of_meter_box = document.getElementById('image_of_meter_box');
      var image_of_meter_box_file = document.getElementById('image_of_meter_box_file');

      image_of_meter_box_file.innerHTML = '<ul id="meter_house_name_ul">';
      for (var i = 0; i < image_of_meter_box.files.length; ++i) {
        image_of_meter_box_file.innerHTML += '<img id="meter_box_att_img" src="#" />';
        image_of_meter_box_file.innerHTML += '<li id="meter_house_input_name">' + image_of_meter_box.files.item(i).name + '</li>';
        image_of_meter_box_file.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" class="delete_certificate_house" id="meter_box_delete_certificate"></img>'
        $( "#meter_name" ).val(image_of_meter_box.files.item(i).name);
      }
      image_of_meter_box_file.innerHTML += '</ul>';  
      
      // document.getElementById("meter_house_name_ul").style.display = "none";
      var image_of_meter_box = document.getElementById("image_of_meter_box")

      if (image_of_meter_box.files && image_of_meter_box.files[0]) {
          var reader = new FileReader();
          reader.onload = function (e) {
              $('#meter_box_att_img').attr('src', e.target.result);
          };
          reader.readAsDataURL(image_of_meter_box.files[0]);
      }
      if (document.getElementById("meter_img") != undefined){ 
          document.getElementById("meter_img").style.display = "none";
          document.getElementById("meter_img_name").style.display = "none";
      }

      $("#meter_box_delete_certificate").click(function() {
        document.getElementById("meter_box_att_img").style.display = "none";
        document.getElementById("meter_house_input_name").style.display = "none";
        document.getElementById("meter_house_name_ul").style.display = "none";
        document.getElementById("meter_box_delete_certificate").style.display = "none";
        document.getElementById("image_of_meter_box").value = "";
        document.getElementById("meter_name").value = "";
        // $("#image_of_meter_box_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });
    }
     $("#meter_box_delete_certificate").click(function() {
        document.getElementById("meter_img").style.display = "none";
          document.getElementById("meter_img_name").style.display = "none";
        document.getElementById("meter_box_delete_certificate").style.display = "none";
       
        // $("#image_of_meter_box_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });

    image_of_meter_box_zoomin=function (e) {
      console.log("88888888888888888888888888888888888")
       var meter_zoomin = document.getElementById('meter_zoomin');

      var image_of_meter_box_file = document.getElementById('image_of_meter_zoomin');

      image_of_meter_box_file.innerHTML = '<ul id="meter_house_name_ul_zoomin">';
      for (var i = 0; i < meter_zoomin.files.length; ++i) {
        image_of_meter_box_file.innerHTML += '<img id="meter_box_att_img_zoomin" src="#" />';
        image_of_meter_box_file.innerHTML += '<li id="meter_house_input_zoomin_name">' + meter_zoomin.files.item(i).name + '</li>';
        image_of_meter_box_file.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" class="delete_certificate_house" id="meter_box_delete_certificate_in"></img>'
        $( "#meter_zoomin_input" ).val(meter_zoomin.files.item(i).name);
      }
      image_of_meter_box_file.innerHTML += '</ul>';  
      
      // document.getElementById("meter_house_name_ul").style.display = "none";
      var meter_zoomin = document.getElementById("meter_zoomin")

      if (meter_zoomin.files && meter_zoomin.files[0]) {
          var reader = new FileReader();
          reader.onload = function (e) {
              $('#meter_box_att_img_zoomin').attr('src', e.target.result);
          };
          reader.readAsDataURL(meter_zoomin.files[0]);
      }
      if (document.getElementById("meter_in_img") != undefined){ 
          document.getElementById("meter_in_img").style.display = "none";
          document.getElementById("meter_img_in_name").style.display = "none";
      }

      $("#meter_box_delete_certificate_in").click(function() {
        console.log("ddddddddddddddddddddddd")
        document.getElementById("meter_box_att_img_zoomin").style.display = "none";
        document.getElementById("meter_house_input_zoomin_name").style.display = "none";
        document.getElementById("meter_house_name_ul_zoomin").style.display = "none";
        document.getElementById("meter_box_delete_certificate_in").style.display = "none";
        document.getElementById("meter_zoomin").value = "";
        document.getElementById("meter_zoomin_input").value = "";
        // $("#image_of_meter_box_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });
    }
    $("#meter_box_delete_certificate_in").click(function() {
        console.log("mmmmmmm''''''----------")
        document.getElementById("meter_in_img").style.display = "none";
          document.getElementById("meter_img_in_name").style.display = "none";
        document.getElementById("meter_box_delete_certificate_in").style.display = "none";
       
        // $("#image_of_meter_box_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });

    image_of_meter_box_zoomout=function (e) {
      console.log("999999999999999999999999")
       var meter_zoomout = document.getElementById('meter_zoomout');
       
      var image_of_meter_box_file = document.getElementById('image_of_meter_zoomout');

      image_of_meter_box_file.innerHTML = '<ul id="meter_house_name_ul_zoomout">';
      for (var i = 0; i < meter_zoomout.files.length; ++i) {
        image_of_meter_box_file.innerHTML += '<img id="meter_box_att_img_zoomout" src="#" />';
        image_of_meter_box_file.innerHTML += '<li id="meter_house_input_zoomout_name">' + meter_zoomout.files.item(i).name + '</li>';
        image_of_meter_box_file.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" class="delete_certificate_house" id="meter_box_delete_certificate_out"></img>'
        $( "#meter_zoomout_input" ).val(meter_zoomout.files.item(i).name);
      }
      image_of_meter_box_file.innerHTML += '</ul>';  
      
      // document.getElementById("meter_house_name_ul").style.display = "none";
      var meter_zoomout = document.getElementById("meter_zoomout")

      if (meter_zoomout.files && meter_zoomout.files[0]) {
          var reader = new FileReader();
          reader.onload = function (e) {
              $('#meter_box_att_img_zoomout').attr('src', e.target.result);
          };
          reader.readAsDataURL(meter_zoomout.files[0]);
      }
      if (document.getElementById("meter_out_img") != undefined){ 
          document.getElementById("meter_out_img").style.display = "none";
          document.getElementById("meter_img_name_out").style.display = "none";
      }

      $("#meter_box_delete_certificate_out").click(function() {
        document.getElementById("meter_box_att_img_zoomout").style.display = "none";
        document.getElementById("meter_house_input_zoomout_name").style.display = "none";
        document.getElementById("meter_house_name_ul_zoomout").style.display = "none";
        document.getElementById("meter_box_delete_certificate_out").style.display = "none";
        document.getElementById("meter_zoomout").value = "";
        document.getElementById("meter_zoomout_input").value = "";
        // $("#image_of_meter_box_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });
    }
    $("#meter_box_delete_certificate_out").click(function() {
        document.getElementById("meter_out_img").style.display = "none";
        document.getElementById("meter_img_name_out").style.display = "none";
        document.getElementById("meter_box_delete_certificate_out").style.display = "none";
        
        // $("#image_of_meter_box_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });
    
    meter_box_wall_pic_fun=function (e) {
      console.log("999999999999999999999999ssssss")
       var meter_box_wall_pic = document.getElementById('meter_box_wall_pic');
       
      var image_of_meter_box_file = document.getElementById('image_of_meter_box_wall_pic');

      image_of_meter_box_file.innerHTML = '<ul id="meter_house_name_ul_box_wall">';
      for (var i = 0; i < meter_box_wall_pic.files.length; ++i) {
        image_of_meter_box_file.innerHTML += '<img id="meter_box_att_img_box_wall" src="#" />';
        image_of_meter_box_file.innerHTML += '<li id="meter_house_input_boxwall_name">' + meter_box_wall_pic.files.item(i).name + '</li>';
        image_of_meter_box_file.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" class="delete_certificate_house" id="meter_box_delete_certificate_wall"></img>'
        $( "#meter_name_box_wall_pic" ).val(meter_box_wall_pic.files.item(i).name);
      }
      image_of_meter_box_file.innerHTML += '</ul>';  
      
      // document.getElementById("meter_house_name_ul").style.display = "none";
      var meter_box_wall_pic = document.getElementById("meter_box_wall_pic")

      if (meter_box_wall_pic.files && meter_box_wall_pic.files[0]) {
          var reader = new FileReader();
          reader.onload = function (e) {
              $('#meter_box_att_img_box_wall').attr('src', e.target.result);
          };
          reader.readAsDataURL(meter_box_wall_pic.files[0]);
      }
      if (document.getElementById("meter_img_wall") != undefined){ 
          document.getElementById("meter_img_wall").style.display = "none";
          document.getElementById("meter_img_name_wall").style.display = "none";
      }

      $("#meter_box_delete_certificate_wall").click(function() {
        document.getElementById("meter_box_att_img_box_wall").style.display = "none";
        document.getElementById("meter_house_input_boxwall_name").style.display = "none";
        document.getElementById("meter_house_name_ul_box_wall").style.display = "none";
        document.getElementById("meter_box_delete_certificate_wall").style.display = "none";
        document.getElementById("meter_box_wall_pic").value = "";
        document.getElementById("meter_name_box_wall_pic").value = "";
        // $("#image_of_meter_box_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });
    }
    $("#meter_box_delete_certificate_wall").click(function() {
      document.getElementById("meter_img_wall").style.display = "none";
      document.getElementById("meter_img_name_wall").style.display = "none";
      document.getElementById("meter_box_delete_certificate_wall").style.display = "none";
        // $("#image_of_meter_box_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });

    pic_battery_need_to_install=function (e) {
      console.log("9999999999999999ssssss99999999ssssss")
       var pic_battery_need = document.getElementById('pic_battery_need');
       
      var image_of_meter_box_file = document.getElementById('image_of_meter_battery_need');

      image_of_meter_box_file.innerHTML = '<ul id="meter_house_name_ul_box_battery">';
      for (var i = 0; i < pic_battery_need.files.length; ++i) {
        image_of_meter_box_file.innerHTML += '<img id="meter_box_att_img_box_battery" src="#" />';
        image_of_meter_box_file.innerHTML += '<li id="meter_house_input_battery_name">' + pic_battery_need.files.item(i).name + '</li>';
        image_of_meter_box_file.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" class="delete_certificate_house" id="meter_box_delete_certificate_install"></img>'
        $( "#pic_battery_need_input" ).val(pic_battery_need.files.item(i).name);
      }
      image_of_meter_box_file.innerHTML += '</ul>';  
      
      // document.getElementById("meter_house_name_ul").style.display = "none";
      var pic_battery_need = document.getElementById("pic_battery_need")

      if (pic_battery_need.files && pic_battery_need.files[0]) {
          var reader = new FileReader();
          reader.onload = function (e) {
              $('#meter_box_att_img_box_battery').attr('src', e.target.result);
          };
          reader.readAsDataURL(pic_battery_need.files[0]);
      }
      if (document.getElementById("meter_img_install") != undefined){ 
          document.getElementById("meter_img_install").style.display = "none";
          document.getElementById("meter_img_name_install").style.display = "none";
      }

      $("#meter_box_delete_certificate_install").click(function() {
        document.getElementById("meter_box_att_img_box_battery").style.display = "none";
        document.getElementById("meter_house_input_battery_name").style.display = "none";
        document.getElementById("meter_house_name_ul_box_battery").style.display = "none";
        document.getElementById("meter_box_delete_certificate_install").style.display = "none";
        document.getElementById("pic_battery_need").value = "";
        document.getElementById("pic_battery_need_input").value = "";
        // $("#image_of_meter_box_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });
    }
     $("#meter_box_delete_certificate_install").click(function() {
        document.getElementById("meter_img_install").style.display = "none";
        document.getElementById("meter_img_name_install").style.display = "none";
        document.getElementById("meter_box_delete_certificate_install").style.display = "none";
        // $("#image_of_meter_box_file").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });

    image_of_meter_box_2_filelist = function(e) {
      var meter_box_2 = document.getElementById('meter_box_2');
      var image_of_meter_box_2_file = document.getElementById('image_of_meter_box_2_file');

      image_of_meter_box_2_file.innerHTML = '<ul id="meter_box2_name_ul">';
      for (var i = 0; i < meter_box_2.files.length; ++i) {
        image_of_meter_box_2_file.innerHTML += '<img id="meter_box_2_att_img" src="#" />';
        image_of_meter_box_2_file.innerHTML += '<li id="meter_house_2_input_name">' + meter_box_2.files.item(i).name + '</li>';
        image_of_meter_box_2_file.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" class="delete_certificate_house" id="meter_box_2_delete_certificate"></img>'
        $( "#meter_box_2_name" ).val(meter_box_2.files.item(i).name);
      }
      image_of_meter_box_2_file.innerHTML += '</ul>';  
      
      var meter_box_2 = document.getElementById("meter_box_2")

      if (meter_box_2.files && meter_box_2.files[0]) {
          var reader = new FileReader();
          reader.onload = function (e) {
              $('#meter_box_2_att_img').attr('src', e.target.result);
          };
          reader.readAsDataURL(meter_box_2.files[0]);
      }
      if (document.getElementById("meter2_img") != undefined){
        document.getElementById("meter2_img").style.display = "none";
        document.getElementById("meter2_img_name").style.display = "none";
      }

      $("#meter_box_2_delete_certificate").click(function() {
        document.getElementById("meter_box_2_att_img").style.display = "none";
        document.getElementById("meter_house_2_input_name").style.display = "none";
        document.getElementById("meter_box2_name_ul").style.display = "none";
        document.getElementById("meter_box_2_delete_certificate").style.display = "none";
        document.getElementById("meter_box_2").value = "";
        document.getElementById("meter_box_2_name").value = "";
      });
    }

    image_of_electricity_billlist = function(e) {
      var image_of_electricity_bill = document.getElementById('image_of_electricity_bill');
      var image_of_electricity_bill_list = document.getElementById('image_of_electricity_bill_list');

      image_of_electricity_bill_list.innerHTML = '<ul id="electricity_bill_house_name_ul">';
      for (var i = 0; i < image_of_electricity_bill.files.length; ++i) {
        image_of_electricity_bill_list.innerHTML += '<img id="electricity_bill_att_img" src="#" />';
        image_of_electricity_bill_list.innerHTML += '<li id="electricity_bill_house_input_name">' + image_of_electricity_bill.files.item(i).name + '</li>';
        image_of_electricity_bill_list.innerHTML += '<img src="/airbid_master/static/src/image/delete.png" class="delete_certificate_house" id="electricity_bill_delete_certificate"></img>'
        $( "#electricity_bill_name" ).val(image_of_electricity_bill.files.item(i).name);
      }
      image_of_electricity_bill_list.innerHTML += '</ul>';  
      
      document.getElementById("house_attachment_file").style.display = "block";
      var image_of_electricity_bill = document.getElementById("image_of_electricity_bill")

      if (image_of_electricity_bill.files && image_of_electricity_bill.files[0]) {
          var reader = new FileReader();
          reader.onload = function (e) {
              $('#electricity_bill_att_img').attr('src', e.target.result);
          };
          reader.readAsDataURL(image_of_electricity_bill.files[0]);
      }
      if (document.getElementById("electricity_img") != undefined){
        document.getElementById("electricity_img").style.display = "none";
        document.getElementById("electricity_img_name").style.display = "none";
      }

      $("#electricity_bill_delete_certificate").click(function() {
        document.getElementById("electricity_bill_att_img").style.display = "none";
        document.getElementById("electricity_bill_house_input_name").style.display = "none";
        document.getElementById("electricity_bill_house_name_ul").style.display = "none";
        document.getElementById("electricity_bill_delete_certificate").style.display = "none";
        document.getElementById("image_of_electricity_bill").value = "";
        document.getElementById("electricity_bill_name").value = "";
        // $("#image_of_electricity_bill_list").append('<input type="text" placeholder="House.png" class="attchment_photo_1" id="attchment_photo" readonly="readonly"/>');
      });
    }
    // ++++++++++++ NEW HOUSE CODE END +++++++++++++++++
    
    // MULTIPLE FILE NAME ++++++++++++++++++++++++
    multiple_files = function() {
      var input = document.getElementById('attchment_photo_multi');
      var output = document.getElementById('fileList');

      output.innerHTML = '<ul>';
      for (var i = 0; i < input.files.length; ++i) {
        output.innerHTML += '<li>' + input.files.item(i).name + '</li>';
      }
      output.innerHTML += '</ul>';
    }
    // MULTIPLE FILE NAME ++++++++++++++++++++++++
  })
})(jQuery)