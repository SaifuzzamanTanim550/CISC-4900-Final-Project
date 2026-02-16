import streamlit as st

st.set_page_config(
    page_title="Admissions Inventory System",
    page_icon="📦",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }
    .big-title { font-size: 44px; font-weight: 800; line-height: 1.1; margin-bottom: 0.25rem; }
    .subtitle { font-size: 16px; opacity: 0.85; margin-bottom: 1.25rem; }
    .card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.10);
        padding: 16px 18px;
        border-radius: 14px;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .card h4 { margin: 0; font-size: 14px; opacity: 0.9; font-weight: 700; }
    .icon { font-size: 28px; line-height: 1; margin-top: 8px; }
    .desc { font-size: 13px; opacity: 0.85; margin-top: 8px; }
    section[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,0.08); }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### 📦 Inventory System")
st.sidebar.caption("Admissions Inventory App")

st.markdown('<div class="big-title">Admissions Inventory Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Track stock, record activity, and spot low inventory fast.</div>', unsafe_allow_html=True)

# IMPORTANT: these must match your actual page file names inside /pages
DASHBOARD_PAGE = "pages/1_Dashboard.py"
STOCK_IN_PAGE = "pages/3_Stock_In.py"
STOCK_OUT_PAGE = "pages/4_Stock_Out.py"

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        """
        <div class="card">
            <div>
                <h4>Go to Dashboard</h4>
                <div class="icon">📊</div>
                <div class="desc">View KPIs, low stock, and usage</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Dashboard", use_container_width=True):
        st.switch_page(DASHBOARD_PAGE)

with c2:
    st.markdown(
        """
        <div class="card">
            <div>
                <h4>Record Stock In</h4>
                <div class="icon">➕</div>
                <div class="desc">Add items into a location</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Stock In", use_container_width=True):
        st.switch_page(STOCK_IN_PAGE)

with c3:
    st.markdown(
        """
        <div class="card">
            <div>
                <h4>Record Stock Out</h4>
                <div class="icon">➖</div>
                <div class="desc">Remove items and send alerts</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Stock Out", use_container_width=True):
        st.switch_page(STOCK_OUT_PAGE)

st.divider()

st.subheader("How to use this app")
st.write(
    """
    Use the sidebar to open a page.
    Dashboard shows quick metrics and low stock.
    Stock In and Stock Out records transactions.
    Reports helps you review activity.
    """
)

