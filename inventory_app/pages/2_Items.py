import streamlit as st
import pandas as pd
from sqlalchemy import select, func
from src.db.database import get_db_session
from src.models.models import Item

st.title("Items")
st.caption("Add and manage inventory items used by the Admissions Office")

session = get_db_session()

try:
    # -------------------------
    # KPIs
    # -------------------------
    total_items = session.execute(select(func.count(Item.id))).scalar() or 0
    active_items = session.execute(
        select(func.count(Item.id)).where(Item.is_active == True)
    ).scalar() or 0
    variant_items = session.execute(
        select(func.count(Item.id)).where(Item.has_variants == True)
    ).scalar() or 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total items", total_items)
    with c2:
        st.metric("Active items", active_items)
    with c3:
        st.metric("Items with variants", variant_items)

    st.divider()

    # -------------------------
    # Add item (clean + compact)
    # -------------------------
    with st.expander("➕ Add a new item", expanded=False):
        categories = [
            "Apparel",
            "Stationery",
            "Printed materials",
            "Fun item",
            "Event equipment",
        ]

        with st.form("add_item_form"):
            name = st.text_input("Item name", placeholder="Example: Brochure, Pen, Hoodie")
            category = st.selectbox("Category", categories)
            has_variants = st.checkbox("This item has size variants")
            submitted = st.form_submit_button("Add item", use_container_width=True)

            if submitted:
                if not name.strip():
                    st.error("Item name is required")
                else:
                    existing = session.execute(
                        select(Item).where(Item.name == name.strip())
                    ).scalar_one_or_none()

                    if existing:
                        st.error("An item with this name already exists")
                    else:
                        item = Item(
                            name=name.strip(),
                            category=category,
                            has_variants=has_variants,
                            is_active=True,
                        )
                        session.add(item)
                        session.commit()
                        st.success("Item added")
                        st.rerun()

    # -------------------------
    # Filters
    # -------------------------
    st.subheader("All items")

    f1, f2, f3 = st.columns([3, 2, 2])
    with f1:
        search = st.text_input("Search", placeholder="Type to search by item name...")
    with f2:
        category_filter = st.selectbox(
            "Category",
            ["All"] + ["Apparel", "Stationery", "Printed materials", "Fun item", "Event equipment"],
        )
    with f3:
        status_filter = st.selectbox("Status", ["All", "Active", "Inactive"])

    items = session.execute(select(Item).order_by(Item.id)).scalars().all()

    if not items:
        st.info("No items yet")
    else:
        rows = []
        for item in items:
            rows.append(
                {
                    "ID": item.id,
                    "Item": item.name,
                    "Category": item.category,
                    "Has variants": "Yes" if item.has_variants else "No",
                    "Status": "Active" if item.is_active else "Inactive",
                }
            )

        df = pd.DataFrame(rows)

        # Apply filters
        if search.strip():
            df = df[df["Item"].str.lower().str.contains(search.strip().lower())]

        if category_filter != "All":
            df = df[df["Category"] == category_filter]

        if status_filter != "All":
            df = df[df["Status"] == status_filter]

        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")

finally:
    session.close()
