odoo.define('airbid_master.aria_radius1', function (require) {
  'use strict';
  var ajax = require('web.ajax');

  $(document).ready(function () {
    

    function initMapCir(){

      var count = $("#area_operates_counter").val()
      var area_operates_city = "area_operates_city"+String(count)

      var address_detail = []

      for (let i = 1; i <= count; i++) {
				// var main_c = String(count)+ '_' + String(i) 
        var area_operates_city = "area_operates_city"+String(i)
        var area_operates_city_inp = document.querySelector('#'+area_operates_city);

        var area_op_postal = "zip_code_no"+String(i)
        var area_op_postal_inp = document.querySelector('#'+area_op_postal);

        var area_op_km = "redius_profile"+String(i)
        var area_op_km_inp = document.querySelector('#'+area_op_km);
        

        if (area_operates_city_inp && area_op_postal_inp && area_op_km_inp){
          var city = area_operates_city_inp.value
          var zipcode = area_op_postal_inp.value
          var km = area_op_km_inp.value
          var dict = {
            'city':city,
            'zipcode':zipcode,
            'km':km
          }
          address_detail.push(dict)
        }
        
			}

      var mapid = document.getElementById("map")

      if (mapid){
        ajax.jsonRpc('/geo/long_late/postal','call',{
          address_detail : address_detail,
        }).then(function (result){
          var add_list = result.address_detail
          init_get_list_city_postal_area(add_list)
        });
      }
    }

    function init_get_list_city_postal_area(add_list) {

      // Australiya
      var mapCenter = new google.maps.LatLng(-25.344, 131.036);

      const map = new google.maps.Map(document.getElementById("map"), {
        zoom: 15,
        center: mapCenter,
        // mapTypeId: "terrain",
        mapTypeId: "hybrid",
        disableDefaultUI: false,
        zoomControl: true,
      });

      var bounds = new google.maps.LatLngBounds();

      add_list.forEach(function(city){

        var city_center = { lat: city.lat, lng: city.lng }

        const cityCircle = new google.maps.Circle({
          strokeColor: "#FF0000",
          strokeOpacity: 0.8,
          strokeWeight: 2,
          fillColor: "#FF0000",
          fillOpacity: 0.35,
          map,
          center: city_center,
          radius: city.km * 1000, // convert Km to Miles
        });
        bounds.union(cityCircle.getBounds())
        

        const marker = new google.maps.Marker({
          position: city_center,
          map: map,
          animation: google.maps.Animation.DROP,
        });
      });
      map.fitBounds(bounds);
    }
    
    $(".save_area_operates").on("click",function(){
      $('#map').fadeOut(1000)
      $('#map').fadeIn(1000);
      initMapCir()
    });

    initMapCir()  
    google.maps.event.addDomListener(window, 'load', initMapCir);

  });
});