import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from sqlalchemy import select, func
from src.db.database import get_db_session
from src.models.models import Transaction, Event, Item, ItemVariant, Location


st.title("Reports")

session = get_db_session()

try:
    st.caption("Usage reports and CSV exports")

    tab1, tab2, tab3 = st.tabs(["Usage by event", "Monthly usage", "Export CSV"])

    with tab1:
        st.subheader("Usage by event")

        events = session.execute(
            select(Event).where(Event.is_active == True).order_by(Event.event_date.desc())
        ).scalars().all()

        if not events:
            st.info("No events yet")
        else:
            event_labels = {f"{e.id}. {e.name} ({e.event_type}, {e.event_date})": e.id for e in events}
            selected_event_label = st.selectbox("Select event", list(event_labels.keys()))
            event_id = event_labels[selected_event_label]

            rows = session.execute(
                select(
                    Transaction.item_id,
                    Transaction.item_variant_id,
                    func.sum(Transaction.quantity).label("total_out"),
                )
                .where(Transaction.transaction_type == "OUT")
                .where(Transaction.event_id == event_id)
                .group_by(Transaction.item_id, Transaction.item_variant_id)
                .order_by(func.sum(Transaction.quantity).desc())
            ).all()

            if not rows:
                st.info("No stock out transactions for this event")
            else:
                out_rows = []
                for item_id, variant_id, total_out in rows:
                    item = session.get(Item, item_id)

                    variant_name = ""
                    if variant_id is not None:
                        variant = session.get(ItemVariant, variant_id)
                        variant_name = variant.variant_name if variant else ""

                    out_rows.append(
                        {
                            "Item": item.name if item else str(item_id),
                            "Variant": variant_name,
                            "Total given out": int(total_out),
                        }
                    )

                df = pd.DataFrame(out_rows)
                st.dataframe(df, use_container_width=True, hide_index=True)

                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download event usage CSV",
                    data=csv_bytes,
                    file_name="event_usage.csv",
                    mime="text/csv",
                )

    with tab2:
        st.subheader("Monthly usage")

        months_back = st.number_input("Months back", min_value=1, step=1, value=6)

        cutoff = datetime.utcnow() - timedelta(days=int(months_back) * 31)

        rows = session.execute(
            select(
                func.date_trunc("month", Transaction.created_at).label("month"),
                Transaction.item_id,
                Transaction.item_variant_id,
                func.sum(Transaction.quantity).label("total_out"),
            )
            .where(Transaction.transaction_type == "OUT")
            .where(Transaction.created_at >= cutoff)
            .group_by(
                func.date_trunc("month", Transaction.created_at),
                Transaction.item_id,
                Transaction.item_variant_id,
            )
            .order_by(func.date_trunc("month", Transaction.created_at).desc())
        ).all()

        if not rows:
            st.info("No usage yet")
        else:
            out_rows = []
            for month, item_id, variant_id, total_out in rows:
                item = session.get(Item, item_id)

                variant_name = ""
                if variant_id is not None:
                    variant = session.get(ItemVariant, variant_id)
                    variant_name = variant.variant_name if variant else ""

                out_rows.append(
                    {
                        "Month": month.strftime("%Y-%m"),
                        "Item": item.name if item else str(item_id),
                        "Variant": variant_name,
                        "Total given out": int(total_out),
                    }
                )

            df = pd.DataFrame(out_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download monthly usage CSV",
                data=csv_bytes,
                file_name="monthly_usage.csv",
                mime="text/csv",
            )

    with tab3:
        st.subheader("Export transactions CSV")

        tx_type = st.selectbox("Transaction type", ["All", "IN", "OUT"])

        start_date = st.date_input("Start date", value=date.today() - timedelta(days=30))
        end_date = st.date_input("End date", value=date.today())

        locations = session.execute(
            select(Location).where(Location.is_active == True).order_by(Location.name)
        ).scalars().all()

        location_labels = ["All"]
        location_map = {"All": None}
        for l in locations:
            label = f"{l.id}. {l.name}"
            location_labels.append(label)
            location_map[label] = l.id

        selected_location_label = st.selectbox("Location", location_labels)
        location_id = location_map[selected_location_label]

        events = session.execute(
            select(Event).where(Event.is_active == True).order_by(Event.event_date.desc())
        ).scalars().all()

        event_labels = ["All"]
        event_map = {"All": None}
        for e in events:
            label = f"{e.id}. {e.name} ({e.event_date})"
            event_labels.append(label)
            event_map[label] = e.id

        selected_event_label = st.selectbox("Event", event_labels)
        event_id = event_map[selected_event_label]

        query = select(Transaction).where(Transaction.created_at >= datetime.combine(start_date, datetime.min.time()))
        query = query.where(Transaction.created_at <= datetime.combine(end_date, datetime.max.time()))

        if tx_type != "All":
            query = query.where(Transaction.transaction_type == tx_type)

        if location_id is not None:
            query = query.where(Transaction.location_id == location_id)

        if event_id is not None:
            query = query.where(Transaction.event_id == event_id)

        txs = session.execute(query.order_by(Transaction.created_at.desc())).scalars().all()

        if not txs:
            st.info("No matching transactions")
        else:
            rows = []
            for tx in txs:
                item = session.get(Item, tx.item_id)
                location = session.get(Location, tx.location_id)

                variant_name = ""
                if tx.item_variant_id is not None:
                    variant = session.get(ItemVariant, tx.item_variant_id)
                    variant_name = variant.variant_name if variant else ""

                event_name = ""
                if tx.event_id is not None:
                    ev = session.get(Event, tx.event_id)
                    event_name = ev.name if ev else ""

                rows.append(
                    {
                        "Time": tx.created_at.strftime("%Y-%m-%d %I:%M %p"),
                        "Type": tx.transaction_type,
                        "Location": location.name if location else "",
                        "Item": item.name if item else "",
                        "Variant": variant_name,
                        "Qty": tx.quantity,
                        "Reason": tx.reason,
                        "By": tx.created_by,
                        "Event": event_name,
                    }
                )

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download transactions CSV",
                data=csv_bytes,
                file_name="transactions_export.csv",
                mime="text/csv",
            )

finally:
    session.close()
