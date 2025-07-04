// +++++++++++++++++Supplier multiple area ++++++++++++++++++++++++++
// $(document).ready(function () {
  // getVal = function() {
    // var data = document.getElementById('area_operates_city1').value;
    // var val = document.getElementById('zip_code_no1').value;
    // var num = document.getElementById('redius_profile1').value;
    
    // for (const rec in data,val) {
    // // Add the circle for this city to the map.
    // const cityCircle = new google.maps.Circle({
    //   strokeColor: "#FF0000",
    //   strokeOpacity: 0.8,
    //   strokeWeight: 2,
    //   fillColor: "#FF0000",
    //   fillOpacity: 0.35,
    //   my_radius,
    //   center: data[rec].center,
    //   radius: Math.sqrt(data[rec].num) *100,
    //  });
    // }
    // $('#my_radius').attr('src',"https://maps.google.com/maps?q="+data +"," + val +"&z=15&output=embed")
    // $('#my_radius').attr('src',"https://maps.google.com/maps?q="+data +"," + val +" " + num +"km" +"&z=15&output=embed")
  // }

// });

// $(document).ready(function () {
  // getMultipleVal = function() {
    // var city = document.getElementById('area_operates_city').value;
    // var zip = document.getElementById('zip_code_no').value;
    // var num = document.getElementById('redius_profile').value;
  
    // for (const rec in city,zip) {
    // // Add the circle for this city to the map.
    // const cityCircle = new google.maps.Circle({
    //   strokeColor: "#FF0000",
    //   strokeOpacity: 0.8,
    //   strokeWeight: 2,
    //   fillColor: "#FF0000",
    //   fillOpacity: 0.35,
    //   my_radius,
    //   center: city[rec].center,
    //   radius: Math.sqrt(city[rec].num) *100,
    //  });
    // }
    // $('#my_radius').attr('src',"https://maps.google.com/maps?q="+city +"," + zip +"&z=15&output=embed")
    // $('#my_radius').attr('src',"https://maps.google.com/maps?q="+city +"," + zip +" " + num +"km" +"&z=15&output=embed")
  // }
// });

// +++++++++++++++++Supplier multiple area end ++++++++++++++++++++++++++
(function(){
  
  // var Widget = require('web.Widget');
  var widget, initAF = function() {

      widget = new AddressFinder.Widget(
          $("#pac-input")[0],
          "YC7LR3EFNXHK6VWPAQ4G",
          'AU'
      );
      if (_.isEmpty(widget)){
        return true
      }else{
        widget.on("result:select", function(fullAddress, metaData) {
         // $('#pac-input').value = metaData.address_line_1;
         $('#addrs_1')[0].value = metaData.address_line_1;
         var lat = metaData.latitude
         var leng = metaData.longitude
         // $('#my_map').attr('src',"https://maps.google.com/maps?q="+lat +"," + leng +"&z=15&output=embed")
         $('#my_map').attr('src',"https://maps.google.com/maps?q="+lat +"," + leng +"&t=k&z=15&output=embed")
         $('#addrs_2')[0].value = metaData.address_line_2;
         $('#city')[0].value = metaData.locality_name;
         $('#state')[0].value = metaData.state_territory;
         $('#postcode')[0].value = metaData.postcode;
         $('#long_address')[0].value = leng;
         $('#let_address')[0].value = lat;
      });
    };

    var lat = $('#let_address')[0].value
    var leng = $('#long_address')[0].value
    if(lat && leng){
      $('#my_map').attr('src',"https://maps.google.com/maps?q="+lat +"," + leng +"&t=k&z=15&output=embed")
    }
  };
  
  $( document ).ready(function() {
    $.getScript('https://api.addressfinder.io/assets/v3/widget.js', initAF);
  });

})();




// ++++++++++++++++++++++++++++++++++ADDRESS++++++++++++++++++

(function(){
  // var Widget = require('web.Widget');
  var widget, initAF = function() {
      widget = new AddressFinder.Widget(
          $("#addrs_1")[0],
          "YC7LR3EFNXHK6VWPAQ4G",
          'AU'
      );
      if (_.isEmpty(widget)){
        return true
      }else{
      widget.on("result:select", function(fullAddress, metaData) {
       $('#addrs_1')[0].value = metaData.address_line_1;
       $('#addrs_2')[0].value = metaData.address_line_2;
       $('#city')[0].value = metaData.locality_name;
       $('#state')[0].value = metaData.state_territory;
       $('#postcode')[0].value = metaData.postcode;
    });
  };
  };
  
  $( document ).ready(function() {
    $.getScript('https://api.addressfinder.io/assets/v3/widget.js', initAF);
  });

})();



// +++++++++++++++++++++++Head office Address++++++++++++++++++++


(function(){
  // var Widget = require('web.Widget');
  var widget, initAF = function() {
      widget = new AddressFinder.Widget(
          $("#head_office_address")[0],
          "YC7LR3EFNXHK6VWPAQ4G",
          'AU'
      );
      if (_.isEmpty(widget)){
         return true
      }else{
      widget.on("result:select", function(fullAddress, metaData) {
       $('#head_office_address')[0].value = metaData.address_line_1;
       $('#head_office_address_more')[0].value = metaData.address_line_2;
       $('#profile_city')[0].value = metaData.locality_name;
       $('#profile_state')[0].value = metaData.state_territory;
       $('#profile_postal_code')[0].value = metaData.postcode;
    });
  };
  };
  
  $( document ).ready(function() {
    $.getScript('https://api.addressfinder.io/assets/v3/widget.js', initAF);
  });

})();

// +++++++++++++++++++++++Head office Address End++++++++++++++++++++