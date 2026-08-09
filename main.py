import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Proctor Compaction Calculator",
    page_icon="🏗️",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

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

.success-card {
    padding: 1rem;
    border-radius: 10px;
    border: 1px solid #2e7d32;
    text-align: center;
}

.warning-card {
    padding: 1rem;
    border-radius: 10px;
    border: 1px solid #ef6c00;
    text-align: center;
}

.footer {
    text-align: center;
    color: #888;
    font-size: 0.85rem;
    margin-top: 2rem;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="title">🏗️ Proctor Compaction Calculator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Laboratory Proctor analysis and field compaction assessment.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

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
        "Mg/m³",
        "g/cm³"
    ]
)

st.sidebar.markdown("---")

st.sidebar.info(
    """
    **Common laboratory standards**

    Standard Proctor:
    ASTM D698 / AASHTO T 99

    Modified Proctor:
    ASTM D1557 / AASHTO T 180

    Always follow the applicable project specification
    and laboratory standard.
    """
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def convert_density_from_kg_m3(value, unit):
    """Convert kg/m³ to selected density unit."""

    if unit == "kg/m³":
        return value

    if unit == "Mg/m³":
        return value / 1000

    if unit == "g/cm³":
        return value / 1000

    return value


def convert_density_to_kg_m3(value, unit):
    """Convert selected density unit to kg/m³."""

    if unit == "kg/m³":
        return value

    if unit == "Mg/m³":
        return value * 1000

    if unit == "g/cm³":
        return value * 1000

    return value


def calculate_dry_density(wet_density, moisture):
    """Calculate dry density from wet density."""

    return wet_density / (1 + moisture / 100)


def calculate_zav(gs, moisture):
    """
    Calculate Zero Air Voids dry density.

    ρ_zav = Gs * ρw / (1 + w)

    Using water density = 1000 kg/m³.
    """

    return (gs * 1000) / (1 + moisture / 100)


# =========================================================
# MAIN TABS
# =========================================================

tab1, tab2, tab3 = st.tabs(
    [
        "🧪 Proctor Laboratory Analysis",
        "📍 Field Compaction",
        "📊 Engineering Summary"
    ]
)


# =========================================================
# TAB 1 — LABORATORY PROCTOR
# =========================================================

with tab1:

    st.header("Laboratory Proctor Analysis")

    st.write(
        "Enter the laboratory measurements for each compacted specimen."
    )

    # -----------------------------------------------------
    # INPUT METHOD
    # -----------------------------------------------------

    input_mode = st.radio(
        "How would you like to enter density data?",
        [
            "Wet Soil Mass + Mold Volume",
            "Wet/Bulk Density",
            "Dry Density"
        ],
        horizontal=True
    )

    # -----------------------------------------------------
    # GENERAL TEST PARAMETERS
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        num_points = st.number_input(
            "Number of test points",
            min_value=3,
            max_value=10,
            value=5,
            step=1
        )

    with col2:

        specific_gravity = st.number_input(
            "Specific Gravity (Gs)",
            min_value=1.0,
            max_value=4.0,
            value=2.65,
            step=0.01
        )

    with col3:

        water_density = st.number_input(
            "Water Density (kg/m³)",
            min_value=900.0,
            max_value=1100.0,
            value=1000.0,
            step=1.0
        )

    st.markdown("---")

    # -----------------------------------------------------
    # MOLD PARAMETERS
    # -----------------------------------------------------

    if input_mode == "Wet Soil Mass + Mold Volume":

        st.subheader("Mold Information")

        mold_col1, mold_col2 = st.columns(2)

        with mold_col1:

            mold_volume_cm3 = st.number_input(
                "Mold Volume (cm³)",
                min_value=100.0,
                value=944.0,
                step=1.0
            )

        with mold_col2:

            mold_mass_g = st.number_input(
                "Mold Mass (g)",
                min_value=0.0,
                value=0.0,
                step=1.0
            )

    # -----------------------------------------------------
    # TEST POINT INPUT
    # -----------------------------------------------------

    st.subheader("Test Specimens")

    rows = []

    for i in range(int(num_points)):

        st.markdown(f"**Specimen {i + 1}**")

        col1, col2, col3 = st.columns(3)

        with col1:

            moisture = st.number_input(
                f"Moisture Content (%) — Point {i + 1}",
                min_value=0.0,
                max_value=100.0,
                value=float(4 + i * 2),
                step=0.1,
                key=f"moisture_{i}"
            )

        with col2:

            if input_mode == "Wet Soil Mass + Mold Volume":

                wet_mass = st.number_input(
                    f"Wet Soil Mass (g) — Point {i + 1}",
                    min_value=0.1,
                    value=1700.0,
                    step=1.0,
                    key=f"wet_mass_{i}"
                )

                density_input = wet_mass

            elif input_mode == "Wet/Bulk Density":

                density_input = st.number_input(
                    f"Wet/Bulk Density ({density_unit}) — Point {i + 1}",
                    min_value=0.001,
                    value=1800.0,
                    step=1.0,
                    key=f"wet_density_{i}"
                )

            else:

                density_input = st.number_input(
                    f"Dry Density ({density_unit}) — Point {i + 1}",
                    min_value=0.001,
                    value=1600.0,
                    step=1.0,
                    key=f"dry_density_{i}"
                )

        with col3:

            if input_mode == "Wet Soil Mass + Mold Volume":

                st.write("")

                st.caption(
                    "Bulk density will be calculated automatically."
                )

            elif input_mode == "Wet/Bulk Density":

                st.write("")

                st.caption(
                    "Dry density will be calculated automatically."
                )

            else:

                st.write("")

                st.caption(
                    "Density entered directly."
                )

        rows.append(
            {
                "Point": i + 1,
                "Moisture Content (%)": moisture,
                "Density Input": density_input
            }
        )

    # -----------------------------------------------------
    # BUILD DATAFRAME
    # -----------------------------------------------------

    df = pd.DataFrame(rows)

    # -----------------------------------------------------
    # CALCULATIONS
    # -----------------------------------------------------

    if input_mode == "Wet Soil Mass + Mold Volume":

        # Convert cm³ to m³
        mold_volume_m3 = mold_volume_cm3 * 1e-6

        # Wet soil mass in kg
        wet_soil_mass_kg = (
            df["Density Input"] - mold_mass_g
        ) / 1000

        # Bulk density kg/m³
        df["Wet Density (kg/m³)"] = (
            wet_soil_mass_kg / mold_volume_m3
        )

        df["Dry Density (kg/m³)"] = (
            df["Wet Density (kg/m³)"] /
            (
                1 +
                df["Moisture Content (%)"] / 100
            )
        )

    elif input_mode == "Wet/Bulk Density":

        df["Wet Density (kg/m³)"] = (
            df["Density Input"].apply(
                lambda x:
                convert_density_to_kg_m3(
                    x,
                    density_unit
                )
            )
        )

        df["Dry Density (kg/m³)"] = (
            df["Wet Density (kg/m³)"] /
            (
                1 +
                df["Moisture Content (%)"] / 100
            )
        )

    else:

        df["Dry Density (kg/m³)"] = (
            df["Density Input"].apply(
                lambda x:
                convert_density_to_kg_m3(
                    x,
                    density_unit
                )
            )
        )

    # -----------------------------------------------------
    # ZAV CALCULATION
    # -----------------------------------------------------

    df["ZAV Density (kg/m³)"] = (
        (
            specific_gravity *
            water_density
        )
        /
        (
            1 +
            df["Moisture Content (%)"] / 100
        )
    )

    # -----------------------------------------------------
    # SORT DATA
    # -----------------------------------------------------

    df = df.sort_values(
        "Moisture Content (%)"
    ).reset_index(drop=True)

    # -----------------------------------------------------
    # DISPLAY RESULTS
    # -----------------------------------------------------

    st.subheader("Calculated Specimen Results")

    display_df = pd.DataFrame(
        {
            "Point":
                df["Point"].astype(int),

            "Moisture Content (%)":
                df["Moisture Content (%)"].round(2),

            "Dry Density":
                df["Dry Density (kg/m³)"].apply(
                    lambda x:
                    round(
                        convert_density_from_kg_m3(
                            x,
                            density_unit
                        ),
                        3
                    )
                ),

            "ZAV Density":
                df["ZAV Density (kg/m³)"].apply(
                    lambda x:
                    round(
                        convert_density_from_kg_m3(
                            x,
                            density_unit
                        ),
                        3
                    )
                )
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    moisture = df[
        "Moisture Content (%)"
    ].values

    dry_density = df[
        "Dry Density (kg/m³)"
    ].values

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
    # CURVE FIT
    # -----------------------------------------------------

    coefficients = np.polyfit(
        moisture,
        dry_density,
        2
    )

    a, b, c = coefficients

    measured_max_index = np.argmax(
        dry_density
    )

    measured_mdd = dry_density[
        measured_max_index
    ]

    measured_omc = moisture[
        measured_max_index
    ]

    # Default to measured maximum
    mdd = measured_mdd
    omc = measured_omc

    # Quadratic fit
    if a < 0:

        estimated_omc = -b / (2 * a)

        estimated_mdd = (
            a * estimated_omc**2
            + b * estimated_omc
            + c
        )

        # Only accept vertex if it lies inside
        # the measured moisture range.

        if (
            moisture.min()
            <= estimated_omc
            <= moisture.max()
        ):

            omc = estimated_omc
            mdd = estimated_mdd

    # -----------------------------------------------------
    # RESULT CARDS
    # -----------------------------------------------------

    st.subheader("Proctor Results")

    result_col1, result_col2, result_col3 = st.columns(3)

    with result_col1:

        st.markdown(
            f"""
            <div class="result-card">

            <div class="result-label">
            Maximum Dry Density (MDD)
            </div>

            <div class="result-value">
            {convert_density_from_kg_m3(mdd, density_unit):.3f}
            </div>

            <div class="result-label">
            {density_unit}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with result_col2:

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

    with result_col3:

        st.markdown(
            f"""
            <div class="result-card">

            <div class="result-label">
            Specific Gravity
            </div>

            <div class="result-value">
            {specific_gravity:.2f}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    # -----------------------------------------------------
    # COMPACTION CURVE
    # -----------------------------------------------------

    st.subheader("Moisture–Density Relationship")

    x_curve = np.linspace(
        moisture.min(),
        moisture.max(),
        300
    )

    if a < 0:

        y_curve = (
            a * x_curve**2
            + b * x_curve
            + c
        )

    else:

        y_curve = np.full_like(
            x_curve,
            measured_mdd
        )

    zav_curve = (
        specific_gravity *
        water_density
        /
        (
            1 +
            x_curve / 100
        )
    )

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    # Experimental data
    ax.scatter(
        moisture,
        dry_density,
        s=70,
        label="Laboratory Data"
    )

    # Fitted curve
    if a < 0:

        ax.plot(
            x_curve,
            y_curve,
            linewidth=2,
            label="Fitted Compaction Curve"
        )

    # ZAV curve
    ax.plot(
        x_curve,
        zav_curve,
        linestyle="--",
        linewidth=1.5,
        label="Zero Air Voids Curve"
    )

    # MDD point
    ax.scatter(
        [omc],
        [mdd],
        s=110,
        marker="X",
        label=f"MDD = {convert_density_from_kg_m3(mdd, density_unit):.3f}"
    )

    # OMC line
    ax.axvline(
        omc,
        linestyle=":",
        linewidth=1
    )

    # MDD line
    ax.axhline(
        mdd,
        linestyle=":",
        linewidth=1
    )

    ax.set_xlabel(
        "Moisture Content (%)"
    )

    ax.set_ylabel(
        f"Dry Density ({density_unit})"
    )

    ax.set_title(
        f"{test_method} Compaction Curve"
    )

    ax.grid(
        True,
        alpha=0.3
    )

    ax.legend()

    st.pyplot(fig)

    # -----------------------------------------------------
    # DOWNLOAD DATA
    # -----------------------------------------------------

    export_df = pd.DataFrame(
        {
            "Point":
                df["Point"].astype(int),

            "Moisture Content (%)":
                df["Moisture Content (%)"],

            "Dry Density":
                df["Dry Density (kg/m³)"].apply(
                    lambda x:
                    convert_density_from_kg_m3(
                        x,
                        density_unit
                    )
                ),

            "ZAV Density":
                df["ZAV Density (kg/m³)"].apply(
                    lambda x:
                    convert_density_from_kg_m3(
                        x,
                        density_unit
                    )
                )
        }
    )

    csv_data = export_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇️ Download Test Data (CSV)",
        data=csv_data,
        file_name="proctor_test_results.csv",
        mime="text/csv"
    )


# =========================================================
# TAB 2 — FIELD COMPACTION
# =========================================================

with tab2:

    st.header("Field Compaction Assessment")

    st.write(
        "Compare a field dry density against the laboratory "
        "Maximum Dry Density."
    )

    field_col1, field_col2 = st.columns(2)

    with field_col1:

        field_density = st.number_input(
            f"Field Dry Density ({density_unit})",
            min_value=0.001,
            value=1750.0,
            step=1.0
        )

    with field_col2:

        laboratory_mdd = st.number_input(
            f"Laboratory MDD ({density_unit})",
            min_value=0.001,
            value=1800.0,
            step=1.0
        )

    st.subheader("Compaction Requirement")

    requirement = st.number_input(
        "Required Minimum Compaction (%)",
        min_value=50.0,
        max_value=110.0,
        value=95.0,
        step=0.5
    )

    if st.button(
        "Calculate Field Compaction",
        type="primary"
    ):

        percent_compaction = (
            field_density /
            laboratory_mdd
        ) * 100

        st.subheader(
            "Field Compaction Result"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Percentage Compaction",
                f"{percent_compaction:.2f}%"
            )

        with col2:

            difference = (
                percent_compaction
                - requirement
            )

            st.metric(
                "Difference from Requirement",
                f"{difference:+.2f}%"
            )

        if percent_compaction >= requirement:

            st.success(
                f"PASS — The field compaction of "
                f"{percent_compaction:.2f}% meets the "
                f"minimum requirement of "
                f"{requirement:.2f}%."
            )

        else:

            st.error(
                f"FAIL — The field compaction of "
                f"{percent_compaction:.2f}% is below the "
                f"minimum requirement of "
                f"{requirement:.2f}%."
            )

        st.info(
            """
            Percentage compaction is calculated as:

            % Compaction =
            (Field Dry Density / Laboratory MDD) × 100
            """
        )


# =========================================================
# TAB 3 — ENGINEERING SUMMARY
# =========================================================

with tab3:

    st.header("Engineering Summary")

    st.write(
        "Key information about the Proctor compaction analysis."
    )

    st.subheader("Test Information")

    summary = pd.DataFrame(
        {
            "Parameter": [
                "Compaction Method",
                "Specific Gravity",
                "Density Unit",
                "Laboratory MDD",
                "Laboratory OMC"
            ],

            "Value": [
                test_method,
                specific_gravity,
                density_unit,
                "Calculated in Laboratory tab",
                "Calculated in Laboratory tab"
            ]
        }
    )

    st.table(summary)

    st.subheader(
        "Engineering Relationships"
    )

    st.markdown(
        """
        ### Dry Density

        When wet/bulk density is known:

        \[
        \\rho_d =
        \\frac{\\rho}{1+w}
        \]

        Where:

        - **ρd** = dry density
        - **ρ** = wet/bulk density
        - **w** = moisture content as a decimal

        ### Percentage Compaction

        \[
        \\%\\ Compaction =
        \\frac{\\rho_{d(field)}}
        {\\rho_{d(max)}} \\times 100
        \]

        ### Zero Air Voids

        \[
        \\rho_{ZAV} =
        \\frac{G_s \\rho_w}
        {1+w}
        \]

        Where:

        - **Gs** = specific gravity of soil solids
        - **ρw** = density of water
        - **w** = moisture content as a decimal
        """
    )

    st.warning(
        """
        **Engineering Disclaimer**

        This software is an engineering calculation aid.
        Results should be checked against the applicable
        laboratory standard, project specification, sample
        preparation procedure, and engineering judgement before
        being used for construction acceptance or design.
        """
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">

    Built for engineers. Powered by code.<br>

    Automation_hub Engineering Group

    </div>
    """,
    unsafe_allow_html=True
)
