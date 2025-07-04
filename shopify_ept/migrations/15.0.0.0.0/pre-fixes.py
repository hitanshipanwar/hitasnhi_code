# Hibou Corp. 2022

def migrate(cr, version):
    # fixes ERROR: insert or update on table "sale_order" violates foreign key constraint "sale_order_shopify_payment_gateway_id_fkey"
    # DETAIL:  Key (shopify_payment_gateway_id)=(21) is not present in table "shopify_payment_gateway_ept". 
    cr.execute('update sale_order set shopify_payment_gateway_id = null;')
    # fixes view errors, probably mostly with children that require a missing parent
    cr.execute("with view_ids as (select res_id from ir_model_data where module = 'shopify_ept' and model = 'ir.ui.view') delete from ir_ui_view where inherit_id in (select res_id from view_ids);")
    cr.execute("with view_ids as (select res_id from ir_model_data where module = 'shopify_ept' and model = 'ir.ui.view') delete from ir_ui_view where id in (select res_id from view_ids);")
    cr.execute("update ir_module_module set state = 'to remove' where name in ('auto_invoice_workflow_ept', 'sale_line_change', 'script_execute_log');")
    cr.execute("update ir_ui_view set active = false where name = 'Odoo Studio: res.company.form customization'")
    # fixes additional modules/models to remove
    # I got 'script.execute.log' from searching from model_id in (554, 553, 414, 384, 383, 505)
    cr.execute("delete from ir_cron where ir_actions_server_id in (select id from ir_act_server where model_name in ('script.execute.log'));")
    cr.execute("delete from ir_act_server where model_name in ('script.execute.log');")
    # fixes "odoo.sql_db: bad query: DELETE FROM sale_workflow_process_ept WHERE id IN (1) ERROR: null value in column "auto_workflow_id" violates not-null constraint"
    # given the above, we have to truncate sale.auto.workflow.configuration as this is a required field in that table
    cr.execute("truncate sale_auto_workflow_configuration;")
