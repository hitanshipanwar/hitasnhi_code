/** @odoo-module **/

import BarcodeModel from '@stock_barcode/models/barcode_model';
import BarcodePickingModel from '@stock_barcode/models/barcode_picking_model';
import { patch } from 'web.utils';
import { _t } from 'web.core';
import { sprintf } from '@web/core/utils/strings';
const Dialog = require('web.Dialog');
const orm = require('web.session').orm;

patch(BarcodePickingModel.prototype, 'o2b_stock_api', {
    _getCommands() {
        const commands = this._super();
        commands['O-BTN.rate'] = this._rate.bind(this);

        const playAudio = async (audioPath) => {
            try {
                const audio = new Audio(audioPath);
                audio.volume = 1.0;
                await audio.play().catch((error) => {
                    console.error("Error playing audio:", error);
                });
            } catch (error) {
                console.error("Audio error:", error);
            }
        };

        // Commands with audio playback
        // const putInPackWithAudio = async () => {
        //     await playAudio('/o2b_stock_api/static/src/audio/product_packed_audio_file.mp3');  // Correct path
        //     await this._putInPack();
        // };

        // const getRateCallWithAudio = async () => {
        //     await playAudio('/o2b_stock_api/static/src/audio/gate_rate_audio_file.mp3');  // Correct path
        //     await this._rate();
        // };

        const printSlipWithAudio = async () => {
            await playAudio('/o2b_stock_api/static/src/audio/print_slip.mp3');
            await this.print(false, 'action_print_delivery_slip');
        };

        const printOpWithAudio = async () => {
            await playAudio('/o2b_stock_api/static/src/audio/print_op.mp3');
            await this.print(false, 'do_print_picking');
        };

        const scrapWithAudio = async () => {
            await playAudio('/o2b_stock_api/static/src/audio/scrap.mp3');
            await this._scrap();
        };

        const cancelWithAudio = async () => {
            await playAudio('/o2b_stock_api/static/src/audio/cancel.mp3');
            await this._cancel();
        };

        const PreviousPageWithAudio = async () => {
            await playAudio('/o2b_stock_api/static/src/audio/previous_page_audio_file.mp3');
            await this.previousPage();
        };

        const NextPageWithAudio = async () => {
            await playAudio('/o2b_stock_api/static/src/audio/next_page_audio_file.mp3');
            await this.nextPage();
        };

        const ChangePageWithAudio = async () => {
            await playAudio('/o2b_stock_api/static/src/audio/page_changed_audio_file.mp3');
            await this._changePage();
        };

        const GoToMenuWithAudio = async () => {
            await playAudio('/o2b_stock_api/static/src/audio/menu_page_audio_file.mp3');
            await this._goToMainMenu();
        };

        // Adding the commands to the `commands` object
        // commands['O-BTN.pack'] = putInPackWithAudio;
        // commands['O-BTN.rate'] = getRateCallWithAudio;
        commands['O-BTN.print-slip'] = printSlipWithAudio;
        commands['O-BTN.print-op'] = printOpWithAudio;
        commands['O-BTN.scrap'] = scrapWithAudio;
        commands['O-CMD.cancel'] = cancelWithAudio;
        commands['O-CMD.PREV'] = PreviousPageWithAudio;
        commands['O-CMD.NEXT'] = NextPageWithAudio;
        commands['O-CMD.PAGER-FIRST'] = ChangePageWithAudio;
        commands['O-CMD.PAGER-LAST'] = ChangePageWithAudio;
        commands['O-CMD.MAIN-MENU'] = GoToMenuWithAudio;

        return commands;
    },

    async _rate(additionalContext = {}) {
        const playAudio = async (audioPath) => {
            try {
                const audio = new Audio(audioPath);
                audio.volume = 1.0;
                await audio.play();
            } catch (error) {
                console.error("Error playing audio:", error);
            }
        };

        if (!this.params.model || !this.params.id) {
            throw new Error("Model or ID information is missing in the params.");
        }

        const methodDetails = {
            model: this.params.model,
            method: 'on_barcode_get_rate_scanned',
            args: [this.params.id],
            kwargs: additionalContext,
        };

        try {
            const result = await this.orm.call(
                methodDetails.model,
                methodDetails.method,
                methodDetails.args,
                { context: methodDetails.kwargs }
            );
            this.trigger('update_rate');
            console.log("Server response:", result);
            await playAudio('/o2b_stock_api/static/src/audio/gate_rate_audio_file.mp3');
            return result;
        } catch (error) {
            console.error("Error during ORM call:", error);
            throw error;
        }
    },

    async validate() {
        await this.save();

        const playAudio = async (audioPath) => {
            try {
                const audio = new Audio(audioPath);
                audio.volume = 1.0;
                await audio.play();
            } catch (error) {
                console.error("Error playing audio:", error);
            }
        };

        const options = {
            on_close: (ev) => this._closeValidate(ev),
        };

        const pickingId = this.record['id'];
        const pickingTypeId = this.record['picking_type_id'];
        const allQuantitiesMatched = this.pages[0].lines.every(
            (line) => line.product_uom_qty === line.qty_done
        );

        if (!allQuantitiesMatched) {
            await playAudio('/o2b_stock_api/static/src/audio/partial_order_not_validate.mp3');
            const message = sprintf(_t("Partial- DO are not allowed in system."));
            Dialog.alert(this, _t(message), { title: _t("Warning") });
            return;
        }else{
            try {
                const pickingTypeResult = await this.orm.read('stock.picking.type', [pickingTypeId], ['sequence_code']);
                if (pickingTypeResult && pickingTypeResult.length > 0) {
                    const sequenceCode = pickingTypeResult[0].sequence_code;
                    console.log("Sequence code:", sequenceCode);

                    if (sequenceCode === 'OUT') {
                        const pickingResult = await this.orm.read('stock.picking', [pickingId], ['time_tracking_ids']);
                        if (pickingResult && pickingResult[0]['time_tracking_ids'].length > 0) {
                            console.log("Time tracking IDs:", pickingResult[0]['time_tracking_ids']);

                            const methodDetails = {
                                model: this.params.model,
                                method: 'get_tracking_data',
                                args: [this.params.id],
                            };

                            try {
                                const trackingDataResult = await this.orm.call(
                                    methodDetails.model,
                                    methodDetails.method,
                                    methodDetails.args,
                                );

                                console.log("Server response:", trackingDataResult);
                            } catch (error) {
                                console.error("Error during ORM call:", error);
                                throw error;
                            }

                            let action, isSuccessful;

                            try {
                                action = await this.orm.call(
                                    this.params.model,
                                    this.validateMethod,
                                    [this.recordIds]
                                );
                                isSuccessful = action;
                            } catch (error) {
                                isSuccessful = false;
                            }
                            if (isSuccessful) {
                                await playAudio('/o2b_stock_api/static/src/audio/order_validate_done.mp3');
                                return options.on_close();
                            } else {
                                return options.on_close();
                            }
                        } else {
                            await playAudio('/o2b_stock_api/static/src/audio/without_timetracking_do.mp3');
                            const message = sprintf(_t("Without Time Tracking Delivery Order can't be executed."));
                            Dialog.alert(this, _t(message), { title: _t("Warning") });
                            return;
                        }
                    } else{
                        let action, isSuccessful;

                        try {
                            action = await this.orm.call(
                                this.params.model,
                                this.validateMethod,
                                [this.recordIds]
                            );
                            isSuccessful = action;
                        } catch (error) {
                            isSuccessful = false;
                        }

                        if (isSuccessful) {
                            await playAudio('/o2b_stock_api/static/src/audio/order_validate_done.mp3');
                            return options.on_close();
                        } else {
                            return options.on_close();
                        }
                    }
                } else {
                    console.error("Failed to fetch stock.picking.type with ID:", pickingTypeId);
                    return;
                }

            } catch (error) {
                console.error("Error during validation:", error);
                throw error;
            }
        }
    },


    selectLine(line) {
        this._super(line);
        this.playAudio('/o2b_stock_api/static/src/audio/item_scann_beep.mp3');

        const allQuantitiesMatched = this.pages[0].lines.every(
            (line) => line.product_uom_qty === line.qty_done
        );

        const pickingTypeId = this.record['picking_type_id'];
        const options = {
            on_close: ev => this._closeValidate(ev)
        };

        if (allQuantitiesMatched) {
            try {
                this.orm.read('stock.picking.type', [pickingTypeId], ['sequence_code'])
                    .then(async (result) => {
                        try {
                            if (result && result.length > 0) {
                                const sequenceCode = result[0].sequence_code;
                                console.log("Sequence code:", sequenceCode);

                                if (sequenceCode === 'PICK') {
                                    const pickingId = this.record['id'];
                                    const pickingResult = await this.orm.read('stock.picking', [pickingId], ['time_tracking_ids']);
                                    
                                    if (pickingResult && pickingResult[0]['time_tracking_ids'].length > 0) {
                                        console.log("Time tracking IDs:", pickingResult[0]['time_tracking_ids']);

                                        const methodDetails = {
                                            model: this.params.model,
                                            method: 'get_tracking_data',
                                            args: [this.params.id],
                                        };

                                        const result = await this.orm.call(
                                            methodDetails.model,
                                            methodDetails.method,
                                            methodDetails.args,
                                        );

                                        await this.validate();
                                        options.on_close(result);
                                    } else {
                                        await this.playAudio('/o2b_stock_api/static/src/audio/without_timetracking_do.mp3');
                                        const message = sprintf(_t("Without Time Tracking, Delivery Order can't be executed."));
                                        Dialog.alert(this, _t(message), { title: _t("Warning") });
                                        return;
                                    }
                                }
                            } else {
                                console.error("Failed to fetch stock.picking.type with ID:", pickingTypeId);
                            }
                        } catch (error) {
                            console.error("Error during sequenceCode check:", error);
                            throw error;
                        }
                    })
                    .catch((error) => {
                        console.error("Error fetching stock.picking.type:", error);
                    });
            } catch (error) {
                console.error("Error in ORM read:", error);
            }
        } else {
            console.log("Not all quantities matched. Skipping operation.");
        }
    },


    async _processBarcode(barcode) {
        await this._super(barcode);
        const barcodeData = await this._parseBarcode(barcode);
        const isSpecialBarcode = ["O-BTN.pack", "O-BTN.rate", "O-BTN.validate"].includes(barcodeData.barcode);
        const isInvalidBarcode = !barcodeData.product && !barcodeData.packageType && !isSpecialBarcode;
        if (isInvalidBarcode){
            console.log("Invalid product barcode.");
            await this.playAudio('/o2b_stock_api/static/src/audio/product_not_exist.mp3');
            Dialog.alert(
                this,
                _t("Invalid Product is selected"),
                { title: _t("Validation Warning") }
            );
            return;
        }

        const pickingTypeId = this.record['picking_type_id'];

        if (barcodeData.packageType && !isSpecialBarcode) {
            try {
                const result = await this.orm.read('stock.picking.type', [pickingTypeId], ['sequence_code']);
                if (result && result.length > 0) {
                    const sequenceCode = result[0].sequence_code;
                    console.log("Sequence code:", sequenceCode);

                    if (sequenceCode === 'PICK') {
                        await this.playAudio('/o2b_stock_api/static/src/audio/no_package_type.mp3');
                        Dialog.alert(
                            this,
                            _t("Cannot select Package Type in PICK DO."),
                            { title: _t("Validation Warning") }
                        );
                    }
                } else {
                    console.error("No sequence code found for stock.picking.type with ID:", pickingTypeId);
                }
            } catch (error) {
                console.error("Error reading stock.picking.type:", error);
            }
        }
    },
});