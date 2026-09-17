# Site Configuration Tool (V6)

This application is the current browser-based configuration manager for the project. It combines CSV template editing, validation, ZIP bundle handling, and secure SSH/SFTP box-to-box transfers into a single Streamlit workflow.

## Overview

`template/app_V6.py` is the active app entry point. It lets a user:
- edit each CSV template in a browser using `st.data_editor`
- keep header schemas locked to the expected format
- validate each template with strict type and format rules
- download individual CSV files or timestamped versions
- export a single `Config.zip` bundle for the full configuration set
- import a previously exported ZIP bundle back into the app
- pull a remote config folder from a source controller
- review and edit all templates in-session
- push the final file set to a target controller

## Latest V6 functionality

- Streamlit app runs in browser mode with a local and network URL
- Browser access is enabled with:

```powershell
cd "C:\Users\ayomide.adesiyan\OneDrive - Endeco-Technologies\Documents\PYTHON_WORK\Modbus Engine and Template"
.\.venv\Scripts\Activate.ps1
python -m streamlit run template/app_V6.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

- Open the app in a browser at:
  - `http://localhost:8501`
  - `http://<machine-ip>:8501`

- Template validation includes:
  - integer checks
  - float/number checks
  - boolean checks (`TRUE`/`FALSE`)
  - interval format validation (`T#<number><ms|s|m|h>`)
  - required text checks
  - strict IPv4 validation for relevant fields

- Template status is visible in the selector and indicates whether a file is:
  - not uploaded
  - validated
  - needs validation

- Each file can optionally bypass a blocking validation rule for the active session while the validation check remains active in the background.

- The source controller step pulls all CSV files from a remote folder, keeps the raw content in session state, and preserves those files for deployment.

- The target push step now includes all pulled files in the transfer payload, even when the files are empty, unvalidated, or not matched to a template in the current editor state.

- Remote deployment supports:
  - password auth or private-key auth
  - directory creation
  - optional backup before overwrite
  - optional post-transfer command execution

## Project structure

- `template/app_V6.py` – active V6 application
- `template/assets/` – branding and images
- `tests/` – regression tests for simulator and app behavior
- `V6_PROCESS.md` – implementation notes and release history

## Quick start

1. Activate the virtual environment.
2. Install dependencies if needed:

```powershell
pip install -r requirements.txt
```

3. Launch V6:

```powershell
python -m streamlit run template/app_V6.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

4. Open the Local URL or Network URL shown by Streamlit.
5. Use the Box-to-Box panel to pull from source and push to target.

## Important latest fix

A recent update fixed a deployment gap: previously, the push list could omit files that had been pulled but were not currently editable in the app or were still considered invalid. The current logic merges the last pulled CSV payload with the active session tables before sending the file set to the target controller, ensuring all pulled files are transferred.
