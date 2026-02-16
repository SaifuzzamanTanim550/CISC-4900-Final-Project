from src.services.inventory_service import get_current_stock

item_id = 1
location_id = 1

stock = get_current_stock(item_id=item_id, location_id=location_id, item_variant_id=None)
print("Current stock:", stock)
