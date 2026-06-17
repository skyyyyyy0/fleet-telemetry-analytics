# Project Charter

## Project Name

Fleet Telemetry Analytics & FEI-Lite Development Using GeoTab Data

---

## Background

The company aims to develop a Fuel Efficiency Index (FEI) framework to evaluate and improve the operational efficiency of commercial fleet vehicles.

The original FEI methodology requires several engine-level diagnostics, including:

- Engine Load
- Fuel Rate
- Engine RPM
- Distance
- Engine Hours
- Engine Torque (preferred)

However, validation of the DHL pilot fleet revealed that several required signals are currently unavailable through GeoTab for the Hyundai pilot vehicles.

As a result, implementation of the Full FEI framework is not currently feasible.

To provide immediate business value while maintaining compatibility with future OEM integration, an FEI-Lite framework is proposed using currently available telemetry signals.

---

## Business Problem

Fleet operators require a consistent and measurable way to evaluate fuel efficiency across vehicles.

Although GeoTab provides access to operational telemetry data, several critical engine diagnostics required for Full FEI calculation are unavailable in the current pilot fleet.

Without an alternative methodology, the company cannot:

- Compare fuel efficiency across vehicles
- Identify inefficient operating patterns
- Benchmark fleet performance
- Establish a foundation for future digital twin development

Therefore, a practical FEI-Lite framework is required to provide immediate operational insights using currently available telemetry data.

---

## Project Objective

The objective of this project is to design, implement, and evaluate an FEI-Lite (Fuel Efficiency Index Lite) framework using GeoTab telemetry data from the DHL pilot fleet.

The project aims to:

- Evaluate vehicle fuel efficiency using available telemetry signals
- Compare performance across fleet vehicles
- Monitor driver operating behavior
- Create a practical fuel-efficiency scoring framework
- Support fleet benchmarking and operational monitoring
- Establish a foundation for future Full FEI implementation
- Prepare the framework for future machine learning enhancement

---

## Project Scope

### Included

- GeoTab telemetry validation
- Signal availability assessment
- Fleet KPI development
- FEI-Lite framework design
- Python data processing pipeline
- Vehicle-level performance scoring
- Fleet-level analytics
- SQL-based analysis
- Tableau dashboard development
- Fleet benchmarking
- Business insight generation

### Excluded

- Full FEI implementation
- OEM diagnostic integration
- Engine Load modeling
- Fuel Rate modeling
- Torque modeling
- DSI implementation
- VEI implementation
- Machine learning model development
- Digital Twin deployment

---

## Available Signals

The following signals have been validated as available from the DHL pilot fleet:

- Vehicle Speed
- Engine RPM
- Distance / Odometer
- Engine Hours
- Total Fuel Used
- Idle Fuel Used
- Idle Time

These signals will serve as the primary inputs for FEI-Lite development.

---

## Expected Deliverables

### Technical Deliverables

- Signal Availability Matrix
- FEI-Lite Methodology Document
- Python Analytics Pipeline
- Vehicle KPI Dataset
- FEI-Lite Score Engine
- SQL Analytics Queries
- Tableau Dashboard

### Portfolio Deliverables

- GitHub Repository
- README Documentation
- Notion Portfolio Page
- Resume Project Summary
- Interview Storytelling Materials

---

## Technology Stack

- Python
- Pandas
- GeoTab API
- SQL
- Tableau
- GitHub

---

## Success Criteria

The project will be considered successful if it:

- Produces a repeatable FEI-Lite scoring framework
- Generates vehicle-level fuel efficiency rankings
- Identifies operational performance differences across vehicles
- Provides actionable fleet analytics insights
- Demonstrates a clear migration path toward future Full FEI implementation

---

## Project Timeline

### Week 1

- Signal Validation
- Data Assessment
- FEI-Lite Framework Design

### Week 2

- KPI Development
- FEI-Lite Calculation
- SQL Analytics
- Tableau Dashboard
- GitHub Documentation
- Portfolio Packaging

---

## Final Goal

Develop a deployable Fleet Telemetry Analytics framework that transforms GeoTab telemetry data into actionable fuel-efficiency insights while establishing a scalable foundation for future Full FEI and machine-learning-based fleet analytics.
