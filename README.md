# 🏗️ Proctor Compaction Calculator

**A simple engineering tool for analyzing laboratory Proctor compaction test data and determining Maximum Dry Density (MDD) and Optimum Moisture Content (OMC).**

> **Built for engineers. Powered by code.**

---

## 📌 Overview

The **Proctor Compaction Calculator** is a web-based geotechnical engineering application developed to simplify the analysis of soil compaction test results.

The application takes moisture content and corresponding density measurements from a Proctor compaction test, calculates dry density where required, develops the moisture–density relationship, and estimates:

* **Maximum Dry Density (MDD)**
* **Optimum Moisture Content (OMC)**
* **Moisture–density compaction curve**

The tool is designed to reduce repetitive manual calculations and provide engineers and laboratory personnel with a quick way to visualize and interpret Proctor test data.

---

## ⚙️ Current Features

### 1. Proctor Test Data Input

Users can enter multiple laboratory test points consisting of:

* Moisture content (%)
* Wet/bulk density
* or dry density

The application supports between **3 and 10 test points**.

### 2. Automatic Dry Density Calculation

When wet/bulk density is entered, the application calculates dry density using:

[
\rho_d = \frac{\rho}{1+w}
]

Where:

* (\rho_d) = dry density
* (\rho) = bulk/wet density
* (w) = moisture content expressed as a decimal

### 3. MDD and OMC Determination

A second-degree polynomial is fitted to the moisture–dry-density data.

The vertex of the fitted curve is used to estimate:

* **Maximum Dry Density (MDD)**
* **Optimum Moisture Content (OMC)**

### 4. Compaction Curve

The application generates a graphical representation of the moisture–density relationship, including:

* Laboratory test points
* Fitted compaction curve
* Estimated MDD
* Estimated OMC

### 5. Test Method Selection

The application currently allows users to identify the test as:

* Standard Proctor
* Modified Proctor
* Custom / Other

Common standards associated with these methods include:

* ASTM D698
* AASHTO T 99
* ASTM D1557
* AASHTO T 180

**Note:** The selected method currently serves primarily as test identification. The calculation engine does not yet implement method-specific corrections or procedures.

---

## 🧮 Engineering Principle

During a Proctor compaction test, soil is compacted at different moisture contents.

As moisture content increases, dry density initially increases because water facilitates particle rearrangement. Beyond the optimum moisture content, additional water occupies increasing pore space and dry density decreases.

This produces the characteristic **moisture–density relationship**:

```text
Dry
Density
  │
  │                 ● MDD
  │              ╭──────╮
  │           ╭──╯      ╰──╮
  │        ╭──╯              ╰──╮
  │     ●                       ●
  │
  └────────────────────────────────── Moisture Content
                     ↑
                    OMC
```

The peak of the curve corresponds approximately to the:

**Maximum Dry Density (MDD)**

and the associated moisture content is the:

**Optimum Moisture Content (OMC).**

---

## 🛠️ Technology Stack

The application is built using:

| Technology | Purpose                   |
| ---------- | ------------------------- |
| Python     | Core programming language |
| Streamlit  | Web application framework |
| NumPy      | Numerical calculations    |
| Pandas     | Data handling             |
| Matplotlib | Engineering plots         |

---

## 🚀 Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/IngBeno28/Proctor-Compaction-Calculator.git
```

### 2. Navigate into the project

```bash
cd Proctor-Compaction-Calculator
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run main.py
```

The application will open in your browser.

---

## 📦 Requirements

The application requires:

```text
streamlit
numpy
pandas
matplotlib
```

These dependencies are listed in `requirements.txt`.

---

## 📊 Typical Workflow

The intended workflow is:

```text
Laboratory Proctor Test
        ↓
Moisture Content + Density
        ↓
Dry Density Calculation
        ↓
Moisture–Density Relationship
        ↓
Polynomial Curve Fitting
        ↓
      MDD + OMC
        ↓
Compaction Curve
```

---

## 🏗️ Planned Features

Future versions are intended to expand the application into a more complete soil-compaction workflow.

### Laboratory Analysis

* [ ] Standard Proctor calculation workflow
* [ ] Modified Proctor calculation workflow
* [ ] Mold volume and mass inputs
* [ ] Automatic bulk density calculation
* [ ] Individual specimen calculations
* [ ] Specific gravity input
* [ ] Zero Air Voids (ZAV) curve
* [ ] Oversize particle correction
* [ ] Improved curve-fitting methods
* [ ] Automatic identification of questionable test points

### Field Compaction

* [ ] Field density input
* [ ] Field moisture content
* [ ] Percentage compaction calculation
* [ ] Required MDD input
* [ ] Compaction specification
* [ ] Automatic Pass/Fail determination

### Reporting

* [ ] Excel export
* [ ] PDF laboratory report
* [ ] Engineering test summary
* [ ] Project information
* [ ] Sample identification
* [ ] Test date
* [ ] Laboratory information
* [ ] Engineer/technician information

### Future Engineering Tools

The long-term goal is to develop a broader collection of practical geotechnical and materials engineering workflow tools under **Automation_hub Engineering Group**.

---

## ⚠️ Engineering Disclaimer

This application is intended as an **engineering calculation and analysis aid**.

Results should be reviewed by a suitably qualified engineer or laboratory professional before being used for design, construction acceptance, quality control, or other engineering decisions.

The applicable project specification and testing standard should always take precedence over the application's default calculations.

---

## 👨🏽‍💻 Developer

Developed by **Ing_Beno**

**Automation_hub Engineering Group**

> **Built for engineers. Powered by code.**

The project is part of an ongoing effort to develop practical software tools for civil engineering, materials engineering, geotechnical engineering, and construction workflows.

---

## 📜 License

This project is released under the license included in this repository.

See the `LICENSE` file for details.

---

## ⭐ Support the Project

If you find the tool useful, consider:

* ⭐ Starring the repository
* 🐛 Reporting bugs
* 💡 Suggesting improvements
* 🔧 Contributing to the project
* 📢 Sharing it with other engineers

Engineering software doesn't always need to be enormous.

Sometimes, one small calculator that eliminates thirty minutes of repetitive work is enough to make a difference.

