# Fleet Telematics Analytics: Fuel Efficiency and Driver Behavior Analysis

## Project Overview

This project analyzes event-driven Geotab telematics data from 12 anonymized fleet vehicles to assess changes in fuel efficiency, engine operation, idling, and driving behavior across vehicle-specific before-and-after periods.

A Python-based analytics pipeline standardizes timestamps, applies signal-level data-quality rules, and uses time-weighted aggregation to account for irregular reporting intervals. Four performance components—Fuel Efficiency (FES), RPM Efficiency (RES), Idling Efficiency (IES), and Driving Stability (DSS)—are combined into a single FEI-Lite index.

The results are presented through interactive Tableau dashboards designed to support fleet-level and vehicle-level performance analysis. Because route, payload, weather, and driver conditions were not fully controlled, the findings represent observed associations rather than causal effects.

---

## Key Results

- **Fleet-level performance:** The fleet-average FEI-Lite score decreased from **104.43** during the Before period to **103.72** during the After period. This represents an absolute change of **-0.71 points** and a percentage change of **-0.68%**.

- **Vehicle-level results:** Of the 12 vehicles analyzed, **4 vehicles improved** and **8 vehicles declined**. All 12 vehicles had sufficient data to calculate a final FEI-Lite score.

- **Overall finding:** Performance varied across individual vehicles, and the small decrease in the fleet-average score did not indicate a consistent fleet-wide improvement during the observed period.

- **Interpretation:** Route, payload, weather, and driver conditions were not fully controlled. Therefore, the results should be interpreted as observed before-and-after associations rather than evidence that the fuel-saving device directly caused the changes.

![Fleet FEI-Lite Performance Overview](images/dashboard_fleet_overview_v2.png)

---

## Business Problem

The fleet operator needed an objective and repeatable method to evaluate whether vehicle performance changed after the installation of a fuel-saving device. A simple comparison of total fuel consumption would not provide a fair assessment because the 12 vehicles differed in vehicle class, distance traveled, operating time, idling behavior, and engine conditions during the Before and After periods.

The Geotab data also presented a measurement challenge. StatusData records were collected on an event-driven basis, resulting in irregular reporting intervals and different levels of signal coverage across vehicles. As a result, simple record-level averages could overrepresent frequently reported operating conditions and produce misleading comparisons.

The primary business goal was to transform the raw telematics data into standardized and comparable performance measures that could answer the following questions:

- Did fuel efficiency change at the fleet and individual vehicle levels?
- Which operational factors—fuel use, engine RPM, idling, or driving stability—contributed to the observed changes?
- Which vehicles or performance areas required further investigation?

The analysis was designed to support fleet monitoring and operational decision-making. However, because route, payload, weather, and driver conditions were not fully controlled, the results were not intended to establish a causal effect of the fuel-saving device.

---

## Data Overview

The analysis used approximately **1.7 million event-driven Geotab StatusData records** collected from 12 anonymized commercial fleet vehicles.

| Category | Description |
|---|---|
| Fleet size | 12 vehicles |
| Vehicle classes | 4 heavy-duty vehicles and 8 light-duty vehicles |
| Data source | Geotab StatusData |
| Comparison periods | Vehicle-specific Before and After periods of approximately 30 days each |
| Reporting structure | Event-driven records with irregular time intervals |
| Vehicle identifiers | Anonymized as `HDV_01`–`HDV_04` and `LDV_01`–`LDV_08` |

Eight vehicles had an installation date of **May 18, 2026**, while the remaining four had an installation date of **May 19, 2026**. The comparison windows were aligned with each vehicle’s installation date to maintain consistent Before and After observation periods.

The available signals included fuel consumption, idle fuel use, engine speed, vehicle speed, ignition status, vehicle activity, odometer readings, outside air temperature, and gear position. Signal availability varied across vehicles, and some measurements were missing or reported inconsistently.

Because the data was collected when signal values changed rather than at fixed time intervals, raw record counts did not represent equal amounts of operating time. Timestamps were therefore standardized, signal-level quality rules were applied, and time-weighted aggregation was used to produce more comparable vehicle-level metrics.

---

## Analytics Pipeline

A reproducible Python pipeline was developed to transform irregular, event-driven Geotab records into consistent vehicle-level metrics for Before and After comparison.

**Pipeline flow:** `Geotab API → Signal Validation → Data Cleaning and Standardization → Time-Aware KPI Engineering → FEI-Lite Scoring → Tableau Dashboards`

### 1. Data Extraction and Signal Validation

Geotab StatusData was extracted for all 12 vehicles using installation-aligned Before and After periods. Available diagnostics and signal coverage were validated before processing because certain measurements were unavailable or inconsistently reported across the fleet.

### 2. Data Cleaning and Standardization

Timestamps were converted to Korea Standard Time (KST), and half-open date intervals were applied to prevent records at installation boundaries from appearing in both periods. Vehicle identifiers were anonymized, duplicate timestamps and invalid numeric values were removed, and signal-level range checks were applied.

Cumulative fuel and distance measurements were reconstructed from valid positive increments. Counter resets, negative changes, and implausible increases were excluded instead of relying on a simple maximum-minus-minimum calculation. Missing measurements were not automatically imputed.

### 3. Time-Aware KPI Engineering

Because Geotab records were generated when signal values changed, simple record-level averages could overrepresent frequently reported operating conditions. RPM, speed, and idling metrics were therefore calculated using the amount of time each valid observation represented.

Intervals longer than five minutes were excluded from time-weighted calculations to avoid carrying stale values across extended reporting gaps. Driving events were consolidated to prevent consecutive records from being counted as separate events and were normalized by distance traveled where appropriate.

The processed signals were then converted into vehicle-level KPIs, including fuel efficiency, average engine RPM, efficient-RPM operating ratio, idle ratio, and driving-event frequency.

### 4. FEI-Lite Scoring

Four component scores—Fuel Efficiency (FES), RPM Efficiency (RES), Idling Efficiency (IES), and Driving Stability (DSS)—were calculated for each vehicle and period. Fixed Before-period benchmarks were used to maintain a consistent reference point, while vehicle-class normalization was applied where necessary to improve comparability between heavy-duty and light-duty vehicles.

The four component scores were then combined using the finalized FEI-Lite weighting structure to produce an overall performance index for each vehicle.

### 5. Validation and Visualization

The final vehicle-level scores and fleet summaries were exported as analysis-ready datasets and validated for consistency across the calculation outputs. Tableau dashboards were then developed to present fleet-level changes, individual vehicle performance, fuel-efficiency results, and operational behavior patterns.

--- 

## KPI and FEI-Lite Methodology

FEI-Lite was developed as a practical vehicle-performance index using the telemetry signals consistently available across the fleet. It combines four complementary components: fuel efficiency, RPM efficiency, idling efficiency, and driving smoothness.

### 1. Vehicle-Level KPIs

The following KPIs were calculated separately for each vehicle and analysis period:

| Component | Underlying KPI | Interpretation | Weight |
|---|---|---|---:|
| Fuel Efficiency Score (FES) | Distance traveled per liter of fuel | Higher is better | 50% |
| RPM Efficiency Score (RES) | Share of engine-on time within the efficient RPM range | Higher is better | 20% |
| Idle Efficiency Score (IES) | Share of engine-on time spent idling | Lower is better | 20% |
| Driving Smoothness Score (DSS) | Harsh braking and side-acceleration events per 100 km | Lower is better | 10% |

### 2. Fuel Efficiency Score (FES)

Fuel efficiency was calculated as:

`Fuel Efficiency (km/L) = Distance Traveled (km) / Fuel Used (L)`

Because heavy-duty and light-duty vehicles have structurally different fuel-consumption patterns, each vehicle was compared with the median fuel efficiency of its own vehicle class during the Before period.

FES was treated as a higher-is-better component:

`FES Index = (Vehicle Fuel Efficiency / Vehicle-Class Before Median) × 100`

Fuel efficiency received the highest weight because it most directly represents productive distance generated from the fuel consumed.

### 3. RPM Efficiency Score (RES)

The efficient engine-speed range was defined as **1,200–1,800 RPM**. Engine-on operation was identified when engine speed exceeded **500 RPM**.

The RPM efficiency ratio was calculated using valid operating time rather than record counts:

`RPM Efficiency Ratio = Time at 1,200–1,800 RPM / Total Engine-On Time`

RES was then indexed against the median Before-period RPM efficiency ratio for the corresponding vehicle class:

`RES Index = (Vehicle RPM Efficiency Ratio / Vehicle-Class Before Median) × 100`

This time-weighted approach prevents frequently reported RPM values from having a disproportionate influence on the result.

### 4. Idle Efficiency Score (IES)

Idling was defined as an interval in which:

- Engine RPM was greater than **500 RPM**
- Vehicle speed was less than **1 km/h**

The idle ratio was calculated as:

`Idle Ratio = Idle Time / Total Engine-On Time`

Because a lower idle ratio represents better performance, IES used an inverse index:

`IES Index = (Vehicle-Class Before Median Idle Ratio / Vehicle Idle Ratio) × 100`

This component measures how effectively engine-on time was converted into productive vehicle operation.

### 5. Driving Smoothness Score (DSS)

Driving behavior was evaluated using harsh-braking and side-acceleration signals. Records meeting the configured threshold of **3.0** were treated as candidate events, and consecutive records occurring within **five seconds** were consolidated into a single event.

The event rate was normalized by distance traveled:

`Driving Events per 100 km = (Harsh-Braking Events + Side-Acceleration Events) / Distance Traveled × 100`

Because fewer events indicate smoother driving, DSS was calculated as an inverse index:

`DSS Index = (Vehicle-Class Before Median Event Rate / Vehicle Event Rate) × 100`

DSS received the lowest weight because driving-event frequency is an indirect proxy for fuel-efficiency performance and may also be affected by traffic and route conditions.

### 6. Fixed Baseline and Index Scale

The median value for each vehicle class during the Before period was used as a fixed benchmark for both periods. The After-period benchmark was not recalculated, ensuring that Before and After scores remained directly comparable.

Each component index was bounded between **0 and 200** to limit the effect of extreme ratios:

- **100** represents the vehicle-class median during the Before period
- **Above 100** indicates performance above the reference level
- **Below 100** indicates performance below the reference level

The component indexes and the final FEI-Lite score are relative performance indexes, not percentages.

### 7. Final FEI-Lite Score

The nominal weighting structure was:

`FEI-Lite = (0.50 × FES) + (0.20 × RES) + (0.20 × IES) + (0.10 × DSS)`

FES received the largest weight because it directly measures fuel utilization. RES and IES each received 20% because engine-speed management and idling materially influence fuel consumption. DSS received 10% because it represents a less direct behavioral indicator.

When a component could not be calculated because the required signals were unavailable or invalid, its weight was proportionally redistributed across the available components:

`Effective Component Weight = Nominal Weight / Sum of Available Nominal Weights`

This approach allowed the final score to use all valid information without automatically assigning a favorable or unfavorable value to a missing component. All 12 vehicles passed the final scoring-validity checks.

---

## Dashboard Analysis

Three Tableau dashboards were developed to translate the vehicle-level KPIs and FEI-Lite results into clear operational insights. Together, they present the overall fleet outcome, isolate changes in fuel efficiency, and show how RPM management, idling, and driving smoothness contributed to the final results.

### Fleet Overview

The Fleet Overview dashboard summarizes the Before and After FEI-Lite results for all 12 vehicles. The fleet-average score decreased from **104.43** to **103.72**, representing an absolute change of **-0.71 points** and a percentage change of **-0.68%**.

At the vehicle level, **4 vehicles improved** and **8 declined**. `LDV_06` recorded the largest improvement at **+8.59 points**, while `LDV_08` experienced the largest decline at **-7.48 points**. Based on the After-period ranking, `HDV_04` achieved the highest FEI-Lite score at **124.51**, while `LDV_05` recorded the lowest score at **87.07**.

The ranking and the amount of change should be interpreted separately. A vehicle could maintain a relatively high After-period score while still declining from its own Before-period performance. Overall, the dashboard shows substantial vehicle-level variation and no consistent fleet-wide improvement during the observed period.

![Fleet FEI-Lite Performance Overview](images/dashboard_fleet_overview_v2.png)

### Fuel Efficiency Analysis

The Fuel Efficiency dashboard focuses on the Fuel Efficiency Score (FES), which compares each vehicle’s fuel efficiency with the fixed Before-period median for its vehicle class.

The fleet-average FES index decreased from **100.05** in the Before period to **98.22** in the After period, resulting in a change of **-1.83 points**. Only **3 of the 12 vehicles improved** in this component, while **9 declined**. `LDV_06` recorded the largest FES improvement at **+4.34 points**, whereas `LDV_08` had the largest decline at **-6.90 points**.

These results indicate that fuel-efficiency performance weakened for most vehicles during the After period. However, FES alone did not fully explain the final vehicle rankings because FEI-Lite also incorporated RPM efficiency, idling efficiency, and driving smoothness.

![Fleet Fuel Efficiency Analytics](images/dashboard_fuel_analytics_v2.png)

### Driver Behavior Analysis

The Driver Behavior dashboard compares the three operational components of FEI-Lite: RPM Efficiency Score (RES), Idle Efficiency Score (IES), and Driving Smoothness Score (DSS).

At the fleet level:

- Average RES changed by **+0.03 points**, indicating that RPM efficiency remained nearly unchanged.
- Average IES changed by **-0.69 points**, indicating a slight deterioration in idling efficiency.
- Average DSS changed by **+3.69 points**, indicating an overall improvement in driving smoothness.

The improvement in DSS partially offset the reductions in FES and IES, which helps explain why the final fleet-average FEI-Lite score declined by only **0.71 points** even though the fuel-efficiency component decreased by **1.83 points**.

The vehicle-level comparisons also show that operational behavior varied across the fleet. Some vehicles improved through more efficient RPM control, reduced idling, or smoother driving, while others weakened in one or more components. Therefore, the final performance changes cannot be explained by fuel consumption alone.

![Fleet Driver Behavior Analytics](images/dashboard_driver_behavior_v2.png)

These dashboards support vehicle-level diagnosis and help identify which performance components require further investigation. Because route, payload, weather, traffic, and driver conditions were not fully controlled, the observed changes should not be interpreted as causal effects of the fuel-saving device.

## Technology Stack

| Category | Technologies | Purpose |
|---|---|---|
| Data Source | Geotab API, StatusData | Extracted vehicle telemetry and diagnostic records |
| Programming | Python | Built the data-processing and scoring pipeline |
| Data Processing | Pandas, NumPy | Cleaned, transformed, aggregated, and validated telemetry data |
| Development | Jupyter Notebook | Supported exploratory analysis and result validation |
| Visualization | Tableau | Developed fleet, fuel-efficiency, and driver-behavior dashboards |
| Version Control | Git, GitHub | Managed source code, documentation, and project history |

This project uses custom Python scripts rather than a machine-learning framework. FEI-Lite was developed as a rule-based analytical index using operational KPIs derived from the available telemetry signals.

---

## Repository Structure

```text
fleet-telemetry-analytics/
├── data/
│   ├── raw/                    # Private raw extracts; excluded from Git
│   ├── private/                # Private mappings and identifiers; excluded from Git
│   ├── processed/              # Anonymized KPI and FEI-Lite datasets
│   └── sample/                 # Sanitized sample data for portfolio review
│
├── src/
│   ├── validation/             # Signal, data-quality, and final-output validation
│   ├── analytics/              # Data cleaning and KPI preparation
│   ├── fei_lite/               # Component scoring and final FEI-Lite calculation
│   └── tableau/                # Tableau-ready dataset generation
│
├── outputs/
│   ├── tables/                 # Summary tables and final analytical outputs
│   ├── charts/                 # Supporting analytical charts
│   └── screenshots/            # Final Tableau dashboard screenshots
│
├── dashboards/                 # Tableau workbook files
├── docs/                       # Methodology and project documentation
├── images/                     # Images displayed in the README
├── README.md
├── requirements.txt
├── .gitignore
└── LICENSE
```

The repository separates private source data, reusable processing logic, analysis-ready outputs, and presentation materials. This structure makes the analytical workflow easier to review while preventing confidential files from being included in the public project.

---

## How to Run

### 1. Clone the Repository

```bash
git clone https://github.com/<your-github-username>/fleet-telemetry-analytics.git
cd fleet-telemetry-analytics
```

### 2. Create and Activate a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

For Windows:

```bash
venv\Scripts\activate
```

### 3. Install the Required Packages

```bash
pip install -r requirements.txt
```

### 4. Run the Core FEI-Lite V2 Pipeline

The following execution sequence assumes that the cleaned and anonymized input datasets are available in `data/processed/`.

```bash
python3 src/fei_lite/01_create_vehicle_kpi_dataset.py
python3 src/fei_lite/02_calculate_fes_scores.py
python3 src/fei_lite/04_calculate_res_scores.py
python3 src/fei_lite/06_calculate_ies_scores.py
python3 src/fei_lite/08_calculate_dss_scores.py
python3 src/fei_lite/14_compare_component_index_methods.py
python3 src/fei_lite/15_calculate_weight_sensitivity.py
python3 src/fei_lite/16_create_final_fei_lite_v2.py
python3 src/tableau/01_create_tableau_dataset_v2.py
python3 src/validation/11_validate_final_fei_v2.py
```

### 5. Review the Generated Outputs

The primary generated outputs include:

- `vehicle_kpi_dataset_v2.csv`
- `vehicle_fei_scores_v2.csv`
- `fei_lite_summary_v2.csv`
- `data_quality_summary.csv`

After generating the Tableau-ready dataset, open the workbook in `dashboards/` and refresh its data source to review the final dashboards.

Direct Geotab API extraction requires authorized account credentials and private vehicle-mapping files. These credentials and mappings are not included in the public repository.

---

## Limitations

This project has several limitations that should be considered when interpreting the results.

### Observational Before-and-After Design

The analysis compared vehicle performance before and after the installation of a fuel-saving device. Route, payload, weather, traffic, and driver conditions were not fully controlled.

Therefore, the observed changes represent associations and should not be interpreted as causal effects of the device.

### Limited Fleet and Observation Period

The analysis covered 12 commercial vehicles over vehicle-specific Before and After periods of approximately 30 days each.

The findings may not generalize to other fleets, vehicle models, operating regions, or longer observation periods.

### Event-Driven Reporting

Geotab StatusData was recorded when signal values changed rather than at fixed time intervals.

Time-weighted aggregation reduced record-frequency bias, but each valid value was still assumed to represent the corresponding interval until the next observation. Intervals longer than five minutes were excluded to limit stale-value carry-forward.

### Incomplete and Inconsistent Signals

Signal availability varied across vehicles. The following variables were either unavailable or not sufficiently consistent for fleet-wide analysis:

- Engine Load
- Fuel Rate
- Engine Torque
- Payload
- Driver ID
- Route classification
- Traffic conditions

Missing values were not automatically imputed. When an FEI-Lite component could not be calculated, its weight was proportionally redistributed across the available components.

### Operational Thresholds

The RPM, idling, data-gap, and driving-event thresholds were selected as practical operational rules for this fleet.

These thresholds may require recalibration before the methodology is applied to different vehicle classes or operating environments.

### Relative Performance Index

FEI-Lite is a portfolio-level analytical framework rather than an industry-certified fuel-efficiency standard.

A score of 100 represents the relevant vehicle-class Before-period benchmark, not perfect vehicle performance. The index is most useful for relative fleet monitoring and vehicle-level diagnosis.

---

## Data Privacy and Anonymization

The original data was collected from a commercial pilot fleet and contained confidential vehicle and operational information. Therefore, the public repository includes only anonymized and sanitized materials.

The following privacy controls were applied:

- Heavy-duty vehicles were renamed `HDV_01`–`HDV_04`.
- Light-duty vehicles were renamed `LDV_01`–`LDV_08`.
- Actual vehicle names, license plates, Device IDs, VINs, serial numbers, and customer identifiers were removed.
- The vehicle-identifier mapping is stored privately and excluded from Git.
- Geotab credentials and environment files are excluded through `.gitignore`.
- Raw API exports and private source files are not included in the public repository.
- Customer and product names were replaced with the general terms **Logistics Pilot Fleet** and **Fuel-Saving Device**.
- Published datasets contain only anonymized processed records and aggregated analytical outputs.
- Dashboard labels, screenshots, documentation, and Tableau workbook text were reviewed for identifying information before publication.

Because the confidential source data and account credentials are not publicly available, this repository is intended to demonstrate the analytical methodology, code structure, and final results rather than fully reproduce the original API extraction process.
