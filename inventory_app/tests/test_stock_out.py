from src.services.inventory_service import create_stock_out, get_current_stock

item_id = 1
location_id = 1

create_stock_out(
    item_id=item_id,
    location_id=location_id,
    quantity=20,
    reason="Giveaway",
    created_by="Tanim",
    item_variant_id=None,
)

stock = get_current_stock(item_id=item_id, location_id=location_id, item_variant_id=None)
print("Current stock after OUT:", stock)
