# Decision Log (Drone Operations Coordinator AI Agent)

## 1) Key Assumptions

1. **Data model extension allowed**: I added a third sheet/table (`Project Assignments`) because assignment and overlap logic require explicit date ranges and requirement fields.
2. **Google Sheets auth model**: I assumed a service account credential payload can be provided in an environment variable (`GOOGLE_SERVICE_ACCOUNT_JSON`).
3. **Single-sheet per entity**: Pilot, drone, and project data each map to one worksheet (or one CSV fallback file).
4. **Location matching policy**: I treated pilot-drone-project location mismatch as a conflict instead of auto-allowing relocation.
5. **Skill hierarchy**: `Beginner < Intermediate < Expert`.

## 2) Trade-offs and Why

- **CLI-first interface with framework-agnostic core instead of heavy web stack**
  - Chosen for reliability in constrained environments and speed in 6 hours.
  - Keeps coordinator logic testable and portable to hosted wrappers.
- **Rule-based conversational commands instead of free-form NLU**
  - Delivers deterministic handling for coordinator-critical actions (assign, status updates, conflict checks).
- **CSV fallback layer**
  - Guarantees local execution and testability when Google credentials aren’t available.
- **Synchronous reads/writes**
  - Simpler implementation; adequate for prototype throughput.

## 3) What I’d Do with More Time

1. Add richer intent parsing with tool-calling LLM orchestration.
2. Introduce transactional assignment planning (simulate before commit).
3. Add audit/event log and undo operations.
4. Improve conflict severity ranking and mitigation suggestions.
5. Add map-based proximity checks rather than exact location matching.
6. Add automated deployment pipeline and production observability.

## 4) Interpretation of “Urgent Reassignments”

I implemented urgent reassignment as:

- First attempt normal assignment.
- If no feasible resources and project priority is `High`/`Urgent`, preempt lower-priority active projects.
- Freed pilot/drone are reassigned to urgent project.
- Displaced project is reopened (`status=Open`) and can be re-planned.

This mirrors real operations where emergency missions can preempt routine work while preserving traceability of displaced assignments.
