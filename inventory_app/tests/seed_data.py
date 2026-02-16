from sqlalchemy import select
from src.db.database import get_db_session
from src.models.models import Item, ItemVariant, Location
from src.services.inventory_service import create_stock_in


def get_or_create_location(session, name, description=None):
    existing = session.execute(select(Location).where(Location.name == name)).scalar_one_or_none()
    if existing:
        return existing

    loc = Location(
        name=name,
        description=description,
        is_active=True,
    )
    session.add(loc)
    session.flush()
    return loc


def get_or_create_item(session, name, category, has_variants):
    existing = session.execute(select(Item).where(Item.name == name)).scalar_one_or_none()
    if existing:
        return existing

    item = Item(
        name=name,
        category=category,
        has_variants=has_variants,
        is_active=True,
    )
    session.add(item)
    session.flush()
    return item


def ensure_variants(session, item_id, sizes):
    existing = session.execute(
        select(ItemVariant).where(ItemVariant.item_id == item_id)
    ).scalars().all()

    existing_names = {v.variant_name for v in existing}

    for size in sizes:
        if size not in existing_names:
            v = ItemVariant(
                item_id=item_id,
                variant_name=size,
                is_active=True,
            )
            session.add(v)

    session.flush()


def seed():
    session = get_db_session()

    try:
        location = get_or_create_location(session, "Storage Room", "Main storage location")

        items_to_add = [
            ("T shirt", "Apparel", True),
            ("Hoodie", "Apparel", True),
            ("Staff jacket", "Apparel", True),
            ("Hat", "Apparel", False),
            ("Tote bag", "Apparel", False),
            ("Pen", "Stationery", False),
            ("Pencil", "Stationery", False),
            ("Folder", "Stationery", False),
            ("Sticker", "Stationery", False),
            ("Keychain", "Stationery", False),
            ("Brochure", "Printed materials", False),
            ("Campus map", "Printed materials", False),
            ("Program guide", "Printed materials", False),
            ("Mascot doll", "Fun item", False),
            ("Name tags", "Event equipment", False),
            ("Badge holders", "Event equipment", False),
            ("Tablecloth", "Event equipment", False),
            ("Banner", "Event equipment", False),
        ]

        size_variants = ["XS", "S", "M", "L", "XL", "XXL"]

        for name, category, has_variants in items_to_add:
            item = get_or_create_item(session, name, category, has_variants)

            if has_variants:
                ensure_variants(session, item.id, size_variants)

        session.commit()

        location_id = location.id

        print("Adding initial stock...")

        realistic_stock = {
            "T shirt": 120,
            "Hoodie": 60,
            "Staff jacket": 25,
            "Hat": 80,
            "Tote bag": 75,
            "Pen": 500,
            "Pencil": 300,
            "Folder": 200,
            "Sticker": 400,
            "Keychain": 150,
            "Brochure": 800,
            "Campus map": 600,
            "Program guide": 250,
            "Mascot doll": 40,
            "Name tags": 150,
            "Badge holders": 150,
            "Tablecloth": 10,
            "Banner": 5,
        }

        for item_name, qty in realistic_stock.items():
            item = session.execute(
                select(Item).where(Item.name == item_name)
            ).scalar_one()

            if item.has_variants:
                variants = session.execute(
                    select(ItemVariant).where(ItemVariant.item_id == item.id)
                ).scalars().all()

                per_size = max(1, qty // len(variants))

                for v in variants:
                    create_stock_in(
                        item_id=item.id,
                        location_id=location_id,
                        quantity=per_size,
                        reason="Initial seeded stock",
                        created_by="System Seed",
                        item_variant_id=v.id,
                        event_id=None,
                    )
            else:
                create_stock_in(
                    item_id=item.id,
                    location_id=location_id,
                    quantity=qty,
                    reason="Initial seeded stock",
                    created_by="System Seed",
                    item_variant_id=None,
                    event_id=None,
                )

        print("Seed complete with initial stock")

    finally:
        session.close()


if __name__ == "__main__":
    seed()
