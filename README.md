# Fleet Telematics Analytics Using GeoTab Data

## Project Overview

This project analyzes real-world fleet telematics data collected from 12 vehicles through the GeoTab platform.

The objective was to evaluate changes in vehicle performance before and after the installation of a fuel-saving device. I built an end-to-end analytics workflow covering API-based data extraction, signal validation, data cleaning, feature engineering, KPI development, FEI-Lite scoring, validation, and Tableau dashboard development.

The analysis processed more than 1.7 million telemetry records and translated complex vehicle data into practical fleet-performance insights.

---

## Business Problem

A complete Fuel Efficiency Index typically requires advanced engine and emissions signals. However, several important signals—including Engine Load, Fuel Rate, NOx, DPF Status, and SCR Efficiency—were unavailable or inconsistently supported across the vehicles.

Instead of excluding vehicles with incomplete data, I developed FEI-Lite: a simplified vehicle-performance scoring framework based on signals that were consistently available across the fleet.

This approach made it possible to compare vehicle performance while clearly documenting the limitations of the available telematics data.

---

## Project Objectives

- Validate the vehicle signals available through the GeoTab API
- Build a clean and reusable telematics dataset
- Measure vehicle performance before and after installation
- Engineer vehicle-level fuel and driving-performance KPIs
- Develop and validate the FEI-Lite scoring framework
- Compare alternative component-index methods
- Evaluate the sensitivity of the final scoring weights
- Build interactive Tableau dashboards
- Translate technical results into business insights

---

## Dataset

### Data Source

- GeoTab API
- 12-vehicle logistics pilot fleet
- Event-driven vehicle telemetry
- More than 1.7 million telemetry records

### Fleet Composition

- Heavy-Duty Vehicles (HDV)
- Light-Duty Vehicles (LDV)

### Study Period

The analysis used approximately 30-day before and after periods aligned with each vehicle’s installation date.

| Period              | Approximate Coverage |
| ------------------- | -------------------- |
| Before Installation | April–May 2026       |
| After Installation  | May–June 2026        |

### Data Privacy

All vehicle identifiers were anonymized before publication. Raw GeoTab records, account credentials, real vehicle identifiers, and other private source information are excluded from this repository.

---

## Project Workflow

```text
GeoTab API
    │
    ▼
Signal Availability Validation
    │
    ▼
Data Cleaning and Quality Checks
    │
    ▼
Vehicle-Level Feature Engineering
    │
    ▼
KPI and Component Score Calculation
    │
    ▼
Index Method Comparison
    │
    ▼
Weight Sensitivity Analysis
    │
    ▼
Final FEI-Lite V2 Calculation
    │
    ▼
Tableau Dataset and Dashboards
    │
    ▼
Final Output Validation
```

---

## Technologies

- Python
- Pandas
- NumPy
- Matplotlib
- GeoTab API
- Tableau
- Jupyter
- Git
- GitHub

---

## Feature Engineering

The following vehicle-level metrics were calculated for the before and after periods:

- Fuel efficiency
- Distance traveled
- Total fuel consumption
- Idle ratio
- Average engine RPM
- Driving smoothness
- Coolant temperature
- Vehicle-level KPI summaries
- Before-versus-after performance changes

These metrics were used to evaluate both fuel performance and vehicle operating behavior.

---

## FEI-Lite Framework

Because the signals required for a complete FEI model were not consistently available, I developed a lightweight scoring framework using four validated components.

| Component                      | Description                                    | Weight |
| ------------------------------ | ---------------------------------------------- | -----: |
| Fuel Efficiency Score (FES)    | Measures relative fuel-efficiency performance  |    50% |
| RPM Efficiency Score (RES)     | Evaluates engine-speed operating behavior      |    20% |
| Idle Efficiency Score (IES)    | Measures performance related to vehicle idling |    20% |
| Driving Smoothness Score (DSS) | Evaluates consistency of driving behavior      |    10% |

The final FEI-Lite score is calculated as:

```text
FEI-Lite
= 0.50 × FES
+ 0.20 × RES
+ 0.20 × IES
+ 0.10 × DSS
```

Before finalizing the framework, alternative component-index methods were compared and the selected weights were evaluated through sensitivity analysis.

FEI-Lite is a relative analytical score designed for fleet comparison. It is not an OEM-certified fuel-efficiency measurement.

---

## Dashboard

The final Tableau workbook contains four dashboard pages.

### 1. Fleet Overview

![Fleet Overview](outputs/screenshots/Dashboard/01_fleet_overview_dashboard.png)

Provides an executive summary of overall fleet performance.

**Main KPIs**

- Fleet-average FEI-Lite score
- Before-versus-after score change
- Vehicle performance ranking
- Number of improved and declined vehicles

### 2. Fuel Analytics

![Fuel Analytics](outputs/screenshots/Dashboard/02_fuel_analytics_dashboard.png)

Focuses on changes in fuel efficiency and the Fuel Efficiency Score.

**Main KPIs**

- Fuel-efficiency comparison
- Fuel Efficiency Score
- Before-versus-after performance
- Vehicle-level fuel-performance differences

### 3. Driver Behavior

![Driver Behavior](outputs/screenshots/Dashboard/03_driver_behavior_dashboard.png)

Examines operational behavior associated with engine RPM, idling, and driving smoothness.

**Main KPIs**

- RPM Efficiency Score
- Idle Efficiency Score
- Driving Smoothness Score
- Vehicle-level behavioral differences

### 4. FEI-Lite Ranking

![FEI-Lite Ranking](outputs/screenshots/Dashboard/04_fei_lite_performance_dashboard.png)

Ranks vehicles by their final FEI-Lite performance and score change.

**Main KPIs**

- Final vehicle ranking
- FEI-Lite score change
- Top-performing vehicles
- Vehicles requiring further investigation

---

## Key Findings

- Signal availability varied across vehicles, confirming that raw telematics data must be validated before KPI development.
- The fleet did not show a consistent overall improvement after installation.
- Performance changes varied substantially by vehicle: some vehicles improved, while others remained stable or declined.
- Fuel efficiency alone did not fully explain vehicle performance. RPM behavior, idling, and driving smoothness provided additional operational context.
- Vehicle-level analysis was more informative than relying only on a fleet-wide average.
- Differences in routes, payloads, drivers, traffic, and vehicle configurations limited direct causal interpretation of the before-and-after results.

---

## Limitations

The analysis was limited by several unavailable or inconsistent variables:

- Engine Load
- Fuel Rate
- Payload
- Driver ID
- Route classification
- Traffic conditions
- Advanced engine and emissions signals

Because these factors were not controlled, the results should be interpreted as vehicle-performance comparisons rather than definitive proof that the fuel-saving device caused the observed changes.

---

## Installation

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Create a `.env` file only when running the GeoTab extraction scripts with authorized API credentials.

---

## Reproducing the Final V2 Analysis

Run the following commands from the project root directory.

### 1. Data Quality Checks

```bash
python src/validation/09_create_data_quality_summary.py
python src/validation/10_validate_day2_outputs.py
```

### 2. KPI and Component Scores

```bash
python src/fei_lite/01_create_vehicle_kpi_dataset.py
python src/fei_lite/02_calculate_fes_scores.py
python src/fei_lite/04_calculate_res_scores.py
python src/fei_lite/06_calculate_ies_scores.py
python src/fei_lite/08_calculate_dss_scores.py
```

### 3. Final FEI-Lite V2

```bash
python src/fei_lite/14_compare_component_index_methods.py
python src/fei_lite/15_calculate_weight_sensitivity.py
python src/fei_lite/16_create_final_fei_lite_v2.py
```

### 4. Tableau Dataset

```bash
python src/tableau/01_create_tableau_dataset_v2.py
```

### 5. Final Validation

```bash
python src/validation/11_validate_final_fei_v2.py
```

The GeoTab extraction and initial cleaning scripts under `src/validation/01` through `08` require authorized API access and private source data. They are separate from the reproducible V2 analysis workflow above.

---

## Repository Structure

```text
fleet-telematics-fei-lite/
│
├── dashboards/              # Tableau workbook
├── data/
│   └── processed/           # Anonymized analytical datasets
├── docs/                    # Methodology and project documentation
├── outputs/
│   ├── charts/              # Python-generated charts
│   ├── screenshots/         # Tableau dashboard screenshots
│   └── tables/              # Final summary tables
├── src/
│   ├── validation/          # Extraction, cleaning, and validation
│   ├── fei_lite/            # KPI and FEI-Lite calculations
│   └── tableau/             # Tableau dataset preparation
├── requirements.txt
└── README.md
```

---

## Future Improvements

Future work may include:

- Machine-learning-based fuel-consumption prediction
- Route and payload normalization
- Weather and traffic normalization
- Driver-behavior clustering
- Time-weighted analysis of event-driven telemetry
- Real-time fleet-performance monitoring
- Full FEI implementation using additional ECU signals
- Digital Twin integration
