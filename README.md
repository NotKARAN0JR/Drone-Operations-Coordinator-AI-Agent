# Drone Operations Coordinator AI Agent

A coordinator agent for drone operations with roster management, assignment tracking, inventory checks, conflict detection, and urgent reassignment.

## Supported data schemas

The loader supports canonical and alias headers from sheet exports.

- Pilot sheet examples:
  - `pilot_id,name,skills,certification,location,status,current_as,available_from`
  - `pilot_id,name,skill_level,certifications,current_location,current_assignment,status,available_from`
- Drone sheet examples:
  - `drone_id,model,capabilitie,status,location,current_as,maintenance_due`
  - `drone_id,model,capabilities,status,location,current_assignment,last_maintenance_date`
- Project sheet examples:
  - `project_id,client,location,required_skill,required_cert,start_date,end_date,priority,status,pilot_id,drone_id`
  - `project_id,project_name,required_skill_level,required_certifications,...`

## Features

- Query pilots and drones
- Detect conflicts (double-booking, skill/cert mismatch, maintenance conflict, location mismatch)
- Assign pilots + drones to projects
- Urgent reassignment with lower-priority preemption
- Google Sheets 2-way sync via environment toggle

## Local run

```bash
pip install -r requirements.txt
python -m app.gradio_app
```

CLI mode is still available:

```bash
python run_agent.py
```

## Quick demo prompts

Use these in the UI command box:

1. `find pilots`
2. `find drones`
3. `detect conflicts`
4. `assign PRJ001`
5. `urgent reassign PRJ002`

## Google Sheets configuration

Environment variables:

- `USE_GOOGLE_SHEETS=true|false`
- `GOOGLE_SHEET_NAME=<your sheet name>`
- `GOOGLE_SERVICE_ACCOUNT_JSON=<full JSON string>`

Expected worksheets:

- `Pilot Roster`
- `Drone Fleet`
- `Project Assignments`

If `USE_GOOGLE_SHEETS=false`, the app uses local CSVs in `data/`.

## Hugging Face Spaces (Gradio) deployment

1. Create a new **Gradio Space** on Hugging Face.
2. Set hardware to **CPU**.
3. Push this repository to the Space.
4. In Space **Settings → Variables and secrets**, add:
   - `USE_GOOGLE_SHEETS=true` (or `false` for CSV mode)
   - `GOOGLE_SHEET_NAME=Drone Operations` (or your sheet name)
5. In **Secrets**, add:
   - `GOOGLE_SERVICE_ACCOUNT_JSON` = full service account JSON value
6. Ensure `app/gradio_app.py` is present; Gradio app launches via Python module entrypoint.

### Suggested Space startup command

```bash
python -m app.gradio_app
```

## Verifying Google Sheets write-back

1. Launch app with `USE_GOOGLE_SHEETS=true` and valid `GOOGLE_SERVICE_ACCOUNT_JSON`.
2. Execute a write action (e.g., `assign PRJ001` or urgent reassignment).
3. Open the source Google Sheet and confirm updated values in pilot/drone/project rows.
4. Re-run `detect conflicts` to verify state consistency.

## Tests

```bash
pytest -q
```
