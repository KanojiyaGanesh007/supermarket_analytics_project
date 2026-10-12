import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Supermarket Sales Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
    .main { background-color: #f7f9fc; }
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #e7ebf2;
        padding: 16px 18px;
        border-radius: 12px;
    }
    .block-container { padding-top: 1.5rem; }
    h1, h2, h3 { color: #172554; }
</style>
""", unsafe_allow_html=True)

st.title("🛒 Supermarket Sales Analytics")
st.caption("Sales performance • Customer behavior • Churn risk • Business recommendations")

DEFAULT_FILE = Path(__file__).parent / "supermarket_sales_cleaned.csv"

# ---------- Data loading and cleaning ----------
@st.cache_data
def load_data(uploaded_file, default_path):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    elif default_path.exists():
        df = pd.read_csv(default_path)
    else:
        return None

    # Standardize column names by trimming whitespace
    df.columns = [str(c).strip() for c in df.columns]

    required = [
        "Invoice ID", "Order Date", "Customer ID", "Product Category",
        "Product", "Region", "Quantity", "Unit Price", "Revenue", "Profit"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce", dayfirst=False)

    numeric_cols = ["Quantity", "Unit Price", "Revenue", "Profit"]
    for col in numeric_cols:
        # Handles values such as ₹1,200.50 or $1,200.50 as well as normal numbers
        cleaned = (
            df[col].astype(str)
            .str.replace(r"[₹$€£,]", "", regex=True)
            .str.replace(r"[^\d.\-]", "", regex=True)
        )
        df[col] = pd.to_numeric(cleaned, errors="coerce")

    text_cols = ["Invoice ID", "Customer ID", "Product Category", "Product", "Region"]
    for col in text_cols:
        df[col] = df[col].astype("string").str.strip()

    df = df.dropna(subset=["Order Date", "Customer ID", "Revenue", "Profit"])
    df = df.drop_duplicates()
    df["Quantity"] = df["Quantity"].fillna(0)
    df["Unit Price"] = df["Unit Price"].fillna(0)
    df = df[df["Revenue"] >= 0].copy()
    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["Month Name"] = df["Order Date"].dt.strftime("%b %Y")
    return df


uploaded = st.sidebar.file_uploader("Upload a sales CSV (optional)", type=["csv"])
try:
    df = load_data(uploaded, DEFAULT_FILE)
except Exception as exc:
    st.error(f"Could not read the dataset: {exc}")
    st.stop()

if df is None or df.empty:
    st.warning(
        "Dataset not found. Put `supermarket_sales_cleaned.csv` in the same folder "
        "as `app.py`, or upload the CSV using the sidebar."
    )
    st.stop()

# ---------- Sidebar filters ----------
st.sidebar.header("🔎 Filters")
min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()
date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

categories = sorted(df["Product Category"].dropna().unique().tolist())
regions = sorted(df["Region"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect("Product category", categories, default=categories)
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

filtered = df[
    (df["Order Date"].dt.date >= start_date)
    & (df["Order Date"].dt.date <= end_date)
    & (df["Product Category"].isin(selected_categories))
    & (df["Region"].isin(selected_regions))
].copy()

if filtered.empty:
    st.warning("No records match these filters. Change the date range, category, or region.")
    st.stop()

# ---------- Customer RFM / churn table ----------
# Use the latest date in the full dataset as the analysis snapshot, not today's date.
snapshot_date = df["Order Date"].max() + pd.Timedelta(days=1)
rfm = (
    df.groupby("Customer ID")
    .agg(
        Last_Order=("Order Date", "max"),
        Frequency=("Invoice ID", "nunique"),
        Monetary=("Revenue", "sum"),
        Total_Profit=("Profit", "sum"),
    )
    .reset_index()
)
rfm["Recency"] = (snapshot_date - rfm["Last_Order"]).dt.days
rfm["Churn Status"] = np.where(rfm["Recency"] >= 180, "At risk (180+ days)", "Recently active")
rfm["Risk Tier"] = pd.cut(
    rfm["Recency"],
    bins=[-1, 60, 120, 179, np.inf],
    labels=["Low", "Medium", "High", "Churn risk"],
).astype(str)

# ---------- Tabs ----------
tab_overview, tab_sales, tab_customers, tab_churn, tab_insights = st.tabs([
    "📊 Overview", "📈 Sales Analytics", "👥 Customer Analysis",
    "⚠️ Churn Analysis", "💡 Business Insights"
])

with tab_overview:
    st.subheader("Executive overview")
    revenue = filtered["Revenue"].sum()
    profit = filtered["Profit"].sum()
    orders = filtered["Invoice ID"].nunique()
    customers = filtered["Customer ID"].nunique()
    aov = revenue / orders if orders else 0
    margin = (profit / revenue * 100) if revenue else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Revenue", f"₹{revenue:,.2f}")
    m2.metric("Total Profit", f"₹{profit:,.2f}")
    m3.metric("Orders", f"{orders:,}")
    m4.metric("Unique Customers", f"{customers:,}")
    m5.metric("Profit Margin", f"{margin:.2f}%")

    left, right = st.columns(2)
    monthly = filtered.groupby("Month", as_index=False).agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"))
    with left:
        st.markdown("#### Monthly revenue")
        fig = px.line(monthly, x="Month", y="Revenue", markers=True, title="Revenue by month")
        fig.update_layout(xaxis_title="", yaxis_title="Revenue (₹)")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("#### Revenue by category")
        cat = filtered.groupby("Product Category", as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=False)
        fig = px.pie(cat, names="Product Category", values="Revenue", hole=0.48, title="Category revenue share")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Filtered transaction data")
    st.dataframe(filtered.sort_values("Order Date", ascending=False), use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download filtered data",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_supermarket_sales.csv",
        mime="text/csv",
    )

with tab_sales:
    st.subheader("Sales performance")
    c1, c2 = st.columns(2)
    with c1:
        cat_sales = filtered.groupby("Product Category", as_index=False).agg(
            Revenue=("Revenue", "sum"), Profit=("Profit", "sum")
        ).sort_values("Revenue", ascending=False)
        fig = px.bar(cat_sales, x="Product Category", y="Revenue", color="Product Category",
                     title="Revenue by product category")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        region_sales = filtered.groupby("Region", as_index=False).agg(
            Revenue=("Revenue", "sum"), Profit=("Profit", "sum")
        ).sort_values("Revenue", ascending=False)
        fig = px.bar(region_sales, x="Region", y="Revenue", color="Region",
                     title="Revenue by region")
        st.plotly_chart(fig, use_container_width=True)

    product_sales = filtered.groupby("Product", as_index=False).agg(
        Quantity=("Quantity", "sum"), Revenue=("Revenue", "sum"), Profit=("Profit", "sum")
    ).sort_values("Profit", ascending=False).head(10)
    fig = px.bar(product_sales, x="Profit", y="Product", orientation="h",
                 title="Top 10 products by profit", text_auto=".2s")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Profit (₹)")
    st.plotly_chart(fig, use_container_width=True)

    monthly = filtered.groupby("Month", as_index=False).agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"))
    fig = px.bar(monthly, x="Month", y=["Revenue", "Profit"], barmode="group",
                 title="Monthly revenue vs profit")
    st.plotly_chart(fig, use_container_width=True)

with tab_customers:
    st.subheader("Customer behavior and RFM segmentation")
    active_ids = set(filtered["Customer ID"].dropna().astype(str))
    rfm_view = rfm[rfm["Customer ID"].astype(str).isin(active_ids)].copy()
    total_customers = len(rfm_view)
    repeat_customers = int((rfm_view["Frequency"] > 1).sum())
    one_time = int((rfm_view["Frequency"] == 1).sum())
    repeat_rate = repeat_customers / total_customers * 100 if total_customers else 0

    a, b, c = st.columns(3)
    a.metric("Customers", f"{total_customers:,}")
    b.metric("Repeat customers", f"{repeat_customers:,}")
    c.metric("Repeat customer rate", f"{repeat_rate:.1f}%")

    left, right = st.columns(2)
    with left:
        frequency_counts = rfm_view["Frequency"].value_counts().sort_index().reset_index()
        frequency_counts.columns = ["Orders per customer", "Customers"]
        fig = px.bar(frequency_counts, x="Orders per customer", y="Customers",
                     title="Customer order frequency")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        tier_counts = rfm_view["Risk Tier"].value_counts().reindex(
            ["Low", "Medium", "High", "Churn risk"], fill_value=0
        ).rename_axis("Risk Tier").reset_index(name="Customers")
        fig = px.bar(tier_counts, x="Risk Tier", y="Customers", color="Risk Tier",
                     title="Customer inactivity segments")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Highest-value customers")
    top_customers = rfm_view.sort_values("Monetary", ascending=False).head(15).copy()
    top_customers["Monetary"] = top_customers["Monetary"].map(lambda x: f"₹{x:,.2f}")
    top_customers["Total_Profit"] = top_customers["Total_Profit"].map(lambda x: f"₹{x:,.2f}")
    st.dataframe(top_customers, use_container_width=True, hide_index=True)

with tab_churn:
    st.subheader("Customer churn-risk monitoring")
    st.info(
        "Demo definition: a customer is flagged as at risk when they have not purchased for "
        "180 days or more relative to the latest transaction date in this dataset. "
        "This is a rule-based inactivity flag, not a validated future churn prediction."
    )
    at_risk = rfm[rfm["Recency"] >= 180].copy()
    at_risk_count = len(at_risk)
    risk_pct = at_risk_count / len(rfm) * 100 if len(rfm) else 0
    x1, x2, x3 = st.columns(3)
    x1.metric("Customers at risk", f"{at_risk_count:,}")
    x2.metric("At-risk share", f"{risk_pct:.1f}%")
    x3.metric("Inactivity threshold", "180 days")

    risk_filter = st.selectbox("Show customers", ["All at-risk customers", "High monetary value", "Sort by longest inactivity"])
    if risk_filter == "High monetary value":
        risk_table = at_risk.sort_values("Monetary", ascending=False)
    elif risk_filter == "Sort by longest inactivity":
        risk_table = at_risk.sort_values("Recency", ascending=False)
    else:
        risk_table = at_risk.sort_values("Recency", ascending=False)

    display = risk_table[["Customer ID", "Last_Order", "Recency", "Frequency", "Monetary", "Total_Profit", "Risk Tier"]].copy()
    display["Monetary"] = display["Monetary"].map(lambda x: f"₹{x:,.2f}")
    display["Total_Profit"] = display["Total_Profit"].map(lambda x: f"₹{x:,.2f}")
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download at-risk customers",
        data=risk_table.to_csv(index=False).encode("utf-8"),
        file_name="customer_churn_risk.csv",
        mime="text/csv",
    )
    st.markdown("#### Suggested retention actions")
    st.markdown("""
    - Send a personalized win-back message to customers with 90–179 days of inactivity.
    - Prioritize high-spend customers in the 180+ day inactivity group for a targeted offer.
    - Track campaign response and repeat purchases before deciding whether the offer is effective.
    """)

with tab_insights:
    st.subheader("Business insights and recommendations")
    total_revenue = filtered["Revenue"].sum()
    total_profit = filtered["Profit"].sum()
    category_summary = filtered.groupby("Product Category")["Revenue"].sum().sort_values(ascending=False)
    region_summary = filtered.groupby("Region")["Revenue"].sum().sort_values(ascending=False)
    month_summary = filtered.groupby("Month")["Revenue"].sum().sort_values(ascending=False)

    if len(category_summary):
        top_category = category_summary.index[0]
        top_category_share = category_summary.iloc[0] / total_revenue * 100 if total_revenue else 0
        st.markdown(f"**Observation 1 — Category leader:** {top_category} is the top revenue category in the current filters, contributing **{top_category_share:.1f}%** of filtered revenue.")
    if len(region_summary):
        st.markdown(f"**Observation 2 — Regional performance:** {region_summary.index[0]} is the leading region in the current filters.")
    if len(month_summary):
        st.markdown(f"**Observation 3 — Strongest month:** {month_summary.index[0]} has the highest revenue among the selected months.")
    margin = total_profit / total_revenue * 100 if total_revenue else 0
    st.markdown(f"**Observation 4 — Profitability:** the filtered profit margin is **{margin:.2f}%**.")
    st.markdown(f"**Observation 5 — Customer retention:** {int((rfm['Frequency'] > 1).sum())} customers have placed more than one order in the full dataset.")

    st.markdown("#### Insights")
    st.write("1. Categories with high revenue should be monitored alongside profit, because sales volume alone does not show profitability.")
    st.write("2. Regional differences may indicate opportunities to adjust inventory, promotions, or local marketing.")
    st.write("3. Customers with multiple purchases are an important audience for loyalty and cross-selling campaigns.")
    st.write("4. Long inactivity can be used to prioritize customer re-engagement.")
    st.write("5. Monthly comparisons can help identify seasonal demand changes.")

    st.markdown("#### Hypotheses to test")
    st.write("- Targeted offers will increase repeat purchase rates among inactive customers.")
    st.write("- Bundling complementary products will increase average order value.")
    st.write("- Region-specific promotions will improve sales in lower-performing regions.")

    st.markdown("#### Actionable recommendations")
    st.write("1. Test a win-back campaign for customers with 90+ days of inactivity and compare against a control group.")
    st.write("2. Bundle profitable accessories with frequently purchased products, then measure profit per order.")
    st.write("3. Review inventory and promotion plans before historically weaker months.")
    st.write("4. Review profit margin by category and product before increasing marketing spend.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Rows loaded: {len(df):,} • Data period: {min_date} to {max_date}")
st.sidebar.caption("Built with Streamlit, Pandas, NumPy and Plotly.")
