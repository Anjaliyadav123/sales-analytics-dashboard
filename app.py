import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Sales Analytics Dashboard")
st.caption("Interactive business intelligence and sales performance")

SAMPLE = pd.DataFrame({
    "order_id": range(1001, 1019),
    "order_date": pd.date_range("2026-01-05", periods=18, freq="10D"),
    "product": [
        "Laptop", "Phone", "Desk", "Chair", "Headphones",
        "Notebook", "Monitor", "Desk", "Pen", "Phone",
        "Chair", "Notebook", "Laptop", "Desk", "Headphones",
        "Pen", "Monitor", "Chair"
    ],
    "category": [
        "Electronics", "Electronics", "Furniture", "Furniture",
        "Electronics", "Stationery", "Electronics", "Furniture",
        "Stationery", "Electronics", "Furniture", "Stationery",
        "Electronics", "Furniture", "Electronics", "Stationery",
        "Electronics", "Furniture"
    ],
    "region": [
        "North", "South", "East", "West", "North", "South",
        "East", "North", "West", "South", "East", "North",
        "West", "South", "East", "North", "West", "South"
    ],
    "quantity": [2, 3, 2, 5, 4, 10, 2, 1, 20, 2, 3, 15, 1, 2, 5, 30, 3, 4],
    "sales": [1200, 900, 500, 750, 400, 100, 600, 250, 100, 600, 450, 150, 600, 500, 500, 150, 900, 600],
    "profit": [240, 180, 80, 125, 100, 30, 120, 40, 35, 120, 75, 45, 120, 80, 125, 50, 180, 100]
})

st.sidebar.header("Dataset")
uploaded = st.sidebar.file_uploader("Upload sales CSV", type=["csv"])

if uploaded:
    try:
        df = pd.read_csv(uploaded)
    except Exception:
        st.error("Could not read the CSV file.")
        st.stop()
else:
    df = SAMPLE.copy()
    st.sidebar.info("Showing built-in sample data.")

df.columns = df.columns.str.strip().str.lower()

required = [
    "order_id", "order_date", "product", "category",
    "region", "quantity", "sales", "profit"
]

missing = set(required) - set(df.columns)

if missing:
    st.error("Missing columns: " + ", ".join(sorted(missing)))
    st.info("Required: " + ", ".join(required))
    st.stop()

df = df[required].copy()

for col in ["product", "category", "region", "order_id"]:
    df[col] = df[col].astype("string").str.strip()

df["order_date"] = pd.to_datetime(
    df["order_date"], errors="coerce"
)

for col in ["quantity", "sales", "profit"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=required)
df = df[
    (df["quantity"] > 0)
    & (df["sales"] >= 0)
    & (df["sales"] < 1e12)
    & (df["profit"].abs() < 1e12)
    & (df["quantity"] < 1e9)
]
df = df.drop_duplicates("order_id", keep="last")

if df.empty:
    st.error("No valid sales records found.")
    st.stop()

st.sidebar.header("Filters")

categories = sorted(df["category"].unique().tolist())
regions = sorted(df["region"].unique().tolist())

selected_categories = st.sidebar.multiselect(
    "Product category", categories, default=categories
)
selected_regions = st.sidebar.multiselect(
    "Region", regions, default=regions
)

min_date = df["order_date"].min().date()
max_date = df["order_date"].max().date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

filtered = df[
    df["category"].isin(selected_categories)
    & df["region"].isin(selected_regions)
].copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    filtered = filtered[
        filtered["order_date"].dt.date.between(
            date_range[0], date_range[1]
        )
    ]

if filtered.empty:
    st.warning("No records match your filters.")
    st.stop()

revenue = filtered["sales"].sum()
profit = filtered["profit"].sum()
orders = filtered["order_id"].nunique()
units = filtered["quantity"].sum()
aov = revenue / orders if orders else 0
margin = profit / revenue * 100 if revenue else 0

st.subheader("Key Performance Indicators")

c1, c2, c3 = st.columns(3)
c1.metric("Total Revenue", f"₹{revenue:,.2f}")
c2.metric("Total Profit", f"₹{profit:,.2f}")
c3.metric("Total Orders", f"{orders:,}")

c4, c5, c6 = st.columns(3)
c4.metric("Average Order Value", f"₹{aov:,.2f}")
c5.metric("Profit Margin", f"{margin:.2f}%")
c6.metric("Units Sold", f"{units:,.0f}")

st.divider()

monthly = (
    filtered.assign(
        month=filtered["order_date"].dt.to_period("M").astype(str)
    )
    .groupby("month")[["sales", "profit"]]
    .sum()
    .sort_index()
)

category_sales = (
    filtered.groupby("category")["sales"]
    .sum().sort_values(ascending=False)
)

product_sales = (
    filtered.groupby("product")["sales"]
    .sum().sort_values(ascending=False)
)

st.subheader("Sales Performance")

left, right = st.columns(2)

with left:
    st.markdown("#### Monthly Revenue and Profit")
    st.line_chart(monthly)

with right:
    st.markdown("#### Revenue by Category")
    st.bar_chart(category_sales)

left, right = st.columns(2)

with left:
    st.markdown("#### Revenue by Region")
    st.bar_chart(region_sales)

with right:
    st.markdown("#### Top Products by Revenue")
    st.bar_chart(product_sales.head(10))

st.divider()
st.subheader("Detailed Sales Records")

display_df = filtered.sort_values("order_date", ascending=False).copy()
display_df["order_date"] = display_df["order_date"].dt.strftime("%Y-%m-%d")

st.dataframe(display_df, use_container_width=True, hide_index=True)

csv = display_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Download Filtered Data as CSV",
    data=csv,
    file_name="sales_analytics.csv",
    mime="text/csv"
)

st.success(
    f"Analysis completed for {len(filtered):,} valid sales records."
)
