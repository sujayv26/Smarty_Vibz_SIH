from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from enum import Enum


class RelationshipType(str, Enum):
    FS = "FS"
    SS = "SS"
    FF = "FF"
    SF = "SF"


@dataclass
class XERActivity:
    activity_id: str
    activity_code: str
    activity_name: str
    discipline: Optional[str] = None
    wbs_code: Optional[str] = None
    wbs_name: Optional[str] = None
    planned_start: Optional[date] = None
    planned_finish: Optional[date] = None
    external_schedule_id: Optional[str] = None
    project_id: Optional[str] = None
    activity_type: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class XERRelationship:
    predecessor_activity_id: str
    successor_activity_id: str
    relationship_type: RelationshipType
    lag: int = 0
    lag_unit: str = "days"


@dataclass
class XERSchedule:
    external_schedule_id: str
    schedule_name: Optional[str] = None
    activities: list[XERActivity] = field(default_factory=list)
    relationships: list[XERRelationship] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class XERParseResult:
    schedule: XERSchedule
    validation_errors: list[dict] = field(default_factory=list)
    rejected_activities: list[dict] = field(default_factory=list)
    rejected_relationships: list[dict] = field(default_factory=list)


class XERParseError(Exception):
    def __init__(self, message: str, line_number: int = None, record_type: str = None):
        self.message = message
        self.line_number = line_number
        self.record_type = record_type
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        parts = [self.message]
        if self.line_number:
            parts.append(f"line {self.line_number}")
        if self.record_type:
            parts.append(f"record {self.record_type}")
        return " | ".join(parts)


def parse_date(value: str) -> Optional[date]:
    if not value or value.strip() == "":
        return None
    formats = [
        "%Y-%m-%d",
        "%d-%b-%y",
        "%d-%b-%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_int(value: str) -> int:
    if not value or value.strip() == "":
        return 0
    try:
        return int(value.strip())
    except ValueError:
        return 0


def parse_relationship_type(value: str) -> RelationshipType:
    value = value.strip().upper()
    if value in ("FS", "SS", "FF", "SF"):
        return RelationshipType(value)
    return RelationshipType.FS


class XERParser:
    def __init__(self):
        self._tables: dict[str, list[list[str]]] = {}
        self._table_headers: dict[str, list[str]] = {}
        self._current_table: str = ""
        self._headers: list[str] = []
        self._line_number = 0

    def parse(self, content: str) -> XERParseResult:
        if not content or not content.strip():
            raise XERParseError("Empty XER file")

        lines = content.splitlines()
        self._parse_lines(lines)

        schedule, rejected_activities, rejected_relationships = self._build_schedule()
        return XERParseResult(
            schedule=schedule,
            rejected_activities=rejected_activities,
            rejected_relationships=rejected_relationships
        )

    def _parse_lines(self, lines: list[str]) -> None:
        for self._line_number, line in enumerate(lines, 1):
            line = line.rstrip("\r\n")
            if not line:
                continue

            if line.startswith("%T\t"):
                self._handle_table_header(line)
            elif line.startswith("%F\t"):
                self._handle_field_header(line)
            elif line.startswith("%R\t"):
                self._handle_data_row(line)
            elif line.startswith("%E"):
                break

    def _handle_table_header(self, line: str) -> None:
        parts = line.split("\t")
        if len(parts) < 2:
            return
        self._current_table = parts[1].strip()
        self._tables[self._current_table] = []
        self._headers = []

    def _handle_field_header(self, line: str) -> None:
        parts = line.split("\t")
        if len(parts) < 2:
            return
        self._headers = [h.strip() for h in parts[1:]]
        if self._current_table:
            self._table_headers[self._current_table] = self._headers

    def _handle_data_row(self, line: str) -> None:
        if not self._current_table or not self._headers:
            return
        parts = line.split("\t")
        if len(parts) < 2:
            return
        values = [v.strip() for v in parts[1:]]
        if len(values) != len(self._headers):
            return
        self._tables[self._current_table].append(values)

    def _build_schedule(self) -> XERSchedule:
        project_data = self._tables.get("PROJECT", [])
        wbs_data = self._tables.get("WBS", [])
        activity_data = self._tables.get("TASK", [])
        pred_data = self._tables.get("TASKPRED", [])

        external_schedule_id = ""
        schedule_name = ""
        if project_data:
            proj = project_data[0]
            proj_headers = self._get_headers("PROJECT")
            external_schedule_id = self._get_field(proj, proj_headers, "proj_id") or ""
            schedule_name = self._get_field(proj, proj_headers, "proj_short_name") or ""

        wbs_map = {}
        wbs_headers = self._get_headers("WBS")
        for row in wbs_data:
            wbs_id = self._get_field(row, wbs_headers, "wbs_id")
            wbs_code = self._get_field(row, wbs_headers, "wbs_short_name")
            wbs_name = self._get_field(row, wbs_headers, "wbs_name")
            if wbs_id:
                wbs_map[wbs_id] = (wbs_code, wbs_name)

        activity_headers = self._get_headers("TASK")
        activities = []
        activity_ids = set()
        rejected = []

        for row in activity_data:
            try:
                activity = self._parse_activity(row, activity_headers, wbs_map)
                if activity.activity_id in activity_ids:
                    rejected.append({
                        "activity_id": activity.activity_id,
                        "error": "Duplicate activity ID",
                        "record": self._row_to_dict(row, activity_headers)
                    })
                    continue
                activity_ids.add(activity.activity_id)
                activities.append(activity)
            except Exception as e:
                rejected.append({
                    "activity_id": self._get_field(row, activity_headers, "task_id") or "unknown",
                    "error": str(e),
                    "record": self._row_to_dict(row, activity_headers)
                })

        pred_headers = self._get_headers("TASKPRED")
        relationships = []
        rejected_rels = []
        for row in pred_data:
            try:
                rel = self._parse_relationship(row, pred_headers)
                relationships.append(rel)
            except Exception as e:
                rejected_rels.append({
                    "predecessor": self._get_field(row, pred_headers, "pred_task_id") or "unknown",
                    "successor": self._get_field(row, pred_headers, "task_id") or "unknown",
                    "error": str(e),
                    "record": self._row_to_dict(row, pred_headers)
                })

        return XERSchedule(
            external_schedule_id=external_schedule_id,
            schedule_name=schedule_name,
            activities=activities,
            relationships=relationships,
            metadata={"table_counts": {k: len(v) for k, v in self._tables.items()}}
        ), rejected, rejected_rels

    def _get_headers(self, table: str) -> list[str]:
        return self._table_headers.get(table, [])

    def _get_field(self, row: list[str], headers: list[str], field_name: str) -> Optional[str]:
        if not headers:
            return None
        try:
            idx = headers.index(field_name)
            if idx < len(row):
                return row[idx]
        except ValueError:
            pass
        return None

    def _row_to_dict(self, row: list[str], headers: list[str]) -> dict:
        return {headers[i]: row[i] for i in range(min(len(headers), len(row)))}

    def _parse_activity(self, row: list[str], headers: list[str], wbs_map: dict) -> XERActivity:
        activity_id = self._get_field(row, headers, "task_id")
        if not activity_id:
            raise XERParseError("Missing activity ID (task_id)", self._line_number, "TASK")

        activity_code = self._get_field(row, headers, "task_code") or activity_id
        activity_name = self._get_field(row, headers, "task_name") or ""
        if not activity_name:
            raise XERParseError("Missing activity name (task_name)", self._line_number, "TASK")

        wbs_id = self._get_field(row, headers, "wbs_id")
        wbs_code, wbs_name = wbs_map.get(wbs_id, (None, None)) if wbs_id else (None, None)

        discipline = self._get_field(row, headers, "task_type") or "Unknown"

        planned_start = parse_date(self._get_field(row, headers, "target_start_date") or "")
        planned_finish = parse_date(self._get_field(row, headers, "target_end_date") or "")

        project_id = self._get_field(row, headers, "proj_id")
        activity_type = self._get_field(row, headers, "task_type")

        metadata = {
            "orig_duration": self._get_field(row, headers, "target_drtn_hr_cnt"),
            "remain_duration": self._get_field(row, headers, "remain_drtn_hr_cnt"),
            "actual_start": self._get_field(row, headers, "act_start_date"),
            "actual_finish": self._get_field(row, headers, "act_end_date"),
            "percent_complete": self._get_field(row, headers, "phys_pct_complete"),
            "total_float": self._get_field(row, headers, "total_float_hr_cnt"),
            "free_float": self._get_field(row, headers, "free_float_hr_cnt"),
        }
        metadata = {k: v for k, v in metadata.items() if v}

        return XERActivity(
            activity_id=activity_id,
            activity_code=activity_code,
            activity_name=activity_name,
            discipline=discipline,
            wbs_code=wbs_code,
            wbs_name=wbs_name,
            planned_start=planned_start,
            planned_finish=planned_finish,
            external_schedule_id=project_id,
            project_id=project_id,
            activity_type=activity_type,
            metadata=metadata,
        )

    def _parse_relationship(self, row: list[str], headers: list[str]) -> XERRelationship:
        pred_id = self._get_field(row, headers, "pred_task_id")
        succ_id = self._get_field(row, headers, "task_id")
        if not pred_id or not succ_id:
            raise XERParseError("Missing predecessor or successor ID", self._line_number, "TASKPRED")

        rel_type_str = self._get_field(row, headers, "pred_type") or "FS"
        rel_type = parse_relationship_type(rel_type_str)

        lag_hr = parse_int(self._get_field(row, headers, "lag_hr_cnt") or "0")
        lag = lag_hr // 8 if lag_hr else 0
        lag_unit = "days"

        return XERRelationship(
            predecessor_activity_id=pred_id,
            successor_activity_id=succ_id,
            relationship_type=rel_type,
            lag=lag,
            lag_unit=lag_unit,
        )


def parse_xer_file(file_path: str) -> XERParseResult:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    parser = XERParser()
    return parser.parse(content)


def parse_xer_content(content: str) -> XERParseResult:
    parser = XERParser()
    return parser.parse(content)