odoo.define('client_vendor_dashboard.vendor_dashboard', function (require) {
    "use strict";
	var rpc = require('web.rpc');
    var ajax = require('web.ajax');
	console.log("fddddddddddddddddddddddddddddddddddddddddddddddddddddddsw")

	console.log("in ready state")
    rpc.query({
        route: '/vendor1',
        params: {
              
        },
        .then(function (data) {
        	console.log(" iin web rpc controller data test ", data)
    });
    ajax.jsonRpc('/vendor1', 'call', {})
        .then(function (data) {
        	console.log(" in jsoncontroller data test ", data)
    // });
});
