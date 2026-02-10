# Drone Operations Coordinator AI Agent

Prototype AI coordinator for drone operations with roster management, assignment logic, inventory tracking, conflict detection, and urgent reassignment handling.

## What is implemented

- **Roster management**
  - Query pilots by attributes (in core engine)
  - Update pilot status with write-back persistence
- **Assignment tracking**
  - Match pilots and drones to project requirements
  - Reassignment support through urgent preemption policy
- **Drone inventory**
  - Query drones by capability/status/location
  - Update drone status with write-back persistence
- **Conflict detection**
  - Overlapping pilot bookings
  - Overlapping drone bookings
  - Certification/skill mismatch
  - Drone-maintenance assignment conflict
  - Pilot-drone location mismatch
- **Google Sheets 2-way sync (optional)**
  - Reads all entities from sheets
  - Writes pilot/drone/project updates back to sheets
  - Falls back to local CSV files when Google integration is not enabled

## Project structure

- `app/coordinator.py` - core decision engine
- `app/data_store.py` - Google Sheets + CSV abstraction
- `app/models.py` - domain models
- `run_agent.py` - conversational CLI interface
- `data/*.csv` - sample roster, fleet, projects
- `docs/DECISION_LOG.md` - design rationale and assumptions

## Conversational interface (CLI)

```bash
python run_agent.py
```

Supported commands:
- `find pilots`
- `find drones`
- `detect conflicts`
- `assign <PROJECT_ID>`
- `urgent reassign <PROJECT_ID>`
- `quit`

## Google Sheets setup (optional)

Set environment variables:

- `USE_GOOGLE_SHEETS=true`
- `GOOGLE_SHEET_NAME="Drone Operations"`
- `GOOGLE_SERVICE_ACCOUNT_JSON='<service-account-json>'`

Expected worksheets:
- `Pilot Roster`
- `Drone Fleet`
- `Project Assignments`

## Tests

```bash
pytest -q
```

## Hosted prototype note

Given this execution environment blocks dependency installation/network egress for app frameworks, this submission provides a fully runnable CLI prototype and deployment-ready core logic. The same coordinator module can be wrapped by FastAPI/Streamlit in a hosted environment.
