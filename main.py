import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Proctor Compaction Calculator",
    page_icon="🏗️",
    layout="wide"
)

# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }

    .title {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #666;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }

    .result-card {
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid #ddd;
        text-align: center;
        background-color: #fafafa;
    }

    .result-value {
        font-size: 2rem;
        font-weight: 700;
    }

    .result-label {
        font-size: 0.9rem;
        color: #666;
    }

    .footer {
        text-align: center;
        color: #888;
        font-size: 0.85rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown(
    '<div class="title">🏗️ Proctor Compaction Calculator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Determine Maximum Dry Density (MDD) and Optimum Moisture Content (OMC) '
    'from Proctor compaction test data.'
    '</div>',
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.header("Test Information")

test_method = st.sidebar.selectbox(
    "Compaction Method",
    [
        "Standard Proctor",
        "Modified Proctor",
        "Custom / Other"
    ]
)

density_unit = st.sidebar.selectbox(
    "Density Unit",
    [
        "kg/m³",
        "g/cm³",
        "Mg/m³"
    ]
)

st.sidebar.markdown("---")

st.sidebar.info(
    """
    **Standard Proctor**

    Commonly associated with ASTM D698 / AASHTO T 99.

    **Modified Proctor**

    Commonly associated with ASTM D1557 / AASHTO T 180.

    Always use the test method specified by your project or laboratory standard.
    """
)

# ---------------------------------------------------------
# INPUT SECTION
# ---------------------------------------------------------
st.subheader("1. Enter Proctor Test Data")

st.write(
    "Enter the moisture content and corresponding wet/bulk density "
    "or dry density obtained from each compaction point."
)

input_mode = st.radio(
    "Input density as:",
    [
        "Wet/Bulk Density",
        "Dry Density"
    ],
    horizontal=True
)

# Number of test points
num_points = st.number_input(
    "Number of test points",
    min_value=3,
    max_value=10,
    value=5,
    step=1
)

# ---------------------------------------------------------
# DATA ENTRY
# ---------------------------------------------------------
data = []

for i in range(int(num_points)):
    col1, col2 = st.columns(2)

    with col1:
        moisture = st.number_input(
            f"Moisture Content Point {i + 1} (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(4 + i * 2),
            step=0.1,
            key=f"moisture_{i}"
        )

    with col2:
        if input_mode == "Wet/Bulk Density":
            density = st.number_input(
                f"Wet/Bulk Density Point {i + 1} ({density_unit})",
                min_value=0.001,
                value=1800.0,
                step=1.0,
                key=f"density_{i}"
            )
        else:
            density = st.number_input(
                f"Dry Density Point {i + 1} ({density_unit})",
                min_value=0.001,
                value=1600.0,
                step=1.0,
                key=f"density_{i}"
            )

    data.append([moisture, density])

df = pd.DataFrame(
    data,
    columns=["Moisture Content (%)", "Input Density"]
)

# ---------------------------------------------------------
# CALCULATE DRY DENSITY
# ---------------------------------------------------------
if input_mode == "Wet/Bulk Density":

    # γd = γ / (1 + w)
    df["Dry Density"] = (
        df["Input Density"] /
        (1 + df["Moisture Content (%)"] / 100)
    )

else:

    df["Dry Density"] = df["Input Density"]

# ---------------------------------------------------------
# DISPLAY DATA
# ---------------------------------------------------------
st.subheader("2. Test Data")

display_df = df.copy()

display_df["Moisture Content (%)"] = display_df[
    "Moisture Content (%)"
].round(2)

display_df["Input Density"] = display_df[
    "Input Density"
].round(3)

display_df["Dry Density"] = display_df[
    "Dry Density"
].round(3)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# ---------------------------------------------------------
# CALCULATION
# ---------------------------------------------------------
if st.button("Calculate MDD & OMC", type="primary"):

    moisture = df["Moisture Content (%)"].values
    dry_density = df["Dry Density"].values

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------
    if len(set(moisture)) != len(moisture):
        st.error(
            "Each moisture content value must be different."
        )
        st.stop()

    if np.any(dry_density <= 0):
        st.error(
            "Dry density values must be greater than zero."
        )
        st.stop()

    # -----------------------------------------------------
    # SORT DATA
    # -----------------------------------------------------
    sort_index = np.argsort(moisture)

    moisture_sorted = moisture[sort_index]
    density_sorted = dry_density[sort_index]

    # -----------------------------------------------------
    # FIND INITIAL MAXIMUM
    # -----------------------------------------------------
    max_index = np.argmax(density_sorted)

    initial_omc = moisture_sorted[max_index]
    initial_mdd = density_sorted[max_index]

    # -----------------------------------------------------
    # PARABOLIC FIT
    # -----------------------------------------------------
    #
    # A second-degree polynomial is fitted to the
    # moisture-density relationship.
    #
    # y = ax² + bx + c
    #
    # Vertex:
    # x = -b / (2a)
    #
    # This gives the estimated OMC and MDD.
    # -----------------------------------------------------

    try:

        # Fit a quadratic
        coefficients = np.polyfit(
            moisture_sorted,
            density_sorted,
            2
        )

        a, b, c = coefficients

        # A valid compaction curve should open downward
        if a >= 0:

            st.warning(
                "The entered data does not produce a clear "
                "downward-opening compaction curve. "
                "The highest measured density will be used."
            )

            omc = initial_omc
            mdd = initial_mdd

        else:

            # Vertex of parabola
            omc = -b / (2 * a)

            # Density at vertex
            mdd = (
                a * omc**2
                + b * omc
                + c
            )

            # Check whether estimated OMC is reasonable
            min_moisture = moisture_sorted.min()
            max_moisture = moisture_sorted.max()

            if (
                omc < min_moisture
                or omc > max_moisture
            ):

                st.warning(
                    "The estimated OMC falls outside the "
                    "range of the measured moisture contents. "
                    "The measured maximum has been used instead."
                )

                omc = initial_omc
                mdd = initial_mdd

    except Exception as e:

        st.error(
            f"Unable to fit the compaction curve: {e}"
        )

        omc = initial_omc
        mdd = initial_mdd

    # -----------------------------------------------------
    # RESULTS
    # -----------------------------------------------------
    st.subheader("3. Proctor Test Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">
                    Maximum Dry Density (MDD)
                </div>
                <div class="result-value">
                    {mdd:.2f}
                </div>
                <div class="result-label">
                    {density_unit}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">
                    Optimum Moisture Content (OMC)
                </div>
                <div class="result-value">
                    {omc:.2f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">
                    Test Method
                </div>
                <div class="result-value">
                    {test_method.split()[0]}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # -----------------------------------------------------
    # COMPACTION CURVE
    # -----------------------------------------------------
    st.subheader("4. Moisture-Density Relationship")

    # Generate smooth curve
    x_curve = np.linspace(
        moisture_sorted.min(),
        moisture_sorted.max(),
        200
    )

    y_curve = (
        a * x_curve**2
        + b * x_curve
        + c
    ) if a < 0 else np.full_like(
        x_curve,
        initial_mdd
    )

    fig, ax = plt.subplots(figsize=(10, 5))

    # Experimental points
    ax.scatter(
        moisture_sorted,
        density_sorted,
        s=60,
        label="Test Data"
    )

    # Fitted curve
    if a < 0:
        ax.plot(
            x_curve,
            y_curve,
            linewidth=2,
            label="Fitted Compaction Curve"
        )

    # MDD / OMC point
    ax.scatter(
        [omc],
        [mdd],
        s=100,
        marker="X",
        label=f"MDD = {mdd:.2f}"
    )

    ax.axvline(
        omc,
        linestyle="--",
        linewidth=1
    )

    ax.axhline(
        mdd,
        linestyle="--",
        linewidth=1
    )

    ax.set_xlabel("Moisture Content (%)")
    ax.set_ylabel(f"Dry Density ({density_unit})")

    ax.set_title(
        f"{test_method} Compaction Curve"
    )

    ax.grid(True, alpha=0.3)
    ax.legend()

    st.pyplot(fig)

    # -----------------------------------------------------
    # RESULTS TABLE
    # -----------------------------------------------------
    st.subheader("5. Calculated Results")

    result_table = pd.DataFrame({
        "Parameter": [
            "Maximum Dry Density (MDD)",
            "Optimum Moisture Content (OMC)",
            "Number of Test Points",
            "Compaction Method"
        ],
        "Result": [
            f"{mdd:.2f} {density_unit}",
            f"{omc:.2f} %",
            str(num_points),
            test_method
        ]
    })

    st.table(result_table)

    # -----------------------------------------------------
    # ENGINEERING NOTE
    # -----------------------------------------------------
    st.info(
        """
        **Engineering Note**

        The MDD and OMC are estimated from the moisture-density
        relationship using a second-degree polynomial fit.

        For project acceptance, the laboratory procedure,
        applicable specification, test method, sample preparation,
        oversize correction, and engineering judgement should be
        considered.
        """
    )

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.markdown(
    """
    <div class="footer">
        Built for engineers. Powered by code.<br>
        Automation_hub Engineering Group
    </div>
    """,
    unsafe_allow_html=True
)
