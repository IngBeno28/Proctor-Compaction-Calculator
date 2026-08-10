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

st.markdown(
    """
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

    .calculated-value {
        font-weight: 600;
    }

    .footer {
        text-align: center;
        color: #888;
        font-size: 0.85rem;
        margin-top: 2rem;
        padding-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)


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

def kg_m3_to_selected_density(value, unit):
    """Convert density from kg/m³ to selected unit."""

    if unit == "kg/m³":
        return value

    if unit == "Mg/m³":
        return value / 1000

    if unit == "g/cm³":
        return value / 1000

    return value


def selected_density_to_kg_m3(value, unit):
    """Convert density from selected unit to kg/m³."""

    if unit == "kg/m³":
        return value

    if unit == "Mg/m³":
        return value * 1000

    if unit == "g/cm³":
        return value * 1000

    return value


def calculate_mdd_omc(moisture, dry_density):
    """
    Determine MDD and OMC using a quadratic fit.

    Returns:
        mdd_kg_m3
        omc_percent
        coefficients
    """

    coefficients = np.polyfit(
        moisture,
        dry_density,
        2
    )

    a, b, c = coefficients

    # Measured maximum
    max_index = np.argmax(dry_density)

    measured_mdd = dry_density[max_index]
    measured_omc = moisture[max_index]

    mdd = measured_mdd
    omc = measured_omc

    # A valid compaction curve should open downward.
    if a < 0:

        estimated_omc = -b / (2 * a)

        estimated_mdd = (
            a * estimated_omc**2
            + b * estimated_omc
            + c
        )

        # Only accept the fitted vertex if it falls
        # within the measured moisture range.
        if (
            moisture.min()
            <= estimated_omc
            <= moisture.max()
        ):

            omc = estimated_omc
            mdd = estimated_mdd

    return mdd, omc, coefficients


# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3 = st.tabs(
    [
        "🧪 Proctor Laboratory Analysis",
        "📍 Field Compaction",
        "📊 Engineering Summary"
    ]
)


# =========================================================
# TAB 1 — LABORATORY PROCTOR ANALYSIS
# =========================================================

with tab1:

    st.header("Laboratory Proctor Analysis")

    st.write(
        "Enter the measured laboratory values below. "
        "Wet soil mass, wet density and dry density are "
        "calculated automatically."
    )

    # -----------------------------------------------------
    # GENERAL TEST INFORMATION
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

    # -----------------------------------------------------
    # MOULD INFORMATION
    # -----------------------------------------------------

    st.subheader("Mould Information")

    mould_col1, mould_col2 = st.columns(2)

    with mould_col1:

        mould_factor = st.number_input(
            "Mould Factor (cm⁻³)",
            min_value=0.000001,
            value=0.001061,
            format="%.9f",
            help=(
                "Mould factor is the inverse of mould volume. "
                "When mass is entered in grams, the resulting "
                "wet density is obtained in g/cm³."
            )
        )

    with mould_col2:

        mould_mass = st.number_input(
            "Mould Mass (g)",
            min_value=0.0,
            value=700.0,
            step=0.1
        )

    st.caption(
        "Mould factor = 1 / mould volume. "
        "For consistency, mould factor is entered in cm⁻³ "
        "when specimen masses are entered in grams."
    )

    st.markdown("---")

    # -----------------------------------------------------
    # SPECIMEN INPUT
    # -----------------------------------------------------

    st.subheader("Proctor Test Specimens")

    st.write(
        "Enter the wet soil + mould mass and moisture "
        "content for each specimen."
    )

    specimen_rows = []

    for i in range(int(num_points)):

        st.markdown(
            f"### Specimen {i + 1}"
        )

        col1, col2 = st.columns(2)

        with col1:

            wet_soil_mould_mass = st.number_input(
                "Wet Soil + Mould Mass (g)",
                min_value=0.1,
                value=1650.0 + (i * 25),
                step=0.1,
                key=f"wet_soil_mould_mass_{i}"
            )

        with col2:

            moisture_content = st.number_input(
                "Moisture Content (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(4 + i * 2),
                step=0.1,
                key=f"moisture_content_{i}"
            )

        # -------------------------------------------------
        # AUTOMATIC CALCULATIONS
        # -------------------------------------------------

        wet_soil_mass = (
            wet_soil_mould_mass
            - mould_mass
        )

        # Wet density in g/cm³
        wet_density_g_cm3 = (
            wet_soil_mass
            * mould_factor
        )

        # Convert to kg/m³
        wet_density_kg_m3 = (
            wet_density_g_cm3
            * 1000
        )

        # Dry density
        dry_density_kg_m3 = (
            wet_density_kg_m3
            /
            (
                1
                +
                moisture_content / 100
            )
        )

        specimen_rows.append(
            {
                "Point": i + 1,
                "Moisture Content (%)":
                    moisture_content,
                "Wet Soil + Mould Mass (g)":
                    wet_soil_mould_mass,
                "Wet Soil Mass (g)":
                    wet_soil_mass,
                "Wet Density (kg/m³)":
                    wet_density_kg_m3,
                "Dry Density (kg/m³)":
                    dry_density_kg_m3
            }
        )

    # -----------------------------------------------------
    # CREATE DATAFRAME
    # -----------------------------------------------------

    df = pd.DataFrame(specimen_rows)

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if np.any(
        df["Wet Soil Mass (g)"] <= 0
    ):

        st.error(
            "Wet Soil Mass must be greater than zero. "
            "Check the mould mass and wet soil + mould mass."
        )

        st.stop()

    if len(
        set(df["Moisture Content (%)"])
    ) != len(df):

        st.error(
            "Each specimen must have a different "
            "moisture content."
        )

        st.stop()

    # -----------------------------------------------------
    # SORT DATA
    # -----------------------------------------------------

    df = df.sort_values(
        "Moisture Content (%)"
    ).reset_index(drop=True)

    # -----------------------------------------------------
    # DISPLAY CALCULATED RESULTS
    # -----------------------------------------------------

    st.subheader("Calculated Specimen Results")

    display_df = pd.DataFrame(
        {
            "Point":
                df["Point"].astype(int),

            "Moisture Content (%)":
                df[
                    "Moisture Content (%)"
                ].round(2),

            "Wet Soil + Mould Mass (g)":
                df[
                    "Wet Soil + Mould Mass (g)"
                ].round(2),

            "Wet Soil Mass (g)":
                df[
                    "Wet Soil Mass (g)"
                ].round(2),

            "Wet Density":
                df[
                    "Wet Density (kg/m³)"
                ].apply(
                    lambda x:
                    round(
                        kg_m3_to_selected_density(
                            x,
                            density_unit
                        ),
                        3
                    )
                ),

            "Dry Density":
                df[
                    "Dry Density (kg/m³)"
                ].apply(
                    lambda x:
                    round(
                        kg_m3_to_selected_density(
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
    # CALCULATE MDD AND OMC
    # -----------------------------------------------------

    moisture = df[
        "Moisture Content (%)"
    ].to_numpy()

    dry_density = df[
        "Dry Density (kg/m³)"
    ].to_numpy()

    mdd, omc, coefficients = calculate_mdd_omc(
        moisture,
        dry_density
    )

    a, b, c = coefficients

    # -----------------------------------------------------
    # ZAV CALCULATION
    # -----------------------------------------------------

    df["ZAV Density (kg/m³)"] = (
        specific_gravity
        * water_density
        /
        (
            1
            +
            df["Moisture Content (%)"] / 100
        )
    )

    # -----------------------------------------------------
    # RESULTS
    # -----------------------------------------------------

    st.subheader("Proctor Test Results")

    result_col1, result_col2, result_col3 = st.columns(3)

    with result_col1:

        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">
                    Maximum Dry Density
                </div>

                <div class="result-value">
                    {
                        kg_m3_to_selected_density(
                            mdd,
                            density_unit
                        ): .3f
                    }
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
                    Optimum Moisture Content
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
            np.max(dry_density)
        )

    # Zero Air Voids curve
    zav_curve = (
        specific_gravity
        * water_density
        /
        (
            1
            +
            x_curve / 100
        )
    )

    # Convert curves to selected unit
    y_curve_display = np.array(
        [
            kg_m3_to_selected_density(
                value,
                density_unit
            )
            for value in y_curve
        ]
    )

    zav_curve_display = np.array(
        [
            kg_m3_to_selected_density(
                value,
                density_unit
            )
            for value in zav_curve
        ]
    )

    dry_density_display = np.array(
        [
            kg_m3_to_selected_density(
                value,
                density_unit
            )
            for value in dry_density
        ]
    )

    mdd_display = kg_m3_to_selected_density(
        mdd,
        density_unit
    )

    # -----------------------------------------------------
    # PLOT
    # -----------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    # Laboratory points
    ax.scatter(
        moisture,
        dry_density_display,
        s=70,
        label="Laboratory Data"
    )

    # Fitted compaction curve
    if a < 0:

        ax.plot(
            x_curve,
            y_curve_display,
            linewidth=2,
            label="Fitted Compaction Curve"
        )

    # ZAV curve
    ax.plot(
        x_curve,
        zav_curve_display,
        linestyle="--",
        linewidth=1.5,
        label="Zero Air Voids Curve"
    )

    # MDD point
    ax.scatter(
        [omc],
        [mdd_display],
        s=110,
        marker="X",
        label=f"MDD = {mdd_display:.3f} {density_unit}"
    )

    # OMC line
    ax.axvline(
        omc,
        linestyle=":",
        linewidth=1
    )

    # MDD line
    ax.axhline(
        mdd_display,
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
    # ENGINEERING CALCULATION DETAILS
    # -----------------------------------------------------

    with st.expander(
        "Show calculation details"
    ):

        st.markdown(
            """
            ### Wet Soil Mass

            The wet soil mass is calculated from:

            **Wet Soil Mass = Wet Soil + Mould Mass − Mould Mass**

            ### Wet Density

            The mould factor is the inverse of mould volume:

            **Mould Factor = 1 / Mould Volume**

            Therefore:

            **Wet Density = Wet Soil Mass × Mould Factor**

            ### Dry Density

            **Dry Density = Wet Density / (1 + w)**

            where **w** is the moisture content expressed
            as a decimal.

            ### Zero Air Voids

            The theoretical zero-air-voids density is calculated
            using the specific gravity of the soil solids.
            """
        )

    # -----------------------------------------------------
    # DOWNLOAD RESULTS
    # -----------------------------------------------------

    export_df = display_df.copy()

    csv_data = export_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇️ Download Test Results (CSV)",
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
        "Compare field dry density with the laboratory "
        "Maximum Dry Density."
    )

    field_col1, field_col2 = st.columns(2)

    with field_col1:

        field_density = st.number_input(
            f"Field Dry Density ({density_unit})",
            min_value=0.001,
            value=1.75 if density_unit != "kg/m³"
            else 1750.0,
            step=0.001 if density_unit != "kg/m³"
            else 1.0
        )

    with field_col2:

        laboratory_mdd = st.number_input(
            f"Laboratory MDD ({density_unit})",
            min_value=0.001,
            value=1.80 if density_unit != "kg/m³"
            else 1800.0,
            step=0.001 if density_unit != "kg/m³"
            else 1.0
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

        field_density_kg_m3 = (
            selected_density_to_kg_m3(
                field_density,
                density_unit
            )
        )

        laboratory_mdd_kg_m3 = (
            selected_density_to_kg_m3(
                laboratory_mdd,
                density_unit
            )
        )

        percent_compaction = (
            field_density_kg_m3
            /
            laboratory_mdd_kg_m3
        ) * 100

        difference = (
            percent_compaction
            - requirement
        )

        st.subheader(
            "Field Compaction Result"
        )

        result_col1, result_col2 = st.columns(2)

        with result_col1:

            st.metric(
                "Percentage Compaction",
                f"{percent_compaction:.2f}%"
            )

        with result_col2:

            st.metric(
                "Difference from Requirement",
                f"{difference:+.2f}%"
            )

        if percent_compaction >= requirement:

            st.success(
                f"PASS — Field compaction is "
                f"{percent_compaction:.2f}%, meeting the "
                f"minimum requirement of {requirement:.2f}%."
            )

        else:

            st.error(
                f"FAIL — Field compaction is "
                f"{percent_compaction:.2f}%, below the "
                f"minimum requirement of {requirement:.2f}%."
            )

        st.info(
            """
            **Percentage Compaction**

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
        "Reference information for the Proctor compaction "
        "calculations used by this application."
    )

    st.subheader("Current Test Configuration")

    summary = pd.DataFrame(
        {
            "Parameter": [
                "Compaction Method",
                "Number of Test Points",
                "Mould Factor",
                "Mould Mass",
                "Specific Gravity",
                "Water Density",
                "Density Unit"
            ],

            "Value": [
                test_method,
                num_points,
                f"{mould_factor:.9f} cm⁻³",
                f"{mould_mass:.2f} g",
                f"{specific_gravity:.2f}",
                f"{water_density:.1f} kg/m³",
                density_unit
            ]
        }
    )

    st.table(summary)

    st.subheader("Calculation Relationships")

    st.markdown(
        """
        ### 1. Wet Soil Mass

        Wet Soil Mass is obtained by subtracting the mould
        mass from the combined wet soil + mould mass.

        ### 2. Wet Density

        Wet density is obtained using the mould factor.

        ### 3. Dry Density

        Dry density is obtained by correcting wet density
        for the measured moisture content.

        ### 4. Maximum Dry Density

        MDD is the maximum dry density obtained from the
        fitted moisture-density relationship.

        ### 5. Optimum Moisture Content

        OMC is the moisture content corresponding to the
        maximum dry density.

        ### 6. Zero Air Voids

        The Zero Air Voids curve represents the theoretical
        dry density at 100% saturation for the specified
        specific gravity.
        """
    )

    st.warning(
        """
        **Engineering Disclaimer**

        This software is an engineering calculation aid.
        Results should be checked against the applicable
        laboratory standard, project specification, sample
        preparation procedure, and engineering judgement
        before being used for construction acceptance or design.
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
