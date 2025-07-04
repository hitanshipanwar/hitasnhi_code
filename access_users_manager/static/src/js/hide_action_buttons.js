/** @odoo-module **/

//import { ActionMenus } from "@web/legacy/js/components/action_menus";
import { registry } from "@web/core/registry";
var core = require('web.core');
const ActionMenus = require('web.ActionMenus');
var rpc = require('web.rpc');
var _t = core._t;
let access_action_registryId = 0;

ActionMenus.prototype._setActionItems = async function(props){
    let access_hide_actions =  await this.rpc({
            model: 'user.management',
            method: 'access_search_action_button',
            args: [[1], this.env.action.res_model]
        })

    let access_async_callback_Actions = (props.items.other || []).map((access_action) =>
        Object.assign({ key: `action-${access_action.description}` }, access_action)
    );

    if(access_hide_actions.length){
        access_async_callback_Actions = _.filter(access_async_callback_Actions,function(val){
            return !_.contains(access_hide_actions,val.description)
        })
    }

    const access_registry_Actions = [];
    for (const { Component, getProps } of registry.category("action_menus").getAll()) {
        const access_item_Props = await getProps(props, this.env);
        if (access_item_Props) {
            access_registry_Actions.push({
                Component,
                key: `registry-action-${access_action_registryId++}`,
                props: access_item_Props,
            });
        }
    }

    const access_all_actions = props.items.action || [];
    const access_format_Actions = access_all_actions.map((access_action) => ({
        action:access_action,
        description: access_action.name,
        key: access_action.id,
    }));



    return [ ...access_async_callback_Actions,...access_format_Actions,...access_registry_Actions];
}