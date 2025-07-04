/** @odoo-module **/

import MainMenu from "@stock_barcode/stock_barcode_menu";

MainMenu.include({
    events: Object.assign({}, MainMenu.prototype.events, {
        'click .button_aisle_transfer': '_onClickAisleUpdate',
        'click .button_mrp_tracking': '_onClickMrpUpdate',
    }),

    // --------------------------------------------------------------------------
    // Handlers
    // --------------------------------------------------------------------------

    /**
     * Open batch picking's kanban view with all batch picking in progress.
     *
     * @private
     */

    _onClickAisleUpdate: function () {
        this._rpc({
                'model': 'stock.aisle',
                'method': 'action_client_action',
                'args': [[]],
            }).then(result => {
                this.do_action(result);
            });
    },
    _onClickMrpUpdate: function () {
        this.do_action('o2b_stock_custom.mrp_production_tree_action');
    },
    _getModel(params) {
        console.log("Params in _getModel:", params);

        if (params.model === 'stock.picking') {
            return new BarcodePickingModel(params);
        } else if (params.model === 'stock.quant') {
            return new BarcodeQuantModel(params);
        } else if (params.model === 'stock.aisle') {
            return new BarcodeAisleModel(params);  // Assuming BarcodeAisleModel is your custom model
        } else {
            throw new Error('No JS model defined');
        }
    }
});
