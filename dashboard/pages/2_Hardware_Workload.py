import streamlit as st
import pandas as pd
import plotly.express as px

from pathlib import Path

st.set_page_config(
    page_title="Hardware & Workload",
    page_icon="🖥️",
    layout="wide",
)

st.title("🖥️ Hardware & Workload Analysis")
st.caption("Developed by: Abrar")
st.markdown(
    "Explore CPU and memory utilization relative to available machine capacity."
)

@st.cache_data(ttl=600)
def load_data():
    csv_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "google_hardware_workload_joined.csv"
    )

    columns = [
        "machine_id",
        "platform_id",
        "start_time",
        "end_time",
        "event_time",
        "duration_minutes",
        "avg_cpu_usage",
        "avg_memory_usage",
        "cpu_capacity",
        "memory_capacity",
        "cpu_to_capacity_ratio",
        "memory_to_capacity_ratio",
    ]

    return pd.read_csv(csv_path, usecols=columns)[columns].copy()

try:
    df = load_data()

    if df.empty:
        st.warning("No workload records were found in the CSV.")
        st.stop()

    for col in ["cpu_to_capacity_ratio", "memory_to_capacity_ratio"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["cpu_utilization_pct"] = df["cpu_to_capacity_ratio"] * 100
    df["memory_utilization_pct"] = df["memory_to_capacity_ratio"] * 100

    st.subheader("Workload Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Workload Records", f"{len(df):,}")
    c2.metric("Unique Machines", f"{df['machine_id'].nunique():,}")
    c3.metric(
        "Average CPU Utilization",
        f"{df['cpu_utilization_pct'].mean():.2f}%"
    )
    c4.metric(
        "Average Memory Utilization",
        f"{df['memory_utilization_pct'].mean():.2f}%"
    )

    st.divider()
    st.subheader("Resource Utilization Distribution")

    left, right = st.columns(2)

    with left:
        cpu_data = df["cpu_utilization_pct"].dropna()
        fig_cpu = px.histogram(
            x=cpu_data,
            nbins=30,
            labels={"x": "CPU utilization (% of capacity)", "y": "Records"},
            title="CPU Utilization Distribution",
            color_discrete_sequence=["#4C78A8"],
        )
        fig_cpu.update_layout(showlegend=False)
        st.plotly_chart(fig_cpu, use_container_width=True)

    with right:
        memory_data = df["memory_utilization_pct"].dropna()
        fig_memory = px.histogram(
            x=memory_data,
            nbins=30,
            labels={"x": "Memory utilization (% of capacity)", "y": "Records"},
            title="Memory Utilization Distribution",
            color_discrete_sequence=["#F58518"],
        )
        fig_memory.update_layout(showlegend=False)
        st.plotly_chart(fig_memory, use_container_width=True)

    st.subheader("CPU vs. Memory Utilization")

    scatter_data = df.dropna(
        subset=["cpu_utilization_pct", "memory_utilization_pct"]
    )

    fig_scatter = px.scatter(
        scatter_data,
        x="cpu_utilization_pct",
        y="memory_utilization_pct",
        hover_data=["machine_id", "platform_id"],
        labels={
            "cpu_utilization_pct": "CPU Utilization (%)",
            "memory_utilization_pct": "Memory Utilization (%)",
        },
        title="Resource Utilization by Workload Record",
        opacity=0.65,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.subheader("Utilization by Threshold")

    threshold = st.slider(
        "Low utilization threshold (%)",
        min_value=1,
        max_value=20,
        value=5,
    )

    cpu_low = (
        df["cpu_utilization_pct"].notna()
        & (df["cpu_utilization_pct"] < threshold)
    )
    memory_low = (
        df["memory_utilization_pct"].notna()
        & (df["memory_utilization_pct"] < threshold)
    )

    a, b, c = st.columns(3)
    a.metric(
        f"CPU Below {threshold}%",
        f"{cpu_low.sum():,}",
        f"{cpu_low.mean() * 100:.1f}% of all records",
    )
    b.metric(
        f"Memory Below {threshold}%",
        f"{memory_low.sum():,}",
        f"{memory_low.mean() * 100:.1f}% of all records",
    )
    c.metric(
        "Records With Both Below Threshold",
        f"{(cpu_low & memory_low).sum():,}",
    )

    st.caption(
        "Low utilization may indicate an opportunity to investigate resource "
        "allocation. It does not, by itself, prove overprovisioning."
    )

    with st.expander("Explore raw workload records"):
        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as exc:
    st.error("Could not load workload data from CSV.")
    st.exception(exc)
    st.info(
        "Check that google_hardware_workload_joined.csv exists "
        "and contains the expected columns."
    )
