import io
import ipaddress
import re
import zipfile
from datetime import datetime
from typing import Dict, List, Set, Tuple

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Table Variable CSV Builder - Version 2", layout="wide")

PAGE_CONFIGS = {
    "Plant_Tag": {
        "title": "Plant Tag CSV Builder",
        "headers": [
            "Index",
            "Name",
            "Node Index",
            "Enable",
            "Interval",
            "Multiplier",
            "Bit Mask",
            "Word Swap",
            "Byte Swap",
            "Data Type",
            "Tag Type",
            "FC Read",
            "FC Write",
            "Address",
            "Length",
            "Unit",
        ],
        "integer_columns": {
            "Index",
            "Node Index",
            "Bit Mask",
            "Data Type",
            "Tag Type",
            "FC Read",
            "FC Write",
            "Address",
            "Length",
            "Unit",
        },
        "float_columns": {"Multiplier"},
        "boolean_columns": {"Enable", "Word Swap", "Byte Swap"},
        "interval_columns": {"Interval"},
        "required_text_columns": {"Name"},
        "ipv4_columns": set(),
        "default_filename": "Plant_Tag.csv",
    },
    "Plant_Node": {
        "title": "Plant Node CSV Builder",
        "headers": [
            "Index",
            "Name",
            "Node Type",
            "UID",
            "Enable",
            "Serial Port",
            "Baudrate",
            "Parity",
            "Stop Bits",
            "TCP Port",
            "IP Address",
            "Timeout",
        ],
        "integer_columns": {
            "Index",
            "Node Type",
            "UID",
            "Serial Port",
            "Baudrate",
            "Parity",
            "Stop Bits",
            "TCP Port",
        },
        "float_columns": set(),
        "boolean_columns": {"Enable"},
        "interval_columns": {"Timeout"},
        "required_text_columns": {"Name", "IP Address"},
        "ipv4_columns": {"IP Address"},
        "default_filename": "Plant_Node.csv",
    },
    "MCLHB_Tags": {
        "title": "MCLHB Tags CSV Builder",
        "headers": [
            "Control Tag",
            "Name",
            "Unit",
            "Enable",
            "Toggle or Count",
            "Start Value",
            "End Value",
            "Count Step",
            "Interval",
        ],
        "integer_columns": {"Toggle or Count", "Count Step"},
        "float_columns": {"Start Value", "End Value"},
        "boolean_columns": {"Enable"},
        "interval_columns": {"Interval"},
        "required_text_columns": {"Control Tag", "Name"},
        "ipv4_columns": set(),
        "default_filename": "MCLHB_Tags.csv",
    },
    "MCLHYST_Tags": {
        "title": "MCLHYST Tags CSV Builder",
        "headers": [
            "Control Tag/Enable",
            "Name/Input Low",
            "Unit/Output Low",
            "Input Tag/Mid Enable",
            "Source Tag/Output Mid",
            "Interval/Input High",
            "Blank/Output High",
            "Blank/Plan ID",
        ],
        "integer_columns": set(),
        "float_columns": set(),
        "boolean_columns": set(),
        "interval_columns": set(),
        "required_text_columns": {"Control Tag/Enable"},
        "ipv4_columns": set(),
        "default_filename": "MCLHYST_Tags.csv",
    },
    "MCLHYSTDYN_Tags": {
        "title": "MCLHYSTDYN Tags CSV Builder",
        "headers": [
            "Control Tag",
            "Name",
            "Unit",
            "Input Tag",
            "Interval",
            "Start",
            "End",
            "Step Size",
            "Steps",
            "Default Output",
        ]
        + [f"Output Step {i}" for i in range(1, 55)],
        "integer_columns": {"Steps"},
        "float_columns": {"Start", "End", "Step Size", "Default Output"}
        | {f"Output Step {i}" for i in range(1, 55)},
        "boolean_columns": set(),
        "interval_columns": {"Interval"},
        "required_text_columns": {"Control Tag", "Name"},
        "ipv4_columns": set(),
        "default_filename": "MCLHYSTDYN_Tags.csv",
    },
    "JSON_TCP_Servers": {
        "title": "JSON TCP Servers Config Builder",
        "headers": ["Port", "Enable", "Idle Time", "Authentication"],
        "integer_columns": {"Port"},
        "float_columns": set(),
        "boolean_columns": {"Enable", "Authentication"},
        "interval_columns": {"Idle Time"},
        "required_text_columns": set(),
        "ipv4_columns": set(),
        "default_filename": "JSON_TCP_Servers.csv",
    },
    "MCLFSM_Tags": {
        "title": "MCLFSM Tags CSV Builder",
        "headers": [
            "Control Tag",
            "Name",
            "Unit",
            "State",
            "State Name",
            "Event Tag",
            "Next State",
            "Enable Event",
            "Event Input Value",
            "Event Output Enable",
            "Event Output Value",
            "Timer",
            "Allow Refresh",
        ],
        "integer_columns": {"State", "Next State"},
        "float_columns": {"Event Input Value", "Event Output Value"},
        "boolean_columns": {"Enable Event", "Event Output Enable", "Allow Refresh"},
        "interval_columns": {"Timer"},
        "required_text_columns": {"Control Tag", "Name", "State Name"},
        "ipv4_columns": set(),
        "default_filename": "MCLFSM_Tags.csv",
    },
    "MCLPROP_Tags": {
        "title": "MCLPROP Tags CSV Builder",
        "headers": [
            "Control Tag",
            "Name",
            "Unit",
            "Input Tag",
            "Source Tag",
            "Source Enable Value",
            "Default Enable",
            "Default Value",
            "Interval",
            "P1 Enable",
            "P1 Input",
            "P1 Output",
            "P2 Enable",
            "P2 Input",
            "P2 Output",
            "P3 Enable",
            "P3 Input",
            "P3 Output",
            "P4 Enable",
            "P4 Input",
            "P4 Output",
            "P5 Enable",
            "P5 Input",
            "P5 Output",
            "P6 Enable",
            "P6 Input",
            "P6 Output",
        ],
        "integer_columns": set(),
        "float_columns": {
            "Source Enable Value",
            "Default Value",
            "P1 Input",
            "P1 Output",
            "P2 Input",
            "P2 Output",
            "P3 Input",
            "P3 Output",
            "P4 Input",
            "P4 Output",
            "P5 Input",
            "P5 Output",
            "P6 Input",
            "P6 Output",
        },
        "boolean_columns": {
            "Default Enable",
            "P1 Enable",
            "P2 Enable",
            "P3 Enable",
            "P4 Enable",
            "P5 Enable",
            "P6 Enable",
        },
        "interval_columns": {"Interval"},
        "required_text_columns": {"Control Tag", "Name"},
        "ipv4_columns": set(),
        "default_filename": "MCLPROP_Tags.csv",
    },
    "ModbusTCP_Servers": {
        "title": "ModbusTCP Servers CSV Builder",
        "headers": ["Index", "Enable", "Port"],
        "integer_columns": {"Index", "Port"},
        "float_columns": set(),
        "boolean_columns": {"Enable"},
        "interval_columns": set(),
        "required_text_columns": set(),
        "ipv4_columns": set(),
        "default_filename": "ModbusTCP_Servers.csv",
    },
    "ModbusTCP_Servers_UID": {
        "title": "ModbusTCP Servers UID CSV Builder",
        "headers": ["Index", "Name", "UID"],
        "integer_columns": {"Index", "UID"},
        "float_columns": set(),
        "boolean_columns": set(),
        "interval_columns": set(),
        "required_text_columns": {"Name"},
        "ipv4_columns": set(),
        "default_filename": "ModbusTCP_Servers_UID.csv",
    },
    "MVBOO_Tags": {
        "title": "MVBOO Tags CSV Builder",
        "headers": [
            "Tag",
            "Name",
            "Unit",
            "Input Tag",
            "Source Tag",
            "Source Enable Value",
            "Interval",
        ],
        "integer_columns": set(),
        "float_columns": {"Source Enable Value"},
        "boolean_columns": set(),
        "interval_columns": {"Interval"},
        "required_text_columns": {"Tag", "Name"},
        "ipv4_columns": set(),
        "default_filename": "MVBOO_Tags.csv",
    },
    "MVJSON_Directory": {
        "title": "MVJSON Directory Config Builder",
        "headers": ["Directory", "Retention"],
        "integer_columns": set(),
        "float_columns": set(),
        "boolean_columns": set(),
        "interval_columns": set(),
        "required_text_columns": {"Directory", "Retention"},
        "ipv4_columns": set(),
        "default_filename": "MVJSON_Directory.csv",
    },
    "MVJSON_Tags": {
        "title": "MVJSON Tags CSV Builder",
        "headers": ["Tag", "Name", "Unit", "Feature Tag", "System ID", "Source IP", "Log"],
        "integer_columns": {"System ID"},
        "float_columns": set(),
        "boolean_columns": {"Log"},
        "interval_columns": set(),
        "required_text_columns": {"Tag", "Name"},
        "ipv4_columns": {"Source IP"},
        "default_filename": "MVJSON_Tags.csv",
    },
    "MVPULSE_Tags": {
        "title": "MVPULSE Tags CSV Builder",
        "headers": ["Tag", "Name", "Unit", "Input Tag", "Multiplier", "Interval"],
        "integer_columns": set(),
        "float_columns": {"Multiplier"},
        "boolean_columns": set(),
        "interval_columns": {"Interval"},
        "required_text_columns": {"Tag", "Name"},
        "ipv4_columns": set(),
        "default_filename": "MVPULSE_Tags.csv",
    },
    "MVSENSOR_Tags": {
        "title": "MVSENSOR Tags CSV Builder",
        "headers": [
            "Tag",
            "Name",
            "Unit",
            "Interval",
            "Delta",
            "Limits",
            "Lower Limit Value",
            "Upper Limit Value",
            "Lower Limit Tag",
            "Upper Limit Tag",
        ]
        + [
            name if i == 0 else f"{name}.{i}"
            for i in range(15)
            for name in [
                "Child Tag",
                "Child Include",
                "Child Multiplier",
                "Child Multiplier Tag",
                "Child Offset",
            ]
        ],
        "integer_columns": {"Tag", "Lower Limit Tag", "Upper Limit Tag"}
        | {"Child Tag" if i == 0 else f"Child Tag.{i}" for i in range(15)}
        | {"Child Multiplier Tag" if i == 0 else f"Child Multiplier Tag.{i}" for i in range(15)},
        "float_columns": {"Lower Limit Value", "Upper Limit Value"}
        | {"Child Multiplier" if i == 0 else f"Child Multiplier.{i}" for i in range(15)}
        | {"Child Offset" if i == 0 else f"Child Offset.{i}" for i in range(15)},
        "boolean_columns": {"Delta", "Limits"}
        | {"Child Include" if i == 0 else f"Child Include.{i}" for i in range(15)},
        "interval_columns": {"Interval"},
        "required_text_columns": {"Name"},
        "ipv4_columns": set(),
        "default_filename": "MVSENSOR_Tags.csv",
    },
    "MVUSER_Tags": {
        "title": "MVUSER Tags CSV Builder",
        "headers": ["Tag", "Name", "Unit", "Interval", "Value"],
        "integer_columns": set(),
        "float_columns": {"Value"},
        "boolean_columns": set(),
        "interval_columns": {"Interval"},
        "required_text_columns": {"Tag", "Name"},
        "ipv4_columns": set(),
        "default_filename": "MVUSER_Tags.csv",
    },
    "MCLIPOP_Tags": {
        "title": "MCLIPOP Tags CSV Builder",
        "headers": [
            "Control Tag",
            "Name",
            "Unit",
            "Input Tag",
            "Control Enable",
            "Repeat Mode",
            "Interval",
            "Multiplier",
            "Offset",
            "Minimum Limit Enable",
            "Minimum Limit",
            "Maximum Limit Enable",
            "Maximum Limit",
        ],
        "integer_columns": {"Repeat Mode"},
        "float_columns": {"Multiplier", "Offset", "Minimum Limit", "Maximum Limit"},
        "boolean_columns": {"Control Enable", "Minimum Limit Enable", "Maximum Limit Enable"},
        "interval_columns": {"Interval"},
        "required_text_columns": {"Control Tag", "Name"},
        "ipv4_columns": set(),
        "default_filename": "MCLIPOP_Tags.csv",
    },
    "MCLLOG_Entries": {
        "title": "MCLLOG Entries CSV Builder",
        "headers": ["Log Option Index", "Log Type", "Tag", "Monitor", "Delta", "Interval"],
        "integer_columns": {"Log Option Index", "Log Type", "Tag"},
        "float_columns": set(),
        "boolean_columns": {"Monitor", "Delta"},
        "interval_columns": {"Interval"},
        "required_text_columns": set(),
        "ipv4_columns": set(),
        "default_filename": "MCLLOG_Entries.csv",
    },
    "MCLLOG_Options": {
        "title": "MCLLOG Options CSV Builder",
        "headers": ["Log Option Index", "Log Type", "Name", "Directory", "Enable"],
        "integer_columns": {"Log Option Index", "Log Type"},
        "float_columns": set(),
        "boolean_columns": {"Enable"},
        "interval_columns": set(),
        "required_text_columns": {"Directory"},
        "ipv4_columns": set(),
        "default_filename": "MCLLOG_Options.csv",
    },
    "MCLLOG_Units": {
        "title": "MCLLOG Units CSV Builder",
        "headers": ["Unit", "Interval", "Interval Index"],
        "integer_columns": {"Unit", "Interval Index"},
        "float_columns": set(),
        "boolean_columns": set(),
        "interval_columns": {"Interval"},
        "required_text_columns": set(),
        "ipv4_columns": set(),
        "default_filename": "MCLLOG_Units.csv",
    },
    "WebClient_Destinations": {
        "title": "WebClient Destinations CSV Builder",
        "headers": ["Index", "Name", "URL", "Interval", "Enable", "Timeout", "Username", "Password"],
        "integer_columns": {"Index"},
        "float_columns": set(),
        "boolean_columns": {"Enable"},
        "interval_columns": {"Interval", "Timeout"},
        "required_text_columns": set(),
        "ipv4_columns": set(),
        "default_filename": "WebClient_Destinations.csv",
    },
}

TEMPLATE_KEYS = list(PAGE_CONFIGS.keys())
BOOL_VALUES = {"TRUE", "FALSE"}
INTERVAL_PATTERN = re.compile(r"^T#\d+(ms|s|m|h)$", flags=re.IGNORECASE)


def to_text_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    text_df = dataframe.copy()
    for column in text_df.columns:
        text_df[column] = text_df[column].astype("string").fillna("")
    return text_df


def validate_dataframe(
    dataframe: pd.DataFrame,
    integer_columns: Set[str],
    float_columns: Set[str],
    boolean_columns: Set[str],
    interval_columns: Set[str],
    required_text_columns: Set[str],
    ipv4_columns: Set[str],
) -> Tuple[bool, Dict[int, List[str]]]:
    errors: Dict[int, List[str]] = {}

    for idx, row in dataframe.iterrows():
        row_errors: List[str] = []

        for column in integer_columns:
            value = str(row[column]).strip()
            if not value:
                row_errors.append(f"{column}: required integer is empty")
                continue
            if not re.fullmatch(r"[-+]?\d+", value):
                row_errors.append(f"{column}: '{value}' is not a valid integer")

        for column in float_columns:
            value = str(row[column]).strip()
            if not value:
                row_errors.append(f"{column}: required number is empty")
                continue
            try:
                float(value)
            except ValueError:
                row_errors.append(f"{column}: '{value}' is not a valid number")

        for column in boolean_columns:
            value = str(row[column]).strip().upper()
            if value not in BOOL_VALUES:
                row_errors.append(f"{column}: value must be one of {sorted(BOOL_VALUES)}")

        for column in interval_columns:
            value = str(row[column]).strip()
            if not value:
                row_errors.append(f"{column}: interval is required")
                continue
            if not INTERVAL_PATTERN.fullmatch(value):
                row_errors.append(f"{column}: '{value}' must match pattern T#<number><ms|s|m|h>")

        for column in required_text_columns:
            if not str(row[column]).strip():
                row_errors.append(f"{column}: required text is empty")

        for column in ipv4_columns:
            value = str(row[column]).strip()
            if not value:
                continue
            try:
                parsed_ip = ipaddress.ip_address(value)
                if parsed_ip.version != 4:
                    row_errors.append(f"{column}: '{value}' is not a valid IPv4 address")
            except ValueError:
                row_errors.append(f"{column}: '{value}' is not a valid IPv4 address")

        if row_errors:
            errors[idx] = row_errors

    return len(errors) == 0, errors


def normalize_headers(columns: List[str]) -> List[str]:
    return [str(column).strip() for column in columns]


def ensure_template_columns(dataframe: pd.DataFrame, headers: List[str]) -> pd.DataFrame:
    return dataframe.reindex(columns=headers)


def get_state_key(page_key: str) -> str:
    return f"table_df_{page_key}"


def ensure_state_initialized(page_key: str) -> None:
    state_key = get_state_key(page_key)
    headers = PAGE_CONFIGS[page_key]["headers"]
    if state_key not in st.session_state:
        st.session_state[state_key] = pd.DataFrame(columns=headers)


def render_page_editor(page_key: str) -> None:
    config = PAGE_CONFIGS[page_key]
    headers: List[str] = config["headers"]
    default_filename: str = config["default_filename"]
    state_key = get_state_key(page_key)

    st.title(config["title"])
    st.caption("Upload and edit table variables with strict checks, then export CSV.")

    if page_key == "Plant_Node":
        st.info("IP Address examples: 192.168.1.11, 10.0.0.5")
    elif page_key == "MVJSON_Tags":
        st.info("Source IP is validated as strict IPv4 (for example 192.168.1.10).")

    uploaded_file = st.file_uploader(
        f"Upload source CSV ({page_key})",
        type=["csv"],
        key=f"uploader_{page_key}",
    )

    if uploaded_file is not None:
        try:
            incoming_df = pd.read_csv(uploaded_file, dtype="string").fillna("")
            incoming_headers = normalize_headers(list(incoming_df.columns))
            incoming_df.columns = incoming_headers

            if incoming_headers != headers:
                st.error("Header mismatch. Expected: " + ", ".join(headers))
            else:
                st.session_state[state_key] = to_text_dataframe(
                    ensure_template_columns(incoming_df, headers)
                )
                st.success("CSV loaded.")
        except Exception as exc:
            st.error(f"Unable to load CSV: {exc}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start with empty template", key=f"empty_btn_{page_key}"):
            st.session_state[state_key] = pd.DataFrame(columns=headers)

    with col2:
        if "Index" in headers and st.button("Auto-number Index (1..N)", key=f"autonum_btn_{page_key}"):
            numbered_df = st.session_state[state_key].copy()
            numbered_df["Index"] = [str(i) for i in range(1, len(numbered_df) + 1)]
            st.session_state[state_key] = to_text_dataframe(numbered_df)
            st.rerun()

    edited_df = st.data_editor(
        st.session_state[state_key],
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        key=f"editor_{page_key}",
    )
    st.session_state[state_key] = to_text_dataframe(edited_df)

    is_valid, validation_errors = validate_dataframe(
        st.session_state[state_key],
        integer_columns=config["integer_columns"],
        float_columns=config["float_columns"],
        boolean_columns=config["boolean_columns"],
        interval_columns=config["interval_columns"],
        required_text_columns=config["required_text_columns"],
        ipv4_columns=config["ipv4_columns"],
    )

    st.subheader("Validation")
    if is_valid:
        st.success("All rows passed strict validation.")
    else:
        st.warning("Fix validation issues before downloads.")
        for row_index, row_errors in validation_errors.items():
            st.markdown(f"**Row {row_index + 1}:**")
            for issue in row_errors:
                st.write(f"- {issue}")

    output_buffer = io.StringIO()
    st.session_state[state_key].to_csv(output_buffer, index=False, lineterminator="\n")
    output_csv = output_buffer.getvalue().encode("utf-8")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_stem = default_filename.rsplit(".", 1)[0]

    dcol1, dcol2 = st.columns(2)
    with dcol1:
        st.download_button(
            label="Download CSV",
            data=output_csv,
            file_name=default_filename,
            mime="text/csv",
            disabled=not is_valid,
            key=f"download_default_{page_key}",
        )

    with dcol2:
        st.download_button(
            label="Download CSV (Timestamped)",
            data=output_csv,
            file_name=f"{file_stem}_{ts}.csv",
            mime="text/csv",
            disabled=not is_valid,
            key=f"download_time_{page_key}",
        )


def validate_all_templates() -> Tuple[bool, Dict[str, Dict[int, List[str]]]]:
    all_errors: Dict[str, Dict[int, List[str]]] = {}

    for page_key, config in PAGE_CONFIGS.items():
        state_key = get_state_key(page_key)
        df = to_text_dataframe(st.session_state[state_key])
        is_valid, validation_errors = validate_dataframe(
            df,
            integer_columns=config["integer_columns"],
            float_columns=config["float_columns"],
            boolean_columns=config["boolean_columns"],
            interval_columns=config["interval_columns"],
            required_text_columns=config["required_text_columns"],
            ipv4_columns=config["ipv4_columns"],
        )
        if not is_valid:
            all_errors[page_key] = validation_errors

    return len(all_errors) == 0, all_errors


def build_config_zip_bytes() -> bytes:
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for page_key, config in PAGE_CONFIGS.items():
            state_key = get_state_key(page_key)
            csv_buffer = io.StringIO()
            st.session_state[state_key].to_csv(csv_buffer, index=False, lineterminator="\n")
            zf.writestr(config["default_filename"], csv_buffer.getvalue().encode("utf-8"))

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


for key in TEMPLATE_KEYS:
    ensure_state_initialized(key)

with st.sidebar:
    st.subheader("Version2")
    selected_page = st.selectbox("Select CSV Template", options=TEMPLATE_KEYS, index=0)

render_page_editor(selected_page)

st.divider()
st.subheader("Combined Config Export")
st.caption("Combine all template entries currently in this app and download as Config.zip.")

all_valid, all_errors = validate_all_templates()

if all_valid:
    st.success("All templates are valid. You can download the combined Config zip.")
else:
    st.warning("Some templates contain validation errors. Fix them before zip download.")
    with st.expander("Show template validation errors"):
        for page_key, page_errors in all_errors.items():
            st.markdown(f"**{page_key}**")
            for row_index, row_errors in page_errors.items():
                st.write(f"Row {row_index + 1}")
                for issue in row_errors:
                    st.write(f"- {issue}")

zip_bytes = build_config_zip_bytes()
st.download_button(
    label="Download Config.zip",
    data=zip_bytes,
    file_name="Config.zip",
    mime="application/zip",
    disabled=not all_valid,
    key="download_config_zip",
)
