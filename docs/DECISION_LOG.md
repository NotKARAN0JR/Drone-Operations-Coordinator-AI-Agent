# Decision Log (Updated)

## Key assumptions

1. Source sheets use compact/truncated headers exactly like the screenshots.
2. Placeholder date cells may appear as `########` in exports.
3. Skill/cert/capability fields may be comma-separated strings.

## Trade-offs

- Chose a **schema-normalization layer in coordinator** to map varying sheet headers into canonical internal fields.
- Kept the core deterministic/rule-based for reliability in coordination workflows.

## Urgent reassignment interpretation

For urgent/high-priority projects:
1. Try normal assignment first.
2. If not feasible, preempt a lower-priority active project.
3. Free pilot+drone, move them to urgent project, reopen displaced project.

## With more time

- Preserve original input sheet column layout on write-back while still using canonical internals.
- Add richer natural language command parsing and recommendations.
