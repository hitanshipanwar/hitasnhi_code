/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import MainComponent from '@stock_barcode/components/main';
import { patch } from 'web.utils';

patch(MainComponent.prototype, 'o2b_stock_api', {

    async willStart() {
        await this._super(...arguments);
        this.env.model.on('update_rate', this, this._fetchMinDeliveryCharges);
        this.fetchMinDeliveryCharges();
    },

    async _fetchMinDeliveryCharges() {
        try {
            const result = await this.orm.read('stock.picking', [this.props.id], ['get_min_cost','carrier_id_name', 'shippment_comparison_rate']);
            if (result && result.length > 0) {
                this.state.minDeliveryCharges = result[0].get_min_cost;
                if (result[0].carrier_id_name == false){
                    this.state.carrier_id_name = ''
                }else{
                    this.state.carrier_id_name = result[0].carrier_id_name;
                }
                if (result[0].shippment_comparison_rate == false){
                    this.state.shippment_comparison_rate = ''
                }else{
                    this.state.shippment_comparison_rate = result[0].shippment_comparison_rate;
                }
            } else {
                this.state.minDeliveryCharges = 0;
                this.state.carrier_id_name = ''
                this.state.shippment_comparison_rate = ''
            }
        } catch (error) {
            console.error("Error fetching Min Delivery Charges:", error);
            this.state.minDeliveryCharges = 0;
            this.state.carrier_id_name = ''
            this.state.shippment_comparison_rate = ''
        }
    },
    async fetchMinDeliveryCharges() {
        try {
            const result = await this.orm.read('stock.picking', [this.props.id], ['get_min_cost','carrier_id_name', 'shippment_comparison_rate']);
            if (result && result.length > 0) {
                this.state.minDeliveryCharges = result[0].get_min_cost;
                if (result[0].carrier_id_name == false){
                    this.state.carrier_id_name = ''
                }else{
                    this.state.carrier_id_name = result[0].carrier_id_name;
                }
                if (result[0].shippment_comparison_rate == false){
                    this.state.shippment_comparison_rate = ''
                }else{
                    this.state.shippment_comparison_rate = result[0].shippment_comparison_rate;
                }
            } else {
                this.state.minDeliveryCharges = 0;
                this.state.carrier_id_name = ''
                this.state.shippment_comparison_rate = ''
            }
        } catch (error) {
            console.error("Error fetching Min Delivery Charges:", error);
            this.state.minDeliveryCharges = 0;
            this.state.carrier_id_name = ''
            this.state.shippment_comparison_rate = ''
        }
    },
});