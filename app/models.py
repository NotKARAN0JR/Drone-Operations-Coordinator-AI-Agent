from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


@dataclass
class Pilot:
    pilot_id: str
    name: str
    skill_level: str
    certifications: str
    drone_experience: str
    current_location: str
    current_assignment: str = ""
    status: str = "Available"
    available_from: date = field(default_factory=date.today)

    def __post_init__(self):
        self.available_from = _parse_date(self.available_from)

    def certification_set(self) -> set[str]:
        return {c.strip().lower() for c in self.certifications.split("|") if c.strip()}

    def to_dict(self) -> Dict[str, str]:
        d = asdict(self)
        d["available_from"] = self.available_from.isoformat()
        return d


@dataclass
class Drone:
    drone_id: str
    model: str
    serial_number: str
    capabilities: str
    current_assignment: str = ""
    status: str = "Available"
    location: str = ""
    last_maintenance_date: date = field(default_factory=date.today)

    def __post_init__(self):
        self.last_maintenance_date = _parse_date(self.last_maintenance_date)

    def capability_set(self) -> set[str]:
        return {c.strip().lower() for c in self.capabilities.split("|") if c.strip()}

    def to_dict(self) -> Dict[str, str]:
        d = asdict(self)
        d["last_maintenance_date"] = self.last_maintenance_date.isoformat()
        return d


@dataclass
class Project:
    project_id: str
    project_name: str
    required_skill_level: str
    required_certifications: str
    required_drone_capabilities: str
    location: str
    start_date: date
    end_date: date
    pilot_id: str = ""
    drone_id: str = ""
    priority: str = "Medium"
    status: str = "Open"

    def __post_init__(self):
        self.start_date = _parse_date(self.start_date)
        self.end_date = _parse_date(self.end_date)

    def required_cert_set(self) -> set[str]:
        return {cert.strip().lower() for cert in self.required_certifications.split("|") if cert.strip()}

    def required_capability_set(self) -> set[str]:
        return {cap.strip().lower() for cap in self.required_drone_capabilities.split("|") if cap.strip()}

    def to_dict(self) -> Dict[str, str]:
        d = asdict(self)
        d["start_date"] = self.start_date.isoformat()
        d["end_date"] = self.end_date.isoformat()
        return d


@dataclass
class StatusUpdateRequest:
    pilot_id: Optional[str] = None
    drone_id: Optional[str] = None
    status: str = ""


@dataclass
class ChatRequest:
    message: str


@dataclass
class ChatResponse:
    response: str
    conflicts: List[str] = field(default_factory=list)
