import streamlit as st
from sqlalchemy import select
from src.db.database import get_db_session
from src.models.models import Item, ItemVariant


st.title("Variants Management")

session = get_db_session()

try:
    st.subheader("Add a size variant")

    items_with_variants = session.execute(
        select(Item).where(Item.has_variants == True).where(Item.is_active == True).order_by(Item.name)
    ).scalars().all()

    if not items_with_variants:
        st.info("No items marked as having variants yet. Go to Items and mark an item as having size variants.")
    else:
        item_options = {f"{i.id}. {i.name}": i.id for i in items_with_variants}

        with st.form("add_variant_form"):
            selected_item_label = st.selectbox("Select item", list(item_options.keys()))
            variant_name = st.selectbox("Size", ["XS", "S", "M", "L", "XL", "XXL"])
            submitted = st.form_submit_button("Add size")

            if submitted:
                item_id = item_options[selected_item_label]

                existing = session.execute(
                    select(ItemVariant)
                    .where(ItemVariant.item_id == item_id)
                    .where(ItemVariant.variant_name == variant_name)
                ).scalar_one_or_none()

                if existing:
                    st.error("This size already exists for the selected item")
                else:
                    v = ItemVariant(item_id=item_id, variant_name=variant_name, is_active=True)
                    session.add(v)
                    session.commit()
                    st.success("Variant added")
                    st.rerun()

    st.subheader("All variants")

    variants = session.execute(
        select(ItemVariant, Item)
        .join(Item, ItemVariant.item_id == Item.id)
        .order_by(Item.name, ItemVariant.variant_name)
    ).all()

    if not variants:
        st.info("No variants yet")
    else:
        header1, header2, header3 = st.columns([5, 2, 2])
        with header1:
            st.write("Item")
        with header2:
            st.write("Size")
        with header3:
            st.write("Status")

        for v, item in variants:
            col1, col2, col3 = st.columns([5, 2, 2])
            with col1:
                st.write(f"{item.name}")
            with col2:
                st.write(v.variant_name)
            with col3:
                st.write("Active" if v.is_active else "Inactive")

except Exception as e:
    st.error(f"Error: {e}")

finally:
    session.close()
