/** @odoo-module **/

import {
    registerInstancePatchModel,
} from'@mail/model/model_core';
import session  from 'web.session';

registerInstancePatchModel('mail.activity', 'crm_history_module/static/src/js/activity.js', {
    /**
     * @override
     */
    async deleteServerRecord() {
        var context=session.user_context
        context['is_delete']=true
        await this.async(() => this.env.services.rpc({
            model: 'mail.activity',
            method: 'unlink',
            args: [[this.id]],
            kwargs: {context: context},
        }));
        this.delete();
    },
    
});
