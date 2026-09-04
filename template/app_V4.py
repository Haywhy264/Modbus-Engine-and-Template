import io
import ipaddress
import os
import posixpath
import re
import socket
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import streamlit as st

try:
    import paramiko
    from scp import SCPClient

    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

st.set_page_config(
    page_title="Table Variable CSV Builder & Box-to-Box Sync - Version 4",
    layout="wide",
    page_icon="📡",
)

# ---------------------------------------------------------------------------
# Template Schemas & Configurations (Full V3 Compatibility)
# ---------------------------------------------------------------------------

PAGE_CONFIGS: Dict[str, dict] = {
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
        "headers": [
            "Index",
            "Name",
            "URL",
            "Interval",
            "Enable",
            "Timeout",
            "Username",
            "Password",
        ],
        "integer_columns": {"Index"},
        "float_columns": set(),
        "boolean_columns": {"Enable"},
        "interval_columns": {"Interval", "Timeout"},
        "required_text_columns": set(),
        "ipv4_columns": set(),
        "default_filename": "WebClient_Destinations.csv",
    },
    "WebClient_Entries": {
        "title": "WebClient Entries CSV Builder",
        "headers": ["Destination Index", "Tag", "Monitor", "Delta"],
        "integer_columns": {"Destination Index", "Tag"},
        "float_columns": set(),
        "boolean_columns": {"Monitor", "Delta"},
        "interval_columns": set(),
        "required_text_columns": set(),
        "ipv4_columns": set(),
        "default_filename": "WebClient_Entries.csv",
    },
    "AncillaryServices": {
        "title": "AncillaryServices CSV Builder",
        "headers": ["Service", "Value"],
        "integer_columns": set(),
        "float_columns": set(),
        "boolean_columns": set(),
        "interval_columns": set(),
        "required_text_columns": set(),
        "ipv4_columns": set(),
        "default_filename": "AncillaryServices.csv",
    },
}

TEMPLATE_KEYS = list(PAGE_CONFIGS.keys())
TEMPLATE_NAME_TO_KEY = {PAGE_CONFIGS[key]["default_filename"]: key for key in TEMPLATE_KEYS}
TEMPLATE_NAMES = list(TEMPLATE_NAME_TO_KEY.keys())
BOOL_VALUES = {"TRUE", "FALSE"}
INTERVAL_PATTERN = re.compile(r"^T#\d+(ms|s|m|h)$", flags=re.IGNORECASE)

# ---------------------------------------------------------------------------
# Dataframe Utilities & Validation
# ---------------------------------------------------------------------------


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


def parse_key_value_csv_text(csv_text: str, headers: List[str]) -> pd.DataFrame:
    raw_df = pd.read_csv(io.StringIO(csv_text), header=None, dtype="string").fillna("")
    values: Dict[str, str] = {}
    for _, row in raw_df.iterrows():
        row_values = [str(item).strip() for item in row.tolist() if str(item).strip()]
        if len(row_values) >= 2:
            values[row_values[0]] = row_values[1]
    data = {header: values.get(header, "") for header in headers}
    return pd.DataFrame([data], columns=headers)


def parse_csv_content(csv_text: str, page_key: str, headers: List[str]) -> pd.DataFrame:
    if page_key in {"JSON_TCP_Servers", "MVJSON_Directory"}:
        return parse_key_value_csv_text(csv_text, headers)

    incoming_df = pd.read_csv(io.StringIO(csv_text), dtype="string").fillna("")
    incoming_headers = normalize_headers(list(incoming_df.columns))
    incoming_df.columns = incoming_headers

    if incoming_headers != headers:
        raise ValueError(
            f"Header mismatch in {PAGE_CONFIGS[page_key]['default_filename']}. "
            f"Expected {len(headers)} columns ({', '.join(headers[:3])}...), "
            f"got {len(incoming_headers)} columns ({', '.join(incoming_headers[:3])}...)"
        )

    return ensure_template_columns(incoming_df, headers)


def parse_uploaded_template(
    uploaded_file: io.BytesIO, page_key: str, headers: List[str]
) -> pd.DataFrame:
    uploaded_file.seek(0)
    csv_text = uploaded_file.read().decode("utf-8", errors="replace")
    return parse_csv_content(csv_text, page_key, headers)


def get_state_key(page_key: str) -> str:
    return f"table_df_{page_key}"


def ensure_state_initialized(page_key: str) -> None:
    state_key = get_state_key(page_key)
    headers = PAGE_CONFIGS[page_key]["headers"]
    if state_key not in st.session_state:
        st.session_state[state_key] = pd.DataFrame(columns=headers)


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


def get_all_template_csv_dict() -> Dict[str, str]:
    """Generates a dict of filename -> CSV string for all 23 templates in session state."""
    csv_dict: Dict[str, str] = {}
    for page_key, config in PAGE_CONFIGS.items():
        state_key = get_state_key(page_key)
        csv_buffer = io.StringIO()
        st.session_state[state_key].to_csv(csv_buffer, index=False, lineterminator="\n")
        csv_dict[config["default_filename"]] = csv_buffer.getvalue()
    return csv_dict


def load_all_template_csv_dict(files_dict: Dict[str, str]) -> Tuple[int, List[str], List[str]]:
    """Loads a dictionary of filename -> CSV content into session_state tables."""
    loaded_count = 0
    loaded_files: List[str] = []
    skipped_files: List[str] = []

    for filename, content in files_dict.items():
        clean_name = posixpath.basename(filename.strip())
        if clean_name in TEMPLATE_NAME_TO_KEY:
            page_key = TEMPLATE_NAME_TO_KEY[clean_name]
            config = PAGE_CONFIGS[page_key]
            try:
                parsed_df = parse_csv_content(content, page_key, config["headers"])
                st.session_state[get_state_key(page_key)] = to_text_dataframe(parsed_df)
                loaded_count += 1
                loaded_files.append(f"{clean_name} ({len(parsed_df)} rows)")
            except Exception as e:
                skipped_files.append(f"{clean_name}: {e}")
        else:
            skipped_files.append(f"{clean_name} (unknown template)")

    return loaded_count, loaded_files, skipped_files


def build_config_zip_bytes() -> bytes:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        csv_dict = get_all_template_csv_dict()
        for filename, content in csv_dict.items():
            zf.writestr(filename, content.encode("utf-8"))
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


# ---------------------------------------------------------------------------
# SSH & SCP Controller Bridge Client
# ---------------------------------------------------------------------------


class ControllerSSHBridge:
    """Handles SSH connection, SFTP/SCP directory transfers, and remote commands."""

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "root",
        password: Optional[str] = None,
        key_content: Optional[str] = None,
        timeout: int = 8,
    ):
        self.host = host.strip()
        self.port = int(port)
        self.username = username.strip()
        self.password = password.strip() if password else None
        self.key_content = key_content.strip() if key_content else None
        self.timeout = timeout
        self.client: Optional[paramiko.SSHClient] = None

    def connect(self) -> paramiko.SSHClient:
        if not PARAMIKO_AVAILABLE:
            raise RuntimeError(
                "Paramiko / SCP libraries are not installed. Install via `pip install paramiko scp`."
            )

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        pkey = None
        if self.key_content:
            key_file = io.StringIO(self.key_content)
            for pkey_cls in (
                paramiko.RSAKey,
                paramiko.Ed25519Key,
                paramiko.ECDSAKey,
                paramiko.DSSKey,
            ):
                try:
                    key_file.seek(0)
                    pkey = pkey_cls.from_private_key(key_file, password=self.password)
                    break
                except Exception:
                    continue
            if pkey is None:
                raise ValueError("Could not parse the provided private SSH key.")

        client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password if not pkey else None,
            pkey=pkey,
            timeout=self.timeout,
            banner_timeout=self.timeout,
            auth_timeout=self.timeout,
            look_for_keys=False,
            allow_agent=False,
        )
        self.client = client
        return client

    def close(self) -> None:
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

    def test_connection(
        self, remote_dir: Optional[str] = None
    ) -> Tuple[bool, str, List[str], List[str]]:
        """Tests SSH connection and optionally inspects remote config directory contents."""
        try:
            client = self.connect()
            transport = client.get_transport()
            banner = transport.get_banner() if transport else "Connected"

            csv_files: List[str] = []
            all_files: List[str] = []

            if remote_dir:
                clean_dir = remote_dir.strip().rstrip("/")
                sftp = client.open_sftp()
                try:
                    entries = sftp.listdir(clean_dir)
                    all_files = sorted(entries)
                    csv_files = [f for f in all_files if f.lower().endswith(".csv")]
                except IOError as err:
                    return (
                        True,
                        f"SSH connected successfully, but remote directory '{clean_dir}' could not be listed: {err}",
                        [],
                        [],
                    )
                finally:
                    sftp.close()

            return True, f"Connection to {self.host}:{self.port} succeeded.", csv_files, all_files
        except socket.timeout:
            return False, f"Connection timed out connecting to {self.host}:{self.port}.", [], []
        except paramiko.AuthenticationException:
            return (
                False,
                f"Authentication failed for user '{self.username}' on {self.host}.",
                [],
                [],
            )
        except Exception as exc:
            return False, f"Connection error: {exc}", [], []
        finally:
            self.close()

    def pull_config_folder(self, remote_dir: str) -> Tuple[bool, str, Dict[str, str]]:
        """Pulls all CSV files found in the remote directory into memory."""
        files_dict: Dict[str, str] = {}
        clean_dir = remote_dir.strip().rstrip("/")

        try:
            client = self.connect()
            sftp = client.open_sftp()
            try:
                entries = sftp.listdir(clean_dir)
                csv_entries = [f for f in entries if f.lower().endswith(".csv")]

                if not csv_entries:
                    return (
                        False,
                        f"Connected, but no .csv files were found in remote directory '{clean_dir}'.",
                        {},
                    )

                for file_name in csv_entries:
                    remote_file_path = f"{clean_dir}/{file_name}"
                    with sftp.open(remote_file_path, "r") as remote_file:
                        content_bytes = remote_file.read()
                        text_content = content_bytes.decode("utf-8", errors="replace")
                        files_dict[file_name] = text_content

                return (
                    True,
                    f"Successfully pulled {len(files_dict)} CSV config files from '{clean_dir}'.",
                    files_dict,
                )
            finally:
                sftp.close()
        except Exception as exc:
            return False, f"Failed to pull config folder from {self.host}: {exc}", {}
        finally:
            self.close()

    def push_config_folder(
        self,
        remote_dir: str,
        files_dict: Dict[str, str],
        create_dir: bool = True,
        backup_first: bool = True,
        post_command: Optional[str] = None,
    ) -> Tuple[bool, str, List[str]]:
        """Pushes CSV files to the target controller via SFTP / SCP, with optional backup and post-command."""
        clean_dir = remote_dir.strip().rstrip("/")
        transfer_logs: List[str] = []

        try:
            client = self.connect()

            # Ensure remote directory exists
            if create_dir:
                mkdir_cmd = f"mkdir -p {clean_dir}"
                stdin, stdout, stderr = client.exec_command(mkdir_cmd)
                exit_code = stdout.channel.recv_exit_status()
                if exit_code != 0:
                    err_msg = stderr.read().decode("utf-8", errors="replace").strip()
                    transfer_logs.append(
                        f"⚠️ Warning creating remote directory '{clean_dir}': {err_msg}"
                    )
                else:
                    transfer_logs.append(
                        f"✓ Ensured remote directory '{clean_dir}' exists on target."
                    )

            # Optional remote backup before overwriting
            if backup_first:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_tar = f"{clean_dir}_backup_{ts}.tar.gz"
                backup_cmd = (
                    f"if [ -d {clean_dir} ]; then tar -czf {backup_tar} -C {clean_dir} . 2>/dev/null || true; fi"
                )
                stdin, stdout, stderr = client.exec_command(backup_cmd)
                stdout.channel.recv_exit_status()
                transfer_logs.append(
                    f"✓ Remote backup created if folder had prior files: {backup_tar}"
                )

            # Transfer files via SFTP
            sftp = client.open_sftp()
            try:
                for filename, content in files_dict.items():
                    remote_file_path = f"{clean_dir}/{filename}"
                    with sftp.open(remote_file_path, "w") as remote_file:
                        remote_file.write(content.encode("utf-8"))
                    transfer_logs.append(
                        f"✓ Transferred {filename} ({len(content.splitlines())} lines)"
                    )
            finally:
                sftp.close()

            # Optional Post-Transfer Command
            if post_command and post_command.strip():
                clean_post_cmd = post_command.strip()
                transfer_logs.append(f"Executing post-transfer command: `{clean_post_cmd}`...")
                stdin, stdout, stderr = client.exec_command(clean_post_cmd, timeout=15)
                cmd_exit = stdout.channel.recv_exit_status()
                out_txt = stdout.read().decode("utf-8", errors="replace").strip()
                err_txt = stderr.read().decode("utf-8", errors="replace").strip()
                if cmd_exit == 0:
                    transfer_logs.append(
                        f"✓ Post-transfer command completed successfully: {out_txt or 'OK'}"
                    )
                else:
                    transfer_logs.append(
                        f"⚠️ Post-transfer command returned code {cmd_exit}: {err_txt or out_txt}"
                    )

            return (
                True,
                f"Successfully pushed {len(files_dict)} config files to {self.host}:{clean_dir}",
                transfer_logs,
            )
        except Exception as exc:
            transfer_logs.append(f"❌ Error during push: {exc}")
            return False, f"Failed to push config folder to {self.host}: {exc}", transfer_logs
        finally:
            self.close()

    def run_remote_command(self, cmd: str) -> Tuple[int, str, str]:
        """Executes a one-off command on the controller and returns (exit_code, stdout, stderr)."""
        try:
            client = self.connect()
            stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
            exit_code = stdout.channel.recv_exit_status()
            out_txt = stdout.read().decode("utf-8", errors="replace")
            err_txt = stderr.read().decode("utf-8", errors="replace")
            return exit_code, out_txt, err_txt
        except Exception as exc:
            return -1, "", str(exc)
        finally:
            self.close()


# ---------------------------------------------------------------------------
# Streamlit Session State Initialization
# ---------------------------------------------------------------------------

for key in TEMPLATE_KEYS:
    ensure_state_initialized(key)

if "audit_logs" not in st.session_state:
    st.session_state["audit_logs"] = []

if "source_config_summary" not in st.session_state:
    st.session_state["source_config_summary"] = None

if "target_config_summary" not in st.session_state:
    st.session_state["target_config_summary"] = None


def add_audit_log(entry: str) -> None:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["audit_logs"].insert(0, f"[{now_str}] {entry}")


# ---------------------------------------------------------------------------
# UI View 1: Template CSV Editor (V3 Core Feature)
# ---------------------------------------------------------------------------


def render_page_editor(page_key: str) -> None:
    config = PAGE_CONFIGS[page_key]
    headers: List[str] = config["headers"]
    default_filename: str = config["default_filename"]
    state_key = get_state_key(page_key)

    st.subheader(f"📝 {config['title']}")
    st.caption(
        f"File: `{default_filename}` • Total columns: {len(headers)} • Current rows: {len(st.session_state[state_key])}"
    )

    if page_key == "Plant_Node":
        st.info("💡 IP Address examples: `192.168.1.11`, `10.0.0.5`")
    elif page_key == "MVJSON_Tags":
        st.info("💡 Source IP is validated as strict IPv4 (for example `192.168.1.10`).")

    ucol1, ucol2 = st.columns([2, 1])
    with ucol1:
        uploaded_file = st.file_uploader(
            f"Upload replacement CSV for `{default_filename}`",
            type=["csv"],
            key=f"uploader_{page_key}",
        )
        if uploaded_file is not None:
            try:
                incoming_df = parse_uploaded_template(uploaded_file, page_key, headers)
                st.session_state[state_key] = to_text_dataframe(incoming_df)
                st.success(f"Loaded {len(incoming_df)} rows from {uploaded_file.name}")
                add_audit_log(f"Uploaded {uploaded_file.name} ({len(incoming_df)} rows)")
            except Exception as exc:
                st.error(f"Unable to load CSV: {exc}")

    with ucol2:
        st.write(" ")
        st.write(" ")
        if st.button("🗑️ Reset to Empty Table", key=f"empty_btn_{page_key}"):
            st.session_state[state_key] = pd.DataFrame(columns=headers)
            st.rerun()

    if "Index" in headers:
        if st.button(
            "🔢 Auto-number Index (1..N)",
            key=f"autonum_btn_{page_key}",
            help="Sequentially fills the Index column starting from 1 to N",
        ):
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

    st.markdown("#### Validation Status")
    if is_valid:
        st.success("✅ All rows passed strict validation.")
    else:
        st.warning("⚠️ Validation issues found. Please fix them before downloading or deploying.")
        with st.expander(f"View {len(validation_errors)} row error(s)", expanded=True):
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
            label=f"💾 Download {default_filename}",
            data=output_csv,
            file_name=default_filename,
            mime="text/csv",
            disabled=not is_valid,
            key=f"download_default_{page_key}",
        )

    with dcol2:
        st.download_button(
            label=f"🕒 Download Timestamped ({file_stem}_{ts}.csv)",
            data=output_csv,
            file_name=f"{file_stem}_{ts}.csv",
            mime="text/csv",
            disabled=not is_valid,
            key=f"download_time_{page_key}",
        )


# ---------------------------------------------------------------------------
# UI View 2: Box-to-Box Communication & Transfer (SSH / SCP)
# ---------------------------------------------------------------------------


def render_box_to_box_view() -> None:
    st.title("📡 Box-to-Box Controller Communication")
    st.markdown(
        """
        Seamlessly copy the **Config folder** from a **Source Controller** via SSH/SCP/SFTP,
        review & edit all 23 template tables directly in this web app,
        and deploy the updated configuration to a **Target Controller**.
        """
    )

    if not PARAMIKO_AVAILABLE:
        st.error(
            "⚠️ Missing required libraries `paramiko` or `scp`. Please install them via: `pip install paramiko scp`."
        )

    # Overview Pipeline Card
    all_valid, all_errors = validate_all_templates()
    total_rows = sum(len(st.session_state[get_state_key(k)]) for k in TEMPLATE_KEYS)
    non_empty_templates = sum(
        1 for k in TEMPLATE_KEYS if len(st.session_state[get_state_key(k)]) > 0
    )

    pcol1, pcol2, pcol3 = st.columns(3)
    with pcol1:
        st.metric(label="📦 Active Config Tables", value=f"{non_empty_templates} / 23 loaded")
    with pcol2:
        st.metric(label="📊 Total Tag/Server Rows", value=f"{total_rows} rows")
    with pcol3:
        if all_valid:
            st.metric(label="🛡️ Global Validation", value="PASSED", delta="Ready to Deploy")
        else:
            st.metric(
                label="🛡️ Global Validation",
                value=f"{len(all_errors)} Errors",
                delta="Fix before Deploy",
                delta_color="inverse",
            )

    st.divider()

    # Two Main Controller Columns: Source (Pull) & Target (Push)
    col_source, col_target = st.columns(2)

    # ------------------ SOURCE CONTROLLER (PULL) ------------------
    with col_source:
        st.markdown("### 📥 1. Source Controller (Pull Config)")
        st.caption("Read and copy the active config directory from the existing controller.")

        src_host = st.text_input(
            "Source Host / IP",
            value="192.168.1.100",
            key="src_host",
            help="IP address or hostname of the source box",
        )
        s_c1, s_c2 = st.columns([1, 2])
        with s_c1:
            src_port = st.number_input(
                "SSH Port", value=22, min_value=1, max_value=65535, key="src_port"
            )
        with s_c2:
            src_user = st.text_input("Username", value="root", key="src_user")

        src_auth_mode = st.radio(
            "Authentication Method",
            options=["Password", "Private Key"],
            horizontal=True,
            key="src_auth_mode",
        )

        src_password = None
        src_key = None
        if src_auth_mode == "Password":
            src_password = st.text_input(
                "Password", type="password", key="src_password", placeholder="Enter SSH password"
            )
        else:
            src_key_file = st.file_uploader(
                "Upload SSH Private Key", key="src_key_file", type=["pem", "key", "id_rsa", "txt"]
            )
            if src_key_file is not None:
                src_key = src_key_file.read().decode("utf-8", errors="replace")
            else:
                src_key = st.text_area(
                    "Or Paste Private Key",
                    key="src_key_text",
                    placeholder="-----BEGIN OPENSSH PRIVATE KEY----- ...",
                )

        src_dir = st.text_input(
            "Remote Config Directory Path",
            value="/opt/config",
            key="src_dir",
            help="Path where CSV config files are located on the source controller (e.g., /opt/config or /home/root/config)",
        )

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button(
                "🔍 Test Source Connection", key="btn_test_src", use_container_width=True
            ):
                with st.spinner("Connecting to Source Controller..."):
                    bridge = ControllerSSHBridge(
                        host=src_host,
                        port=int(src_port),
                        username=src_user,
                        password=src_password,
                        key_content=src_key,
                    )
                    success, msg, csv_list, all_list = bridge.test_connection(remote_dir=src_dir)
                    if success:
                        st.success(f"✅ {msg}")
                        if csv_list:
                            st.info(
                                f"Found {len(csv_list)} CSV files in `{src_dir}`: {', '.join(csv_list)}"
                            )
                        else:
                            st.warning(f"Connected, but no .csv files found in `{src_dir}`.")
                    else:
                        st.error(f"❌ {msg}")

        with bcol2:
            if st.button(
                "📥 Pull Config from Source",
                key="btn_pull_src",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner(f"Pulling config files from {src_host}:{src_dir}..."):
                    bridge = ControllerSSHBridge(
                        host=src_host,
                        port=int(src_port),
                        username=src_user,
                        password=src_password,
                        key_content=src_key,
                    )
                    success, msg, pulled_files = bridge.pull_config_folder(src_dir)
                    if success and pulled_files:
                        loaded_count, loaded_names, skipped = load_all_template_csv_dict(
                            pulled_files
                        )
                        st.success(
                            f"✅ Successfully pulled and loaded {loaded_count} matching templates into the web app!"
                        )
                        add_audit_log(
                            f"Pulled {loaded_count} config CSVs from Source Controller ({src_host}:{src_dir})"
                        )
                        st.session_state["source_config_summary"] = {
                            "host": src_host,
                            "dir": src_dir,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "loaded": loaded_names,
                            "skipped": skipped,
                        }
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        if st.session_state.get("source_config_summary"):
            summary = st.session_state["source_config_summary"]
            with st.expander(
                f"ℹ️ Last Pulled from {summary['host']} at {summary['time']}", expanded=False
            ):
                st.write("**Loaded Templates:**")
                for item in summary["loaded"]:
                    st.write(f"- {item}")
                if summary["skipped"]:
                    st.write("**Unmapped/Skipped Files:**")
                    for item in summary["skipped"]:
                        st.write(f"- {item}")

    # ------------------ TARGET CONTROLLER (PUSH) ------------------
    with col_target:
        st.markdown("### 🚀 2. Target Controller (Push Config)")
        st.caption("Deploy the verified in-memory configuration to the destination controller.")

        tgt_host = st.text_input(
            "Target Host / IP",
            value="192.168.1.101",
            key="tgt_host",
            help="IP address or hostname of the destination box",
        )
        t_c1, t_c2 = st.columns([1, 2])
        with t_c1:
            tgt_port = st.number_input(
                "SSH Port", value=22, min_value=1, max_value=65535, key="tgt_port"
            )
        with t_c2:
            tgt_user = st.text_input("Username", value="root", key="tgt_user")

        tgt_auth_mode = st.radio(
            "Authentication Method",
            options=["Password", "Private Key"],
            horizontal=True,
            key="tgt_auth_mode",
        )

        tgt_password = None
        tgt_key = None
        if tgt_auth_mode == "Password":
            tgt_password = st.text_input(
                "Password", type="password", key="tgt_password", placeholder="Enter SSH password"
            )
        else:
            tgt_key_file = st.file_uploader(
                "Upload SSH Private Key", key="tgt_key_file", type=["pem", "key", "id_rsa", "txt"]
            )
            if tgt_key_file is not None:
                tgt_key = tgt_key_file.read().decode("utf-8", errors="replace")
            else:
                tgt_key = st.text_area(
                    "Or Paste Private Key",
                    key="tgt_key_text",
                    placeholder="-----BEGIN OPENSSH PRIVATE KEY----- ...",
                )

        tgt_dir = st.text_input(
            "Remote Destination Directory Path",
            value="/opt/config",
            key="tgt_dir",
            help="Destination folder on target controller",
        )

        with st.expander("⚙️ Deployment Safety & Post-Transfer Actions", expanded=False):
            backup_target = st.checkbox(
                "Backup remote directory on target before overwriting",
                value=True,
                help="Creates a timestamped .tar.gz archive in the parent directory before writing new CSV files",
            )
            require_valid = st.checkbox(
                "Enforce strict validation check before pushing",
                value=True,
                help="Blocks transfer if any table has validation errors",
            )
            post_command = st.text_input(
                "Post-Transfer SSH Command (Optional)",
                value="systemctl restart modbus-engine 2>/dev/null || true",
                help="Shell command executed on target controller after files are uploaded (e.g. reload service)",
            )

        tbcol1, tbcol2 = st.columns(2)
        with tbcol1:
            if st.button(
                "🔍 Test Target Connection", key="btn_test_tgt", use_container_width=True
            ):
                with st.spinner("Connecting to Target Controller..."):
                    bridge = ControllerSSHBridge(
                        host=tgt_host,
                        port=int(tgt_port),
                        username=tgt_user,
                        password=tgt_password,
                        key_content=tgt_key,
                    )
                    success, msg, csv_list, all_list = bridge.test_connection(remote_dir=tgt_dir)
                    if success:
                        st.success(f"✅ {msg}")
                        if all_list:
                            st.info(
                                f"Remote folder `{tgt_dir}` currently has {len(all_list)} items."
                            )
                        else:
                            st.info(
                                f"Connected! Remote directory `{tgt_dir}` will be created upon push if it does not exist."
                            )
                    else:
                        st.error(f"❌ {msg}")

        with tbcol2:
            if st.button(
                "🚀 Push Config to Target",
                key="btn_push_tgt",
                type="primary",
                use_container_width=True,
            ):
                if require_valid and not all_valid:
                    st.error(
                        "❌ Push blocked: Some templates contain validation errors! Fix them or uncheck 'Enforce strict validation'."
                    )
                else:
                    with st.spinner(f"Pushing config files to {tgt_host}:{tgt_dir}..."):
                        csv_dict = get_all_template_csv_dict()
                        bridge = ControllerSSHBridge(
                            host=tgt_host,
                            port=int(tgt_port),
                            username=tgt_user,
                            password=tgt_password,
                            key_content=tgt_key,
                        )
                        success, msg, logs = bridge.push_config_folder(
                            remote_dir=tgt_dir,
                            files_dict=csv_dict,
                            create_dir=True,
                            backup_first=backup_target,
                            post_command=post_command if post_command else None,
                        )
                        if success:
                            st.success(f"✅ {msg}")
                            add_audit_log(
                                f"Pushed {len(csv_dict)} CSVs to Target Controller ({tgt_host}:{tgt_dir})"
                            )
                            st.session_state["target_config_summary"] = {
                                "host": tgt_host,
                                "dir": tgt_dir,
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "logs": logs,
                            }
                        else:
                            st.error(f"❌ {msg}")

                        with st.expander("Transfer Log Details", expanded=True):
                            for log in logs:
                                st.write(log)

    st.divider()

    # ------------------ REMOTE SSH DIAGNOSTIC TERMINAL ------------------
    with st.expander("🛠️ Remote Diagnostic Commands (Execute on Controller)", expanded=False):
        st.caption(
            "Run ad-hoc inspection commands on either controller (e.g. `ls -la /opt/config`, `systemctl status modbus-engine`, `uptime`)"
        )
        diag_col1, diag_col2 = st.columns([1, 3])
        with diag_col1:
            diag_target = st.selectbox(
                "Target Controller", options=["Source Box", "Target Box"], key="diag_target_box"
            )
        with diag_col2:
            diag_cmd = st.text_input(
                "Command to Execute",
                value="ls -la /opt/config",
                key="diag_cmd_input",
                placeholder="e.g. ls -la /opt/config",
            )

        if st.button("▶️ Execute Command", key="btn_run_diag"):
            is_src = diag_target == "Source Box"
            h = src_host if is_src else tgt_host
            p = src_port if is_src else tgt_port
            u = src_user if is_src else tgt_user
            pwd = src_password if is_src else tgt_password
            k = src_key if is_src else tgt_key

            with st.spinner(f"Executing `{diag_cmd}` on {h}..."):
                bridge = ControllerSSHBridge(
                    host=h, port=int(p), username=u, password=pwd, key_content=k
                )
                code, out, err = bridge.run_remote_command(diag_cmd)
                st.markdown(f"**Exit Code:** `{code}`")
                if out:
                    st.code(out, language="bash")
                if err:
                    st.error(f"STDERR:\n{err}")

    # Activity / Audit Log
    st.subheader("📜 Activity & Transfer History")
    if st.session_state["audit_logs"]:
        for log in st.session_state["audit_logs"][:15]:
            st.text(log)
    else:
        st.caption("No transfers recorded in this session yet.")


# ---------------------------------------------------------------------------
# UI View 3: Batch Config & ZIP Hub
# ---------------------------------------------------------------------------


def render_batch_overview_view() -> None:
    st.title("📦 All Configs Overview & Batch Manager")
    st.caption(
        "Inspect all 23 CSV templates simultaneously, import/export full config bundles, or check global validation."
    )

    all_valid, all_errors = validate_all_templates()

    # Summary table of all 23 templates
    summary_data = []
    for key in TEMPLATE_KEYS:
        cfg = PAGE_CONFIGS[key]
        state_key = get_state_key(key)
        df = st.session_state[state_key]
        is_val, errs = validate_dataframe(
            to_text_dataframe(df),
            integer_columns=cfg["integer_columns"],
            float_columns=cfg["float_columns"],
            boolean_columns=cfg["boolean_columns"],
            interval_columns=cfg["interval_columns"],
            required_text_columns=cfg["required_text_columns"],
            ipv4_columns=cfg["ipv4_columns"],
        )
        summary_data.append(
            {
                "CSV Filename": cfg["default_filename"],
                "Template Key": key,
                "Rows": len(df),
                "Columns": len(cfg["headers"]),
                "Status": "✅ VALID" if is_val else f"⚠️ {len(errs)} invalid row(s)",
            }
        )

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, width="stretch", hide_index=True)

    if not all_valid:
        with st.expander("🔍 Detailed Validation Errors across all templates", expanded=True):
            for pkey, perrs in all_errors.items():
                st.markdown(f"**{PAGE_CONFIGS[pkey]['default_filename']} ({pkey}):**")
                for row_idx, r_errors in perrs.items():
                    st.write(f"- Row {row_idx + 1}: {', '.join(r_errors)}")

    st.divider()

    # Bulk Zip Import & Export
    st.subheader("Combined Config Zip Bundle")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📤 Export Config.zip")
        st.write("Generates a single ZIP archive containing all 23 template CSV files.")
        zip_bytes = build_config_zip_bytes()
        st.download_button(
            label="💾 Download Config.zip",
            data=zip_bytes,
            file_name="Config.zip",
            mime="application/zip",
            disabled=not all_valid,
            key="btn_download_zip_batch",
            use_container_width=True,
        )
        if not all_valid:
            st.warning("Fix validation errors above to enable Config.zip download.")

    with col2:
        st.markdown("#### 📥 Import Config.zip")
        st.write("Upload a `Config.zip` bundle to populate all 23 template tables at once.")
        zip_upload = st.file_uploader("Upload Config.zip", type=["zip"], key="zip_batch_uploader")
        if zip_upload is not None:
            if st.button("Apply ZIP to Session Tables", key="btn_apply_zip"):
                try:
                    with zipfile.ZipFile(zip_upload, "r") as zf:
                        zip_files_dict = {}
                        for zinfo in zf.infolist():
                            if not zinfo.is_dir() and zinfo.filename.lower().endswith(".csv"):
                                with zf.open(zinfo.filename) as zf_file:
                                    zip_files_dict[zinfo.filename] = zf_file.read().decode(
                                        "utf-8", errors="replace"
                                    )

                        loaded_cnt, loaded_names, skipped = load_all_template_csv_dict(
                            zip_files_dict
                        )
                        st.success(f"Loaded {loaded_cnt} template files from ZIP!")
                        add_audit_log(f"Imported {loaded_cnt} files from uploaded ZIP")
                        st.rerun()
                except Exception as exc:
                    st.error(f"Failed to extract and parse ZIP: {exc}")


# ---------------------------------------------------------------------------
# Sidebar Navigation & Main App Router
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("⚙️ Modbus Engine Config")
    st.caption("Version 4 • Box-to-Box SSH/SCP & Template Editor")

    app_mode = st.radio(
        "Navigation Mode",
        options=[
            "📡 Box-to-Box Transfer (SSH/SCP)",
            "📝 Single Template Editor",
            "📦 All Configs & ZIP Hub",
        ],
        index=0,
    )

    st.divider()

    if app_mode == "📝 Single Template Editor":
        st.subheader("Select Template")
        selected_template_name = st.selectbox(
            "CSV Template File", options=TEMPLATE_NAMES, index=0, key="sb_template_select"
        )
        selected_page = TEMPLATE_NAME_TO_KEY[selected_template_name]
    else:
        st.subheader("Quick Switch to Editor")
        quick_template_name = st.selectbox(
            "Jump to Template CSV",
            options=TEMPLATE_NAMES,
            index=0,
            key="sb_quick_template_select",
        )
        if st.button("Open in Editor", use_container_width=True):
            st.session_state["nav_to_editor"] = quick_template_name

if st.session_state.get("nav_to_editor"):
    target_tpl = st.session_state.pop("nav_to_editor")
    selected_page = TEMPLATE_NAME_TO_KEY[target_tpl]
    render_page_editor(selected_page)
elif app_mode == "📡 Box-to-Box Transfer (SSH/SCP)":
    render_box_to_box_view()
elif app_mode == "📝 Single Template Editor":
    render_page_editor(selected_page)
elif app_mode == "📦 All Configs & ZIP Hub":
    render_batch_overview_view()
