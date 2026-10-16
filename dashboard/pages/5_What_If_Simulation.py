import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


st.title("🔮 What-If Simulation")
st.caption("Developed by: Amal")
st.caption("Interactive Server Selection & Energy Efficiency Analysis")

st.write(
    "Explore how performance and power constraints affect "
    "server selection using real SPECpower benchmark results."
)


@st.cache_data(ttl=600)
def load_servers():
    import pandas as pd

    csv_path = Path(__file__).resolve().parents[2] / "data" / "specpower_energy.csv"

    df = pd.read_csv(csv_path)

    columns = [
        "hardware_vendor",
        "server_model",
        "ssj_ops_100",
        "avg_watts_100",
        "ssj_ops_per_watt",
        "efficiency_100",
    ]

    df = df[columns].copy()

    for col in ["ssj_ops_100", "avg_watts_100", "ssj_ops_per_watt", "efficiency_100"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df[
        (df["ssj_ops_100"] > 0)
        & (df["avg_watts_100"] > 0)
        & (df["ssj_ops_per_watt"] > 0)
        & (df["efficiency_100"] > 0)
    ].copy()


try:
    df = load_servers()

    if df.empty:
        st.warning("No server benchmark data is available.")
        st.stop()

    st.subheader("⚙️ Configure Your Scenario")

    min_performance = st.slider(
        "Minimum Required Performance (ssj_ops)",
        min_value=0.0,
        max_value=float(df["ssj_ops_100"].max()),
        value=0.0,
        step=100000.0,
    )

    max_power = st.slider(
        "Maximum Full-Load Power (Watts)",
        min_value=0.0,
        max_value=float(df["avg_watts_100"].max()),
        value=float(df["avg_watts_100"].max()),
    )

    eligible = df[
        (df["ssj_ops_100"] >= min_performance)
        & (df["avg_watts_100"] <= max_power)
    ].copy()

    st.metric("Matching Servers", len(eligible))

    if eligible.empty:
        st.warning("No servers match your selected requirements.")

    else:
        eligible = eligible.sort_values(
            "efficiency_100", ascending=False
        )

        best = eligible.iloc[0]

        # Recommended Server
        st.subheader("🏆 Recommended Server")

        st.success(
            f"{best['hardware_vendor']} — {best['server_model']}"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Performance",
            f"{best['ssj_ops_100']:,.0f} ssj_ops"
        )

        col2.metric(
            "Full-Load Power",
            f"{best['avg_watts_100']:,.1f} W"
        )

        col3.metric(
            "Full-Load Efficiency",
            f"{best['efficiency_100']:,.1f} ops/W"
        )

        # Scenario Comparison
        st.subheader("🔍 Scenario Comparison")

        baseline = df.loc[df["efficiency_100"].idxmax()]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🏆 Best Overall Server**")
            st.write(baseline["server_model"])

            st.metric(
                "Full-Load Efficiency",
                f"{baseline['efficiency_100']:,.1f} ops/W"
            )

            st.metric(
                "Full-Load Power",
                f"{baseline['avg_watts_100']:,.1f} W"
            )

        with col2:
            st.markdown("**⚙️ Best Server Under Your Constraints**")
            st.write(best["server_model"])

            st.metric(
                "Full-Load Efficiency",
                f"{best['efficiency_100']:,.1f} ops/W"
            )

            st.metric(
                "Full-Load Power",
                f"{best['avg_watts_100']:,.1f} W"
            )

        st.info(
            "This comparison shows how your selected constraints "
            "affect server recommendations. Power values are "
            "SPECpower benchmark measurements, not predicted savings."
        )

        # Efficiency Visualization
        st.subheader("📈 Server Efficiency Comparison")

        top_servers = eligible.head(10).copy()

        top_servers["server_label"] = (
            top_servers["hardware_vendor"].fillna("Unknown")
            + " — "
            + top_servers["server_model"].fillna("Unknown")
        )

        st.bar_chart(
            top_servers,
            x="server_label",
            y="efficiency_100",
            x_label="Server Model",
            y_label="Full-Load Efficiency (ssj_ops/W)",
            horizontal=True,
            sort="-efficiency_100",
            width="stretch",
        )

        # Matching Servers Table
        st.subheader("📊 Top 10 Matching Servers")

        st.dataframe(
            eligible[
                [
                    "hardware_vendor",
                    "server_model",
                    "ssj_ops_100",
                    "avg_watts_100",
                    "efficiency_100",
                ]
            ].head(10),
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "Recommendations are based on SPECpower benchmark results "
        "at 100% load. Actual power consumption and performance "
        "may differ in production environments."
    )

except Exception as e:
    st.error(f"Unable to load simulation data: {e}")
