# Drone Operations Coordinator AI Agent

This implementation is updated to work with the **actual CSV/Google Sheet schema** shown in your screenshots:

- `pilot_roster`: `pilot_id,name,skills,certification,location,status,current_as,available_from`
- `drone_fleet`: `drone_id,model,capabilitie,status,location,current_as,maintenance_due`
- `project_assignments`: `project_id,client,location,required_skill,required_cert,start_date,end_date,priority,status,pilot_id,drone_id`

## What the agent does

- Roster queries + pilot status updates (write-back sync)
- Assignment matching using skill/cert/location/capability/date overlap checks
- Drone inventory checks + drone status updates
- Conflict detection for:
  - pilot double-booking
  - drone double-booking
  - missing certification
  - skill mismatch
  - drone in maintenance
  - pilot-drone location mismatch
- Urgent reassignment preemption for `High`/`Urgent` projects

## Important robustness fixes

- Handles placeholder dates like `########` (falls back safely)
- Handles comma-delimited fields (`"DGCA,NightOps"`, `"Thermal,RGB"`)
- Accepts alias/truncated column names from sheet exports

## Run CLI

```bash
python run_agent.py
```

Commands:
- `find pilots`
- `find drones`
- `detect conflicts`
- `assign <PROJECT_ID>`
- `urgent reassign <PROJECT_ID>`
- `quit`

## Google Sheets 2-way sync (optional)

Set:
- `USE_GOOGLE_SHEETS=true`
- `GOOGLE_SHEET_NAME="Drone Operations"`
- `GOOGLE_SERVICE_ACCOUNT_JSON='<service-account-json>'`

Worksheets:
- `Pilot Roster`
- `Drone Fleet`
- `Project Assignments`

## Tests

```bash
pytest -q
```
