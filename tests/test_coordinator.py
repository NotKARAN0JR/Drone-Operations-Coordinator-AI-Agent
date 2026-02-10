from app.coordinator import DroneOpsCoordinator
from app.data_store import DataStore


def test_detects_conflicts_returns_list():
    coordinator = DroneOpsCoordinator(DataStore("data"))
    conflicts = coordinator.detect_conflicts()
    assert isinstance(conflicts, list)


def test_assign_project_success_or_no_feasible():
    coordinator = DroneOpsCoordinator(DataStore("data"))
    result = coordinator.assign_project("PRJ-102")
    assert "PRJ-102" in result


def test_urgent_reassignment_handles_urgent_project():
    coordinator = DroneOpsCoordinator(DataStore("data"))
    result = coordinator.urgent_reassignment("PRJ-104")
    assert "PRJ-104" in result
