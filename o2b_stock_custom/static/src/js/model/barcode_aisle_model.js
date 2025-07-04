/** @odoo-module **/

import BarcodeModel from '@stock_barcode/models/barcode_model';
import {_t} from "web.core";
import { sprintf } from '@web/core/utils/strings';

export default class BarcodeAisleModel extends BarcodeModel {
    constructor(params) {
        super(...arguments);
        this.lineModel = params.model;
        this.lineFormViewReference = 'o2b_stock_custom.stock_aisle_barcode';
//        this.validateMessage = _t("The aisle adjustment has been validated");
//        this.validateMethod = 'action_validate';
    }

    async apply() {
        await this.save();
        const linesToApply = this.pageLines.filter(line => line.inventory_quantity_set);
        if (linesToApply.length === 0) {
            const message = _t("There is nothing to apply in this page.");
            return this.notification.add(message, { type: 'warning' });
        }
        const action = await this.orm.call('stock.aisle', 'action_validate',
            [linesToApply.map(aisle => aisle.id)]
        );
        const notifyAndGoAhead = res => {
            if (res && res.special) {
                return this.trigger('refresh');
            }
            if (this.pages.length > 1) {
                this.notification.add(_t("Aisle adjustment was saved"), { type: 'success' });
                this.trigger('refresh');
            } else {
                this.notification.add(_t("The aisle adjustment has been validated"), { type: 'success' });
                this.trigger('history-back');
            }
        };
        if (action && action.res_model) {
            const options = { on_close: notifyAndGoAhead };
            return this.trigger('do-action', { action, options });
        }
        notifyAndGoAhead();
    }

    // Add more methods as needed, similar to the structure of BarcodeQuantModel
}
