# FEI-Lite Methodology

## Objective

The objective of FEI-Lite is to create a practical fuel-efficiency scoring framework using currently available GeoTab telemetry data from the DHL Korea pilot fleet.

Full FEI implementation requires advanced OEM signals such as Engine Load, Fuel Rate, and Engine Torque. Since these signals were not available in the current pilot dataset, FEI-Lite was designed as a proxy-based methodology using available operational signals.

## FEI-Lite Components

FEI-Lite consists of four scoring components:

| Component                      | Description                                           | Weight |
| ------------------------------ | ----------------------------------------------------- | -----: |
| Fuel Efficiency Score (FES)    | Measures fuel consumed relative to distance traveled  |    50% |
| RPM Efficiency Score (RES)     | Measures engine operation within efficient RPM range  |    20% |
| Idle Efficiency Score (IES)    | Measures fuel wasted during idle operation            |    20% |
| Driving Smoothness Score (DSS) | Measures driving stability and operational smoothness |    10% |

Final FEI-Lite Score:

FEI-Lite = 100 × [(0.50 × FES) + (0.20 × RES) + (0.20 × IES) + (0.10 × DSS)]

## Fuel Efficiency Score (FES)

### Purpose

The Fuel Efficiency Score (FES) measures how effectively a vehicle converts fuel into productive distance traveled.

Among all available GeoTab telemetry signals, fuel consumption and vehicle distance provide the most direct indication of operational fuel efficiency. Therefore, FES represents the largest component of the FEI-Lite framework.

### Methodology

Fuel efficiency is calculated as:

Fuel Efficiency = Distance Traveled ÷ Fuel Used

Where:

- Distance Traveled = Total distance traveled during the analysis period (km)
- Fuel Used = Total fuel consumed during the analysis period (L)

Higher values indicate more efficient fuel utilization.

### Fleet Normalization

Because vehicle operating conditions differ across routes and utilization levels, each vehicle is evaluated relative to the fleet median.

Normalized Fuel Efficiency Score:

FES = Vehicle Fuel Efficiency ÷ Fleet Median Fuel Efficiency

The resulting score is capped at 1.0 to prevent extreme outliers from disproportionately influencing the final FEI-Lite score.

### Business Rationale

Fuel consumption is the primary operating cost for commercial fleets.

By measuring distance generated per unit of fuel consumed, FES provides a simple and interpretable indicator of operational efficiency.

Within FEI-Lite, FES serves as the foundational measure of productive fuel utilization.

### Limitations

Distance/Odometer data were not consistently available across all vehicles within the DHL pilot fleet.

As a result, FES may only be calculated for vehicles with sufficient distance-related telemetry.

Future implementation of Full FEI will incorporate Engine Load, Fuel Rate, and Engine Torque to improve estimation accuracy.

## RPM Efficiency Score (RES)

### Purpose

The RPM Efficiency Score (RES) measures how efficiently the engine operates within its recommended RPM range.

Excessively high RPM operation generally increases fuel consumption, while excessively low RPM operation may reduce engine efficiency and increase engine stress.

RES was designed to evaluate how consistently a vehicle operates within an efficient engine-speed range.

### Methodology

Based on industry references and diesel engine operating characteristics, the recommended RPM efficiency range was defined as:

1200 RPM – 1800 RPM

For event-driven GeoTab telemetry, RPM efficiency is calculated using timestamp-weighted operating time rather than simple record counts.

RES is calculated as:

RES = Time Within Efficient RPM Range ÷ Total Engine Operating Time

### Example

Efficient RPM Time = 6 hours

Total Engine Operating Time = 8 hours

RES = 0.75

### Business Rationale

Engine RPM is one of the most widely available indicators of engine operating behavior.

Monitoring operation within an efficient RPM band provides insight into fuel-efficient driving patterns and engine utilization.

### Limitations

RPM alone does not represent engine workload.

Future Full FEI implementation will incorporate Engine Load and Torque to better estimate actual engine work.

## Idle Efficiency Score (IES)

### Purpose

The Idle Efficiency Score (IES) measures fuel consumed during non-productive engine operation.

Idle operation consumes fuel while generating little or no vehicle movement and was identified as one of the most important factors affecting fuel economy within the DHL pilot fleet.

### Methodology

Idle conditions are defined as:

- Engine RPM > 500
- Vehicle Speed < 1 km/h

Idle Fuel Ratio is calculated as:

Idle Fuel Ratio = Idle Fuel Used ÷ Total Fuel Used

The Idle Efficiency Score is then calculated as:

IES = 1 − Idle Fuel Ratio

### Example

Total Fuel Used = 50 L

Idle Fuel Used = 10 L

Idle Fuel Ratio = 20%

IES = 0.80

### Business Rationale

During validation of the DHL fleet, increased idle activity was consistently associated with higher fuel consumption and lower apparent fuel economy.

Separating idle fuel consumption from productive driving activity improves interpretation of overall vehicle efficiency.

### Limitations

Idle Time and Idle Fuel Used are derived metrics and depend on the accuracy of underlying RPM and Vehicle Speed signals.

## Driving Smoothness Score (DSS)

### Purpose

The Driving Smoothness Score (DSS) evaluates operational stability during vehicle movement.

Aggressive acceleration, harsh braking, and highly variable driving patterns are typically associated with increased fuel consumption.

### Methodology

DSS is based on available GeoTab operational signals including:

- Vehicle Speed
- Longitudinal Acceleration
- Braking Events

Driving variability is measured using speed fluctuations and event frequency.

Higher operational stability results in a higher DSS score.

### Business Rationale

Driving behavior has a direct impact on fuel consumption.

Vehicles exhibiting smoother operating patterns generally achieve better fuel efficiency and reduced mechanical stress.

### Limitations

DSS serves as a proxy for driving behavior and does not directly measure driver intent or traffic conditions.

## FEI-Lite Weighting Logic

### Objective

The FEI-Lite weighting framework was designed to balance direct fuel-efficiency measurements with operational behavior indicators.

Not all telemetry signals contribute equally to overall vehicle efficiency.

Therefore, greater weight was assigned to metrics that directly influence fuel consumption.

### Weight Distribution

| Component                      | Weight |
| ------------------------------ | ------ |
| Fuel Efficiency Score (FES)    | 50%    |
| RPM Efficiency Score (RES)     | 20%    |
| Idle Efficiency Score (IES)    | 20%    |
| Driving Smoothness Score (DSS) | 10%    |

### Weighting Rationale

#### Fuel Efficiency Score (50%)

Fuel efficiency represents the primary objective of the framework.

Distance traveled relative to fuel consumed provides the most direct measure of vehicle performance.

Therefore, FES receives the highest weighting.

#### RPM Efficiency Score (20%)

RPM behavior influences fuel consumption and engine efficiency.

Maintaining operation within an efficient RPM range generally improves fuel utilization and reduces unnecessary engine stress.

#### Idle Efficiency Score (20%)

Idle activity was identified as one of the most significant factors affecting fuel consumption within the DHL pilot fleet.

Several vehicles exhibited substantial increases in idle operation during the treatment period.

As a result, idle efficiency was assigned a weighting equivalent to RPM efficiency.

#### Driving Smoothness Score (10%)

Driving behavior affects fuel consumption indirectly through acceleration patterns, braking frequency, and operating stability.

Because its impact is less direct than fuel consumption and idle behavior, DSS receives the lowest weighting.

### Final FEI-Lite Formula

FEI-Lite = 100 ×

(0.50 × FES +
0.20 × RES +
0.20 × IES +
0.10 × DSS)

The resulting score is normalized to a scale ranging from 0 to 100.

## Score Interpretation

### Purpose

The FEI-Lite score is intended to provide a simple and intuitive indicator of overall vehicle fuel-efficiency performance.

Scores are categorized into performance bands to support fleet-level benchmarking and operational decision-making.

### Rating Scale

| FEI-Lite Score | Rating            |
| -------------- | ----------------- |
| 90 – 100       | Excellent         |
| 80 – 89        | Good              |
| 70 – 79        | Average           |
| Below 70       | Needs Improvement |

### Interpretation

#### Excellent (90 – 100)

Vehicle demonstrates highly efficient fuel utilization, low idle losses, and stable operating behavior.

#### Good (80 – 89)

Vehicle operates efficiently with only minor opportunities for improvement.

#### Average (70 – 79)

Vehicle performance is acceptable but may be affected by increased idle activity or inefficient operating patterns.

#### Needs Improvement (<70)

Vehicle exhibits significant inefficiencies that warrant operational review.

Potential contributing factors include:

- Excessive idle operation
- Inefficient RPM utilization
- Aggressive driving behavior
- Increased fuel consumption

## Limitations

The current FEI-Lite framework was developed using the telemetry signals available within the DHL Korea pilot fleet.

Several high-value engine performance signals were unavailable during this phase of the project, including:

- Engine Load
- Fuel Rate
- Engine Torque
- Accelerator Pedal Position (APS)
- DPF Differential Pressure
- DPF Soot Load
- Regeneration Activity

As a result, FEI-Lite should be interpreted as a practical proxy-based fuel efficiency framework rather than a complete Digital Twin implementation.

The methodology provides directional insight into fleet fuel-efficiency performance while maintaining compatibility with currently available GeoTab telemetry data.

Future versions of the framework may incorporate additional engine and emissions signals to improve predictive accuracy and support full FEI implementation.

## Future Full FEI Integration

The long-term objective of this project is the implementation of the full Fuel Efficiency Index (FEI) framework described within the Cero Digital Twin Intelligence Platform.

Full FEI implementation requires advanced engine and operational parameters including:

- Engine Load
- Fuel Rate
- Engine Torque
- Accelerator Pedal Position (APS)
- Ambient Conditions
- Route Characteristics

These signals enable estimation of expected fuel consumption under specific operating conditions and support development of a Digital Twin model capable of comparing expected and actual vehicle performance.

FEI-Lite represents the first implementation stage of this vision and serves as a practical methodology for fleets where advanced engine telemetry is not currently available.
