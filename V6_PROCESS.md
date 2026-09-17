# Version 6 Implementation Process and Current Scope

## Goal
The V6 release keeps the configuration editor, validation logic, ZIP workflow, and SSH/SCP deployment flow, while adding a stronger browser-based operating model and a fix for deployment completeness.

## Current V6 features

### 1. Browser-first configuration workflow
- The app is a Streamlit web application served at a local and network URL.
- It can be run with:

```powershell
python -m streamlit run template/app_V6.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

- Browser access is available on:
  - `http://localhost:8501`
  - `http://<machine-ip>:8501`

### 2. Template editing with schema locking
- All template CSV files remain schema-locked to the expected column names and order.
- The editor supports `st.data_editor` editing in the browser.
- Each page has strict validation rules for integers, floats, booleans, intervals, required text, and IPv4 addresses where required.

### 3. Validation and status UX
- The selector displays file-state labels such as:
  - `Not uploaded`
  - `Validated`
  - `Needs validation`
- Each template row can be checked against the validation logic in the editor.
- The workaround ignore toggle suppresses a blocking validation requirement per file while keeping actual validation active in the session.

### 4. ZIP bundle import/export
- The app can export a full `Config.zip` bundle containing all template CSV files.
- It can also import a previously generated ZIP bundle and restore the full set of templates into the app.

### 5. Source pull and target push communication
- The Source Controller section connects over SSH/SFTP and pulls the remote config folder into the browser session.
- The Target Controller section deploys that configuration to a remote directory using SSH/SFTP.
- Supported actions include:
  - password or private-key auth
  - remote directory creation
  - optional backup before overwrite
  - optional post-transfer command execution

### 6. Full pushed-file coverage
This was the key release fix:
- pulled files are stored in memory and merged with the active session tables before push
- every pulled file is included in the deployment payload, even if it is:
  - empty
  - unvalidated
  - not yet uploaded into the UI
  - not mapped to a visible template page

This prevents a situation where a valid remote file is discovered but silently missing from the final push-set.

## Implementation history

### Phase 1: Preserve the base functionality
- Kept the CSV template engine, validation framework, ZIP bundle tooling, and controller bridge.
- Preserved the original V5/V4 capabilities without rewriting the underlying logic.

### Phase 2: Browser experience and version refinement
- Updated the version label and app branding to reflect V6.
- Added clearer template status labels and layout improvements.
- Kept the session-level validation workflow understandable and visible.

### Phase 3: Deployment-completeness fix
- Identified that pulled files were not always being merged into the effective push payload.
- Implemented a merge layer for the last pulled CSV payload and in-memory template dictionaries.
- Added a regression test to lock that behavior in place.

## Validation performed
- Syntax and import checks were used to validate the updated app module.
- A focused regression test was run for the push behavior.
- Result: `1 passed`.

## Notes
- The active app is `template/app_V6.py`.
- This release is focused on operational reliability, browser usability, and making sure remote config data is not dropped during the push step.
