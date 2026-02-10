# Decision Log — Drone Operations Coordinator AI Agent

## Scope and assumptions

1. **Schema variability is expected**: Pilot, drone, and project sheets can have alias/truncated column names from exports (e.g., `skills` vs `skill_level`, `capabilitie` vs `capabilities`). The coordinator normalizes these fields into canonical internal models.
2. **Date fields may be dirty**: Inputs can contain ISO dates, common regional formats, Excel serial numbers, or placeholders like `########`. The parser treats invalid placeholders safely and falls back to a valid date object.
3. **Priority semantics**: `Urgent > High > Medium/Standard > Low`. Urgent reassignment logic only forces preemption when target project is High/Urgent.
4. **Operational status semantics**:
   - Pilot availability: only `Available` is assignable.
   - Drone availability: only `Available` is assignable.
   - `Maintenance` drones are non-assignable and conflict if assigned.

## Trade-offs

### 1) CLI + Gradio UI vs full agent stack
- Kept existing CLI behavior intact and added a minimal Gradio hosted demo.
- Chosen to preserve current APIs while adding a lightweight web entrypoint suitable for Hugging Face Spaces.

### 2) Greedy assignment vs global optimization
- Current assignment uses a deterministic greedy first-feasible match.
- This is fast and simple for prototype behavior but not globally optimal across many concurrent projects.

### 3) Google Sheets vs DB backend
- Kept existing `DataStore` model with environment-toggled Google Sheets and CSV fallback.
- Advantage: low ops overhead and easy evaluator setup.
- Limitation: no ACID transactions or concurrent write coordination.

### 4) Conflict detection style
- Explicit rule checks for required edge cases: overlap, cert mismatch, maintenance conflict, location mismatch.
- Chosen for predictable outputs and testability rather than opaque model-based reasoning.

## Interpretation of “urgent reassignments”

Implemented as a policy workflow:
1. Attempt normal assignment first.
2. If no feasible match and project is High/Urgent, iterate lower-priority active projects as donors.
3. Free donor pilot/drone, mark donor project back to `Open`, and retry assignment.
4. If assignment still fails, return a failure message.

### Safety and rollback notes
- Current implementation performs controlled preemption and writes through existing save methods.
- If reassignment fails after preemption attempt, no invalid assignment is forced.
- Future hardening should include transactional rollback snapshots to guarantee atomicity across pilot/drone/project tables.

## Hosted demo decisions (Hugging Face Spaces)

- Added `app/gradio_app.py` using `gr.Blocks` with:
  - chat-like command box,
  - quick action buttons,
  - optional filter controls,
  - process-local JSON upload for service account testing,
  - Sheets runtime status banner when env vars are missing/invalid.
- UI calls `coordinator.refresh()` before each action to capture external changes.

## What I would do next with more time

1. Add optimization-based assignment (MILP/CP-SAT) for fleet-wide scheduling quality.
2. Add calendar integration (Google Calendar) to make overlap checks authoritative.
3. Add transactionality/version checks for multi-table writes and concurrent edits.
4. Preserve original sheet column layouts during write-back while retaining canonical internals.
5. Add structured audit log (who/what/when) and one-click rollback for operations safety.
6. Add richer conversational intent parsing with constrained tool-use for natural language inputs.
