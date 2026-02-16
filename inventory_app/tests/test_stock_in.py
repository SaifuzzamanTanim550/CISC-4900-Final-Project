from src.services.inventory_service import create_stock_in, get_current_stock

item_id = 1
location_id = 1

create_stock_in(
    item_id=item_id,
    location_id=location_id,
    quantity=50,
    reason="Initial stock",
    created_by="Tanim",
    item_variant_id=None,
)

stock = get_current_stock(item_id=item_id, location_id=location_id, item_variant_id=None)
print("Current stock after IN:", stock)
