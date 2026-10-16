
import streamlit as st
import plotly.express as px
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Cloud Cost Analysis",
    page_icon="☁️",
    layout="wide",
)

st.title("☁️ Cloud Cost Analysis")
st.caption("Developed by: Atheer Aldawsari")
st.markdown(
    "Explore AWS EC2 pricing and compare compute and memory costs."
)


@st.cache_data(ttl=600)
def load_cloud_cost():
    csv_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "aws_ec2_pricing_cleaned.csv"
    )

    df = pd.read_csv(csv_path)

    for col in ["hourly_price_usd", "vcpu", "memory_gb"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["hourly_cost_per_vcpu_usd"] = (
        df["hourly_price_usd"] / df["vcpu"].replace(0, float("nan"))
    )

    df["hourly_cost_per_gb_memory_usd"] = (
        df["hourly_price_usd"] / df["memory_gb"].replace(0, float("nan"))
    )

    return df.sort_values("hourly_price_usd").reset_index(drop=True)


try:
    df = load_cloud_cost()

    if df.empty:
        st.warning("No cloud pricing data found.")
        st.stop()

    st.sidebar.header("Filters")

    families = sorted(df["instance_family"].dropna().unique())

    selected_families = st.sidebar.multiselect(
        "Instance family",
        families,
        default=families,
    )

    available_types = sorted(
        df.loc[
            df["instance_family"].isin(selected_families),
            "instance_type",
        ].dropna().unique()
    )

    selected_types = st.sidebar.multiselect(
        "Instance type",
        available_types,
        default=available_types,
    )

    filtered = df[
        df["instance_family"].isin(selected_families)
        & df["instance_type"].isin(selected_types)
    ].copy()

    if filtered.empty:
        st.warning("No instances match the selected filters.")
        st.stop()

    st.subheader("Pricing Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Instance Types",
        f"{filtered['instance_type'].nunique():,}",
    )

    c2.metric(
        "Instance Families",
        f"{filtered['instance_family'].nunique():,}",
    )

    c3.metric(
        "Average Hourly Price",
        f"${filtered['hourly_price_usd'].mean():,.4f}",
    )

    c4.metric(
        "Lowest Hourly Price",
        f"${filtered['hourly_price_usd'].min():,.5f}",
    )

    st.caption("AWS On-Demand pricing from the selected dataset.")

    st.subheader("Hourly Price by Instance Type")

    price_df = filtered.sort_values("hourly_price_usd")

    fig_price = px.bar(
        price_df,
        x="instance_type",
        y="hourly_price_usd",
        color="instance_family",
        hover_data=[
            "vcpu",
            "memory_gb",
            "physical_processor",
        ],
        labels={
            "instance_type": "Instance Type",
            "hourly_price_usd": "Hourly Price (USD)",
            "instance_family": "Instance Family",
        },
    )

    fig_price.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(
        fig_price,
        use_container_width=True,
    )

    st.subheader("Cost Efficiency by Instance Family")

    family_df = (
        filtered.groupby("instance_family", as_index=False)
        .agg(
            instance_count=("instance_type", "nunique"),
            avg_hourly_price=("hourly_price_usd", "mean"),
            avg_cost_per_vcpu=("hourly_cost_per_vcpu_usd", "mean"),
            avg_cost_per_gb_memory=(
                "hourly_cost_per_gb_memory_usd",
                "mean",
            ),
        )
        .sort_values("avg_hourly_price")
    )

    left, right = st.columns(2)

    with left:
        fig_cpu = px.bar(
            family_df,
            x="instance_family",
            y="avg_cost_per_vcpu",
            color="instance_family",
            title="Average Hourly Cost per vCPU",
            labels={
                "instance_family": "Instance Family",
                "avg_cost_per_vcpu": "Cost per vCPU (USD)",
            },
        )

        st.plotly_chart(
            fig_cpu,
            use_container_width=True,
        )

    with right:
        fig_memory = px.bar(
            family_df,
            x="instance_family",
            y="avg_cost_per_gb_memory",
            color="instance_family",
            title="Average Hourly Cost per GB Memory",
            labels={
                "instance_family": "Instance Family",
                "avg_cost_per_gb_memory": "Cost per GB (USD)",
            },
        )

        st.plotly_chart(
            fig_memory,
            use_container_width=True,
        )

    st.subheader("Instance Pricing Details")

    search = st.text_input(
        "Search by instance type or processor"
    )

    display_df = filtered.copy()

    if search:
        mask = (
            display_df["instance_type"].str.contains(
                search,
                case=False,
                na=False,
            )
            | display_df["physical_processor"].str.contains(
                search,
                case=False,
                na=False,
            )
        )

        display_df = display_df[mask]

    columns = [
        "instance_type",
        "instance_family",
        "vcpu",
        "memory_gb",
        "physical_processor",
        "region",
        "hourly_price_usd",
        "monthly_price_usd",
        "annual_price_usd",
        "hourly_cost_per_vcpu_usd",
        "hourly_cost_per_gb_memory_usd",
    ]

    st.dataframe(
        display_df[columns],
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download filtered data as CSV",
        data=display_df.to_csv(index=False).encode("utf-8"),
        file_name="cloud_cost_analysis.csv",
        mime="text/csv",
    )

except Exception as e:
    st.error("Unable to load Cloud Cost data from CSV.")
    st.exception(e)
