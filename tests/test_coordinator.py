from __future__ import annotations

from copy import deepcopy

from app.coordinator import DroneOpsCoordinator


class FakeStore:
    def __init__(self, pilots, drones, projects):
        self.tables = {
            "pilot_roster": deepcopy(pilots),
            "drone_fleet": deepcopy(drones),
            "project_assignments": deepcopy(projects),
        }

    def read_table(self, name: str, worksheet_name: str):
        return deepcopy(self.tables[name])

    def write_table(self, name: str, worksheet_name: str, rows):
        self.tables[name] = deepcopy(rows)


def _base_rows():
    pilots = [
        {
            "pilot_id": "P1",
            "name": "A",
            "skills": "Mapping",
            "certification": "DGCA",
            "location": "Bangalore",
            "status": "Available",
            "current_as": "",
            "available_from": "2026-02-10",
        },
        {
            "pilot_id": "P2",
            "name": "B",
            "skills": "Inspection",
            "certification": "DGCA",
            "location": "Mumbai",
            "status": "Available",
            "current_as": "",
            "available_from": "2026-02-10",
        },
    ]

    drones = [
        {
            "drone_id": "D1",
            "model": "M300",
            "capabilitie": "Thermal,RGB",
            "status": "Available",
            "location": "Bangalore",
            "current_as": "",
            "maintenance_due": "2026-03-01",
        },
        {
            "drone_id": "D2",
            "model": "Mavic",
            "capabilitie": "Inspection",
            "status": "Available",
            "location": "Mumbai",
            "current_as": "",
            "maintenance_due": "2026-03-01",
        },
    ]

    projects = [
        {
            "project_id": "PRJ1",
            "client": "Client A",
            "location": "Bangalore",
            "required_skill": "Mapping",
            "required_cert": "DGCA",
            "start_date": "2026-02-12",
            "end_date": "2026-02-13",
            "priority": "High",
            "status": "Open",
            "pilot_id": "",
            "drone_id": "",
        }
    ]
    return pilots, drones, projects


def test_assign_project_success():
    pilots, drones, projects = _base_rows()
    coordinator = DroneOpsCoordinator(FakeStore(pilots, drones, projects))

    result = coordinator.assign_project("PRJ1")

    assert "Assigned" in result
    assigned = next(p for p in coordinator.projects if p.project_id == "PRJ1")
    assert assigned.pilot_id == "P1"
    assert assigned.drone_id == "D1"


def test_detects_double_booking_and_location_mismatch():
    pilots, drones, projects = _base_rows()
    projects = [
        {
            "project_id": "PRA",
            "client": "A",
            "location": "Bangalore",
            "required_skill": "Mapping",
            "required_cert": "DGCA",
            "start_date": "2026-02-12",
            "end_date": "2026-02-14",
            "priority": "High",
            "status": "Active",
            "pilot_id": "P1",
            "drone_id": "D1",
        },
        {
            "project_id": "PRB",
            "client": "B",
            "location": "Mumbai",
            "required_skill": "Mapping",
            "required_cert": "DGCA",
            "start_date": "2026-02-13",
            "end_date": "2026-02-15",
            "priority": "High",
            "status": "Active",
            "pilot_id": "P1",
            "drone_id": "D1",
        },
    ]
    drones[0]["location"] = "Mumbai"

    coordinator = DroneOpsCoordinator(FakeStore(pilots, drones, projects))
    conflicts = coordinator.detect_conflicts()

    assert any("Double-booked pilot P1" in c for c in conflicts)
    assert any("Double-booked drone D1" in c for c in conflicts)
    assert any("Location mismatch" in c for c in conflicts)


def test_detects_certification_mismatch_and_maintenance_issue():
    pilots, drones, projects = _base_rows()
    pilots[0]["certification"] = "DGCA"
    drones[0]["status"] = "Maintenance"
    projects[0]["required_cert"] = "DGCA,NightOps"
    projects[0]["status"] = "Active"
    projects[0]["pilot_id"] = "P1"
    projects[0]["drone_id"] = "D1"

    coordinator = DroneOpsCoordinator(FakeStore(pilots, drones, projects))
    conflicts = coordinator.detect_conflicts()

    assert any("Certification mismatch" in c for c in conflicts)
    assert any("Maintenance issue" in c for c in conflicts)


def test_urgent_reassignment_forces_preemption_from_lower_priority():
    pilots, drones, projects = _base_rows()

    pilots = [
        {
            "pilot_id": "P1",
            "name": "A",
            "skills": "Mapping",
            "certification": "DGCA",
            "location": "Bangalore",
            "status": "Assigned",
            "current_as": "LOW1",
            "available_from": "2026-02-10",
        }
    ]

    drones = [
        {
            "drone_id": "D1",
            "model": "M300",
            "capabilitie": "Thermal,RGB",
            "status": "Deployed",
            "location": "Bangalore",
            "current_as": "LOW1",
            "maintenance_due": "2026-03-01",
        }
    ]

    projects = [
        {
            "project_id": "LOW1",
            "client": "Routine",
            "location": "Bangalore",
            "required_skill": "Mapping",
            "required_cert": "DGCA",
            "start_date": "2026-02-10",
            "end_date": "2026-02-15",
            "priority": "Low",
            "status": "Active",
            "pilot_id": "P1",
            "drone_id": "D1",
        },
        {
            "project_id": "URG1",
            "client": "Emergency",
            "location": "Bangalore",
            "required_skill": "Mapping",
            "required_cert": "DGCA",
            "start_date": "2026-02-11",
            "end_date": "2026-02-12",
            "priority": "Urgent",
            "status": "Open",
            "pilot_id": "",
            "drone_id": "",
        },
    ]

    coordinator = DroneOpsCoordinator(FakeStore(pilots, drones, projects))
    result = coordinator.urgent_reassignment("URG1")

    assert "Urgent reassignment completed" in result
    urgent = next(p for p in coordinator.projects if p.project_id == "URG1")
    donor = next(p for p in coordinator.projects if p.project_id == "LOW1")
    assert urgent.status == "Active"
    assert urgent.pilot_id == "P1"
    assert donor.status == "Open"
