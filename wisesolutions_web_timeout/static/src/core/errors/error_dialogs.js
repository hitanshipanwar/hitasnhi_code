/** @odoo-module **/

import { useService } from '@web/core/utils/hooks';
import { Dialog } from "@web/core/dialog/dialog";
import { _lt } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

import { Component, onWillStart } from "@odoo/owl";

export class WiseSessionExpiredDialog extends Component {
    setup() {
        this.rpc = useService('rpc');
        onWillStart(async () => {
            this.message = await this.rpc('/crash_manager/message');
        });
    }

    onClick() {
        window.location.reload();
    }
}
WiseSessionExpiredDialog.template = "web.SessionExpiredDialog";
WiseSessionExpiredDialog.components = { Dialog };
WiseSessionExpiredDialog.title = _lt("Odoo Session Expired");
registry
    .category("error_dialogs")
    .add("odoo.http.SessionExpiredException", WiseSessionExpiredDialog, {force: true, sequence: 100})
    .add("werkzeug.exceptions.Forbidden", WiseSessionExpiredDialog, {force: true, sequence: 100});