/** @odoo-module **/

import { download } from "@web/core/network/download";
import { PivotView } from "@web/views/pivot/pivot_view";
import { patch } from 'web.utils';

patch(PivotView.prototype, 'crm_history_module/static/src/js/pivot_view.js PivotView', {
    onDownloadCsvButtonClicked() {
        if (this.model.getTableWidth() > 16384) {
            throw new Error(
                this.env._t(
                    "For Csv compatibility, data cannot be exported if there are more than 16384 columns.\n\nTip: try to flip axis, filter further or reduce the number of measures."
                )
            );
        }
        const table = this.model.exportData();
        download({
            url: "/web/pivot/export_csv",
            data: { data: JSON.stringify(table) },
        });
    }

});