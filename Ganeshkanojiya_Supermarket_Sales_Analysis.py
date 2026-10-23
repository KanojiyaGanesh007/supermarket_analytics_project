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


# ---------- Single-page dashboard ----------
st.subheader("📊 Executive Dashboard")
st.caption("All charts update together when you change the date, category, or region filters.")

revenue = filtered["Revenue"].sum()
profit = filtered["Profit"].sum()
orders = filtered["Invoice ID"].nunique()
customers = filtered["Customer ID"].nunique()
aov = revenue / orders if orders else 0
margin = (profit / revenue * 100) if revenue else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Revenue", f"₹{revenue:,.2f}")
k2.metric("Total Profit", f"₹{profit:,.2f}")
k3.metric("Orders", f"{orders:,}")
k4.metric("Unique Customers", f"{customers:,}")
k5.metric("Average Order Value", f"₹{aov:,.2f}")
k6.metric("Profit Margin", f"{margin:.2f}%")

st.markdown("---")
st.subheader("📈 Sales Performance")

monthly = (
    filtered.groupby("Month", as_index=False)
    .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"))
    .sort_values("Month")
)
cat_sales = (
    filtered.groupby("Product Category", as_index=False)
    .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"))
    .sort_values("Revenue", ascending=False)
)
region_sales = (
    filtered.groupby("Region", as_index=False)
    .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"))
    .sort_values("Revenue", ascending=False)
)
product_sales = (
    filtered.groupby("Product", as_index=False)
    .agg(Quantity=("Quantity", "sum"), Revenue=("Revenue", "sum"), Profit=("Profit", "sum"))
    .sort_values("Profit", ascending=False)
    .head(10)
)

left, right = st.columns(2)
with left:
    fig = px.line(monthly, x="Month", y=["Revenue", "Profit"], markers=True,
                  title="Monthly Revenue vs. Profit")
    fig.update_layout(xaxis_title="Month", yaxis_title="Amount (₹)", legend_title="")
    st.plotly_chart(fig, use_container_width=True)
with right:
    fig = px.pie(cat_sales, names="Product Category", values="Revenue", hole=0.48,
                 title="Revenue Share by Category")
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    fig = px.bar(cat_sales, x="Product Category", y=["Revenue", "Profit"], barmode="group",
                 title="Revenue and Profit by Category")
    fig.update_layout(xaxis_title="", yaxis_title="Amount (₹)", legend_title="")
    st.plotly_chart(fig, use_container_width=True)
with right:
    fig = px.bar(region_sales, x="Region", y=["Revenue", "Profit"], barmode="group",
                 title="Revenue and Profit by Region")
    fig.update_layout(xaxis_title="", yaxis_title="Amount (₹)", legend_title="")
    st.plotly_chart(fig, use_container_width=True)

fig = px.bar(product_sales, x="Profit", y="Product", orientation="h",
             title="Top 10 Products by Profit", text_auto=".2s")
fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Profit (₹)")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("👥 Customer Behavior & Segmentation")

active_ids = set(filtered["Customer ID"].dropna().astype(str))
rfm_view = rfm[rfm["Customer ID"].astype(str).isin(active_ids)].copy()
total_customers = len(rfm_view)
repeat_customers = int((rfm_view["Frequency"] > 1).sum())
repeat_rate = repeat_customers / total_customers * 100 if total_customers else 0
one_time = int((rfm_view["Frequency"] == 1).sum())

c1, c2, c3 = st.columns(3)
c1.metric("Customers in Filter", f"{total_customers:,}")
c2.metric("Repeat Customers", f"{repeat_customers:,}")
c3.metric("Repeat Customer Rate", f"{repeat_rate:.1f}%")

left, right = st.columns(2)
with left:
    frequency_counts = rfm_view["Frequency"].value_counts().sort_index().reset_index()
    frequency_counts.columns = ["Orders per Customer", "Customers"]
    fig = px.bar(frequency_counts, x="Orders per Customer", y="Customers",
                 title="Customer Order Frequency")
    st.plotly_chart(fig, use_container_width=True)
with right:
    tier_counts = (
        rfm_view["Risk Tier"].value_counts()
        .reindex(["Low", "Medium", "High", "Churn risk"], fill_value=0)
        .rename_axis("Risk Tier").reset_index(name="Customers")
    )
    fig = px.bar(tier_counts, x="Risk Tier", y="Customers", color="Risk Tier",
                 title="Customer Inactivity Segments")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("⚠️ Churn-Risk Overview")
st.info(
    "Demo definition: a customer is flagged as at risk after 180 or more days without a purchase, "
    "measured against the latest transaction date in the dataset. This is a rule-based inactivity "
    "flag, not a validated future churn prediction."
)
at_risk = rfm[rfm["Recency"] >= 180].copy()
at_risk_count = len(at_risk)
risk_pct = at_risk_count / len(rfm) * 100 if len(rfm) else 0
ch1, ch2, ch3 = st.columns(3)
ch1.metric("Customers at Risk", f"{at_risk_count:,}")
ch2.metric("At-Risk Share", f"{risk_pct:.1f}%")
ch3.metric("Inactivity Threshold", "180 days")

risk_chart_data = (
    at_risk["Risk Tier"].value_counts()
    .reindex(["Low", "Medium", "High", "Churn risk"], fill_value=0)
    .rename_axis("Risk Tier").reset_index(name="Customers")
)
left, right = st.columns(2)
with left:
    fig = px.histogram(at_risk, x="Recency", nbins=20, title="At-Risk Customers by Inactivity Days")
    fig.update_layout(xaxis_title="Days Since Last Purchase", yaxis_title="Customers")
    st.plotly_chart(fig, use_container_width=True)
with right:
    risk_value = at_risk.sort_values("Monetary", ascending=False).head(10)
    fig = px.bar(risk_value, x="Customer ID", y="Monetary",
                 title="Top 10 At-Risk Customers by Total Spend")
    fig.update_layout(xaxis_title="Customer ID", yaxis_title="Total Spend (₹)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("💡 Business Insights")
total_revenue = filtered["Revenue"].sum()
total_profit = filtered["Profit"].sum()
category_summary = filtered.groupby("Product Category")["Revenue"].sum().sort_values(ascending=False)
region_summary = filtered.groupby("Region")["Revenue"].sum().sort_values(ascending=False)
month_summary = filtered.groupby("Month")["Revenue"].sum().sort_values(ascending=False)

insight_cols = st.columns(3)
if len(category_summary):
    top_category = category_summary.index[0]
    share = category_summary.iloc[0] / total_revenue * 100 if total_revenue else 0
    insight_cols[0].metric("Leading Category", top_category, f"{share:.1f}% of revenue")
if len(region_summary):
    insight_cols[1].metric("Leading Region", region_summary.index[0])
if len(month_summary):
    insight_cols[2].metric("Best Revenue Month", month_summary.index[0])

st.markdown("**Recommended actions**")
st.markdown("""
- Compare category revenue with profit before increasing promotions.
- Review regional performance to improve inventory and marketing decisions.
- Test targeted win-back offers for inactive customers and measure repeat purchases.
- Use monthly revenue and profit trends to plan inventory and seasonal campaigns.
""")

st.markdown("---")
st.subheader("📋 Customer & Transaction Details")
table_left, table_right = st.columns(2)
with table_left:
    st.markdown("#### Highest-Value Customers")
    top_customers = rfm_view.sort_values("Monetary", ascending=False).head(15).copy()
    top_customers["Monetary"] = top_customers["Monetary"].map(lambda x: f"₹{x:,.2f}")
    top_customers["Total_Profit"] = top_customers["Total_Profit"].map(lambda x: f"₹{x:,.2f}")
    st.dataframe(top_customers, use_container_width=True, hide_index=True)
with table_right:
    st.markdown("#### At-Risk Customers")
    risk_table = at_risk.sort_values("Recency", ascending=False)
    display = risk_table[["Customer ID", "Last_Order", "Recency", "Frequency",
                          "Monetary", "Total_Profit", "Risk Tier"]].copy()
    display["Monetary"] = display["Monetary"].map(lambda x: f"₹{x:,.2f}")
    display["Total_Profit"] = display["Total_Profit"].map(lambda x: f"₹{x:,.2f}")
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download at-risk customers",
        data=risk_table.to_csv(index=False).encode("utf-8"),
        file_name="customer_churn_risk.csv",
        mime="text/csv",
    )

st.markdown("#### Filtered Transaction Data")
st.dataframe(filtered.sort_values("Order Date", ascending=False),
             use_container_width=True, hide_index=True)
st.download_button(
    "⬇️ Download filtered data",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_supermarket_sales.csv",
    mime="text/csv",
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Rows loaded: {len(df):,} • Data period: {min_date} to {max_date}")
st.sidebar.caption("Built with Streamlit, Pandas, NumPy and Plotly.")
