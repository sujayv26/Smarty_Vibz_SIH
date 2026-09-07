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
class MPPActivity:
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
class MPPRelationship:
    predecessor_activity_id: str
    successor_activity_id: str
    relationship_type: RelationshipType
    lag: int = 0
    lag_unit: str = "days"


@dataclass
class MPPSchedule:
    external_schedule_id: str
    schedule_name: Optional[str] = None
    activities: list[MPPActivity] = field(default_factory=list)
    relationships: list[MPPRelationship] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class MPPParseResult:
    schedule: MPPSchedule
    validation_errors: list[dict] = field(default_factory=list)
    rejected_activities: list[dict] = field(default_factory=list)
    rejected_relationships: list[dict] = field(default_factory=list)


class MPPParseError(Exception):
    def __init__(self, message: str, task_id: str = None):
        self.message = message
        self.task_id = task_id
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        parts = [self.message]
        if self.task_id:
            parts.append(f"task {self.task_id}")
        return " | ".join(parts)


def parse_date_mpp(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        if not value.strip():
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


def parse_relationship_type_mpp(value: str) -> RelationshipType:
    value = value.strip().upper()
    if value in ("FS", "SS", "FF", "SF"):
        return RelationshipType(value)
    return RelationshipType.FS


class MPPParser:
    def __init__(self):
        self._tasks = []
        self._relationships = []
        self._project_info = {}

    def parse(self, file_path: str) -> MPPParseResult:
        try:
            from mpxj import ProjectReader
        except ImportError:
            raise MPPParseError("mpxj library not installed. Install with: pip install mpxj")

        reader = ProjectReader()
        project = reader.read(file_path)

        self._extract_project_info(project)
        self._extract_tasks(project)
        self._extract_relationships(project)

        schedule, rejected_activities, rejected_relationships = self._build_schedule()
        return MPPParseResult(
            schedule=schedule,
            rejected_activities=rejected_activities,
            rejected_relationships=rejected_relationships
        )

    def _extract_project_info(self, project) -> None:
        self._project_info = {
            "project_id": str(project.get_project_id()) if project.get_project_id() else "unknown",
            "schedule_name": project.get_name() or "Imported MPP Schedule",
        }

    def _extract_tasks(self, project) -> None:
        for task in project.get_tasks():
            if task.get_id() is None:
                continue

            activity_id = str(task.get_id())
            activity_code = task.get_name() or activity_id
            activity_name = task.get_name() or ""

            wbs_code = None
            if task.get_wbs():
                wbs_code = str(task.get_wbs())

            discipline = "Unknown"
            if task.get_text1():
                discipline = str(task.get_text1())
            elif task.get_outline_level() is not None:
                if task.get_outline_level() == 1:
                    discipline = "Summary"
                else:
                    discipline = "Task"

            planned_start = parse_date_mpp(task.get_start())
            planned_finish = parse_date_mpp(task.get_finish())

            metadata = {}
            if task.get_duration():
                metadata["duration"] = str(task.get_duration())
            if task.get_actual_start():
                metadata["actual_start"] = str(task.get_actual_start())
            if task.get_actual_finish():
                metadata["actual_finish"] = str(task.get_actual_finish())
            if task.get_percentage_complete() is not None:
                metadata["percent_complete"] = str(task.get_percentage_complete())

            self._tasks.append(MPPActivity(
                activity_id=activity_id,
                activity_code=activity_code,
                activity_name=activity_name,
                discipline=discipline,
                wbs_code=wbs_code,
                planned_start=planned_start,
                planned_finish=planned_finish,
                external_schedule_id=self._project_info["project_id"],
                project_id=self._project_info["project_id"],
                activity_type=discipline,
                metadata=metadata,
            ))

    def _extract_relationships(self, project) -> None:
        for task in project.get_tasks():
            if task.get_id() is None:
                continue
            successor_id = str(task.get_id())

            for rel in task.get_predecessors():
                pred_task = rel.get_predecessor_task()
                if pred_task and pred_task.get_id() is not None:
                    predecessor_id = str(pred_task.get_id())

                    rel_type = RelationshipType.FS
                    if rel.get_type():
                        rel_type_str = str(rel.get_type()).upper()
                        rel_type = parse_relationship_type_mpp(rel_type_str)

                    lag = 0
                    if rel.get_lag():
                        lag_duration = rel.get_lag()
                        if hasattr(lag_duration, 'get_duration'):
                            lag = lag_duration.get_duration() // 86400000  # Convert ms to days

                    self._relationships.append(MPPRelationship(
                        predecessor_activity_id=predecessor_id,
                        successor_activity_id=successor_id,
                        relationship_type=rel_type,
                        lag=lag,
                        lag_unit="days",
                    ))

    def _build_schedule(self):
        external_schedule_id = self._project_info.get("project_id", "unknown")
        schedule_name = self._project_info.get("schedule_name", "Imported MPP Schedule")

        activity_ids = set()
        activities = []
        rejected = []

        for task in self._tasks:
            if task.activity_id in activity_ids:
                rejected.append({
                    "activity_id": task.activity_id,
                    "error": "Duplicate activity ID",
                    "record": {"activity_id": task.activity_id, "activity_name": task.activity_name}
                })
                continue
            activity_ids.add(task.activity_id)
            activities.append(task)

        rejected_rels = []
        relationships = []
        for rel in self._relationships:
            if rel.predecessor_activity_id in activity_ids and rel.successor_activity_id in activity_ids:
                relationships.append(rel)
            else:
                rejected_rels.append({
                    "predecessor": rel.predecessor_activity_id,
                    "successor": rel.successor_activity_id,
                    "error": "Referenced activity not found",
                    "record": {"predecessor": rel.predecessor_activity_id, "successor": rel.successor_activity_id}
                })

        return MPPSchedule(
            external_schedule_id=external_schedule_id,
            schedule_name=schedule_name,
            activities=activities,
            relationships=relationships,
            metadata={"task_count": len(activities), "relationship_count": len(relationships)}
        ), rejected, rejected_rels


def parse_mpp_file(file_path: str) -> MPPParseResult:
    parser = MPPParser()
    return parser.parse(file_path)


def parse_mpp_content(file_bytes: bytes) -> MPPParseResult:
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mpp") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        return parse_mpp_file(tmp_path)
    finally:
        os.unlink(tmp_path)