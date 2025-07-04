/** @odoo-module **/

import BarcodeModel from '@stock_barcode/models/barcode_model';
import BarcodePickingModel from '@stock_barcode/models/barcode_picking_model';
import { patch } from 'web.utils';
import { sprintf } from '@web/core/utils/strings';
import {_t} from "web.core";
const Dialog = require('web.Dialog');

patch(BarcodeModel.prototype, 'om_foods_barcode_scan', {

    async _createNewLine(params) {
        if (params.copyOf && params.copyOf.product_id.id === params.fieldsParams.product_id.id && params.copyOf.product_uom_qty === params.copyOf.qty_done) {
            const message = sprintf(_t("You cannot add more quantity than demand quantity of '%s'"),params.copyOf.display_name);
            Dialog.alert(this, _t(message), {title: _t("Warning")});
            return;
        }
        var currentPage = this.pages[this.pageIndex];
        var product_id_list = []
        for (var z = 0; z < currentPage.lines.length; z++){
            var lineInCurrentPage = currentPage.lines[z];
            product_id_list.push(lineInCurrentPage.product_id.id)
        }
        // H13733 - Jared Kipe - Special case where there is no TotalProductQty because we created a transfer in the barcode app
        var TotalProductQty = this.pages[0].lines.reduce((prev,next) => prev + next.product_uom_qty,0);
        if (TotalProductQty && product_id_list && !product_id_list.includes(params.fieldsParams.product_id.id)) {
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
            await this.playAudio('/o2b_stock_api/static/src/audio/product_not_exist.mp3');
            const message = sprintf(_t("The scanned product is not in '%s'"),this.name || 'Current Order');
            Dialog.alert(this, _t(message), {title: _t("Warning")});
            return;
        }
        // H13733 - Jared Kipe - commented out something that raises an exception if it ever got there
        // replace with version of super from below function
        // const newLine = super._createNewLine(params);
        const newLine = this._super(params);
        return newLine;
    },

    async validate() {
        var ProductQty = this.pages[0].lines.reduce((prev,next) => prev + next.product_uom_qty,0);
        var QtyDone = this.pages[0].lines.reduce((prev,next) => prev + next.qty_done,0);
        // H13733 - Jared Kipe - Special case where there is no ProductQty because we created a transfer in the barcode app
        if (ProductQty && ProductQty !== QtyDone){
            var message = _t('You cannot validate order because all quantities are not scanned yet.');
            Dialog.alert(this, _t(message), {title: _t("Warning")});
            return;
        }
        const res = this._super()
        return res;
    },
});

patch(BarcodePickingModel.prototype, 'om_foods_barcode_scan', {

    async _processPackageType(barcodeData) {
        const { packageType } = barcodeData;
        const line = this.selectedLine;
        // if (!line || !line.qty_done) {
        //     barcodeData.stopped = true;
        //     const message = _t("You can't apply a package type. First, scan product or select a line");
        //     return this.notification.add(message, { type: 'warning' });
        // }
        const resultPackage = line.result_package_id;
        if (!resultPackage) { // No package on the line => Do a put in pack.
            const additionalContext = { default_package_type_id: packageType.id };
            if (barcodeData.packageName) {
                additionalContext.default_name = barcodeData.packageName;
            }
            await this._putInPack(additionalContext);
        } else if (resultPackage.package_type_id.id !== packageType.id) {
            // Changes the package type for the scanned one.
            await this.save();
            await this.orm.write('stock.quant.package', [resultPackage.id], {
                package_type_id: packageType.id,
            });
            const message = sprintf(
                _t("Package type %s was correctly applied to the package %s"),
                packageType.name, resultPackage.name
            );
            this.notification.add(message, { type: 'success' });
            this.trigger('refresh');
        }
    },

    async playAudio(audioPath) {
        try {
            const audio = new Audio(audioPath);
            audio.volume = 1.0;  // Set desired volume
            await audio.play();
        } catch (error) {
            console.error("Error playing audio:", error);  // Handle audio errors
        }
    },

    async _getNoteText(htmlContent) {
        const tempElement = document.createElement('div');
        tempElement.innerHTML = htmlContent;
        return tempElement.textContent || tempElement.innerText || "";
    },

    async _putInPack(additionalContext = {}) {
        const context = Object.assign({ barcode_view: true }, additionalContext);
        if (!this.groups.group_tracking_lot) {
                return this.notification.add(
                    _t("To use packages, enable 'Packages' in the settings"),
                    { type: 'danger'}
                );
            }
        await this.save();
        const allQuantitiesMatched = this.pages[0].lines.every(
                (line) => line.product_uom_qty === line.qty_done
            );

        let totalWeight = 0
        let packageWeightLimit = 0 

        if ('default_package_type_id' in context) {
            const packageTypeId = context.default_package_type_id;
            const packageTypeResult = await this.orm.read(
                'stock.package.type',
                [packageTypeId],
                ['max_weight']
            );

            if (packageTypeResult && packageTypeResult.length > 0) {
                packageWeightLimit = packageTypeResult[0].max_weight;

                for (const line of this.pages[0].lines) {
                    if (line.product_id && line.qty_done && !line.result_package_id) {
                        const productDetails = await this.orm.read(
                            'product.product',
                            [line.product_id.id],
                            ['weight']
                        );

                        if (productDetails && productDetails.length > 0 && 'weight' in productDetails[0]) {
                            const productWeight = productDetails[0].weight;
                            const weight = line.qty_done * productWeight;
                            totalWeight += weight;
                        }
                    }
                }
            }
        };
        if (totalWeight > packageWeightLimit) {
            await this.playAudio('/o2b_stock_api/static/src/audio/weight_exceeds.mp3');
            const message = sprintf(_t("Total weight exceeds the package limit."));
            Dialog.alert(this, _t(message), {title: _t("Warning")});
            return;
        };
        
        const pickingTypeId = this.record['picking_type_id'];
        this.orm.read('stock.picking.type', [pickingTypeId], ['sequence_code'])
            .then(async (result) => {
                if (result && result.length > 0) {
                    const sequenceCode = result[0].sequence_code;
                    console.log("Sequence code:", sequenceCode);
                    console.log("context code:", context);
                    if (sequenceCode === 'OUT') {
                        const result = await this.orm.call(
                            this.params.model,
                            'action_select_package',
                            [[this.params.id]],
                            { context }
                        );
                        if ('default_package_type_id' in context) {
                            await this.playAudio('/o2b_stock_api/static/src/audio/package_selected.mp3');
                            const allQuantitiesMatched = this.pages[0].lines.every(
                                (line) => line.product_uom_qty === line.qty_done
                            );
                            if (allQuantitiesMatched) {
                                console.log("DEF_DELAY:");
                                const DEF_DELAY = 1000;
                                function sleep(ms) {
                                  return new Promise(resolve => setTimeout(resolve, ms || DEF_DELAY));
                                }
                                await sleep(1000);
                                console.log("DEF_DELAY:");
                                await this._putInPack()
                                // await sleep(1000);
                                // await this._rate()
                                this.trigger('update');
                                this.trigger('refresh');
                            } else{
                                console.log("DEF_DELAY:");
                                const DEF_DELAY = 2000;
                                function sleep(ms) {
                                  return new Promise(resolve => setTimeout(resolve, ms || DEF_DELAY));
                                }
                                await sleep(2000);
                                console.log("DEF_DELAY:");
                                await this.playAudio('/o2b_stock_api/static/src/audio/product_packed_audio_file.mp3');
                                await this._putInPack()
                                this.trigger('update');
                                this.trigger('refresh');
                            }
                        }else{
                            // await this._putInPack()
                            // const allQuantitiesMatched = this.pages[0].lines.every(
                            //     (line) => line.product_uom_qty === line.qty_done
                            // );
                            if (allQuantitiesMatched) {
                                // await this._putInPack()
                                await this._rate()

                                const pickingId = this.record['id'];
                                const pickingcostResult = await this.orm.read('stock.picking', [pickingId], ['get_min_cost']);
                                const pickingnote = await this.orm.read('stock.picking', [pickingId], ['note']);
                                const customernoteResult = await this.orm.read('stock.picking', [pickingId], ['x_studio_field_F7ZDy']);
                                const permanentcustomernoteResult = await this.orm.read('stock.picking', [pickingId], ['x_studio_permanent_customer_notes']);
                                const settings = await this.orm.call('res.config.settings', 'default_get', [['shipping_max_value']]);
                                const shippingMaxValue = settings.shipping_max_value;

                                const noteTextPromise = this._getNoteText(pickingnote[0]['note']);
                                const permanentCustomerNoteTextPromise = this._getNoteText(permanentcustomernoteResult[0]['x_studio_permanent_customer_notes']);

                                Promise.all([noteTextPromise, permanentCustomerNoteTextPromise]).then(([noteText, permanentCustomerNoteText]) => {
                                    console.log("Note Text:", noteText);
                                    console.log("Permanent Customer Note Text:", permanentCustomerNoteText);

                                    if ((pickingcostResult[0]['get_min_cost'] <= shippingMaxValue) && ((!customernoteResult[0]['x_studio_field_F7ZDy'])) && (!permanentCustomerNoteText || permanentCustomerNoteText == false || permanentCustomerNoteText == 'false') && (!noteText || noteText == false || noteText == 'false')) {
                                        this.validate();
                                    } else {
                                        this.trigger('update');
                                        this.trigger('refresh');
                                    }
                                });
                                // this.trigger('update');
                            }else{
                                this.trigger('update');
                                this.trigger('refresh');
                            }
                        }
                    } else{
                        if (!('default_package_type_id' in context)) {
                            await this.playAudio('/o2b_stock_api/static/src/audio/no_putinpack_in_pick_do.mp3');
                            const message = sprintf(_t("PICK DO does Not Allow PUT IN PACK Operation"));
                            Dialog.alert(this, _t(message), {title: _t("Warning")});
                            return;
                        }
                    }
                }
            });
    },

    // async _putInPack(additionalContext = {}) {
    //     const context = Object.assign({ barcode_view: true }, additionalContext);
    //     if (!this.groups.group_tracking_lot) {
    //         return this.notification.add(
    //             _t("To use packages, enable 'Packages' in the settings"),
    //             { type: 'danger'}
    //         );
    //     }
    //     await this.save();
    //     const result = await this.orm.call(
    //         this.params.model,
    //         'action_select_package',
    //         [[this.params.id]],
    //         { context }
    //     );
    //     const allQuantitiesMatched = this.pages[0].lines.every(
    //         (line) => line.product_uom_qty === line.qty_done
    //     );
    //     const pickingTypeId = this.record['picking_type_id'];
    //     this.orm.read('stock.picking.type', [pickingTypeId], ['sequence_code'])
    //         .then(async (result) => {
    //             if (result && result.length > 0) {
    //                 const sequenceCode = result[0].sequence_code;
    //                 console.log("Sequence code:", sequenceCode);

    //                 if ('default_package_type_id' in context) {
    //                     if (sequenceCode === 'OUT') {
    //                         await this.playAudio('/o2b_stock_api/static/src/audio/package_selected.mp3');
    //                         await this._putInPack()
    //                         const allQuantitiesMatched = this.pages[0].lines.every(
    //                             (line) => line.product_uom_qty === line.qty_done
    //                         );
    //                         if (allQuantitiesMatched) {
    //                             await this._rate()
    //                         }
    //                         this.trigger('update');
    //                         this.trigger('refresh');
    //                     }
    //                 } else {
    //                     if(!allQuantitiesMatched){
    //                     await this.playAudio('/o2b_stock_api/static/src/audio/product_packed_audio_file.mp3');
    //                     // await this._putInPack()
    //                     this.trigger('update');
    //                     this.trigger('refresh');
    //                     }
    //                 }
    //             }else {
    //                 console.error("Failed to fetch stock.picking.type with ID:", pickingTypeId);
    //             }
    //         })
    //         .catch((error) => {
    //             console.error("Error during ORM call:", error); // Handle ORM errors
    //         });
    // },

});