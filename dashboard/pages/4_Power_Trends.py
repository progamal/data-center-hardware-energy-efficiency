
import math

import altair as alt
import pandas as pd
import streamlit as st

from pathlib import Path


# ---------------------------------
# Page Header
# ---------------------------------
st.title("📈 Power Utilization Trends")
st.caption("Developed by: Nouf")

st.write(
    "Explore how measured power utilization compares "
    "with estimated production power utilization "
    "over time using Google Power data."
)

st.info(
    "**Why this matters:** Comparing measured power "
    "utilization with production-attributed power "
    "utilization helps us understand power usage "
    "patterns and identify periods that may require "
    "further analysis."
)


# ---------------------------------
# Load Data from CSV
# ---------------------------------
@st.cache_data(ttl=600)
def load_power_data():
    csv_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "google_power_cella_pdu10_cleaned.csv"
    )

    columns = [
        "hours_from_start",
        "cell",
        "pdu",
        "measured_power_util",
        "production_power_util",
    ]

    df = pd.read_csv(csv_path, usecols=columns)

    return df.sort_values(
        "hours_from_start"
    ).reset_index(drop=True)


try:
    df = load_power_data()

    if df.empty:
        st.warning("No power data available.")
        st.stop()

    # ---------------------------------
    # Prepare Data
    # ---------------------------------
    numeric_columns = [
        "hours_from_start",
        "measured_power_util",
        "production_power_util",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=["hours_from_start"]
    ).copy()

    df = df[
        df["hours_from_start"].map(math.isfinite)
    ].copy()

    if df.empty:
        st.warning("No valid time values available.")
        st.stop()

    # ---------------------------------
    # Filters
    # ---------------------------------
    st.subheader("Filters")

    st.markdown("**Power Source:** Google Cell A — PDU10")

    # The source dataset contains only PDU10.
    pdu_df = df[
        df["pdu"].astype(str).str.upper().isin(["PDU10", "10"])
    ].copy()

    if pdu_df.empty:
        st.warning("No PDU10 data available.")
        st.stop()

    min_hour = float(
        pdu_df["hours_from_start"].min()
    )

    max_hour = float(
        pdu_df["hours_from_start"].max()
    )

    if min_hour < max_hour:
        slider_min = math.floor(min_hour)
        slider_max = math.ceil(max_hour)

        selected_hours = st.slider(
            "Select Time Range (Hours from Start)",
            min_value=slider_min,
            max_value=slider_max,
            value=(slider_min, slider_max),
            step=1,
        )

        filtered_df = pdu_df[
            pdu_df["hours_from_start"].between(
                selected_hours[0],
                selected_hours[1],
            )
        ].copy()

    else:
        filtered_df = pdu_df.copy()

        st.info(
            f"Available time: {min_hour:.1f} hours"
        )

    if filtered_df.empty:
        st.warning(
            "No measurements in the selected time range."
        )
        st.stop()

    # ---------------------------------
    # Summary Metrics
    # ---------------------------------
    st.subheader("Power Utilization Summary")

    avg_measured = (
        filtered_df["measured_power_util"].mean()
    )

    avg_production = (
        filtered_df["production_power_util"].mean()
    )

    peak_measured = (
        filtered_df["measured_power_util"].max()
    )

    # Calculate the gap for records that have
    # both measured and production values.
    paired_df = filtered_df.dropna(
        subset=[
            "measured_power_util",
            "production_power_util",
        ]
    ).copy()

    paired_df["gap_pp"] = (
        paired_df["measured_power_util"]
        - paired_df["production_power_util"]
    ) * 100

    avg_gap = paired_df["gap_pp"].mean()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Avg. Measured Utilization",
            (
                f"{avg_measured:.1%}"
                if pd.notna(avg_measured)
                else "N/A"
            ),
            help=(
                "Average total measured power utilization."
            ),
        )

    with col2:
        st.metric(
            "Avg. Production Utilization",
            (
                f"{avg_production:.1%}"
                if pd.notna(avg_production)
                else "N/A"
            ),
            help=(
                "Average estimated power utilization "
                "attributed to production workloads."
            ),
        )

    with col3:
        st.metric(
            "Avg. Utilization Gap",
            (
                f"{avg_gap:+.1f} pp"
                if pd.notna(avg_gap)
                else "N/A"
            ),
            help=(
                "Measured utilization minus production "
                "utilization, averaged across paired "
                "records. pp = percentage points."
            ),
        )

    with col4:
        st.metric(
            "Peak Measured Utilization",
            (
                f"{peak_measured:.1%}"
                if pd.notna(peak_measured)
                else "N/A"
            ),
            help=(
                "Highest measured utilization "
                "in the selected time range."
            ),
        )

    st.caption(
        f"Total records in selected range: "
        f"{len(filtered_df):,}"
    )

    # ---------------------------------
    # Explain the Metrics
    # ---------------------------------
    with st.expander(
        "What do Measured, Production, and Gap mean?"
    ):
        st.markdown(
            """
            **Measured Power Utilization**

            Total measured power utilization,
            including power used by supporting
            equipment such as cooling.

            **Production Power Utilization**

            Estimated power utilization attributed
            to production workloads.

            **Utilization Gap**

            The difference between measured and
            production utilization, expressed in
            percentage points.

            **Why compare them?**

            Comparing these metrics helps us
            understand how total power usage
            relates to production workloads
            over time.

            **Important:** The gap does not
            directly measure wasted electricity
            or energy savings.
            """
        )

    # ---------------------------------
    # Main Power Trends Chart
    # ---------------------------------
    st.subheader(
        "Measured vs. Production Power Utilization"
    )

    st.write(
        "This chart compares measured power utilization "
        "and estimated production power utilization "
        "throughout the selected period."
    )

    chart_df = filtered_df.melt(
        id_vars=["hours_from_start"],
        value_vars=[
            "measured_power_util",
            "production_power_util",
        ],
        var_name="Power Type",
        value_name="Power Utilization",
    ).dropna(
        subset=["Power Utilization"]
    )

    chart_df["Power Type"] = (
        chart_df["Power Type"].replace(
            {
                "measured_power_util": "Measured Power",
                "production_power_util": "Production Power",
            }
        )
    )

    if chart_df.empty:
        st.info(
            "No valid utilization values available "
            "for the chart."
        )

    else:
        chart = (
            alt.Chart(chart_df)
            .mark_line()
            .encode(
                x=alt.X(
                    "hours_from_start:Q",
                    title="Hours from Start",
                ),
                y=alt.Y(
                    "Power Utilization:Q",
                    title="Power Utilization",
                    axis=alt.Axis(format=".0%"),
                    scale=alt.Scale(domain=[0, 1]),
                ),
                color=alt.Color(
                    "Power Type:N",
                    title="Power Type",
                    scale=alt.Scale(
                        domain=[
                            "Measured Power",
                            "Production Power",
                        ],
                        range=[
                            "#38BDF8",
                            "#14B8A6",
                        ],
                    ),
                ),
                tooltip=[
                    alt.Tooltip(
                        "hours_from_start:Q",
                        title="Hour",
                        format=".2f",
                    ),
                    alt.Tooltip("Power Type:N"),
                    alt.Tooltip(
                        "Power Utilization:Q",
                        title="Utilization",
                        format=".1%",
                    ),
                ],
            )
            .properties(height=380)
            .interactive()
        )

        st.altair_chart(
            chart,
            use_container_width=True,
        )

    st.caption(
        "Values represent power utilization ratios, "
        "not electricity consumption in kWh."
    )

    # ---------------------------------
    # Utilization Gap Chart
    # ---------------------------------
    st.subheader("Utilization Gap Over Time")

    st.write(
        "This chart shows how the difference between "
        "measured and production power utilization "
        "changes over time."
    )

    if paired_df.empty:
        st.info(
            "No paired utilization values available "
            "for the gap chart."
        )

    else:
        gap_chart = (
            alt.Chart(paired_df)
            .mark_area(
                line=True,
                opacity=0.35,
                color="#38BDF8",
            )
            .encode(
                x=alt.X(
                    "hours_from_start:Q",
                    title="Hours from Start",
                ),
                y=alt.Y(
                    "gap_pp:Q",
                    title=(
                        "Utilization Gap "
                        "(percentage points)"
                    ),
                    scale=alt.Scale(zero=True),
                ),
                tooltip=[
                    alt.Tooltip(
                        "hours_from_start:Q",
                        title="Hour",
                        format=".2f",
                    ),
                    alt.Tooltip(
                        "gap_pp:Q",
                        title="Gap (pp)",
                        format="+.2f",
                    ),
                ],
            )
            .properties(height=260)
            .interactive()
        )

        st.altair_chart(
            gap_chart,
            use_container_width=True,
        )

    st.info(
        "**Why analyze the gap?** "
        "Changes in the gap help us identify periods "
        "when total measured power and production-attributed "
        "power differ more or less than usual."
    )

    st.caption(
        "A larger utilization gap does not automatically "
        "indicate energy waste or poor efficiency."
    )

    # ---------------------------------
    # Key Takeaway
    # ---------------------------------
    st.subheader("Key Takeaway")

    st.write(
        "This dashboard helps us understand power "
        "utilization patterns over time by comparing "
        "total measured power with estimated "
        "production-attributed power. These insights "
        "support further investigation into data "
        "center energy efficiency."
    )

except Exception as e:
    st.error(
        f"Unable to load power data: {e}"
    )
