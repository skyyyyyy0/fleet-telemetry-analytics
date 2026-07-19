# FEI-Lite Final Findings

## Project Overview

This project developed a FEI-Lite (Fuel Efficiency Index Lite) framework using GeoTab telematics data collected from a logistics pilot fleet consisting of 12 vehicles.

The objective was to evaluate fleet fuel-efficiency performance before and after device installation using a simplified proxy model based on available telematics signals.

---

## FEI-Lite Methodology

The final FEI-Lite score was calculated using four component scores:

- Fuel Efficiency Score (FES) – 50%
- RPM Efficiency Score (RES) – 20%
- Idle Efficiency Score (IES) – 20%
- Driving Smoothness Score (DSS) – 10%

Vehicle classes were separated into:

- 11.5Ton Xcient
- 1Ton Porter

Fuel-efficiency baselines were calculated separately for each vehicle class.

Driving smoothness was normalized using driving events per 100 km.

---

## Fleet-Level Results

| Metric         | Before | After |
| -------------- | ------ | ----- |
| Fleet FEI-Lite | 95.01  | 93.88 |

Overall fleet FEI-Lite decreased by approximately 1.14 points (-0.97%).

The pilot did not demonstrate a clear fleet-wide fuel-efficiency improvement.

---

## Vehicle-Level Results

### Most Improved Vehicle

LDV_06

- FEI-Lite Improvement: +11.45 points

### Largest Decline

LDV_08

- FEI-Lite Change: -11.20 points

Vehicle-level performance varied significantly across the fleet.

---

## Operational Insights

Key observations:

- Fleet fuel efficiency slightly declined during the analysis period.
- Driving smoothness improved after normalization using driving events per 100 km.
- Idle behavior remained a significant contributor to score variation.
- Vehicle-level variation was larger than fleet-level change.

---

## Limitations

The following variables were unavailable:

- Engine Load
- Fuel Rate
- Payload Information
- Driver ID
- Route Classification
- Traffic Conditions

Because these variables were unavailable, the analysis cannot establish a causal relationship between device installation and fuel-efficiency improvement.

---

## Future Work

Future FEI development should include:

- Expected Fuel Consumption Model
- Engine Load Normalization
- Payload Adjustment
- Driver-Level Scoring
- Route Classification
- Digital Twin FEI Framework

The current FEI-Lite framework should be considered a first-generation fleet-efficiency proxy model.
