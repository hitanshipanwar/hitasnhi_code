/** @odoo-module **/

import { patch } from 'web.utils';
import MainMenu from '@stock_barcode/stock_barcode_menu'; // Adjust the import path
import Session from 'web.session';
import BarcodeScanner from '@web_enterprise/webclient/barcode/barcode_scanner';
import {_t} from 'web.core';
import { sprintf } from '@web/core/utils/strings';
const Dialog = require('web.Dialog');

// // const _t = core._t;

let record_status = '';

patch(MainMenu.prototype, 'o2b_stock_api', {
    _onBarcodeScanned: function (barcode) {
        if (!$.contains(document, this.el)) {
            return;
        }
        if (!['O-BTN.empty'].includes(barcode)) {
        // if (!['checkin', 'checkout','O-BTN.create', 'O-BTN.confirm', 'O-BTN.update', 'O-BTN.edit', 'O-BTN.free'].includes(barcode)) {
            Session.rpc('/stock_barcode/scan_from_main_menu', { barcode }).then((result) => {
                if (result.warning === 'Duplicate records are not allowed'){
                    const audioPath = '/o2b_stock_api/static/src/audio/al_no_duplicate.mp3';
                    this.displayNotification({
                        type: 'warning',
                        message:_t("Duplicate records are not allowed."),
                    });
                    try {
                        const audio = new Audio(audioPath);
                        audio.volume = 1.0;
                        audio.play();
                    } catch (error) {
                        console.error('Error playing audio:', error);
                    }
                } else if (result.action && result.action.res_model === 'stock.picking') {
                    if (result.action) {
                        this.do_action(result.action);
                    } else if (result.warning) {
                        this.displayNotification({ title: result.warning, type: 'danger' });
                    }
                    const audioPath = '/o2b_stock_api/static/src/audio/record_opened.mp3';
                    try {
                        const audio = new Audio(audioPath);
                        audio.volume = 1.0;
                        audio.play();
                    } catch (error) {
                        console.error('Error playing audio:', error);
                    }
                } else if(result.model && result.model === 'hr.employee') {
                    if (result.action) {
                        this.do_action(result.action);
                    } else if (result.warning) {
                        this.displayNotification({ title: result.warning, type: 'danger' });
                    }
                    const audioPath = '/o2b_stock_api/static/src/audio/employee_barcode.mp3';
                    this.displayNotification({
                        type: 'warning',
                        message:_t("Employee Barcode Scanned."),
                    });
                    try {
                        const audio = new Audio(audioPath);
                        audio.volume = 1.0;
                        audio.play();
                    } catch (error) {
                        console.error('Error playing audio:', error);
                    }
                } else if (result.action && result.action.res_model === 'mrp.production') {
                    if (result.action) {
                        this.do_action(result.action);
                    } else if (result.warning) {
                        this.displayNotification({ title: result.warning, type: 'danger' });
                    }
                    record_status = result.mrp_production[0].state
                    const audioPath = '/o2b_stock_api/static/src/audio/mo_barcode_scanned.mp3';
                    this.displayNotification({
                        type: 'warning',
                        message:_t("Manufacturing Order Barcode Scanned."),
                    });
                    try {
                        const audio = new Audio(audioPath);
                        audio.volume = 1.0;
                        audio.play();
                    } catch (error) {
                        console.error('Error playing audio:', error);
                    }
                } else if(result && result.model === 'product.product') {
                    if (result.action) {
                        this.do_action(result.action);
                    } else if (result.warning) {
                        this.displayNotification({ title: result.warning, type: 'danger' });
                        return;
                    }
                    const audioPath = '/o2b_stock_api/static/src/audio/aisle_updated.mp3';
                    this.displayNotification({
                        type: 'warning',
                        message:_t("Aisle Updated"),
                    });
                    try {
                        const audio = new Audio(audioPath);
                        audio.volume = 1.0;
                        audio.play();
                    } catch (error) {
                        console.error('Error playing audio:', error);
                    }
                } else if(result && result.model === 'stock.aisle') {
                    if (result.action) {
                        this.do_action(result.action);
                    } else if (result.warning) {
                        this.displayNotification({ title: result.warning, type: 'danger' });
                    }
                    const audioPath = '/o2b_stock_api/static/src/audio/aisle_selected.mp3';
                    this.displayNotification({
                        type: 'warning',
                        message:_t("Aisle Selected."),
                    });
                    try {
                        const audio = new Audio(audioPath);
                        audio.volume = 1.0;
                        audio.play();
                    } catch (error) {
                        console.error('Error playing audio:', error);
                    }
                } else if (barcode === 'checkin' && result && result['warning'] !== 'Please scan the Employee Barcode first'){
                    if (record_status == 'done'){
                        if (result.action) {
                            this.do_action(result.action);
                        } else if (result.warning) {
                            this.displayNotification({ title: result.warning, type: 'danger' });
                        }
                        const audioPath = '/o2b_stock_api/static/src/audio/no_checkin.mp3';
                        const message = sprintf(_t("Manufacturing Order is already done and cannot do Check-In."));
                        Dialog.alert(this, _t(message), {title: _t("Warning")});
                        try {
                            const audio = new Audio(audioPath);
                            audio.volume = 1.0;
                            audio.play();
                        } catch (error) {
                            console.error('Error playing audio:', error);
                        }
                    } else{
                        if (result.action) {
                            this.do_action(result.action);
                        } else if (result.warning) {
                            this.displayNotification({ title: result.warning, type: 'danger' });
                        }
                        const audioPath = '/o2b_stock_api/static/src/audio/check_in.mp3';
                        this.displayNotification({
                            type: 'success',
                            message:_t("Check-In process initiated."),
                        });
                        try {
                            const audio = new Audio(audioPath);
                            audio.volume = 1.0;
                            audio.play();
                        } catch (error) {
                            console.error('Error playing audio:', error);
                        }
                    }
                } else if (barcode === 'checkout'){
                    if (result.action) {
                        this.do_action(result.action);
                    } else if (result.warning) {
                        this.displayNotification({ title: result.warning, type: 'danger' });
                    }
                    const audioPath = '/o2b_stock_api/static/src/audio/check_out.mp3';
                    this.displayNotification({
                        type: 'warning',
                        message:_t("Check out process completed."),
                    });
                    try {
                        const audio = new Audio(audioPath);
                        audio.volume = 1.0;
                        audio.play();
                    } catch (error) {
                        console.error('Error playing audio:', error);
                    }
                } else if(result && result['warning'] == 'Please scan the Employee Barcode first'){
                    const audioPath = '/o2b_stock_api/static/src/audio/scan_emp.mp3';
                    this.displayNotification({
                        type: 'warning',
                        message:_t("Please scan the Employee Barcode first"),
                    });
                    try {
                        const audio = new Audio(audioPath);
                        audio.volume = 1.0;
                        audio.play();
                    } catch (error) {
                        console.error('Error playing audio:', error);
                    }
                } else {
                    if (result.action) {
                        this.do_action(result.action);
                    } else if (result.warning) {
                        const audioPath = '/o2b_stock_api/static/src/audio/scanned_no_rec.mp3';
                        this.displayNotification({
                            type: 'warning',
                            message: _.str.sprintf(
                            _t("No picking or location or product or Aisle corresponding to barcode %s"),
                            barcode
                        ) });
                        try {
                            const audio = new Audio(audioPath);
                            audio.volume = 1.0;
                            audio.play();
                        } catch (error) {
                            console.error('Error playing audio:', error);
                        }
                        // this.displayNotification({ title: result.warning, type: 'danger' });
                    }
                }
            });
        // } else if (barcode === 'checkin'){
        //     if (record_status == 'done'){
        //         const audioPath = '/o2b_stock_api/static/src/audio/no_checkin.mp3';
        //         const message = sprintf(_t("Manufacturing Order is already done and cannot do Check-In."));
        //         Dialog.alert(this, _t(message), {title: _t("Warning")});
        //         try {
        //             const audio = new Audio(audioPath);
        //             audio.volume = 1.0;
        //             audio.play();
        //         } catch (error) {
        //             console.error('Error playing audio:', error);
        //         }
        //     } else{
        //         const audioPath = '/o2b_stock_api/static/src/audio/check_in.mp3';
        //         this.displayNotification({
        //             type: 'success',
        //             message:_t("Check-In process initiated."),
        //         });
        //         try {
        //             const audio = new Audio(audioPath);
        //             audio.volume = 1.0;
        //             audio.play();
        //         } catch (error) {
        //             console.error('Error playing audio:', error);
        //         }
        //     }
        // } else if (barcode === 'checkout'){
        //     const audioPath = '/o2b_stock_api/static/src/audio/check_out.mp3';
        //     this.displayNotification({
        //         type: 'warning',
        //         message:_t("Check out process completed."),
        //     });
        //     try {
        //         const audio = new Audio(audioPath);
        //         audio.volume = 1.0;
        //         audio.play();
        //     } catch (error) {
        //         console.error('Error playing audio:', error);
        //     }
        // } else if (barcode === 'O-BTN.create'){
        //     Session.rpc('/stock_barcode/scan_from_main_menu', { barcode }).then(result => {
        //         if (result.action) {
        //             this.do_action(result.action);
        //         } else if (result.warning) {
        //             this.displayNotification({ title: result.warning, type: 'danger' });
        //         }
        //     });
        //     const audioPath = '/o2b_stock_api/static/src/audio/for_creating.mp3';
        //     this.displayNotification({
        //         type: 'success',
        //         message:_t("For Creating New Aisle."),
        //     });
        //     try {
        //         const audio = new Audio(audioPath);
        //         audio.volume = 1.0;
        //         audio.play();
        //     } catch (error) {
        //         console.error('Error playing audio:', error);
        //     }
        // } else if (barcode === 'O-BTN.update'){
        //     Session.rpc('/stock_barcode/scan_from_main_menu', { barcode }).then(result => {
        //         if (result.action) {
        //             this.do_action(result.action);
        //         } else if (result.warning) {
        //             this.displayNotification({ title: result.warning, type: 'danger' });
        //         }
        //     });
        //     const audioPath = '/o2b_stock_api/static/src/audio/for_updating.mp3';
        //     this.displayNotification({
        //         type: 'success',
        //         message:_t("For Updateing Aisle."),
        //     });
        //     try {
        //         const audio = new Audio(audioPath);
        //         audio.volume = 1.0;
        //         audio.play();
        //     } catch (error) {
        //         console.error('Error playing audio:', error);
        //     }
        // } else if (barcode === 'O-BTN.confirm'){
        //     Session.rpc('/stock_barcode/scan_from_main_menu', { barcode }).then(result => {
        //         if (result.action) {
        //             this.do_action(result.action);
        //         } else if (result.warning) {
        //             this.displayNotification({ title: result.warning, type: 'danger' });
        //         }
        //     });
        //     const audioPath = '/o2b_stock_api/static/src/audio/aisle_created.mp3';
        //     this.displayNotification({
        //         type: 'success',
        //         message:_t("Aisle Created."),
        //     });
        //     try {
        //         const audio = new Audio(audioPath);
        //         audio.volume = 1.0;
        //         audio.play();
        //     } catch (error) {
        //         console.error('Error playing audio:', error);
        //     }
        //     setTimeout(() => {
        //         console.log("DEF_DELAY:");
        //         this.trigger('refresh');
        //         window.location.reload();
        //     }, 2000);
        // } else if (barcode === 'O-BTN.edit'){
        //     Session.rpc('/stock_barcode/scan_from_main_menu', { barcode }).then(result => {
        //         if (result.action) {
        //             this.do_action(result.action);
        //         } else if (result.warning) {
        //             this.displayNotification({ title: result.warning, type: 'danger' });
        //         }
        //     });
        //     const audioPath = '/o2b_stock_api/static/src/audio/aisle_updated.mp3';
        //     this.displayNotification({
        //         type: 'success',
        //         message:_t("Aisle Updated."),
        //     });
        //     try {
        //         const audio = new Audio(audioPath);
        //         audio.volume = 1.0;
        //         audio.play();
        //     } catch (error) {
        //         console.error('Error playing audio:', error);
        //     }
        //     setTimeout(() => {
        //         console.log("DEF_DELAY:");
        //         this.trigger('refresh');
        //         window.location.reload();
        //     }, 2000);
        } else if (barcode === 'O-BTN.empty'){
            Session.rpc('/stock_barcode/scan_from_main_menu', { barcode }).then(result => {
                if (result.action) {
                    this.do_action(result.action);
                } else if (result.warning) {
                    const audioPath = '/o2b_stock_api/static/src/audio/aisle_already_empty.mp3';
                    this.displayNotification({
                        type: 'success',
                        message:_t("Aisle location is already emptied"),
                    });
                    try {
                        const audio = new Audio(audioPath);
                        audio.volume = 1.0;
                        audio.play();
                    } catch (error) {
                        console.error('Error playing audio:', error);
                    }
                    setTimeout(() => {
                        console.log("DEF_DELAY:");
                        this.trigger('refresh');
                        window.location.reload();
                    }, 2500);
                } else {
                    const audioPath = '/o2b_stock_api/static/src/audio/empty_aisel.mp3';
                    this.displayNotification({
                        type: 'success',
                        message:_t("Empty the selected aisle locations."),
                    });
                    try {
                        const audio = new Audio(audioPath);
                        audio.volume = 1.0;
                        audio.play();
                    } catch (error) {
                        console.error('Error playing audio:', error);
                    }
                    setTimeout(() => {
                        console.log("DEF_DELAY:");
                        this.trigger('refresh');
                        window.location.reload();
                    }, 2000);
                }
            });
        } else {
            Session.rpc('/stock_barcode/scan_from_main_menu', { barcode }).then(result => {
                if (result.action) {
                    this.do_action(result.action);
                } else if (result.warning) {
                    this.displayNotification({ title: result.warning, type: 'danger' });
                }
            });
        }
    },
});
