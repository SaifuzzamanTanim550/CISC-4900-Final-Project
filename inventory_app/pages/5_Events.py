import streamlit as st
from sqlalchemy import select, func
from src.db.database import get_db_session
from src.models.models import Event, Location, Transaction, Item, ItemVariant


st.title("Events")

session = get_db_session()

try:
    st.subheader("Create event")

    locations = session.execute(
        select(Location).where(Location.is_active == True).order_by(Location.name)
    ).scalars().all()

    location_labels = ["None"]
    location_map = {"None": None}

    for l in locations:
        label = f"{l.id}. {l.name}"
        location_labels.append(label)
        location_map[label] = l.id

    with st.form("create_event_form"):
        name = st.text_input("Event name")
        event_type = st.text_input("Event type")
        event_date = st.date_input("Event date")
        selected_location_label = st.selectbox("Default location (optional)", location_labels)
        notes = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("Create event")

        if submitted:
            if not name.strip():
                st.error("Event name is required")
            elif not event_type.strip():
                st.error("Event type is required")
            else:
                loc_id = location_map[selected_location_label]
                e = Event(
                    name=name.strip(),
                    event_type=event_type.strip(),
                    event_date=event_date,
                    location_id=loc_id,
                    notes=notes.strip() if notes.strip() else None,
                    is_active=True,
                )
                session.add(e)
                session.commit()
                st.success("Event created")
                st.rerun()

    st.divider()

    st.subheader("Event summary")

    events = session.execute(
        select(Event).where(Event.is_active == True).order_by(Event.event_date.desc())
    ).scalars().all()

    if not events:
        st.info("No events yet")
        st.stop()

    event_options = {f"{e.id}. {e.name} ({e.event_type}, {e.event_date})": e.id for e in events}
    selected_event_label = st.selectbox("Select event", list(event_options.keys()))
    event_id = event_options[selected_event_label]

    st.write("Items given out for this event")

    summary_rows = session.execute(
        select(
            Transaction.item_id,
            Transaction.item_variant_id,
            func.sum(Transaction.quantity).label("total_out"),
        )
        .where(Transaction.event_id == event_id)
        .where(Transaction.transaction_type == "OUT")
        .group_by(Transaction.item_id, Transaction.item_variant_id)
        .order_by(func.sum(Transaction.quantity).desc())
    ).all()

    if not summary_rows:
        st.info("No stock out transactions linked to this event yet")
    else:
        for item_id, variant_id, total_out in summary_rows:
            item = session.get(Item, item_id)
            variant_label = ""
            if variant_id is not None:
                variant = session.get(ItemVariant, variant_id)
                variant_label = f" ({variant.variant_name})" if variant else ""
            st.write(f"{item.name}{variant_label}: {int(total_out)}")

    st.divider()

    st.subheader("Transactions for this event")

    txs = session.execute(
        select(Transaction)
        .where(Transaction.event_id == event_id)
        .order_by(Transaction.created_at.desc())
        .limit(50)
    ).scalars().all()

    if not txs:
        st.info("No transactions yet")
    else:
        for tx in txs:
            item = session.get(Item, tx.item_id)
            variant_label = ""
            if tx.item_variant_id is not None:
                variant = session.get(ItemVariant, tx.item_variant_id)
                variant_label = f" ({variant.variant_name})" if variant else ""

            st.write(
                f"{tx.created_at} | {tx.transaction_type} | {item.name}{variant_label} | qty {tx.quantity} | {tx.reason} | by {tx.created_by}"
            )

finally:
    session.close()
