import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import os
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    HRFlowable,
    Image as RLImage
)
from reportlab.pdfgen import canvas as pdfcanvas

LOGO_PATH = "assets/2.png"


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

project_name = st.sidebar.text_input(
    "Project Name",
    value="",
    placeholder="Unnamed Project"
)

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


def fit_compaction_curve(moisture, dry_density, num_curve_points=400):
    """
    Fit a smooth curve through the measured (moisture, dry density)
    points and determine MDD/OMC from its peak.

    Uses a spline that passes exactly through every measured point
    (matching the classic smoothed Proctor curve), falling back to a
    quadratic regression only if there are too few points for a spline.

    Returns:
        mdd, omc, x_curve, y_curve, peak_within_range
    """

    order = np.argsort(moisture)
    moisture_sorted = moisture[order]
    dry_density_sorted = dry_density[order]

    n = len(moisture_sorted)

    # Spline order: cubic for 4+ points, quadratic for exactly 3.
    k = min(3, n - 1)

    x_curve = np.linspace(
        moisture_sorted.min(),
        moisture_sorted.max(),
        num_curve_points
    )

    try:
        from scipy.interpolate import make_interp_spline

        spline = make_interp_spline(
            moisture_sorted,
            dry_density_sorted,
            k=k
        )

        y_curve = spline(x_curve)

    except Exception:

        # Fallback: quadratic regression if spline fitting fails.
        coefficients = np.polyfit(moisture_sorted, dry_density_sorted, 2)
        a, b, c = coefficients
        y_curve = a * x_curve**2 + b * x_curve + c

    peak_index = np.argmax(y_curve)

    mdd = y_curve[peak_index]
    omc = x_curve[peak_index]

    # The peak is considered genuinely "found" only if it sits inside
    # the tested range rather than right at either endpoint, which
    # would mean the true optimum wasn't bracketed by the data.
    edge_margin = max(1, num_curve_points // 100)

    peak_within_range = (
        edge_margin < peak_index < (num_curve_points - 1 - edge_margin)
    )

    return mdd, omc, x_curve, y_curve, peak_within_range


def check_density_plausibility(dry_density_kg_m3):
    """
    Flag dry density values that fall far outside a physically
    plausible range for a soil (roughly 800-3000 kg/m3), and try to
    identify the specific scale of the error (e.g. ~1000x too small)
    so the message can point at the actual likely cause rather than
    a generic list of possibilities.

    Returns a warning message string, or None if values look plausible.
    """

    min_density = float(np.min(dry_density_kg_m3))
    max_density = float(np.max(dry_density_kg_m3))

    if 800 <= min_density and max_density <= 3000:
        return None

    typical_density = 1900.0
    mid_density = (min_density + max_density) / 2

    if mid_density <= 0:
        implied_factor = None
    else:
        implied_factor = typical_density / mid_density

    # Try to identify a recognisable, specific cause from the size
    # of the implied error factor.
    specific_cause = None

    if implied_factor is not None:

        if 500 <= implied_factor <= 2000:
            specific_cause = (
                "This looks like a ~1000\u00d7 scale error \u2014 the "
                "most common cause is 'Wet Soil + Mould Mass' (or "
                "'Mould Mass') being entered in kilograms instead of "
                "grams. Both mass fields expect grams (e.g. 1850, "
                "not 1.85)."
            )

        elif 0.0005 <= implied_factor <= 0.002:
            specific_cause = (
                "This looks like a ~1000\u00d7-too-large scale error "
                "\u2014 check whether 'Wet Soil + Mould Mass' was "
                "entered in milligrams instead of grams, or whether "
                "an extra zero was added."
            )

        elif 5 <= implied_factor <= 15:
            specific_cause = (
                "This looks like a ~10\u00d7 scale error \u2014 double "
                "check the Mould Volume value against your mould's "
                "calibration certificate."
            )

        elif 200000 <= implied_factor <= 3000000:
            specific_cause = (
                "This looks like a ~1,000,000\u00d7 scale error \u2014 "
                "check that Mould Volume was entered in cubic "
                "centimetres (cm\u00b3), not cubic metres (m\u00b3). A "
                "standard mould is about 944 cm\u00b3, not 0.000944."
            )

    message = (
        f"Calculated dry densities ({min_density:.1f}\u2013"
        f"{max_density:.1f} kg/m\u00b3) look outside the physically "
        f"plausible range for a soil (roughly 800\u20133000 kg/m\u00b3). "
        f"This is almost always caused by a units mismatch rather "
        f"than the soil itself."
    )

    if specific_cause:
        message += " " + specific_cause
    else:
        message += (
            " Double check the Mould Volume, Mould Mass, and "
            "Wet Soil + Mould Mass values and units against your "
            "mould's calibration certificate."
        )

    return message


# =========================================================
# PDF REPORT GENERATION
# =========================================================

BRAND_BLUE = colors.HexColor("#2f5fa8")
TEXT_DARK = colors.HexColor("#1a1a1a")
TEXT_GREY = colors.HexColor("#555555")
TEXT_LIGHT_GREY = colors.HexColor("#888888")
LINE_GREY = colors.HexColor("#dddddd")

FOOTER_COPYRIGHT = (
    "Automation_hub Engineering Group Limited | "
    "\u00a9 2026 Proctor Compaction Calculator | "
    "Built for engineering precision"
)
FOOTER_CONTACT = (
    "Tel: +233501365878/+233256346244 | "
    "Web: https://automationapps.streamlit.app/"
)


class NumberedCanvas(pdfcanvas.Canvas):
    """
    A canvas that defers drawing page footers until the full document
    has been laid out, so it can display 'Page X/Y' with a correct
    total page count, and draw the top brand band on the cover page.
    """

    def __init__(self, *args, **kwargs):
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)

        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_furniture(total_pages)
            pdfcanvas.Canvas.showPage(self)

        pdfcanvas.Canvas.save(self)

    def _draw_page_furniture(self, total_pages):

        page_width, page_height = letter

        # Top brand band — cover page only
        if self._pageNumber == 1:
            self.saveState()
            self.setFillColor(BRAND_BLUE)
            self.rect(
                0,
                page_height - 0.16 * inch,
                page_width,
                0.16 * inch,
                stroke=0,
                fill=1
            )
            self.restoreState()

        # Footer — every page
        self.saveState()

        self.setStrokeColor(LINE_GREY)
        self.setLineWidth(0.5)
        self.line(
            0.75 * inch,
            0.62 * inch,
            page_width - 0.75 * inch,
            0.62 * inch
        )

        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_GREY)
        self.drawString(
            0.75 * inch,
            0.46 * inch,
            FOOTER_COPYRIGHT
        )
        self.drawRightString(
            page_width - 0.75 * inch,
            0.46 * inch,
            f"Page {self._pageNumber}/{total_pages}"
        )

        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXT_LIGHT_GREY)
        self.drawString(
            0.75 * inch,
            0.32 * inch,
            FOOTER_CONTACT
        )

        self.restoreState()


def _add_logo_or_fallback(elements, title_style):
    """Add the centered brand logo to the cover page, or a text fallback."""

    if os.path.isfile(LOGO_PATH):

        try:
            from PIL import Image as PILImage

            with PILImage.open(LOGO_PATH) as pil_logo:
                logo_w, logo_h = pil_logo.size

            max_width = 1.6 * inch
            max_height = 1.6 * inch
            scale = min(max_width / logo_w, max_height / logo_h)

            logo = RLImage(
                LOGO_PATH,
                width=logo_w * scale,
                height=logo_h * scale
            )
            logo.hAlign = "CENTER"

            elements.append(logo)
            elements.append(Spacer(1, 10))
            return

        except Exception:
            pass

    elements.append(Paragraph("🏗️ Automation_hub", title_style))
    elements.append(Spacer(1, 10))


def generate_pdf_report(
    project_name,
    test_method,
    density_unit,
    specific_gravity,
    water_density,
    mould_volume_cm3,
    mould_factor,
    mould_mass,
    display_df,
    mdd_display,
    omc,
    peak_within_range,
    fig
):
    """Build a branded, multi-page PDF report of the Proctor test results."""

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=1.1 * inch,
        bottomMargin=0.9 * inch,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=22,
        textColor=BRAND_BLUE,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=11,
        textColor=TEXT_GREY,
        spaceAfter=14
    )

    tagline_style = ParagraphStyle(
        "ReportTagline",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        textColor=TEXT_LIGHT_GREY,
        fontName="Helvetica-Oblique"
    )

    page_title_style = ParagraphStyle(
        "PageTitle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=17,
        textColor=TEXT_DARK,
        spaceAfter=16
    )

    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=16,
        spaceAfter=8,
        textColor=TEXT_DARK
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey
    )

    generated_at = datetime.now()
    generated_date_str = generated_at.strftime("%Y-%m-%d")
    generated_datetime_str = generated_at.strftime("%Y-%m-%d %H:%M")

    elements = []

    # =====================================================
    # PAGE 1 — COVER PAGE
    # =====================================================

    elements.append(Spacer(1, 0.6 * inch))

    _add_logo_or_fallback(elements, title_style)

    elements.append(
        Paragraph("Proctor Compaction Test Report", title_style)
    )
    elements.append(
        Paragraph(
            f"{test_method} Compaction Analysis",
            subtitle_style
        )
    )

    elements.append(
        HRFlowable(
            width="35%",
            thickness=2,
            color=BRAND_BLUE,
            spaceAfter=22,
            hAlign="CENTER"
        )
    )

    cover_data = [
        ["Project", project_name or "Unnamed Project"],
        ["Prepared By", "Automation_hub Engineering Group Limited"],
        ["Date Generated", generated_datetime_str],
        ["Compaction Method", test_method],
        ["Number of Specimens", str(len(display_df))]
    ]

    cover_table = Table(cover_data, colWidths=[2.2 * inch, 3.8 * inch])
    cover_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), TEXT_DARK),
                ("TEXTCOLOR", (1, 0), (1, -1), TEXT_GREY),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE_GREY),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE_GREY)
            ]
        )
    )
    elements.append(cover_table)

    elements.append(Spacer(1, 0.6 * inch))
    elements.append(
        Paragraph(
            "\u00a9 2026 Proctor Compaction Calculator | "
            "Built for engineering precision",
            tagline_style
        )
    )

    elements.append(PageBreak())

    # =====================================================
    # PAGE 2 — TEST CONFIGURATION, RESULTS & INTERPRETATION
    # =====================================================

    elements.append(
        Paragraph("Test Configuration & Specimen Results", page_title_style)
    )

    elements.append(Paragraph("Test Configuration", section_style))

    config_data = [
        ["Parameter", "Value"],
        ["Compaction Method", test_method],
        ["Specific Gravity (Gs)", f"{specific_gravity:.2f}"],
        ["Water Density", f"{water_density:.1f} kg/m\u00b3"],
        ["Mould Volume", f"{mould_volume_cm3:,.1f} cm\u00b3"],
        ["Mould Factor", f"{mould_factor:.2f} m\u207b\u00b3"],
        ["Mould Mass", f"{mould_mass:.2f} g"],
        ["Density Unit", density_unit]
    ]

    config_table = Table(config_data, colWidths=[2.5 * inch, 3.5 * inch])
    config_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), TEXT_GREY),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE_GREY)
            ]
        )
    )
    elements.append(config_table)

    elements.append(Paragraph("Calculated Specimen Results", section_style))

    table_data = (
        [list(display_df.columns)]
        + display_df.astype(str).values.tolist()
    )

    specimen_table = Table(table_data, repeatRows=1)
    specimen_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE_GREY),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5)
            ]
        )
    )
    elements.append(specimen_table)

    elements.append(Paragraph("Proctor Test Results", section_style))

    results_data = [
        ["Maximum Dry Density", f"{mdd_display:.3f} {density_unit}"],
        ["Optimum Moisture Content", f"{omc:.2f}%"],
        ["Specific Gravity", f"{specific_gravity:.2f}"]
    ]

    results_table = Table(results_data, colWidths=[3 * inch, 3 * inch])
    results_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE_GREY)
            ]
        )
    )
    elements.append(results_table)

    elements.append(Paragraph("Engineering Interpretation", section_style))

    if peak_within_range:
        interpretation_text = (
            f"The fitted moisture-density curve shows a clear peak within "
            f"the tested moisture range. Maximum Dry Density (MDD) = "
            f"{mdd_display:.3f} {density_unit} at an Optimum Moisture "
            f"Content (OMC) of {omc:.2f}%. The Zero Air Voids curve was "
            f"calculated using an assumed specific gravity (Gs) of "
            f"{specific_gravity:.2f} and a water density of "
            f"{water_density:.1f} kg/m\u00b3."
        )
    else:
        interpretation_text = (
            f"The fitted curve does not show a clear peak within the "
            f"tested moisture range, so the reported Maximum Dry Density "
            f"({mdd_display:.3f} {density_unit}) and Optimum Moisture "
            f"Content ({omc:.2f}%) correspond to the highest measured "
            f"data point rather than a true fitted peak. Additional "
            f"specimens at higher and/or lower moisture contents are "
            f"recommended to bracket the actual optimum. The Zero Air "
            f"Voids curve was calculated using an assumed specific "
            f"gravity (Gs) of {specific_gravity:.2f} and a water density "
            f"of {water_density:.1f} kg/m\u00b3."
        )

    elements.append(Paragraph(interpretation_text, body_style))

    elements.append(PageBreak())

    # =====================================================
    # PAGE 3 — COMPACTION CURVE CHART
    # =====================================================

    elements.append(
        Paragraph("Moisture\u2013Density Relationship", page_title_style)
    )

    img_buffer = BytesIO()
    fig.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
    img_buffer.seek(0)

    elements.append(
        RLImage(img_buffer, width=6.3 * inch, height=3.78 * inch)
    )

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph(
            "Engineering Disclaimer: This report is generated by an "
            "engineering calculation aid. Results should be verified "
            "against the applicable laboratory standard, project "
            "specification, and engineering judgement before use for "
            "construction acceptance or design.",
            disclaimer_style
        )
    )

    elements.append(PageBreak())

    # =====================================================
    # PAGE 4 — CERTIFICATION
    # =====================================================

    elements.append(Paragraph("Certification", page_title_style))

    elements.append(
        Paragraph(
            "This Proctor compaction test report has been reviewed and "
            "is certified as suitable for the stated project and "
            "engineering requirements.",
            body_style
        )
    )

    elements.append(Spacer(1, 26))

    elements.append(
        Paragraph(
            "Engineer Name: "
            "________________________________________",
            body_style
        )
    )
    elements.append(
        Paragraph(f"Date: {generated_date_str}", body_style)
    )

    elements.append(Spacer(1, 14))
    elements.append(Paragraph("Signature / Stamp", section_style))

    signature_box = Table(
        [[""]],
        colWidths=[5.5 * inch],
        rowHeights=[1.0 * inch]
    )
    signature_box.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, LINE_GREY)
            ]
        )
    )
    elements.append(signature_box)

    elements.append(Spacer(1, 26))
    elements.append(
        Paragraph(
            "Report prepared using Proctor Compaction Calculator by "
            "Automation_hub Engineering Group Limited. "
            "\u00a9 2026 Proctor Compaction Calculator | "
            "Built for engineering precision",
            disclaimer_style
        )
    )

    doc.build(
        elements,
        canvasmaker=NumberedCanvas
    )

    buffer.seek(0)
    return buffer


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

    MOULD_PRESETS = {
        "Standard mould (~944 cm³ / 4 in dia.)": 944.0,
        "Modified/CBR mould (~2124 cm³ / 6 in dia.)": 2124.0,
        "Custom": None
    }

    mould_preset = st.selectbox(
        "Mould Size",
        list(MOULD_PRESETS.keys()),
        help=(
            "Pick a standard mould size, or choose Custom to enter "
            "your own measured mould volume."
        )
    )

    mould_col1, mould_col2 = st.columns(2)

    with mould_col1:

        preset_volume = MOULD_PRESETS[mould_preset]

        mould_volume_cm3 = st.number_input(
            "Mould Volume (cm³)",
            min_value=1.0,
            value=preset_volume if preset_volume is not None else 944.0,
            step=1.0,
            disabled=(preset_volume is not None),
            help=(
                "The internal volume of the compaction mould, in cubic "
                "centimetres. This is the value printed on the mould's "
                "calibration certificate."
            )
        )

    with mould_col2:

        mould_mass = st.number_input(
            "Mould Mass (g)",
            min_value=0.0,
            value=700.0,
            step=0.1,
            help=(
                "Mass of the empty mould (and base plate, if it is "
                "weighed with the specimen). Check this against your "
                "mould's calibration sheet — a wrong mould mass is a "
                "common source of density errors."
            )
        )

    # Mould factor = 1 / mould volume, derived here so the user never
    # has to enter a reciprocal value themselves (a common source of
    # large, uniform unit errors in the calculated densities).
    mould_factor = 1_000_000.0 / mould_volume_cm3

    st.caption(
        f"Mould Volume = {mould_volume_cm3:,.1f} cm³ → "
        f"Mould Factor = {mould_factor:,.2f} m⁻³ "
        "(computed automatically as 1 / mould volume). "
        "Wet soil mass is converted from grams to kilograms "
        "before calculating wet density."
    )

    st.markdown("---")

    # -----------------------------------------------------
    # SPECIMEN INPUT
    # -----------------------------------------------------

    st.subheader("Proctor Test Specimens")

    st.write(
        "Enter the measured Wet Soil + Mould Mass and "
        "Moisture Content for each specimen."
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
        # CALCULATED VALUES
        # -------------------------------------------------

        # Wet soil mass in grams
        wet_soil_mass_g = (
            wet_soil_mould_mass
            - mould_mass
        )

        # Convert grams to kilograms
        wet_soil_mass_kg = (
            wet_soil_mass_g / 1000
        )

        # Wet density directly in kg/m³
        wet_density_kg_m3 = (
            wet_soil_mass_kg
            * mould_factor
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
                    wet_soil_mass_g,
                "Wet Density (kg/m³)":
                    wet_density_kg_m3,
                "Dry Density (kg/m³)":
                    dry_density_kg_m3
            }
        )

    # -----------------------------------------------------
    # DATAFRAME
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
            "Check the mould mass and Wet Soil + Mould Mass."
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
    # MDD AND OMC
    # -----------------------------------------------------

    moisture = df[
        "Moisture Content (%)"
    ].to_numpy()

    dry_density = df[
        "Dry Density (kg/m³)"
    ].to_numpy()

    plausibility_warning = check_density_plausibility(dry_density)

    if plausibility_warning:
        st.error("⚠️ " + plausibility_warning)

    mdd, omc, x_curve, y_curve, peak_within_range = fit_compaction_curve(
        moisture,
        dry_density
    )

    # -----------------------------------------------------
    # ZAV CURVE
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

    mdd_display = kg_m3_to_selected_density(
        mdd,
        density_unit
    )

    result_col1, result_col2, result_col3 = st.columns(3)

    with result_col1:
        st.markdown(
            f'<div class="result-card">'
            f'<div class="result-label">Maximum Dry Density</div>'
            f'<div class="result-value">{mdd_display:.3f}</div>'
            f'<div class="result-label">{density_unit}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with result_col2:
        st.markdown(
            f'<div class="result-card">'
            f'<div class="result-label">Optimum Moisture Content</div>'
            f'<div class="result-value">{omc:.2f}%</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with result_col3:
        st.markdown(
            f'<div class="result-card">'
            f'<div class="result-label">Specific Gravity</div>'
            f'<div class="result-value">{specific_gravity:.2f}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # -----------------------------------------------------
    # COMPACTION CURVE
    # -----------------------------------------------------

    st.subheader("Moisture–Density Relationship")

    if not peak_within_range:

        st.warning(
            "The fitted curve does not show a clear peak within "
            "the tested moisture range, so Maximum Dry Density and "
            "Optimum Moisture Content are being reported from the "
            "curve's edge rather than a true interior peak. Add "
            "specimens at higher and/or lower moisture contents to "
            "bracket the actual optimum."
        )

    # ZAV curve, sampled over the same moisture range as the fitted curve
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

    # Convert to selected density unit
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

    # -----------------------------------------------------
    # PLOT
    # -----------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    ax.scatter(
        moisture,
        dry_density_display,
        s=70,
        label="Laboratory Data"
    )

    ax.plot(
        x_curve,
        y_curve_display,
        linewidth=2,
        label="Fitted Compaction Curve"
    )

    ax.plot(
        x_curve,
        zav_curve_display,
        linestyle="--",
        linewidth=1.5,
        label="Zero Air Voids Curve"
    )

    ax.scatter(
        [omc],
        [mdd_display],
        s=110,
        marker="X",
        label=(
            f"MDD = "
            f"{mdd_display:.3f} "
            f"{density_unit}"
        )
    )

    ax.axvline(
        omc,
        linestyle=":",
        linewidth=1
    )

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
    # CALCULATION DETAILS
    # -----------------------------------------------------

    with st.expander(
        "Show calculation details"
    ):

        st.markdown(
            """
            ### 1. Wet Soil Mass

            Wet Soil Mass is calculated as:

            **Wet Soil Mass = Wet Soil + Mould Mass − Mould Mass**

            ### 2. Mould Factor

            The mould factor is the inverse of mould volume:

            **Mould Factor = 1 / Mould Volume**

            Since the mould factor is entered in **m⁻³**,
            the wet soil mass is converted from grams to
            kilograms before calculating density.

            ### 3. Wet Density

            **Wet Density = Wet Soil Mass × Mould Factor**

            The resulting density is in **kg/m³**.

            ### 4. Dry Density

            **Dry Density = Wet Density / (1 + w)**

            where **w** is the moisture content expressed
            as a decimal.

            ### 5. Maximum Dry Density

            MDD is obtained from the fitted moisture-density
            relationship.

            ### 6. Optimum Moisture Content

            OMC is the moisture content corresponding to the
            Maximum Dry Density.

            ### 7. Zero Air Voids

            The Zero Air Voids curve is calculated using:

            **ρZAV = Gs × ρw / (1 + w)**

            where:

            - **Gs** = specific gravity of soil solids
            - **ρw** = density of water
            - **w** = moisture content as a decimal
            """
        )

    # -----------------------------------------------------
    # DOWNLOAD RESULTS
    # -----------------------------------------------------

    export_df = display_df.copy()

    csv_data = export_df.to_csv(
        index=False
    ).encode("utf-8")

    pdf_buffer = generate_pdf_report(
        project_name=project_name,
        test_method=test_method,
        density_unit=density_unit,
        specific_gravity=specific_gravity,
        water_density=water_density,
        mould_volume_cm3=mould_volume_cm3,
        mould_factor=mould_factor,
        mould_mass=mould_mass,
        display_df=display_df,
        mdd_display=mdd_display,
        omc=omc,
        peak_within_range=peak_within_range,
        fig=fig
    )

    download_col1, download_col2 = st.columns(2)

    with download_col1:
        st.download_button(
            label="⬇️ Download Test Results (CSV)",
            data=csv_data,
            file_name="proctor_test_results.csv",
            mime="text/csv",
            use_container_width=True
        )

    with download_col2:
        st.download_button(
            label="📄 Download Test Report (PDF)",
            data=pdf_buffer,
            file_name="proctor_test_report.pdf",
            mime="application/pdf",
            use_container_width=True
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

        if density_unit == "kg/m³":
            default_field_density = 1750.0
            density_step = 1.0

        else:
            default_field_density = 1.75
            density_step = 0.001

        field_density = st.number_input(
            f"Field Dry Density ({density_unit})",
            min_value=0.001,
            value=default_field_density,
            step=density_step
        )

    with field_col2:

        if density_unit == "kg/m³":
            default_mdd = 1800.0

        else:
            default_mdd = 1.80

        laboratory_mdd = st.number_input(
            f"Laboratory MDD ({density_unit})",
            min_value=0.001,
            value=default_mdd,
            step=density_step
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
                "Mould Volume",
                "Mould Factor",
                "Mould Mass",
                "Specific Gravity",
                "Water Density",
                "Density Unit"
            ],

            "Value": [
                test_method,
                num_points,
                f"{mould_volume_cm3:,.1f} cm³",
                f"{mould_factor:.2f} m⁻³",
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
        ### Wet Soil Mass

        **Wet Soil Mass = Wet Soil + Mould Mass − Mould Mass**

        ### Wet Density

        **Wet Density = Wet Soil Mass × Mould Factor**

        where the wet soil mass is expressed in kg and the
        mould factor is expressed in m⁻³.

        Therefore, the resulting wet density is in kg/m³.

        ### Dry Density

        **Dry Density = Wet Density / (1 + w)**

        where **w** is the moisture content expressed as a decimal.

        ### Percentage Compaction

        **% Compaction = (Field Dry Density / Laboratory MDD) × 100**

        ### Zero Air Voids

        **ρZAV = Gs × ρw / (1 + w)**

        The Zero Air Voids curve represents the theoretical
        dry density corresponding to 100% saturation.
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
