from sqlalchemy import select, func, case
from src.db.database import get_db_session
from src.models.models import Transaction, Item, ItemVariant, Location, Event
from src.services.email_service import send_stock_out_email, send_low_stock_email


def get_current_stock(item_id, location_id, item_variant_id=None):
    """
    Returns current stock for:
    - item_id
    - location_id
    - optional item_variant_id
    """

    session = get_db_session()

    try:
        stmt = (
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (Transaction.transaction_type == "IN", Transaction.quantity),
                            else_=-Transaction.quantity,
                        )
                    ),
                    0,
                )
            )
            .where(Transaction.item_id == item_id)
            .where(Transaction.location_id == location_id)
        )

        if item_variant_id is not None:
            stmt = stmt.where(Transaction.item_variant_id == item_variant_id)
        else:
            stmt = stmt.where(Transaction.item_variant_id.is_(None))

        result = session.execute(stmt).scalar_one()

        return result

    finally:
        session.close()


def create_stock_in(
    item_id,
    location_id,
    quantity,
    reason,
    created_by,
    item_variant_id=None,
    event_id=None,
):
    session = get_db_session()

    try:
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a whole number greater than 0")

        if not reason or not reason.strip():
            raise ValueError("Reason is required")

        if not created_by or not created_by.strip():
            raise ValueError("Created_by is required")

        item = session.get(Item, item_id)
        if not item or not item.is_active:
            raise ValueError("Item not found or inactive")

        if item.has_variants:
            if item_variant_id is None:
                raise ValueError("Variant is required for this item")
            variant = session.get(ItemVariant, item_variant_id)
            if not variant or not variant.is_active or variant.item_id != item_id:
                raise ValueError("Variant not found, inactive, or does not match item")
        else:
            if item_variant_id is not None:
                raise ValueError("Variant must be empty for this item")

        tx = Transaction(
            transaction_type="IN",
            item_id=item_id,
            item_variant_id=item_variant_id,
            location_id=location_id,
            event_id=event_id,
            quantity=quantity,
            reason=reason.strip(),
            created_by=created_by.strip(),
        )

        session.add(tx)
        session.commit()
        session.refresh(tx)

        return tx

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def create_stock_out(
    item_id,
    location_id,
    quantity,
    reason,
    created_by,
    item_variant_id=None,
    event_id=None,
):
    session = get_db_session()

    try:
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a whole number greater than 0")

        if not reason or not reason.strip():
            raise ValueError("Reason is required")

        if not created_by or not created_by.strip():
            raise ValueError("Created_by is required")

        item = session.get(Item, item_id)
        if not item or not item.is_active:
            raise ValueError("Item not found or inactive")

        if item.has_variants:
            if item_variant_id is None:
                raise ValueError("Variant is required for this item")
            variant = session.get(ItemVariant, item_variant_id)
            if not variant or not variant.is_active or variant.item_id != item_id:
                raise ValueError("Variant not found, inactive, or does not match item")
        else:
            if item_variant_id is not None:
                raise ValueError("Variant must be empty for this item")

        current_stock = get_current_stock(
            item_id=item_id,
            location_id=location_id,
            item_variant_id=item_variant_id,
        )

        if quantity > current_stock:
            raise ValueError(f"Not enough stock. Current stock is {current_stock}")

        tx = Transaction(
            transaction_type="OUT",
            item_id=item_id,
            item_variant_id=item_variant_id,
            location_id=location_id,
            event_id=event_id,
            quantity=quantity,
            reason=reason.strip(),
            created_by=created_by.strip(),
        )

        session.add(tx)
        session.commit()
        session.refresh(tx)

        # -----------------------------
        # Step 7: Send stock out email
        # -----------------------------

        new_stock = get_current_stock(
            item_id=item_id,
            location_id=location_id,
            item_variant_id=item_variant_id,
        )

        item_name = item.name
        location_obj = session.get(Location, location_id)

        variant_line = ""
        if item_variant_id is not None:
            v = session.get(ItemVariant, item_variant_id)
            if v:
                variant_line = f"Size: {v.variant_name}\n"

        subject = f"Stock out recorded: {item_name}"
        body = (
            f"Stock out recorded\n\n"
            f"Item: {item_name}\n"
            f"{variant_line}"
            f"Location: {location_obj.name}\n"
            f"Quantity: {quantity}\n"
            f"New on hand: {new_stock}\n"
            f"Reason: {reason}\n"
            f"Created by: {created_by}\n"
        )

        if event_id is not None:
            ev = session.get(Event, event_id)
            if ev:
                body += f"Event: {ev.name}\n"

        send_stock_out_email(subject, body)

        check_and_send_low_stock_alert(
            item_id=item_id,
            location_id=location_id,
            item_variant_id=item_variant_id,
            threshold=10,
        )

        return tx

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


# Step 6: Low stock helper
def check_and_send_low_stock_alert(item_id, location_id, item_variant_id, threshold=10):
    session = get_db_session()

    try:
        current_stock = get_current_stock(
            item_id=item_id,
            location_id=location_id,
            item_variant_id=item_variant_id,
        )

        if current_stock > threshold:
            return

        item = session.get(Item, item_id)
        location = session.get(Location, location_id)

        variant_text = ""
        if item_variant_id is not None:
            variant = session.get(ItemVariant, item_variant_id)
            if variant:
                variant_text = f"Size: {variant.variant_name}\n"

        subject = f"Low stock alert: {item.name} at {location.name}"
        body = (
            f"Low stock alert\n\n"
            f"Item: {item.name}\n"
            f"{variant_text}"
            f"Location: {location.name}\n"
            f"On hand: {current_stock}\n"
            f"Threshold: {threshold}\n"
        )

        send_low_stock_email(subject, body)

    finally:
        session.close()
