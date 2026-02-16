import streamlit as st
from sqlalchemy import select
from src.db.database import get_db_session
from src.models.models import Location


st.title("Locations Management")

session = get_db_session()

try:
    st.subheader("Add a new location")

    with st.form("add_location_form"):
        name = st.text_input("Location name")
        description = st.text_input("Description (optional)")
        submitted = st.form_submit_button("Add location")

        if submitted:
            if not name.strip():
                st.error("Location name is required")
            else:
                existing = session.execute(
                    select(Location).where(Location.name == name.strip())
                ).scalar_one_or_none()

                if existing:
                    st.error("A location with this name already exists")
                else:
                    loc = Location(
                        name=name.strip(),
                        description=description.strip() if description.strip() else None,
                        is_active=True,
                    )
                    session.add(loc)
                    session.commit()
                    st.success("Location added")
                    st.rerun()

    st.subheader("All locations")

    locations = session.execute(select(Location).order_by(Location.id)).scalars().all()

    if not locations:
        st.info("No locations yet")
    else:
        for loc in locations:
            col1, col2, col3 = st.columns([3, 4, 2])

            with col1:
                st.write(f"{loc.id}. {loc.name}")

            with col2:
                st.write(loc.description or "")

            with col3:
                status = "Active" if loc.is_active else "Inactive"
                st.write(status)

except Exception as e:
    st.error(f"Error: {e}")

finally:
    session.close()
