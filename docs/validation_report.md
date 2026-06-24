# GeoTab Signal Validation Report

## Project Overview

The objective of this validation study was to determine whether the available GeoTab telemetry data collected from the DHL Korea pilot fleet could support the implementation of the Fuel Efficiency Index (FEI), Diesel Sustainability Index (DSI), and Vehicle Emission Index (VEI) frameworks.

A total of 12 DHL Hyundai fleet vehicles were analyzed using GeoTab StatusData and diagnostic mappings. Each required signal was compared against the theoretical requirements of the FEI, DSI, and VEI methodologies.

---

# Validation Approach

The validation process consisted of:

1. Identifying required signals for FEI, DSI, and VEI.
2. Comparing required signals against available GeoTab diagnostics.
3. Verifying actual signal availability within the DHL pilot fleet.
4. Identifying missing signals and OEM limitations.
5. Assessing feasibility for Full FEI, DSI, and VEI implementation.

---

# FEI Validation Results

## Available Signals

- Timestamp
- VIN
- Vehicle ID
- Engine RPM
- Distance / Odometer
- Vehicle Speed
- Fuel Used
- Idle Status
- Cruise Status
- Coolant Temperature

## Missing Critical Signals

- Engine Load
- Fuel Rate
- Engine Torque

## Assessment

The DHL pilot fleet does not currently provide Engine Load, Fuel Rate, or Torque measurements required for Full FEI implementation.

As a result, Full FEI is not currently feasible.

However, sufficient operational telemetry exists to support development of an FEI-Lite framework using fuel consumption, engine RPM, idle behavior, and vehicle utilization metrics.

### FEI Feasibility

- Full FEI: Not Feasible
- FEI-Lite: Feasible

---

# DSI Validation Results

## Available Signals

- Engine RPM
- Fuel Used
- Vehicle Speed
- DPF Differential Pressure (Partial)
- DPF Intake Temperature (Partial)
- DPF Outlet Temperature (Partial)

## Missing Critical Signals

- DPF Soot Load
- Regeneration Status
- Regeneration Count

## Assessment

Several DPF-related diagnostics were observed within the pilot fleet; however, availability was limited to a subset of vehicles and was not consistent across the entire fleet.

Critical regeneration monitoring signals were not observed.

### DSI Feasibility

- Full DSI: Not Feasible
- DSI-Lite: Feasible

---

# VEI Validation Results

## Available Signals

- Engine RPM
- Vehicle Speed
- Fuel Used
- Coolant Temperature
- Oil Temperature

## Missing Critical Signals

- NOx Concentration
- SCR Efficiency
- DPF Emission Data

## Assessment

The DHL pilot fleet does not currently provide the emissions diagnostics required to support VEI implementation.

The absence of NOx and SCR-related measurements prevents meaningful emissions scoring.

### VEI Feasibility

- Full VEI: Not Feasible
- VEI-Lite: Not Feasible

---

# Signal Gap Analysis

## FEI Gaps

- Engine Load
- Fuel Rate
- Engine Torque

## DSI Gaps

- DPF Soot Load
- Regeneration Status
- Regeneration Count

## VEI Gaps

- NOx Concentration
- SCR Efficiency
- DPF Emission Data

---

# OEM Limitation Summary

The GeoTab platform is capable of supporting advanced fleet telemetry analytics. However, the primary limitation identified during this study is the availability of OEM-specific ECU diagnostics within the DHL Hyundai fleet.

Several high-value diagnostics supported by GeoTab were not transmitted by the vehicle OEM configuration, preventing implementation of Full FEI, DSI, and VEI methodologies.

The limitation is therefore attributed primarily to OEM signal availability rather than GeoTab platform capability.

---

# Key Findings

- GeoTab successfully provides a large set of operational vehicle telemetry signals.
- Critical FEI signals including Engine Load, Fuel Rate, and Torque were unavailable.
- DPF diagnostics were partially available but not fleet-wide.
- Emissions-related diagnostics including NOx and SCR efficiency were unavailable.
- FEI-Lite and DSI-Lite frameworks can be developed using currently available signals.
- Full FEI, DSI, and VEI implementation requires additional OEM-level diagnostics.

---

# Recommended Next Steps

1. Develop FEI-Lite using currently available telemetry signals.
2. Develop DSI-Lite using available DPF-related diagnostics.
3. Continue validation on additional vehicle types.
4. Request OEM-level access to Engine Load, Fuel Rate, Torque, NOx, and SCR diagnostics.
5. Establish a migration path from FEI-Lite to Full FEI when OEM diagnostics become available.

---

# Conclusion

The GeoTab validation study successfully identified the capabilities and limitations of the DHL pilot fleet telemetry data.

While Full FEI, DSI, and VEI implementation is not currently possible due to missing OEM diagnostics, sufficient operational telemetry exists to support development of FEI-Lite and DSI-Lite frameworks.

These findings establish a technical foundation for future fleet analytics, digital twin modeling, and machine learning-based efficiency assessment.
