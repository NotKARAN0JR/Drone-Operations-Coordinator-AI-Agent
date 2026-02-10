from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from app.data_store import DataStore
from app.models import Drone, Pilot, Project

SKILL_ORDER = {"beginner": 1, "intermediate": 2, "expert": 3}


class DroneOpsCoordinator:
    def __init__(self, store: Optional[DataStore] = None) -> None:
        self.store = store or DataStore()
        self.refresh()

    def refresh(self) -> None:
        self.pilots = [Pilot(**row) for row in self.store.read_table("pilot_roster", "Pilot Roster")]
        self.drones = [Drone(**row) for row in self.store.read_table("drone_fleet", "Drone Fleet")]
        self.projects = [
            Project(**row)
            for row in self.store.read_table("project_assignments", "Project Assignments")
        ]

    def _save_pilots(self) -> None:
        self.store.write_table(
            "pilot_roster",
            "Pilot Roster",
            [pilot.to_dict() for pilot in self.pilots],
        )

    def _save_drones(self) -> None:
        self.store.write_table(
            "drone_fleet",
            "Drone Fleet",
            [drone.to_dict() for drone in self.drones],
        )

    def _save_projects(self) -> None:
        self.store.write_table(
            "project_assignments",
            "Project Assignments",
            [proj.to_dict() for proj in self.projects],
        )

    def query_pilots(self, skill: str = "", cert: str = "", location: str = "") -> List[Pilot]:
        pilots = self.pilots
        if skill:
            pilots = [p for p in pilots if p.skill_level.lower() == skill.lower()]
        if cert:
            pilots = [p for p in pilots if cert.lower() in p.certification_set()]
        if location:
            pilots = [p for p in pilots if p.current_location.lower() == location.lower()]
        return pilots

    def query_drones(self, capability: str = "", location: str = "", status: str = "") -> List[Drone]:
        drones = self.drones
        if capability:
            drones = [d for d in drones if capability.lower() in d.capability_set()]
        if location:
            drones = [d for d in drones if d.location.lower() == location.lower()]
        if status:
            drones = [d for d in drones if d.status.lower() == status.lower()]
        return drones

    def update_pilot_status(self, pilot_id: str, status: str) -> str:
        for pilot in self.pilots:
            if pilot.pilot_id == pilot_id:
                pilot.status = status
                self._save_pilots()
                return f"Pilot {pilot_id} status updated to {status}."
        return f"Pilot {pilot_id} not found."

    def update_drone_status(self, drone_id: str, status: str) -> str:
        for drone in self.drones:
            if drone.drone_id == drone_id:
                drone.status = status
                self._save_drones()
                return f"Drone {drone_id} status updated to {status}."
        return f"Drone {drone_id} not found."

    def _dates_overlap(self, s1: date, e1: date, s2: date, e2: date) -> bool:
        return not (e1 < s2 or e2 < s1)

    def detect_conflicts(self) -> List[str]:
        conflicts: List[str] = []

        active_projects = [p for p in self.projects if p.status.lower() in {"active", "open"}]
        for i, p1 in enumerate(active_projects):
            for p2 in active_projects[i + 1 :]:
                if p1.pilot_id and p1.pilot_id == p2.pilot_id and self._dates_overlap(
                    p1.start_date, p1.end_date, p2.start_date, p2.end_date
                ):
                    conflicts.append(
                        f"Double-booked pilot {p1.pilot_id} on {p1.project_id} and {p2.project_id}."
                    )
                if p1.drone_id and p1.drone_id == p2.drone_id and self._dates_overlap(
                    p1.start_date, p1.end_date, p2.start_date, p2.end_date
                ):
                    conflicts.append(
                        f"Double-booked drone {p1.drone_id} on {p1.project_id} and {p2.project_id}."
                    )

        pilot_by_id: Dict[str, Pilot] = {p.pilot_id: p for p in self.pilots}
        drone_by_id: Dict[str, Drone] = {d.drone_id: d for d in self.drones}

        for project in active_projects:
            pilot = pilot_by_id.get(project.pilot_id)
            drone = drone_by_id.get(project.drone_id)

            if pilot:
                if not project.required_cert_set().issubset(pilot.certification_set()):
                    conflicts.append(
                        f"Certification mismatch: {pilot.pilot_id} lacks requirement for {project.project_id}."
                    )
                if SKILL_ORDER.get(pilot.skill_level.lower(), 0) < SKILL_ORDER.get(
                    project.required_skill_level.lower(), 0
                ):
                    conflicts.append(
                        f"Skill mismatch: {pilot.pilot_id} skill too low for {project.project_id}."
                    )

            if drone:
                if drone.status.lower() == "maintenance":
                    conflicts.append(
                        f"Maintenance issue: {drone.drone_id} assigned to {project.project_id} while in maintenance."
                    )
                if not project.required_capability_set().issubset(drone.capability_set()):
                    conflicts.append(
                        f"Capability mismatch: {drone.drone_id} cannot meet {project.project_id} capability requirements."
                    )

            if pilot and drone and pilot.current_location.lower() != drone.location.lower():
                conflicts.append(
                    f"Location mismatch: {pilot.pilot_id} ({pilot.current_location}) and {drone.drone_id} ({drone.location}) for {project.project_id}."
                )

        return conflicts

    def _pilot_is_available_for_project(self, pilot: Pilot, project: Project) -> bool:
        if pilot.status.lower() != "available":
            return False
        if SKILL_ORDER.get(pilot.skill_level.lower(), 0) < SKILL_ORDER.get(
            project.required_skill_level.lower(), 0
        ):
            return False
        if not project.required_cert_set().issubset(pilot.certification_set()):
            return False
        if pilot.current_location.lower() != project.location.lower():
            return False
        for p in self.projects:
            if p.project_id == project.project_id or p.status.lower() != "active" or p.pilot_id != pilot.pilot_id:
                continue
            if self._dates_overlap(project.start_date, project.end_date, p.start_date, p.end_date):
                return False
        return True

    def _drone_is_available_for_project(self, drone: Drone, project: Project) -> bool:
        if drone.status.lower() != "available":
            return False
        if drone.location.lower() != project.location.lower():
            return False
        if not project.required_capability_set().issubset(drone.capability_set()):
            return False
        for p in self.projects:
            if p.project_id == project.project_id or p.status.lower() != "active" or p.drone_id != drone.drone_id:
                continue
            if self._dates_overlap(project.start_date, project.end_date, p.start_date, p.end_date):
                return False
        return True

    def assign_project(self, project_id: str) -> str:
        project = next((p for p in self.projects if p.project_id == project_id), None)
        if not project:
            return f"Project {project_id} not found."

        best_pilot = next((p for p in self.pilots if self._pilot_is_available_for_project(p, project)), None)
        best_drone = next((d for d in self.drones if self._drone_is_available_for_project(d, project)), None)

        if not best_pilot or not best_drone:
            return f"No feasible assignment found for {project_id}."

        project.pilot_id = best_pilot.pilot_id
        project.drone_id = best_drone.drone_id
        project.status = "Active"

        best_pilot.status = "Assigned"
        best_pilot.current_assignment = project_id

        best_drone.status = "Deployed"
        best_drone.current_assignment = project_id

        self._save_projects()
        self._save_pilots()
        self._save_drones()

        return f"Assigned {best_pilot.name} ({best_pilot.pilot_id}) and {best_drone.drone_id} to {project_id}."

    def urgent_reassignment(self, project_id: str) -> str:
        """
        Urgent reassignment interpretation:
        - For urgent/high-priority project, free up resources from lower-priority active projects if needed.
        - Reassign displaced project back to Open.
        """
        project = next((p for p in self.projects if p.project_id == project_id), None)
        if not project:
            return f"Project {project_id} not found."

        direct = self.assign_project(project_id)
        if "Assigned" in direct:
            return f"Urgent reassignment not needed. {direct}"

        priority_rank = {"urgent": 3, "high": 2, "medium": 1, "low": 0}
        target_rank = priority_rank.get(project.priority.lower(), 0)

        if target_rank < 2:
            return f"Project {project_id} is not high/urgent priority; no forced reassignment performed."

        active_projects = sorted(
            [p for p in self.projects if p.status.lower() == "active" and p.project_id != project_id],
            key=lambda x: priority_rank.get(x.priority.lower(), 0),
        )

        for donor in active_projects:
            if priority_rank.get(donor.priority.lower(), 0) >= target_rank:
                continue

            donor_pilot = next((p for p in self.pilots if p.pilot_id == donor.pilot_id), None)
            donor_drone = next((d for d in self.drones if d.drone_id == donor.drone_id), None)
            if not donor_pilot or not donor_drone:
                continue

            donor_pilot.status = "Available"
            donor_pilot.current_assignment = ""
            donor_drone.status = "Available"
            donor_drone.current_assignment = ""
            donor.status = "Open"
            donor.pilot_id = ""
            donor.drone_id = ""

            forced = self.assign_project(project_id)
            if "Assigned" in forced:
                self._save_projects()
                self._save_pilots()
                self._save_drones()
                return (
                    f"Urgent reassignment completed. Moved resources from {donor.project_id} to {project_id}."
                )

        return f"Unable to complete urgent reassignment for {project_id}."
