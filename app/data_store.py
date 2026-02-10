from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List


class DataStore:
    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)
        self.use_google_sheets = os.getenv("USE_GOOGLE_SHEETS", "false").lower() == "true"
        self.sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Drone Operations")
        self._client = None

        if self.use_google_sheets:
            self._client = self._build_sheets_client()

    def _build_sheets_client(self):
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError as exc:
            raise RuntimeError("Google Sheets dependencies not installed: gspread/google-auth") from exc

        creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not creds_json:
            raise ValueError("USE_GOOGLE_SHEETS=true but GOOGLE_SERVICE_ACCOUNT_JSON not set")

        creds_info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        return gspread.authorize(creds)

    def _read_csv(self, name: str) -> List[Dict[str, Any]]:
        path = self.data_dir / f"{name}.csv"
        with path.open("r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _write_csv(self, name: str, rows: List[Dict[str, Any]]) -> None:
        path = self.data_dir / f"{name}.csv"
        if not rows:
            return
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def _read_sheet(self, worksheet_name: str) -> List[Dict[str, Any]]:
        sheet = self._client.open(self.sheet_name).worksheet(worksheet_name)
        return sheet.get_all_records()

    def _write_sheet(self, worksheet_name: str, rows: List[Dict[str, Any]]) -> None:
        if not rows:
            return
        sheet = self._client.open(self.sheet_name).worksheet(worksheet_name)
        headers = list(rows[0].keys())
        values = [headers] + [[row.get(h, "") for h in headers] for row in rows]
        sheet.clear()
        sheet.update(values)

    def read_table(self, name: str, worksheet_name: str) -> List[Dict[str, Any]]:
        if self.use_google_sheets:
            return self._read_sheet(worksheet_name)
        return self._read_csv(name)

    def write_table(self, name: str, worksheet_name: str, rows: List[Dict[str, Any]]) -> None:
        if self.use_google_sheets:
            self._write_sheet(worksheet_name, rows)
        else:
            self._write_csv(name, rows)
