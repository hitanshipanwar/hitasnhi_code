 /** @odoo-module **/

import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { MessagingMenu } from "@mail/components/messaging_menu/messaging_menu";
import { patch } from 'web.utils';

const rpc = require('web.rpc')


odoo.__DEBUG__ && console.log("Console log inside the patch function in messaging_menu", MessagingMenu.prototype, "form_controller");
patch(MessagingMenu.prototype, "o2b_Conversation_AccessRights.MessagingMenuPatch", {
    async setup() {

        const _super = this._super.bind(this);
        
        this.state = useState({
            hasChatterAccess: false,
        });

        try {
            const response = await rpc.query({
                model: 'res.users',
                method: 'has_group',
                args: ['o2b_Conversation_AccessRights.group_conversation_access'],
            });
            console.log("RPC response:", response);
            this.state.hasChatterAccess = response;
            this.render(); 
        } catch (error) {
            console.error('RPC call failed:', error);
            this.state.hasChatterAccess = false;
        }
    },
   
});