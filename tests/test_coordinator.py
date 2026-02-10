from pathlib import Path
import shutil

from app.coordinator import DroneOpsCoordinator
from app.data_store import DataStore


def _sandboxed_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    shutil.copytree("data", data_dir)
    return data_dir


def test_loads_alias_csv_schema(tmp_path):
    coordinator = DroneOpsCoordinator(DataStore(str(_sandboxed_data_dir(tmp_path))))
    assert coordinator.pilots[0].pilot_id == "P001"
    assert coordinator.drones[0].drone_id == "D001"
    assert coordinator.projects[0].project_id == "PRJ001"


def test_assign_project_with_alias_schema(tmp_path):
    coordinator = DroneOpsCoordinator(DataStore(str(_sandboxed_data_dir(tmp_path))))
    result = coordinator.assign_project("PRJ001")
    assert "PRJ001" in result


def test_urgent_reassignment_with_urgent_priority(tmp_path):
    coordinator = DroneOpsCoordinator(DataStore(str(_sandboxed_data_dir(tmp_path))))
    result = coordinator.urgent_reassignment("PRJ002")
    assert "PRJ002" in result
