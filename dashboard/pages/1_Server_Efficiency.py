
import streamlit as st
import pandas as pd
from pathlib import Path

@st.cache_data(ttl=600)
def load_data():
    csv_path = Path(__file__).resolve().parents[2] / "data" / "specpower_energy.csv"
    df = pd.read_csv(csv_path)
    for col in ["ssj_ops_per_watt", "avg_watts_100", "avg_watts_idle"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

st.title("⚡ Server Energy Efficiency")
st.caption("Developed by: Ghadi")
st.markdown(
    "Explore server energy efficiency, power consumption, "
    "and hardware performance."
)

try:
    df = load_data()

    # 1. Summary KPIs
    summary = pd.DataFrame([{
        "total_records": len(df),
        "vendors": df["hardware_vendor"].nunique(),
        "server_models": df["server_model"].nunique(),
        "avg_efficiency": df["ssj_ops_per_watt"].mean(),
        "avg_full_load_watts": df["avg_watts_100"].mean(),
        "avg_idle_watts": df["avg_watts_idle"].mean(),
    }])

    # 2. Average efficiency by vendor and server model
    valid_models = df.dropna(
        subset=["hardware_vendor", "server_model", "ssj_ops_per_watt"]
    )

    models = (
        valid_models
        .groupby(["hardware_vendor", "server_model"])
        .agg(
            records=("ssj_ops_per_watt", "size"),
            avg_efficiency=("ssj_ops_per_watt", "mean"),
            avg_full_load_watts=("avg_watts_100", "mean"),
            avg_idle_watts=("avg_watts_idle", "mean"),
        )
        .reset_index()
        .sort_values("avg_efficiency", ascending=False)
    )

    # 3. Records for the power-efficiency comparison
    scatter = df.dropna(
        subset=["avg_watts_100", "ssj_ops_per_watt"]
    )[
        ["hardware_vendor", "server_model",
         "avg_watts_100", "ssj_ops_per_watt"]
    ].copy()

    if summary.empty:
        st.warning("No server efficiency data was returned.")
        st.stop()

    metrics = summary.iloc[0]

    st.subheader("Key Performance Indicators")
    c1, c2, c3 = st.columns(3)
    c1.metric("Server Records", f"{int(metrics['total_records']):,}")
    c2.metric("Hardware Vendors", f"{int(metrics['vendors']):,}")
    c3.metric("Server Models", f"{int(metrics['server_models']):,}")

    c4, c5, c6 = st.columns(3)
    c4.metric(
        "Avg. Efficiency",
        f"{metrics['avg_efficiency']:,.1f}"
        if pd.notna(metrics["avg_efficiency"]) else "N/A",
        help="Average SSJ operations per watt, as provided by the dataset.",
    )
    c5.metric(
        "Avg. Full-Load Power",
        f"{metrics['avg_full_load_watts']:,.1f} W"
        if pd.notna(metrics["avg_full_load_watts"]) else "N/A",
    )
    c6.metric(
        "Avg. Idle Power",
        f"{metrics['avg_idle_watts']:,.1f} W"
        if pd.notna(metrics["avg_idle_watts"]) else "N/A",
    )

    st.divider()
    st.subheader("Explore Server Models")

    vendors = sorted(models["hardware_vendor"].dropna().unique().tolist())
    selected_vendors = st.multiselect(
        "Filter by hardware vendor",
        options=vendors,
        default=[],
        help="Leave empty to include all vendors.",
    )

    filtered = models.copy()
    if selected_vendors:
        filtered = filtered[
            filtered["hardware_vendor"].isin(selected_vendors)
        ]

    if filtered.empty:
        st.info("No models match the selected filters.")
    else:
        top_models = filtered.head(10).copy()
        top_models["model_label"] = (
            top_models["hardware_vendor"].astype(str)
            + " — "
            + top_models["server_model"].astype(str)
        )

        st.subheader("Top 10 Models by Average Energy Efficiency")
        st.caption(
            "Models are ranked by average SSJ operations per watt. "
            "Record counts show how many dataset records contribute "
            "to each model's average."
        )
        chart_data = top_models.set_index("model_label")[
            ["avg_efficiency"]
        ]
        st.bar_chart(chart_data, horizontal=True)

        st.subheader("Power Consumption vs. Energy Efficiency")
        if not scatter.empty:
            scatter_view = scatter.copy()
            if selected_vendors:
                scatter_view = scatter_view[
                    scatter_view["hardware_vendor"].isin(selected_vendors)
                ]

            st.scatter_chart(
                scatter_view,
                x="avg_watts_100",
                y="ssj_ops_per_watt",
                color="hardware_vendor",
                size=70,
            )
            st.caption(
                "Each point represents a dataset record. "
                "Higher efficiency means more SSJ operations per watt; "
                "power is measured in watts at full load."
            )

        st.subheader("Server Model Details")
        display = filtered.rename(columns={
            "hardware_vendor": "Hardware Vendor",
            "server_model": "Server Model",
            "records": "Record Count",
            "avg_efficiency": "Avg. Efficiency (SSJ/W)",
            "avg_full_load_watts": "Avg. Full-Load Power (W)",
            "avg_idle_watts": "Avg. Idle Power (W)",
        })

        st.dataframe(
            display,
            width="stretch",
            hide_index=True,
        )

except Exception as e:
    st.error("Unable to load server efficiency data from CSV.")
    st.exception(e)
