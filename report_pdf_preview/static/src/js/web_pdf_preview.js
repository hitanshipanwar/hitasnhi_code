/** @odoo-module **/

/*import {download} from "@web/core/network/download";*/
import {registry} from "@web/core/registry";
import Dialog from 'web.Dialog';
import { qweb as QWeb, _t } from 'web.core';
import { actionService } from "@web/webclient/actions/action_service";

registry
    .category("ir.actions.report handlers")
    .add("deload_handler", async function (action, options, env) {
        const link = '<br><br><a href="http://wkhtmltopdf.org/" target="_blank">wkhtmltopdf.org</a>';
        const WKHTMLTOPDF_MESSAGES = {
            broken:
                env._t(
                    "Your installation of Wkhtmltopdf seems to be broken. The report will be shown " +
                        "in html."
                ) + link,
            install:
                env._t(
                    "Unable to find Wkhtmltopdf on this system. The report will be shown in " + "html."
                ) + link,
            upgrade:
                env._t(
                    "You should upgrade your version of Wkhtmltopdf to at least 0.12.0 in order to " +
                        "get a correct display of headers and footers as well as support for " +
                        "table-breaking between pages."
                ) + link,
            workers: env._t(
                "You need to start Odoo with at least two workers to print a pdf version of " +
                    "the reports."
            ),
        };
        let wkhtmltopdfStateProm;
        if (action.report_type === 'qweb-pdf') {
            // check the state of wkhtmltopdf before proceeding
            if (!wkhtmltopdfStateProm) {
                wkhtmltopdfStateProm = env.services.rpc("/report/check_wkhtmltopdf");
            }
            const state = await wkhtmltopdfStateProm;
            // display a notification according to wkhtmltopdf's state
            if (state in WKHTMLTOPDF_MESSAGES) {
                env.services.notification.add(WKHTMLTOPDF_MESSAGES[state], {
                    sticky: true,
                    title: env._t("Report"),
                });
            }
            if (state === "upgrade" || state === "ok") {
                // if(action && action.binding_type){

                // trigger the download of the PDF report
                
                let type="pdf"
                // let url = `/web/static/lib/pdfjs/web/viewer.html?file=/report/${type}/${action.report_name}`;
                let url = `/report/${type}/${action.report_name}`;
                const actionContext = action.context || {};
                if (action.data && JSON.stringify(action.data) !== "{}") {
                    // build a query string with `action.data` (it's the place where reports
                    // using a wizard to customize the output traditionally put their options)
                    const options = encodeURIComponent(JSON.stringify(action.data));
                    const context = encodeURIComponent(JSON.stringify(actionContext));
                    url += `?options=${options}&context=${context}`;
                } else {
                    if (actionContext.active_ids) {
                        url += `/${actionContext.active_ids.join(",")}`;
                    }
                    if (type === "html") {
                        const context = encodeURIComponent(JSON.stringify(env.services.user.context));
                        url += `?context=${context}`;
                    }
                }
                // console.log("url================",url)
                const dialog = new Dialog(this, {
                    title: action.name,
                    size: 'large',
                    $content: $(QWeb.render('report_pdf_preview.ReportViewer', {url: url})),
                });
                return dialog.open();
                 // }
                //return false
                //return _triggerDownload(action, options, "pdf");
            } 
            /*return this.call('report', 'checkWkhtmltopdf').then(function (state) {
                const url = `/web/static/lib/pdfjs/web/viewer.html?file=${self._makeReportUrls(action).pdf}`

                const dialog = new Dialog(this, {
                    title: action.name,
                    size: 'large',
                    $content: $(qweb.render('report_pdf_preview.ReportViewer', {url: url})),
                });
                dialog.open();
            });*/

        }/* else {
            return self._super(action, options);
        }*/
        //return Promise.resolve(false);
    });