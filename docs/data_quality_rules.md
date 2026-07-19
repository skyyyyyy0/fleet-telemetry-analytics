# Data Quality Rules

These rules are frozen for the version 2 KPI and FEI-Lite recalculation.

## 1. Time Standard

- Source GeoTab timestamps are interpreted as UTC.
- All analysis timestamps are converted to `Asia/Seoul` (KST).
- Records are sorted by `vehicle`, `signal`, and `dateTime`.
- `time_delta_seconds` is calculated from the current timestamp to the next timestamp within each vehicle and signal.

## 2. Signal Validity Rules

| Signal               | Validity rule                          |
| -------------------- | -------------------------------------- |
| Vehicle speed        | 0–160 km/h                             |
| Engine RPM           | 0–4,500 RPM                            |
| Coolant temperature  | -40–130°C                              |
| Cumulative fuel      | Value ≥ 0 and increase rate ≤ 100 L/h  |
| Odometer             | Value ≥ 0 and implied speed ≤ 160 km/h |
| Incremental distance | Value ≥ 0 and implied speed ≤ 160 km/h |

## 3. Timestamp Gap Rule

- Valid time-weighted interval: `0 < time_delta_seconds ≤ 300`.
- Intervals longer than 300 seconds are excluded from time-weighted KPI calculations.
- Duplicate or non-increasing timestamps are excluded and counted.
- Long gaps do not automatically invalidate cumulative fuel or odometer values.

## 4. Cumulative Reset Rule

- A reset is detected when the vehicle-level cumulative difference is negative.
- Reset intervals are excluded from fuel and distance totals.
- Calculation resumes from the new cumulative segment.
- Positive jumps are validated using fuel consumption rate or implied vehicle speed.

## 5. Outlier Handling

- Raw data is never overwritten.
- Invalid records or increments are excluded rather than capped.
- Removed record counts and percentages must be reported by signal and analysis period.
- Current audit detected zero cumulative fuel and odometer resets.
