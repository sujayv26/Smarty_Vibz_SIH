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
)
from app.models.schedule import ScheduleActivity
from app.models.xer import ScheduleRelationship, ExternalSchedule


class XERImportService:
    def __init__(self, db: Session):
        self.db = db

    def import_xer(self, content: str, source_filename: str = "import.xer") -> dict:
        result = parse_xer_content(content)

        external_schedule = self._create_external_schedule(result.schedule, source_filename)
        self.db.add(external_schedule)
        self.db.flush()

        imported_count = 0
        rejected_activities = []
        activity_id_map = {}

        for xer_activity in result.schedule.activities:
            try:
                activity = self._import_activity(external_schedule.id, xer_activity)
                if activity:
                    activity_id_map[xer_activity.activity_id] = activity.id
                    imported_count += 1
            except Exception as e:
                rejected_activities.append({
                    "activity_id": xer_activity.activity_id,
                    "activity_code": xer_activity.activity_code,
                    "error": str(e)
                })

        relationship_count = 0
        rejected_relationships = []
        for xer_rel in result.schedule.relationships:
            try:
                pred_id = activity_id_map.get(xer_rel.predecessor_activity_id)
                succ_id = activity_id_map.get(xer_rel.successor_activity_id)
                if pred_id and succ_id:
                    if pred_id == succ_id:
                        rejected_relationships.append({
                            "predecessor": xer_rel.predecessor_activity_id,
                            "successor": xer_rel.successor_activity_id,
                            "error": "Self-referencing relationship not allowed"
                        })
                        continue
                    self._import_relationship(external_schedule.id, pred_id, succ_id, xer_rel)
                    relationship_count += 1
                else:
                    rejected_relationships.append({
                        "predecessor": xer_rel.predecessor_activity_id,
                        "successor": xer_rel.successor_activity_id,
                        "error": "Referenced activity not found"
                    })
            except Exception as e:
                rejected_relationships.append({
                    "predecessor": xer_rel.predecessor_activity_id,
                    "successor": xer_rel.successor_activity_id,
                    "error": str(e)
                })

        self.db.commit()

        return {
            "source_format": "XER",
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
            "validation_errors": result.validation_errors,
        }

    def _create_external_schedule(self, schedule: XERSchedule, source_filename: str) -> ExternalSchedule:
        existing = self.db.query(ExternalSchedule).filter(
            ExternalSchedule.external_schedule_id == schedule.external_schedule_id
        ).first()

        if existing:
            existing.schedule_name = schedule.schedule_name
            existing.source_filename = source_filename
            return existing

        return ExternalSchedule(
            external_schedule_id=schedule.external_schedule_id,
            schedule_name=schedule.schedule_name or "Imported Schedule",
            source_filename=source_filename,
            source_format="XER",
        )

    def _import_activity(self, external_schedule_id: int, xer_activity: XERActivity) -> Optional[ScheduleActivity]:
        existing = self.db.query(ScheduleActivity).filter(
            ScheduleActivity.activity_code == xer_activity.activity_code
        ).first()

        wbs = xer_activity.wbs_code or xer_activity.wbs_name or "UNKNOWN"

        if existing:
            existing.activity_name = xer_activity.activity_name
            existing.discipline = xer_activity.discipline or "Unknown"
            existing.wbs = wbs
            existing.planned_start = xer_activity.planned_start
            existing.planned_finish = xer_activity.planned_finish
            existing.external_activity_id = xer_activity.activity_id
            existing.external_schedule_id = external_schedule_id
            existing.source_format = "XER"
            return existing

        activity = ScheduleActivity(
            activity_code=xer_activity.activity_code,
            activity_name=xer_activity.activity_name,
            discipline=xer_activity.discipline or "Unknown",
            wbs=wbs,
            planned_start=xer_activity.planned_start,
            planned_finish=xer_activity.planned_finish,
            external_schedule_id=external_schedule_id,
            external_activity_id=xer_activity.activity_id,
            source_format="XER",
        )
        self.db.add(activity)
        self.db.flush()
        return activity

    def _import_relationship(
        self,
        external_schedule_id: int,
        pred_activity_id: int,
        succ_activity_id: int,
        xer_rel: XERRelationship
    ) -> ScheduleRelationship:
        existing = self.db.query(ScheduleRelationship).filter(
            ScheduleRelationship.predecessor_activity_id == pred_activity_id,
            ScheduleRelationship.successor_activity_id == succ_activity_id,
            ScheduleRelationship.relationship_type == xer_rel.relationship_type.value,
        ).first()

        if existing:
            existing.lag = xer_rel.lag
            existing.lag_unit = xer_rel.lag_unit
            return existing

        relationship = ScheduleRelationship(
            external_schedule_id=external_schedule_id,
            predecessor_activity_id=pred_activity_id,
            successor_activity_id=succ_activity_id,
            relationship_type=xer_rel.relationship_type.value,
            lag=xer_rel.lag,
            lag_unit=xer_rel.lag_unit,
        )
        self.db.add(relationship)
        return relationship


def get_relationships(db: Session, external_schedule_id: int = None) -> list[ScheduleRelationship]:
    query = db.query(ScheduleRelationship)
    if external_schedule_id:
        query = query.filter(ScheduleRelationship.external_schedule_id == external_schedule_id)
    return query.all()