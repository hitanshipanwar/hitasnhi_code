/** @odoo-module **/

import {
    registerPatch
} from'@mail/model/model_core';
import { attr } from '@mail/model/model_field';

registerPatch({
    name: 'Attachment',
    modelMethods: {
        /**
         * @override
         */
        convertData(data) {
            const res = this._super(data);
            if ('is_sent_on_bill_com' in data) {
                res.is_sent_on_bill_com = data.is_sent_on_bill_com
            }
            return res;
        },
    },
    recordMethods: {
        /**
        * @static
        */
        async performRpc() {
            let self = this;
            const result = await self.messaging.rpc({
                model: 'account.move',
                method: 'send_attachment_to_bill_com',
                args: [ [this.originThread.id], this.id] //$target.data('id') ]
            })
            if (result) {
                self.update({ is_sent_on_bill_com: true });
            }
            
       },
        onClickSyncToBillDotCom (ev) {
           ev.stopPropagation();
           this.performRpc();
       },

    },
    fields: {
        is_sent_on_bill_com: attr({
            default: false,
        }),
        account_move_bill_id: attr({
            default: false,
        })
    },

})