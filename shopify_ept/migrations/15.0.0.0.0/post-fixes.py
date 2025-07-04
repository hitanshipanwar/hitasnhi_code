# Hibou Corp. 2022

def migrate(cr, version):
    # post migration, the shopify fields are empty, but are not editable due to them being active
    cr.execute("update shopify_instance_ept set active = false;")
