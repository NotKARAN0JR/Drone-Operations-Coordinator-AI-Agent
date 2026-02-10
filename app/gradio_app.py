from __future__ import annotations

import json
import os
from typing import List, Tuple

import gradio as gr

from app.coordinator import DroneOpsCoordinator


# Build a friendly runtime status banner for CSV/Sheets mode.
def _status_banner() -> str:
    use_sheets = os.getenv("USE_GOOGLE_SHEETS", "false").lower() == "true"
    if not use_sheets:
        return "✅ **Mode:** CSV fallback (`USE_GOOGLE_SHEETS=false`)"

    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not raw:
        return "⚠️ **Google Sheets warning:** `USE_GOOGLE_SHEETS=true` but `GOOGLE_SERVICE_ACCOUNT_JSON` is missing."

    try:
        creds = json.loads(raw)
    except json.JSONDecodeError:
        return "❌ **Google Sheets error:** `GOOGLE_SERVICE_ACCOUNT_JSON` is not valid JSON."

    if not isinstance(creds, dict) or "client_email" not in creds:
        return "❌ **Google Sheets error:** JSON is invalid (missing `client_email`)."

    return "✅ **Mode:** Google Sheets enabled and credential JSON looks valid."


# Markdown-friendly result formatting helpers.
def _format_pilots(pilots) -> str:
    if not pilots:
        return "No pilots found."
    return "\n".join(
        f"- **{p.pilot_id}** · {p.name}  \\n  Skill: `{p.skill_level}` · Status: `{p.status}` · Location: `{p.current_location}`"
        for p in pilots
    )


def _format_drones(drones) -> str:
    if not drones:
        return "No drones found."
    return "\n".join(
        f"- **{d.drone_id}** · {d.model}  \\n  Capability: `{d.capabilities}` · Status: `{d.status}` · Location: `{d.location}`"
        for d in drones
    )


def _format_conflicts(conflicts: List[str]) -> str:
    if not conflicts:
        return "No conflicts detected."
    return "\n".join(f"- {item}" for item in conflicts)


def _execute(coordinator: DroneOpsCoordinator, message: str) -> str:
    text = message.strip()
    lower = text.lower()

    if lower == "find pilots":
        return f"### Pilots\n{_format_pilots(coordinator.pilots)}"
    if lower == "find drones":
        return f"### Drones\n{_format_drones(coordinator.drones)}"
    if lower == "detect conflicts":
        return f"### Conflicts\n{_format_conflicts(coordinator.detect_conflicts())}"
    if lower.startswith("assign "):
        project_id = text.split(maxsplit=1)[1].strip().upper()
        msg = coordinator.assign_project(project_id)
        conflicts = coordinator.detect_conflicts()
        return f"### Assignment Result\n{msg}\n\n### Conflicts\n{_format_conflicts(conflicts)}"
    if lower.startswith("urgent reassign "):
        project_id = text.split(maxsplit=2)[2].strip().upper()
        msg = coordinator.urgent_reassignment(project_id)
        conflicts = coordinator.detect_conflicts()
        return f"### Urgent Reassignment Result\n{msg}\n\n### Conflicts\n{_format_conflicts(conflicts)}"

    return (
        "### Supported commands\n"
        "- `find pilots`\n"
        "- `find drones`\n"
        "- `detect conflicts`\n"
        "- `assign <PROJECT_ID>`\n"
        "- `urgent reassign <PROJECT_ID>`"
    )


# Optional local upload helper for service account JSON.
def _apply_uploaded_service_account(file_obj) -> str:
    if file_obj is None:
        return _status_banner()
    try:
        with open(file_obj.name, "r", encoding="utf-8") as fh:
            raw = fh.read().strip()
        json.loads(raw)
        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"] = raw
        return "✅ Uploaded service account JSON loaded for this process."
    except Exception as exc:
        return f"❌ Failed to load uploaded JSON: {exc}"


def _filter_preview(
    coordinator: DroneOpsCoordinator,
    pilot_skill: str,
    pilot_location: str,
    drone_capability: str,
    drone_location: str,
) -> str:
    blocks: List[str] = []

    if pilot_skill or pilot_location:
        pilots = coordinator.query_pilots(skill=pilot_skill or "", location=pilot_location or "")
        blocks.append(f"### Filtered Pilots\n{_format_pilots(pilots)}")

    if drone_capability or drone_location:
        drones = coordinator.query_drones(capability=drone_capability or "", location=drone_location or "")
        blocks.append(f"### Filtered Drones\n{_format_drones(drones)}")

    return "\n\n---\n\n".join(blocks)


def _handle_command(
    command: str,
    pilot_skill: str,
    pilot_location: str,
    drone_capability: str,
    drone_location: str,
) -> Tuple[str, str]:
    try:
        coordinator = DroneOpsCoordinator()
        coordinator.refresh()

        preview = _filter_preview(
            coordinator,
            pilot_skill=(pilot_skill or "").strip(),
            pilot_location=(pilot_location or "").strip(),
            drone_capability=(drone_capability or "").strip(),
            drone_location=(drone_location or "").strip(),
        )

        response = _execute(coordinator, command)
        output = response if not preview else f"{preview}\n\n---\n\n{response}"
        return output, _status_banner()
    except Exception as exc:
        return f"### Error\n`{exc}`", _status_banner()


def _load_filter_options() -> Tuple[List[str], List[str], List[str], List[str]]:
    try:
        coordinator = DroneOpsCoordinator()
        coordinator.refresh()
        pilot_skills = sorted(
            {
                token.strip()
                for p in coordinator.pilots
                for token in p.skill_level.replace("|", ",").split(",")
                if token.strip()
            }
        )
        pilot_locations = sorted({p.current_location for p in coordinator.pilots if p.current_location})
        drone_capabilities = sorted(
            {
                token.strip()
                for d in coordinator.drones
                for token in d.capabilities.replace("|", ",").split(",")
                if token.strip()
            }
        )
        drone_locations = sorted({d.location for d in coordinator.drones if d.location})
        return pilot_skills, pilot_locations, drone_capabilities, drone_locations
    except Exception:
        return [], [], [], []


def build_demo() -> gr.Blocks:
    pilot_skills, pilot_locations, drone_capabilities, drone_locations = _load_filter_options()

    # Gradio theme + light custom CSS for spacing/balance.
    theme = gr.themes.Soft(primary_hue="blue", secondary_hue="emerald")
    css = """
    .app-shell {max-width: 980px; margin: 0 auto; padding: 18px 8px 24px 8px;}
    .app-card {border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px;}
    .app-subtle {color: #475569; margin-top: -6px;}
    """

    with gr.Blocks(theme=theme, css=css, title="Drone Operations Coordinator") as demo:
        with gr.Column(elem_classes=["app-shell"]):
            # Header section (title + status indicator).
            gr.Markdown("## 🚁 Drone Operations Coordinator AI Agent")
            gr.Markdown(
                "Use command mode or quick actions to manage pilots, drones, assignments, and conflicts.",
                elem_classes=["app-subtle"],
            )
            status = gr.Markdown(value=_status_banner(), elem_classes=["app-card"])

            # Primary command input row.
            with gr.Row():
                command = gr.Textbox(
                    label="Command",
                    placeholder="Try: find pilots",
                    info="Supported: find pilots, find drones, detect conflicts, assign <ID>, urgent reassign <ID>",
                    scale=6,
                )
                run_btn = gr.Button("Run", variant="primary", scale=1)

            # Related action buttons grouped together.
            with gr.Row():
                assign_project_id = gr.Textbox(
                    label="Assign Project ID",
                    value="PRJ001",
                    placeholder="Enter project id for assign",
                    info="Used by Assign button",
                    scale=2,
                )
                urgent_project_id = gr.Textbox(
                    label="Urgent Project ID",
                    value="PRJ002",
                    placeholder="Enter project id for urgent reassignment",
                    info="Used by Urgent Reassign button",
                    scale=2,
                )
                quick_assign = gr.Button("Assign", variant="secondary", scale=1)
                quick_urgent = gr.Button("Urgent Reassign", variant="secondary", scale=1)
                quick_detect_conflicts = gr.Button("Detect Conflicts", variant="secondary", scale=1)

            # Advanced filters grouped in an accordion.
            with gr.Accordion("Advanced Filters", open=False):
                with gr.Row():
                    pilot_skill = gr.Dropdown(
                        choices=pilot_skills,
                        label="Pilot Skill",
                        value=None,
                        multiselect=False,
                        allow_custom_value=True,
                        info="Optional pilot skill filter",
                    )
                    pilot_location = gr.Dropdown(
                        choices=pilot_locations,
                        label="Pilot Location",
                        value=None,
                        multiselect=False,
                        allow_custom_value=True,
                        info="Optional pilot location filter",
                    )
                with gr.Row():
                    drone_capability = gr.Dropdown(
                        choices=drone_capabilities,
                        label="Drone Capability",
                        value=None,
                        multiselect=False,
                        allow_custom_value=True,
                        info="Optional drone capability filter",
                    )
                    drone_location = gr.Dropdown(
                        choices=drone_locations,
                        label="Drone Location",
                        value=None,
                        multiselect=False,
                        allow_custom_value=True,
                        info="Optional drone location filter",
                    )

            # Optional credential upload for local testing of Sheets mode.
            with gr.Row():
                upload = gr.File(
                    label="Optional: Upload Google Service Account JSON",
                    file_types=[".json"],
                )
                upload_btn = gr.Button("Load JSON", variant="secondary")

            # Styled markdown output panel.
            output = gr.Markdown(value="### Results\nReady.", elem_classes=["app-card"])

            run_btn.click(
                _handle_command,
                [command, pilot_skill, pilot_location, drone_capability, drone_location],
                [output, status],
            )
            quick_assign.click(
                lambda pid, ps, pl, dc, dl: _handle_command(f"assign {pid}", ps, pl, dc, dl),
                [assign_project_id, pilot_skill, pilot_location, drone_capability, drone_location],
                [output, status],
            )
            quick_urgent.click(
                lambda pid, ps, pl, dc, dl: _handle_command(f"urgent reassign {pid}", ps, pl, dc, dl),
                [urgent_project_id, pilot_skill, pilot_location, drone_capability, drone_location],
                [output, status],
            )
            quick_detect_conflicts.click(
                lambda ps, pl, dc, dl: _handle_command("detect conflicts", ps, pl, dc, dl),
                [pilot_skill, pilot_location, drone_capability, drone_location],
                [output, status],
            )
            upload_btn.click(_apply_uploaded_service_account, [upload], [status])

    return demo


def main() -> None:
    demo = build_demo()
    demo.launch()


if __name__ == "__main__":
    main()
