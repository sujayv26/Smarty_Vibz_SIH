from typing import Optional
from sqlalchemy.orm import Session
from app.services.xer.parser import (
    XERParser,
    parse_xer_content,
    XERParseResult,
    XERSchedule,
    XERActivity,
    XERRelationship,
    XERParseError,
    RelationshipType,
)
from app.models.schedule import ScheduleActivity
from app.models.xer import ScheduleRelationship, ExternalSchedule


class ScheduleImportService:
    def __init__(self, db: Session, organization_id: int = None, project_id: int = None):
        self.db = db
        self.organization_id = organization_id
        self.project_id = project_id

    def import_schedule(self, parse_result, source_filename: str, source_format: str = "XER") -> dict:
        schedule = parse_result.schedule
        external_schedule = self._create_external_schedule(schedule, source_filename, source_format)
        self.db.add(external_schedule)
        self.db.flush()

        imported_count = 0
        rejected_activities = []
        activity_id_map = {}

        for activity_data in schedule.activities:
            try:
                activity = self._import_activity(external_schedule.id, activity_data, source_format)
                if activity:
                    activity_id_map[activity_data.activity_id] = activity.id
                    imported_count += 1
            except Exception as e:
                rejected_activities.append({
                    "activity_id": activity_data.activity_id,
                    "activity_code": activity_data.activity_code,
                    "error": str(e)
                })

        relationship_count = 0
        rejected_relationships = []
        for rel_data in schedule.relationships:
            try:
                pred_id = activity_id_map.get(rel_data.predecessor_activity_id)
                succ_id = activity_id_map.get(rel_data.successor_activity_id)
                if pred_id and succ_id:
                    if pred_id == succ_id:
                        rejected_relationships.append({
                            "predecessor": rel_data.predecessor_activity_id,
                            "successor": rel_data.successor_activity_id,
                            "error": "Self-referencing relationship not allowed"
                        })
                        continue
                    self._import_relationship(external_schedule.id, pred_id, succ_id, rel_data)
                    relationship_count += 1
                else:
                    rejected_relationships.append({
                        "predecessor": rel_data.predecessor_activity_id,
                        "successor": rel_data.successor_activity_id,
                        "error": "Referenced activity not found"
                    })
            except Exception as e:
                rejected_relationships.append({
                    "predecessor": rel_data.predecessor_activity_id,
                    "successor": rel_data.successor_activity_id,
                    "error": str(e)
                })

        self.db.commit()

        return {
            "source_format": source_format,
            "source_filename": source_filename,
            "external_schedule_id": external_schedule.external_schedule_id,
            "external_schedule_name": external_schedule.schedule_name,
            "internal_schedule_id": external_schedule.id,
            "imported_activity_count": imported_count,
            "rejected_activity_count": len(rejected_activities),
            "rejected_activities": rejected_activities,
            "imported_relationship_count": relationship_count,
            "rejected_relationship_count": len(rejected_relationships),
            "rejected_relationships": rejected_relationships,
            "validation_errors": getattr(parse_result, 'validation_errors', []),
        }

    def _create_external_schedule(self, schedule, source_filename: str, source_format: str) -> ExternalSchedule:
        existing = self.db.query(ExternalSchedule).filter(
            ExternalSchedule.external_schedule_id == schedule.external_schedule_id
        ).first()

        if existing:
            existing.schedule_name = schedule.schedule_name
            existing.source_filename = source_filename
            existing.source_format = source_format
            return existing

        return ExternalSchedule(
            external_schedule_id=schedule.external_schedule_id,
            schedule_name=schedule.schedule_name or "Imported Schedule",
            source_filename=source_filename,
            source_format=source_format,
        )

    def _import_activity(self, external_schedule_id: int, activity_data, source_format: str) -> Optional[ScheduleActivity]:
        existing = self.db.query(ScheduleActivity).filter(
            ScheduleActivity.activity_code == activity_data.activity_code,
            ScheduleActivity.organization_id == self.organization_id,
            ScheduleActivity.project_id == self.project_id
        ).first()

        wbs = getattr(activity_data, 'wbs_code', None) or getattr(activity_data, 'wbs_name', None) or "UNKNOWN"

        if existing:
            existing.activity_name = activity_data.activity_name
            existing.discipline = getattr(activity_data, 'discipline', None) or "Unknown"
            existing.wbs = wbs
            existing.planned_start = activity_data.planned_start
            existing.planned_finish = activity_data.planned_finish
            existing.external_activity_id = activity_data.activity_id
            existing.external_schedule_id = external_schedule_id
            existing.source_format = source_format
            return existing

        activity = ScheduleActivity(
            organization_id=self.organization_id,
            project_id=self.project_id,
            activity_code=activity_data.activity_code,
            activity_name=activity_data.activity_name,
            discipline=getattr(activity_data, 'discipline', None) or "Unknown",
            wbs=wbs,
            planned_start=activity_data.planned_start,
            planned_finish=activity_data.planned_finish,
            external_schedule_id=external_schedule_id,
            external_activity_id=activity_data.activity_id,
            source_format=source_format,
        )
        self.db.add(activity)
        self.db.flush()
        return activity

    def _import_relationship(
        self,
        external_schedule_id: int,
        pred_activity_id: int,
        succ_activity_id: int,
        rel_data
    ) -> ScheduleRelationship:
        rel_type = getattr(rel_data, 'relationship_type', None)
        if hasattr(rel_type, 'value'):
            rel_type = rel_type.value
        elif rel_type is None:
            rel_type = "FS"

        existing = self.db.query(ScheduleRelationship).filter(
            ScheduleRelationship.predecessor_activity_id == pred_activity_id,
            ScheduleRelationship.successor_activity_id == succ_activity_id,
            ScheduleRelationship.relationship_type == rel_type,
        ).first()

        if existing:
            existing.lag = getattr(rel_data, 'lag', 0)
            existing.lag_unit = getattr(rel_data, 'lag_unit', 'days')
            return existing

        relationship = ScheduleRelationship(
            external_schedule_id=external_schedule_id,
            predecessor_activity_id=pred_activity_id,
            successor_activity_id=succ_activity_id,
            relationship_type=rel_type,
            lag=getattr(rel_data, 'lag', 0),
            lag_unit=getattr(rel_data, 'lag_unit', 'days'),
        )
        self.db.add(relationship)
        return relationship


class XERImportService:
    def __init__(self, db: Session, organization_id: int = None, project_id: int = None):
        self.db = db
        self._service = ScheduleImportService(db, organization_id, project_id)

    def import_xer(self, content: str, source_filename: str = "import.xer") -> dict:
        result = parse_xer_content(content)
        return self._service.import_schedule(result, source_filename, "XER")


def get_relationships(db: Session, external_schedule_id: int = None) -> list[ScheduleRelationship]:
    query = db.query(ScheduleRelationship)
    if external_schedule_id:
        query = query.filter(ScheduleRelationship.external_schedule_id == external_schedule_id)
    return query.all()