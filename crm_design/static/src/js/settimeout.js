/** @odoo-module **/


import session from 'web.session';
import {getCookie, setCookie, deleteCookie} from 'web.utils.cookies';

function getconfigminuts(){
    session.rpc('/get_minutes').then( function (result){
        if(result){
            setCookie('config_min', result);
            setCookie('remaining_min', result);
            setCookie('is_set', true);
            runtimer();
        }
    })
}
if(! getCookie('config_min')){
    getconfigminuts()
}

if(getCookie('is_set')){
    runtimer();
}

function runtimer(){
setInterval(function() {
    setCookie('remaining_min', getCookie('remaining_min')-1);
    if(getCookie('remaining_min') == 0){
        getconfigminuts();
        session.session_logout()
    }
      
  }, 60 * 1000); 
}

    
