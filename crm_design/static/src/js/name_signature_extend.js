odoo.define('crm_design.name_signature_extend', function (require) {
'use strict';

var core = require('web.core');
var config = require('web.config');
var utils = require('web.utils');
var Widget = require('web.Widget');

var _t = core._t;

const Mycomment = require('web.name_and_signature');

Mycomment.NameAndSignature.include({

    template: 'web.sign_name_and_signature',
    xmlDependencies: ['/crm_design/static/src/legacy/xml/name_and_signature.xml'],

	/**
     * @override
     */
	start: function () {

        var self = this;
		this.$commentInput = this.$('.o_web_design_comment_input');
        // signature and name input
        this.$signatureGroup = this.$('.o_web_sign_signature_group');
        this.$signatureField = this.$('.o_web_sign_signature');
        this.$nameInput = this.$('.o_web_sign_name_input');
        this.$nameInputGroup = this.$('.o_web_sign_name_group');

        // mode selection buttons
        this.$drawButton = this.$('a.o_web_sign_draw_button');
        this.$autoButton = this.$('a.o_web_sign_auto_button');
        this.$loadButton = this.$('a.o_web_sign_load_button');

        // mode: draw
        this.$drawClear = this.$('.o_web_sign_draw_clear');

        // mode: auto
        this.$autoSelectStyle = this.$('.o_web_sign_auto_select_style');
        this.$autoFontSelection = this.$('.o_web_sign_auto_font_selection');
        this.$autoFontList = this.$('.o_web_sign_auto_font_list');
        for (var i in this.fonts) {
            var $img = $('<img/>').addClass('img-fluid');
            var $a = $('<a/>').addClass('btn p-0').append($img).data('fontNb', i);
            this.$autoFontList.append($a);
        }

        // mode: load
        this.$loadFile = this.$('.o_web_sign_load_file');
        this.$loadInvalid = this.$('.o_web_sign_load_invalid');

        if (this.fonts && this.fonts.length < 2) {
            this.$autoSelectStyle.hide();
        }

        if (this.noInputName) {
            if (this.defaultName === "") {
                this.$autoButton.hide();
            }
            this.$nameInputGroup.hide();
        }

        // Resize the signature area if it is resized
        $(window).on('resize.o_web_sign_name_and_signature', _.debounce(function () {
            if (self.isDestroyed()) {
                // May happen since this is debounced
                return;
            }
            self.resizeSignature();
        }, 250));

        return this._super.apply(this, arguments);
    },

    /**
     * Gets the Comment currently given by the user.
     *
     * @returns {string} comment
     */
    getComment: function () {
        return this.$commentInput.val();
    },
});

});
