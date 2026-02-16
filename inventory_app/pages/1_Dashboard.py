import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import select, func, case
from src.db.database import get_db_session
from src.models.models import Transaction, Item, ItemVariant, Location


st.title("Dashboard")

session = get_db_session()

try:
    st.caption("Simple overview")

    # ----------------------------
    # Better chart: Top items only
    # ----------------------------
    st.subheader("Top items by stock on hand")

    top_n = st.slider("How many items to show", 5, 15, 8)

    stock_by_item = session.execute(
        select(
            Transaction.item_id,
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.transaction_type == "IN", Transaction.quantity),
                        else_=-Transaction.quantity,
                    )
                ),
                0,
            ).label("on_hand"),
        )
        .group_by(Transaction.item_id)
        .order_by(
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.transaction_type == "IN", Transaction.quantity),
                        else_=-Transaction.quantity,
                    )
                ),
                0,
            ).desc()
        )
        .limit(top_n)
    ).all()

    if not stock_by_item:
        st.info("No stock data yet. Add Stock In first.")
    else:
        labels = []
        values = []

        # reverse so biggest appears at top in barh
        for item_id, on_hand in reversed(stock_by_item):
            item = session.get(Item, item_id)
            labels.append(item.name if item else str(item_id))
            values.append(int(on_hand))

        fig, ax = plt.subplots(figsize=(7, 3.2))
        ax.barh(labels, values)
        ax.set_xlabel("On hand")
        plt.tight_layout()
        st.pyplot(fig)

    st.divider()

    # ----------------------------
    # Low stock table
    # ----------------------------
    st.subheader("Low stock")

    threshold = st.number_input("Low stock threshold", min_value=1, step=1, value=10)

    stock_rows = session.execute(
        select(
            Transaction.location_id,
            Transaction.item_id,
            Transaction.item_variant_id,
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.transaction_type == "IN", Transaction.quantity),
                        else_=-Transaction.quantity,
                    )
                ),
                0,
            ).label("on_hand"),
        )
        .group_by(Transaction.location_id, Transaction.item_id, Transaction.item_variant_id)
    ).all()

    low_rows = []
    for location_id, item_id, variant_id, on_hand in stock_rows:
        on_hand_int = int(on_hand)
        if on_hand_int <= int(threshold):
            location = session.get(Location, location_id)
            item = session.get(Item, item_id)

            variant_name = ""
            if variant_id is not None:
                variant = session.get(ItemVariant, variant_id)
                variant_name = variant.variant_name if variant else ""

            low_rows.append(
                {
                    "Location": location.name if location else "",
                    "Item": item.name if item else "",
                    "Variant": variant_name,
                    "On hand": on_hand_int,
                }
            )

    if not low_rows:
        st.info("No low stock items at this threshold")
    else:
        low_df = pd.DataFrame(low_rows).sort_values(by=["On hand", "Item"])
        st.dataframe(low_df, use_container_width=True, hide_index=True)

    st.divider()

    # ----------------------------
    # Recent transactions
    # ----------------------------
    st.subheader("Recent transactions")

    txs = session.execute(
        select(Transaction)
        .order_by(Transaction.created_at.desc())
        .limit(50)
    ).scalars().all()

    if not txs:
        st.info("No transactions yet")
    else:
        rows = []
        for tx in txs:
            item = session.get(Item, tx.item_id)
            location = session.get(Location, tx.location_id)

            variant_name = ""
            if tx.item_variant_id is not None:
                variant = session.get(ItemVariant, tx.item_variant_id)
                variant_name = variant.variant_name if variant else ""

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
                }
            )

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

finally:
    session.close()
