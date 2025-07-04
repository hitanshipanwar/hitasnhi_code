odoo.define('crm_design.customer_signature', function (require) {
'use strict';
var core = require('web.core');
var publicWidget = require('web.public.widget');
var NameAndSignature = require('web.name_and_signature').NameAndSignature;
var qweb = core.qweb;
var NameAndSignature = require('web.name_and_signature').NameAndSignature;
var qweb = core.qweb;

var _t = core._t;
const MySignatureForm = require('portal.signature_form');

MySignatureForm.SignatureForm.include({


    /**
     * Overridden to allow options.
     *
     * @constructor
     * @param {Widget} parent
     * @param {Object} options
     * @param {string} options.callUrl - make RPC to this url
     * @param {string} [options.sendLabel='Accept & Sign'] - label of the
     *  send button
     * @param {Object} [options.rpcParams={}] - params for the RPC
     * @param {Object} [options.nameAndSignatureOptions={}] - options for
     *  @see NameAndSignature.init()
     */
    init: function (parent, options) {
        this._super.apply(this, arguments);

        this.csrf_token = odoo.csrf_token;

        this.callUrl = options.callUrl || '';
        this.rpcParams = options.rpcParams || {};
        this.sendLabel = options.sendLabel || _t("Accept & Sign");

        const params = new Proxy(new URLSearchParams(this.callUrl), {
            get: (searchParams, prop) => searchParams.get(prop),
        });
        if(params.type != null){
            this.sendLabel = options.sendLabel || _t("Reject & Sign");
        }
        else{
           this.sendLabel = options.sendLabel || _t("Accept & Sign");
        }
        this.nameAndSignature = new NameAndSignature(this,
            options.nameAndSignatureOptions || {});
    },

    start: async function () {
        await this._super(...arguments);


        var self = this;
        const params = new Proxy(new URLSearchParams(this.callUrl), {
            get: (searchParams, prop) => searchParams.get(prop),
        });
        // Get the value of "some_key" in eg "https://example.com/?some_key=some_value"
        this.$designInput = params.design_id;
        if(params.type != null){
            this.$('.o_web_sign_name_and_signature').before("<textarea id='description' class='textarea o_web_design_comment_input' name='description' cols='70' rows='4' required='required' placeholder='Write Reason Here...'></textarea>");    
            this.$commentInput = this.$('.o_web_design_comment_input');
            // this.$('.o_portal_sign_submit').replace("<button type='submit' class='o_portal_sign_submit btn btn-primary' disabled='disabled'><i class='fa fa-check'/>Reject</button>")
            // this.$('.o_portal_sign_submit t').replace("")
        }
        else{
            this.$('.o_web_sign_name_and_signature').before("<textarea id='description' style='display:none;' class='textarea o_web_design_comment_input' name='description' cols='70' rows='4' required='required' placeholder='Write Reason Here...'></textarea>");    
            this.$commentInput = this.$('.o_web_design_comment_input');
        }
    },


	_onClickSignSubmit: function (ev) {
        var self = this;
        ev.preventDefault();

        if (!this.nameAndSignature.validateSignature()) {
            return;
        }

        var name = this.nameAndSignature.getName();
        var signature = this.nameAndSignature.getSignatureImage()[1];
        var comment = this.$commentInput.val();
        return this._rpc({
            route: this.callUrl,
            params: _.extend(this.rpcParams, {
                'name': name,
                'signature': signature,
                'design_id': this.$designInput,
                'comment':comment,
            }),
        }).then(function (data) {
            if (data.error) {
                self.$('.o_portal_sign_error_msg').remove();
                self.$controls.prepend(qweb.render('portal.portal_signature_error', {widget: data}));
            } else if (data.success) {
                var $success = qweb.render('portal.portal_signature_success', {widget: data});
                self.$el.empty().append($success);
            }
            if (data.force_refresh) {
                if (data.redirect_url) {
                    window.location = data.redirect_url;
                } else {
                    window.location.reload();
                }
                // no resolve if we reload the page
                return new Promise(function () { });
            }
        });
    },
});

});