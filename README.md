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

## How to check the project is working (clear steps)

### 1) Verify required files exist
```bash
python - << 'PYCHECK'
from pathlib import Path
required = [
    'run_agent.py',
    'app/coordinator.py',
    'app/models.py',
    'app/data_store.py',
    'data/pilot_roster.csv',
    'data/drone_fleet.csv',
    'data/project_assignments.csv',
]
missing = [p for p in required if not Path(p).exists()]
print('OK' if not missing else f'Missing: {missing}')
PYCHECK
```
Expected output: `OK`

### 2) Run automated tests
```bash
pytest -q
```
Expected output contains: `3 passed`

### 3) Run a CLI smoke test (non-interactive)
```bash
python run_agent.py << 'EOCMD'
find pilots
find drones
detect conflicts
assign PRJ001
urgent reassign PRJ002
quit
EOCMD
```
Expected behavior:
- Prints pilot/drone lists
- Prints conflict check result
- Returns clear assignment and urgent reassignment messages
- Exits cleanly on `quit`

### 4) Run an interactive check (optional)
```bash
python run_agent.py
```
Then type these commands one by one:
- `find pilots`
- `find drones`
- `detect conflicts`
- `assign PRJ001`
- `urgent reassign PRJ002`
- `quit`

### 5) Validate write-back in CSV mode
After performing actions, inspect persisted rows:
```bash
python - << 'PYCHECK'
import csv
for f in ['data/pilot_roster.csv','data/drone_fleet.csv','data/project_assignments.csv']:
    print('\n==', f, '==')
    with open(f, newline='', encoding='utf-8') as fh:
        for i, row in enumerate(csv.DictReader(fh), start=1):
            if i <= 3:
                print(row)
PYCHECK
```

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

Then run the same CLI checks; updates will write back to Sheets.
