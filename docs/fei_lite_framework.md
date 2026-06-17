# FEI-Lite Framework

## Overview

The FEI-Lite (Fuel Efficiency Index Lite) framework is a simplified fuel-efficiency scoring system developed using currently available GeoTab telemetry data.

The original FEI methodology requires several OEM-level diagnostics, including:

- Engine Load
- Fuel Rate
- Engine Torque

These signals are currently unavailable from the DHL Hyundai pilot fleet.

To enable immediate deployment and operational evaluation, FEI-Lite uses available telemetry signals while maintaining compatibility with future Full FEI implementation.

---

# Framework Objectives

The FEI-Lite framework aims to:

- Evaluate vehicle fuel efficiency
- Compare fleet performance
- Monitor driver operating behavior
- Identify inefficient operating patterns
- Support fleet benchmarking
- Establish a foundation for future Full FEI development

---

# Available Signals

The following signals have been validated as available through GeoTab.

| Signal              | Purpose                  |
| ------------------- | ------------------------ |
| Vehicle Speed       | Driving behavior         |
| Engine RPM          | Engine efficiency        |
| Distance / Odometer | Productivity measurement |
| Engine Hours        | Utilization measurement  |
| Total Fuel Used     | Fuel consumption         |
| Idle Fuel Used      | Idle efficiency          |
| Idle Time           | Idle behavior            |

---

# Missing Signals

The following Full FEI signals are currently unavailable.

| Signal        | Status        |
| ------------- | ------------- |
| Engine Load   | Not Available |
| Fuel Rate     | Not Available |
| Engine Torque | Not Available |

As a result, Full FEI implementation is currently not feasible.

---

# FEI-Lite Framework Structure

The FEI-Lite score consists of four independent components.

| Component                      | Weight |
| ------------------------------ | ------ |
| Fuel Efficiency Score (FES)    | 50%    |
| RPM Efficiency Score (RES)     | 20%    |
| Idle Efficiency Score (IES)    | 20%    |
| Driving Smoothness Score (DSS) | 10%    |

Total:

FEI-Lite = 100 Points

---

# 1. Fuel Efficiency Score (FES)

## Purpose

Measures how efficiently a vehicle converts fuel into distance traveled.

This is the most important component because fuel efficiency is the primary business objective.

---

## Calculation

Fuel Efficiency

Distance Traveled ÷ Fuel Used

Example

Distance = 500 km

Fuel Used = 50 L

Fuel Efficiency = 10 km/L

---

## Fleet Normalization

Each vehicle is compared against the fleet median.

FES

Vehicle Fuel Efficiency ÷ Fleet Median Fuel Efficiency

Maximum Score = 1.0

---

# 2. RPM Efficiency Score (RES)

## Purpose

Measures engine operation within an efficient RPM range.

Excessively high RPM operation generally increases fuel consumption.

---

## Efficient RPM Range

1200 RPM – 1800 RPM

---

## Calculation

RES

Time Within Efficient RPM Range ÷ Total Operating Time

Example

Efficient RPM Time = 6 Hours

Total Operating Time = 8 Hours

RES = 0.75

---

# 3. Idle Efficiency Score (IES)

## Purpose

Measures fuel wasted while the vehicle is idling.

Long idle periods increase fuel consumption without producing useful work.

---

## Calculation

Idle Fuel Ratio

Idle Fuel Used ÷ Total Fuel Used

IES

1 − Idle Fuel Ratio

Example

Idle Fuel Used = 10 L

Total Fuel Used = 50 L

Idle Fuel Ratio = 20%

IES = 0.80

---

# 4. Driving Smoothness Score (DSS)

## Purpose

Measures driving consistency and operating stability.

Frequent acceleration and deceleration events typically increase fuel consumption.

---

## Calculation

Speed Variability

Standard Deviation of Vehicle Speed

DSS

1 − Normalized Speed Variability

Higher values indicate smoother vehicle operation.

---

# Final FEI-Lite Formula

FEI-Lite

= 100 ×

(0.50 × FES

- 0.20 × RES

- 0.20 × IES

- 0.10 × DSS)

---

# FEI-Lite Rating Scale

| Score    | Rating            |
| -------- | ----------------- |
| 90 – 100 | Excellent         |
| 80 – 89  | Good              |
| 70 – 79  | Average           |
| Below 70 | Needs Improvement |

---

# Expected Outputs

The framework will generate:

- Vehicle-level FEI-Lite scores
- Fleet ranking tables
- Fuel efficiency comparisons
- Idle efficiency comparisons
- RPM efficiency comparisons
- Driver behavior comparisons

Example:

| Vehicle   | FEI-Lite |
| --------- | -------- |
| Vehicle A | 92       |
| Vehicle B | 84       |
| Vehicle C | 76       |

---

# Validation Plan

The FEI-Lite framework will be validated through fleet-level comparisons.

Validation objectives:

- Compare FEI-Lite rankings across vehicles
- Identify high-efficiency vehicles
- Identify low-efficiency vehicles
- Verify score consistency across operating periods
- Compare FEI-Lite trends against actual fuel consumption

---

# Future Enhancement Strategy

## Phase 1

Deploy FEI-Lite using available GeoTab telemetry signals.

---

## Phase 2

Acquire OEM-enabled datasets containing:

- Engine Load
- Fuel Rate
- Engine Torque

---

## Phase 3

Calculate Full FEI using OEM diagnostics.

---

## Phase 4

Train machine learning models using Full FEI as ground truth.

Potential models:

- XGBoost
- LightGBM
- Random Forest

---

## Phase 5

Predict Full FEI for vehicles lacking OEM diagnostics.

---

# Conclusion

The FEI-Lite framework provides a practical and deployable fuel-efficiency scoring system using currently available GeoTab telemetry data.

Although Engine Load, Fuel Rate, and Torque are not currently available, FEI-Lite establishes an operational analytics framework that supports immediate fleet benchmarking while maintaining a clear migration path toward future Full FEI implementation.
