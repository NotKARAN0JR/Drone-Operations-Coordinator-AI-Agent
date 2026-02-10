from __future__ import annotations

import json
import os
from typing import List, Tuple

import gradio as gr

from app.coordinator import DroneOpsCoordinator


def _status_banner() -> str:
    use_sheets = os.getenv("USE_GOOGLE_SHEETS", "false").lower() == "true"
    if not use_sheets:
        return "✅ Running in CSV fallback mode (`USE_GOOGLE_SHEETS=false`)."

    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not raw:
        return "⚠️ `USE_GOOGLE_SHEETS=true` but `GOOGLE_SERVICE_ACCOUNT_JSON` is missing."

    try:
        creds = json.loads(raw)
    except json.JSONDecodeError:
        return "❌ `GOOGLE_SERVICE_ACCOUNT_JSON` is not valid JSON."

    if not isinstance(creds, dict) or "client_email" not in creds:
        return "❌ `GOOGLE_SERVICE_ACCOUNT_JSON` is invalid (missing `client_email`)."

    return "✅ Google Sheets mode enabled and service-account JSON appears valid."


def _format_pilots(pilots) -> str:
    if not pilots:
        return "No pilots found."
    return "\n".join(
        f"- {p.pilot_id}: {p.name} | skill={p.skill_level} | status={p.status} | location={p.current_location}"
        for p in pilots
    )


def _format_drones(drones) -> str:
    if not drones:
        return "No drones found."
    return "\n".join(
        f"- {d.drone_id}: {d.model} | capability={d.capabilities} | status={d.status} | location={d.location}"
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
        return _format_pilots(coordinator.pilots)
    if lower == "find drones":
        return _format_drones(coordinator.drones)
    if lower == "detect conflicts":
        return _format_conflicts(coordinator.detect_conflicts())
    if lower.startswith("assign "):
        project_id = text.split(maxsplit=1)[1].strip().upper()
        msg = coordinator.assign_project(project_id)
        conflicts = coordinator.detect_conflicts()
        return f"{msg}\n\nConflicts:\n{_format_conflicts(conflicts)}"
    if lower.startswith("urgent reassign "):
        project_id = text.split(maxsplit=2)[2].strip().upper()
        msg = coordinator.urgent_reassignment(project_id)
        conflicts = coordinator.detect_conflicts()
        return f"{msg}\n\nConflicts:\n{_format_conflicts(conflicts)}"

    return (
        "Supported commands:\n"
        "- find pilots\n"
        "- find drones\n"
        "- detect conflicts\n"
        "- assign <PROJECT_ID>\n"
        "- urgent reassign <PROJECT_ID>"
    )


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


def _handle_command(command: str, filter_type: str, filter_value: str) -> Tuple[str, str]:
    try:
        coordinator = DroneOpsCoordinator()
        coordinator.refresh()

        cleaned_filter_value = (filter_value or "").strip()
        if cleaned_filter_value:
            if filter_type == "Pilot Skill":
                filtered = coordinator.query_pilots(skill=cleaned_filter_value)
                preview = f"Pilot filter results ({filter_type}={cleaned_filter_value}):\n{_format_pilots(filtered)}"
            elif filter_type == "Pilot Location":
                filtered = coordinator.query_pilots(location=cleaned_filter_value)
                preview = f"Pilot filter results ({filter_type}={cleaned_filter_value}):\n{_format_pilots(filtered)}"
            elif filter_type == "Drone Capability":
                filtered = coordinator.query_drones(capability=cleaned_filter_value)
                preview = f"Drone filter results ({filter_type}={cleaned_filter_value}):\n{_format_drones(filtered)}"
            else:
                filtered = coordinator.query_drones(location=cleaned_filter_value)
                preview = f"Drone filter results ({filter_type}={cleaned_filter_value}):\n{_format_drones(filtered)}"
        else:
            preview = ""

        response = _execute(coordinator, command)
        console = response if not preview else f"{preview}\n\n---\n\n{response}"
        return console, _status_banner()
    except Exception as exc:
        return f"Error: {exc}", _status_banner()


def build_demo() -> gr.Blocks:
    with gr.Blocks(theme=gr.themes.Soft(), title="Drone Operations Coordinator") as demo:
        gr.Markdown("## Drone Operations Coordinator AI Agent")
        status = gr.Markdown(value=_status_banner())

        with gr.Row():
            command = gr.Textbox(
                label="Command",
                placeholder="find pilots | find drones | detect conflicts | assign PRJ001 | urgent reassign PRJ002",
                scale=5,
            )
            run_btn = gr.Button("Run", variant="primary", scale=1)

        with gr.Row():
            quick_find_pilots = gr.Button("Find Pilots")
            quick_find_drones = gr.Button("Find Drones")
            quick_detect_conflicts = gr.Button("Detect Conflicts")

        with gr.Row():
            assign_project_id = gr.Textbox(label="Project ID for Assign", value="PRJ001")
            urgent_project_id = gr.Textbox(label="Project ID for Urgent Reassign", value="PRJ002")
            quick_assign = gr.Button("Assign")
            quick_urgent = gr.Button("Urgent Reassign")

        with gr.Row():
            filter_type = gr.Dropdown(
                choices=["Pilot Skill", "Pilot Location", "Drone Capability", "Drone Location"],
                value="Pilot Skill",
                label="Optional Filter",
            )
            filter_value = gr.Textbox(label="Filter Value", placeholder="e.g., Mapping, Bangalore, Thermal")

        upload = gr.File(label="Optional: Upload Google Service Account JSON", file_types=[".json"])
        upload_btn = gr.Button("Load JSON")

        console = gr.Textbox(label="Results", lines=18)

        run_btn.click(_handle_command, [command, filter_type, filter_value], [console, status])

        quick_find_pilots.click(
            lambda ft, fv: _handle_command("find pilots", ft, fv),
            [filter_type, filter_value],
            [console, status],
        )
        quick_find_drones.click(
            lambda ft, fv: _handle_command("find drones", ft, fv),
            [filter_type, filter_value],
            [console, status],
        )
        quick_detect_conflicts.click(
            lambda ft, fv: _handle_command("detect conflicts", ft, fv),
            [filter_type, filter_value],
            [console, status],
        )

        quick_assign.click(
            lambda pid, ft, fv: _handle_command(f"assign {pid}", ft, fv),
            [assign_project_id, filter_type, filter_value],
            [console, status],
        )
        quick_urgent.click(
            lambda pid, ft, fv: _handle_command(f"urgent reassign {pid}", ft, fv),
            [urgent_project_id, filter_type, filter_value],
            [console, status],
        )

        upload_btn.click(_apply_uploaded_service_account, [upload], [status])

    return demo


def main() -> None:
    demo = build_demo()
    demo.launch()


if __name__ == "__main__":
    main()
