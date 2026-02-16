import streamlit as st
from sqlalchemy import select
from src.db.database import get_db_session
from src.models.models import Item, ItemVariant, Location, Event
from src.services.inventory_service import create_stock_in, get_current_stock


st.title("Stock In")

session = get_db_session()

try:
    locations = session.execute(
        select(Location).where(Location.is_active == True).order_by(Location.name)
    ).scalars().all()

    items = session.execute(
        select(Item).where(Item.is_active == True).order_by(Item.name)
    ).scalars().all()

    events = session.execute(
        select(Event).where(Event.is_active == True).order_by(Event.event_date.desc())
    ).scalars().all()

    if not locations:
        st.warning("No locations found. Add a location first.")
        st.stop()

    if not items:
        st.warning("No items found. Add an item first.")
        st.stop()

    location_options = {f"{l.id}. {l.name}": l.id for l in locations}
    item_options = {f"{i.id}. {i.name}": i.id for i in items}

    st.subheader("Choose item and location")

    selected_location_label = st.selectbox("Location", list(location_options.keys()))
    selected_item_label = st.selectbox("Item", list(item_options.keys()))

    location_id = location_options[selected_location_label]
    item_id = item_options[selected_item_label]

    selected_item = session.get(Item, item_id)

    item_variant_id = None
    if selected_item.has_variants:
        variants = session.execute(
            select(ItemVariant)
            .where(ItemVariant.item_id == item_id)
            .where(ItemVariant.is_active == True)
            .order_by(ItemVariant.variant_name)
        ).scalars().all()

        if not variants:
            st.warning("This item needs variants, but none exist yet. Add sizes first in Variants.")
            st.stop()

        variant_options = {f"{v.variant_name}": v.id for v in variants}
        selected_variant_label = st.selectbox("Size", list(variant_options.keys()))
        item_variant_id = variant_options[selected_variant_label]
    else:
        st.caption("This item has no variants.")

    st.subheader("Current stock")
    current_stock = get_current_stock(
        item_id=item_id,
        location_id=location_id,
        item_variant_id=item_variant_id,
    )
    st.write(current_stock)

    st.subheader("Add stock in")

    event_id = None
    event_labels = ["None"]
    event_map = {"None": None}

    for e in events:
        label = f"{e.id}. {e.name} ({e.event_type}, {e.event_date})"
        event_labels.append(label)
        event_map[label] = e.id

    with st.form("stock_in_form"):
        quantity = st.number_input("Quantity", min_value=1, step=1)
        reason = st.text_input("Reason")
        created_by = st.text_input("Created by")
        selected_event_label = st.selectbox("Event (optional)", event_labels)

        submitted = st.form_submit_button("Stock In")

        if submitted:
            event_id = event_map[selected_event_label]

            try:
                create_stock_in(
                    item_id=item_id,
                    location_id=location_id,
                    quantity=int(quantity),
                    reason=reason,
                    created_by=created_by,
                    item_variant_id=item_variant_id,
                    event_id=event_id,
                )
                st.success("Stock in recorded")
                st.rerun()

            except Exception as e:
                st.error(str(e))

finally:
    session.close()
