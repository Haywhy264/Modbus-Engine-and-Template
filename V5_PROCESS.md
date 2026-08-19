# Version 5 Implementation Process

## Goal
Create a Version 5 simulator with behavior matching Version 4, scaled from 50 to 500 dummy sensor tags, and provide a compatible 500-tag Plant Tag CSV.

## What Was Done
1. Reviewed Version 4 simulator and GUI files to preserve runtime behavior.
2. Duplicated Version 4 files into new Version 5 files.
3. Updated core constants and metadata in the simulator:
   - `SENSOR_COUNT` from `50` to `500`
   - `TOTAL_REGISTERS` follows `SENSOR_COUNT`
   - tag naming from `sensor_01..sensor_50` to `sensor_001..sensor_500`
   - version identity strings changed from V4 to V5
   - default port moved to `5023` to avoid conflict with existing launchers
4. Updated GUI launcher for Version 5:
   - now points to `modbus_meter_simulator_v5.py`
   - default port `5023`
   - register map label updated to 500 tags
   - register table now displays `sensor_001..sensor_500`
5. Added V5 batch launchers:
   - `run_modbus_simulator_v5.bat`
   - `run_modbus_simulator_v5_gui.bat`
6. Added test coverage copy for v5 and updated assertions for 500-tag behavior.
7. Generated `Plant_tag.csv` with 500 contiguous tag rows and addresses `0..499`.

## Files Added
- `modbus_meter_simulator_v5.py`
- `modbus_simulator_v5_gui.py`
- `run_modbus_simulator_v5.bat`
- `run_modbus_simulator_v5_gui.bat`
- `tests/test_simulator_v5.py`
- `Plant_tag.csv`
- `V5_PROCESS.md`

## Validation Approach
- Static checks via updated tests in `tests/test_simulator_v5.py`:
  - register map size and contiguous addresses
  - generator output count and value bounds
  - packed register count and uint16 bounds

## Notes
- The new CSV keeps the same schema and defaults as `_50_Plant_Tag.csv`.
- Tag names in v5 are zero-padded to 3 digits for consistent sorting (`sensor_001`...`sensor_500`).
