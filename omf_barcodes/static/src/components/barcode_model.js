/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import BarcodeModel from '@stock_barcode/models/barcode_model';

patch(BarcodeModel.prototype, 'omf_barcodes/static/src/components/barcode_model.js', {
    _sortingMethod(l1, l2) {
        // New lines always on top.
        if (!l1.id && l2.id) {
            return -1;
        } else if (l1.id && !l2.id) {
            return 1;
        } else if (l1.id && l2.id) {
            // Sort by aisle name of product.
            const aisle1 = l1.product_id.aisle_name || '';
            const aisle2 = l2.product_id.aisle_name || '';
            if (aisle1 < aisle2) {
                return -1;
            } else if (aisle1 > aisle2) {
                return 1;
            }
            // Sort by display name of product.
            const product1 = l1.product_id.display_name;
            const product2 = l2.product_id.display_name;
            if (product1 < product2) {
                return -1;
            } else if (product1 > product2) {
                return 1;
            }
            // Sort by picking name.
            const picking1 = l1.picking_id && l1.picking_id.name || '';
            const picking2 = l2.picking_id && l2.picking_id.name || '';
            if (picking1 < picking2) {
                return -1;
            } else if (picking1 > picking2) {
                return 1;
            }

            if (l1.id < l2.id) {
                return -1;
            } else if (l1.id > l2.id) {
                return 1;
            }
        }
        // Sort by id and/or virtual_id (creation of the line).
        if (l1.virtual_id > l2.virtual_id) {
            return -1;
        } else if (l1.virtual_id < l2.virtual_id) {
            return 1;
        }
        return 0;
    }
});
