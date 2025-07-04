/** @odoo-module **/

import LazyBarcodeCache from '@stock_barcode/lazy_barcode_cache';
import { patch } from 'web.utils';

patch(LazyBarcodeCache.prototype, 'o2b_stock_api', {
    constructor() {
        this._super(...arguments);

        const someCacheData = {};
        this.barcodeCache = new LazyBarcodeCache(someCacheData);
    },

    getRecord(model, id) {

        const record = this._super(model, id);

        if (model === 'stock.picking') {
            const audioPath = '/o2b_stock_api/static/src/audio/record_opened.mp3'; // Your audio file
            try {
                const audio = new Audio(audioPath);
                audio.volume = 1.0; // Set volume level
                audio.play().catch((error) => {
                    console.error("Error playing audio:", error);
                });
            } catch (error) {
                console.error("Audio playback error:", error);
            }
        }

        if (model === 'hr.employee') {
            const audioPath = '/o2b_stock_api/static/src/audio/employee_barcode.mp3'; // Your audio file
            try {
                const audio = new Audio(audioPath);
                audio.volume = 1.0; // Set volume level
                audio.play().catch((error) => {
                    console.error("Error playing audio:", error);
                });
            } catch (error) {
                console.error("Audio playback error:", error);
            }
        }

        return record;
    },

    // async _getBarcodeField(model) {
    //     // Check if the model is 'stock.picking' to play audio when scanned
    //     if (model === 'stock.picking') {
    //         try {
    //             const audio = new Audio('/o2b_stock_api/static/src/audio/record_opened.mp3'); // Ensure correct path
    //             audio.volume = 1.0;
    //             await audio.play().catch((error) => {
    //                 console.error("Error playing audio:", error);
    //             });
    //         } catch (error) {
    //             console.error("Exception while playing audio:", error);
    //         }
    //     }

    //     // Return the barcode field if it exists for the given model
    //     // if (!this.barcodeFieldByModel.hasOwnProperty(model)) {
    //     //     console.log("Barcode field not found for model:", model);
    //     //     return null;
    //     // }

    //     return this.barcodeFieldByModel[model];
    // },

    // async _getBarcodeField(model) {
    //     if (!this.barcodeFieldByModel.hasOwnProperty(model)) {
    //         return null;
    //     }
    //     if (model === 'stock.picking') {
    //         try {
    //             const audio = new Audio('/o2b_stock_api/static/src/audio/record_opened.mp3'); // Ensure correct path
    //             audio.volume = 1.0;
    //             await audio.play().catch((error) => {
    //                 console.error("Error playing audio:", error);
    //             });
    //         } catch (error) {
    //             console.error("Exception while playing audio:", error);
    //         }
    //     }
    //     return this.barcodeFieldByModel[model];
    // },
});