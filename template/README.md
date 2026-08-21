# Streamlit Table Variable CSV Builder (Version 2)

This project provides a Streamlit web application that:
- accepts table variable CSV files matching seven different config schemas,
- uses the CSV headers as fixed identifiers,
- allows row editing in the browser,
- validates data strictly,
- exports a downloadable CSV with the same format.

## What I Built

- `app.py`
  - Adds 21 template pages in one app:
    `Plant_Tag`, `Plant_Node`, `MCLHB_Tags`, `MCLHYST_Tags`, `MCLHYSTDYN_Tags`,
    `JSON_TCP_Servers`, `MCLFSM_Tags`, `MCLPROP_Tags`, `ModbusTCP_Servers`,
    `ModbusTCP_Servers_UID`, `MVBOO_Tags`, `MVJSON_Directory`, `MVJSON_Tags`,
    `MVPULSE_Tags`, `MVSENSOR_Tags`, `MVUSER_Tags`, `MCLIPOP_Tags`,
    `MCLLOG_Entries`, `MCLLOG_Options`, `MCLLOG_Units`, `WebClient_Destinations`
  - Sidebar uses a dropdown (`st.selectbox`) for 21 pages instead of a radio list
  - Enforces exact header order and names per page
  - Editable grid using `st.data_editor`
  - Strict validation per template:
    - Integer fields
    - Float fields (where applicable)
    - Boolean fields (`TRUE` or `FALSE`)
    - Interval fields (`T#<number><ms|s|m|h>`)
    - Required text fields
    - IPv4 format for Plant_Node `IP Address`
  - Auto-number button for `Index` (`1..N`) — only shown on pages that have an Index column
  - Download button enabled only when validation passes
  - Default filename download and timestamped download for each page
  - Plant_Node inline helper with valid IP address examples

- `requirements.txt`
  - `streamlit`
  - `pandas`

## Setup

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the original app:

```bash
streamlit run app.py
```

4. Run the new combined export app:

```bash
streamlit run version2.py
```

The `version2.py` app lets you edit each template and then download a single `config.zip`
bundle containing all template CSV files.

5. Run the CSV-name based app (V3):

```bash
streamlit run app_V3.py
```

The `app_V3.py` app keeps all `version2.py` features, but the template selector displays
template names as CSV filenames.

## Process Notes (App_V3)

1. Created `app_V3.py` by cloning `version2.py` to preserve behavior and reduce regression risk.
2. Updated page metadata so selector names are tied to `default_filename` values (CSV names).
3. Added missing templates from your provided files:
  - `WebClient_Entries.csv`
  - `AncillaryServices.csv`
4. Kept strict validation and per-template CSV downloads from the V2 implementation.
5. Kept combined bundle export as `config.zip`, containing one CSV per template.
6. Added compatibility parsing for legacy key-value CSV shapes so these upload cleanly:
  - `JSON_TCP_Servers.csv`
  - `MVJSON_Directory.csv`
7. Verified the new app launches successfully with Streamlit.

## Process Notes

1. Reviewed all 21 CSV structures and mapped each schema to validation rules.
2. Reused the shared page engine; each new page requires only a config dict entry.
3. Key observations per new CSV:
   - `MCLPROP_Tags`: 6 proportional point groups (P1–P6), each with Enable/Input/Output.
   - `ModbusTCP_Servers` / `ModbusTCP_Servers_UID`: small fixed-column tables with Index.
   - `MVBOO_Tags`, `MVPULSE_Tags`, `MVUSER_Tags`: simple tag tables with Interval.
   - `MVJSON_Directory`: two-row key-value config adapted to a single-row flat table; original has no standard header row.
   - `MVJSON_Tags`: adds IPv4 validation on `Source IP`, same as Plant_Node on `IP Address`.
   - `MVSENSOR_Tags`: 15 repeated Child column groups; pandas auto-disambiguates duplicate headers with `.1`–`.14` suffixes — config headers match this to keep upload validation working.
   - `MCLIPOP_Tags`: proportional output controller with limit enable/value pairs.
   - `MCLLOG_Entries` / `MCLLOG_Options` / `MCLLOG_Units`: logging config tables.
   - `WebClient_Destinations`: two interval fields (`Interval` and `Timeout`); optional text fields (Name, URL, Username, Password) left as free-form per original data.
4. Switched sidebar template selector from `st.radio` to `st.selectbox` — better UX for 21 options.
5. Auto-number Index button remains conditional — only shown on pages with an `Index` column.

## Thoughts (Design Rationale)

1. Why one app with two pages:
  - This keeps the user flow simple (single Streamlit entry point) while still separating the two schemas clearly.

2. Why a shared page engine:
  - All pages need the same workflow but different rules.
  - A shared function means adding a new page requires only a new config dict — no new UI code.

3. Why strict per-template validation:
  - Different CSVs have different required and typed columns.
  - Validating based on template configuration avoids false positives and prevents silent format drift.
  - Plant_Node now includes strict IPv4 checking for `IP Address`.

4. Why keep headers locked:
  - Your configuration files are schema-sensitive.
  - Exact header order/name enforcement ensures exported CSVs remain compatible.

5. Why keep both download styles:
  - Default filename supports drop-in replacement workflows.
  - Timestamped filename prevents accidental overwrite when keeping historical snapshots.

## Questions Asked During Build

1. Should columns be locked to source headers?
   - Your answer: Yes.
2. Default filename for download?
   - Your answer: `Plant_Tag.csv`.
3. Validation strictness?
   - Your answer: strict validation.
4. Should `Index` auto-numbering be added?
  - Your answer: yes, and it is implemented.
5. Should a timestamped download option be added?
  - Your answer: yes, and it is implemented.
