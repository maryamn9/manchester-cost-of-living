import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------------------------
# Manchester Cost-of-Living Explorer
# A simple, interactive dashboard comparing cost-of-living metrics
# across UK regions. Built with Streamlit.
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Manchester Cost-of-Living Explorer",
    page_icon="📊",
    layout="wide",
)

# ---------- Load data ----------
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df.columns = [c.strip().lower() for c in df.columns]  # tidy column names
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Couldn't find data.csv — make sure it's in the same repo as this app.")
    st.stop()

# Your CSV needs a 'region' column, a 'year' column, and one or more
# numeric columns (e.g. avg_monthly_rent, avg_energy_bill).
if not {"region", "year"}.issubset(df.columns):
    st.error(f"data.csv must have 'region' and 'year' columns. Found: {list(df.columns)}")
    st.stop()

metric_cols = [
    c for c in df.columns
    if c not in ("region", "year") and pd.api.types.is_numeric_dtype(df[c])
]
if not metric_cols:
    st.error("No numeric metric columns found (e.g. avg_monthly_rent). Check your CSV.")
    st.stop()

# ---------- Header ----------
st.title("📊 Manchester Cost-of-Living Explorer")
st.caption("Comparing the cost of living across UK regions using open data.")

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")

metric = st.sidebar.selectbox(
    "Metric",
    metric_cols,
    format_func=lambda x: x.replace("_", " ").title(),
)

all_regions = sorted(df["region"].unique())
preferred = [r for r in all_regions if r.lower() in ("manchester", "london", "birmingham", "uk", "united kingdom")]
default_regions = preferred if preferred else all_regions[:4]
regions = st.sidebar.multiselect("Regions", all_regions, default=default_regions)

year_min, year_max = int(df["year"].min()), int(df["year"].max())
if year_min == year_max:
    year_range = (year_min, year_max)
    st.sidebar.write(f"Year: **{year_min}**")
else:
    year_range = st.sidebar.slider("Year range", year_min, year_max, (year_min, year_max))

# ---------- Apply filters ----------
f = df[df["region"].isin(regions) & df["year"].between(year_range[0], year_range[1])].copy()
if f.empty:
    st.warning("No data for those filters — pick at least one region.")
    st.stop()

pretty = metric.replace("_", " ").title()
latest_year = int(f["year"].max())
latest = f[f["year"] == latest_year]

# ---------- KPI cards ----------
c1, c2, c3 = st.columns(3)
c1.metric("Latest year", latest_year)

man_latest = latest[latest["region"].str.lower() == "manchester"]
if not man_latest.empty:
    c2.metric(f"Manchester — {pretty}", f"{man_latest[metric].iloc[0]:,.0f}")

man_all = f[f["region"].str.lower() == "manchester"].sort_values("year")
if len(man_all) >= 2 and man_all[metric].iloc[0]:
    change = man_all[metric].iloc[-1] - man_all[metric].iloc[0]
    pct = change / man_all[metric].iloc[0] * 100
    c3.metric(f"Manchester change ({year_range[0]}–{year_range[1]})", f"{change:,.0f}", f"{pct:+.1f}%")

# ---------- Line chart: trend over time ----------
st.subheader(f"{pretty} over time")
fig_line = px.line(f.sort_values("year"), x="year", y=metric, color="region", markers=True)
fig_line.update_layout(yaxis_title=pretty, xaxis_title="Year", legend_title="Region")
st.plotly_chart(fig_line, use_container_width=True)

# ---------- Bar chart: latest-year comparison ----------
st.subheader(f"{pretty} by region — {latest_year}")
fig_bar = px.bar(latest.sort_values(metric, ascending=False), x="region", y=metric, color="region")
fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title=pretty)
st.plotly_chart(fig_bar, use_container_width=True)

# ---------- Data table + download ----------
with st.expander("See the data behind the charts"):
    st.dataframe(f.sort_values(["region", "year"]), use_container_width=True)
    st.download_button("Download filtered data (CSV)", f.to_csv(index=False), "filtered_data.csv", "text/csv")

st.caption("Data source: UK ONS / gov.uk open data · Dashboard by Maryam Naveen")
