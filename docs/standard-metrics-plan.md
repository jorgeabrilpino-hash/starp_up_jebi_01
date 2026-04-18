# Standard metrics refactor plan

## Objective
Replace custom/invented operator dimensions with standard, defensible operational KPIs and signal metrics.

## Metrics to keep as standard / defensible
- cycle_time_avg_s
- cycle_time_std_s
- cycle_time_cv
- cycles_per_hour
- estimated_trucks_per_hour
- service_time_per_truck_min
- left_cycle_time_avg_s
- right_cycle_time_avg_s
- side_delta_s
- jerk_avg
- jerk_p95
- jerk_max
- smoothness_index
- extreme_jerk_event_count
- smoothness_by_block
- smoothness_decay_per_block

## Metrics to remove from operator evaluation
- dark_mineral_pct as operator quality KPI
- material/color-based quality score
- any score naming presented as industry standard when it is not

## Presentation change
Dashboard and report should present:
1. Standard operational KPIs
2. IMU motion-control indicators
3. Temporal stability indicators
4. Interpreted recommendations

## Composite layer
If a composite score remains, present it as:
- Internal summary index
- not as an industry standard metric
