from typing import Optional
from sqlalchemy.orm import Session
from app.models.schedule import ScheduleActivity
from app.models.xer import ExternalSchedule, ScheduleRelationship
from app.models.confidence import PlannerReview, AuditRecord, DecisionType, ReviewStatus
from app.models.progress import ProgressEvent
from datetime import date, datetime
import io


class XERExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_schedule(
        self,
        external_schedule_id: int,
        include_approved_actuals: bool = True,
    ) -> tuple[str, dict]:
        ext_schedule = self.db.query(ExternalSchedule).filter(
            ExternalSchedule.id == external_schedule_id
        ).first()

        if not ext_schedule:
            raise ValueError(f"External schedule {external_schedule_id} not found")

        activities = ext_schedule.activities.all()
        relationships = self.db.query(ScheduleRelationship).filter(
            ScheduleRelationship.external_schedule_id == external_schedule_id
        ).all()

        approved_actuals = {}
        if include_approved_actuals:
            approved_actuals = self._get_approved_actuals(external_schedule_id)

        xer_content = self._generate_xer(
            ext_schedule,
            activities,
            relationships,
            approved_actuals,
        )

        stats = {
            "external_schedule_id": ext_schedule.external_schedule_id,
            "schedule_name": ext_schedule.schedule_name,
            "exported_activity_count": len(activities),
            "exported_relationship_count": len(relationships),
            "approved_actuals_count": len(approved_actuals),
            "exported_at": datetime.utcnow().isoformat(),
            "warnings": [],
        }

        return xer_content, stats

    def _get_approved_actuals(self, external_schedule_id: int) -> dict:
        ext_schedule = self.db.query(ExternalSchedule).filter(
            ExternalSchedule.id == external_schedule_id
        ).first()
        if not ext_schedule:
            return {}

        activity_codes = [a.activity_code for a in ext_schedule.activities.all()]
        if not activity_codes:
            return {}

        reviews = self.db.query(PlannerReview).join(ProgressEvent).filter(
            PlannerReview.status.in_([
                ReviewStatus.APPROVED,
                ReviewStatus.CORRECTED,
                ReviewStatus.NEW_ACTIVITY_CREATED,
            ]),
            ProgressEvent.activity_reference.in_(activity_codes)
        ).all()

        actuals = {}
        for review in reviews:
            final_activity = review.final_activity
            new_activity = review.new_activity
            target_activity = final_activity or new_activity
            if target_activity and target_activity.activity_code in activity_codes:
                event = self.db.query(ProgressEvent).filter(
                    ProgressEvent.id == review.progress_event_id
                ).first()
                if event:
                    if event.event_type == "START" and event.event_date:
                        actuals.setdefault(target_activity.activity_code, {})["actual_start"] = event.event_date
                    if event.event_type == "COMPLETE" and event.event_date:
                        actuals.setdefault(target_activity.activity_code, {})["actual_finish"] = event.event_date

        return actuals

    def _generate_xer(
        self,
        ext_schedule: ExternalSchedule,
        activities: list[ScheduleActivity],
        relationships: list[ScheduleRelationship],
        approved_actuals: dict,
    ) -> str:
        lines = []

        lines.append("%T\tPROJECT")
        lines.append("%F\tproj_id\tproj_short_name\tproj_name\tdata_date")
        lines.append(f"%R\t{ext_schedule.external_schedule_id}\t{ext_schedule.schedule_name or 'Exported'}\t{ext_schedule.schedule_name or 'Exported Schedule'}\t{date.today().strftime('%Y-%m-%d')}")
        lines.append("%T\tWBS")
        lines.append("%F\twbs_id\twbs_short_name\twbs_name\tproj_id")

        wbs_codes = set()
        for a in activities:
            if a.wbs and a.wbs not in wbs_codes:
                wbs_codes.add(a.wbs)
                lines.append(f"%R\t{a.wbs}\t{a.wbs}\t{a.wbs}\t{ext_schedule.external_schedule_id}")

        lines.append("%T\tTASK")
        lines.append("%F\ttask_id\ttask_code\ttask_name\twbs_id\tproj_id\ttask_type\ttarget_start_date\ttarget_end_date\tact_start_date\tact_end_date\tphys_pct_complete")

        for a in activities:
            actuals = approved_actuals.get(a.activity_code, {})
            act_start = actuals.get("actual_start")
            act_finish = actuals.get("actual_finish")
            pct_complete = 100 if act_finish else (0 if not act_start else 50)

            task_id = a.external_activity_id or a.activity_code
            lines.append(
                f"%R\t{task_id}\t"
                f"{a.activity_code}\t"
                f"{a.activity_name}\t"
                f"{a.wbs or 'UNKNOWN'}\t"
                f"{ext_schedule.external_schedule_id}\t"
                f"{a.discipline or 'Unknown'}\t"
                f"{a.planned_start.strftime('%Y-%m-%d') if a.planned_start else ''}\t"
                f"{a.planned_finish.strftime('%Y-%m-%d') if a.planned_finish else ''}\t"
                f"{act_start.strftime('%Y-%m-%d') if act_start else ''}\t"
                f"{act_finish.strftime('%Y-%m-%d') if act_finish else ''}\t"
                f"{pct_complete}"
            )

        lines.append("%T\tTASKPRED")
        lines.append("%F\ttask_id\tpred_task_id\tpred_type\tlag_hr_cnt")

        for r in relationships:
            pred = self.db.query(ScheduleActivity).filter(ScheduleActivity.id == r.predecessor_activity_id).first()
            succ = self.db.query(ScheduleActivity).filter(ScheduleActivity.id == r.successor_activity_id).first()
            if pred and succ:
                lag_hr = r.lag * 8
                lines.append(
                    f"%R\t{succ.external_activity_id or succ.activity_code}\t"
                    f"{pred.external_activity_id or pred.activity_code}\t"
                    f"{r.relationship_type}\t"
                    f"{lag_hr}"
                )

        lines.append("%E")
        return "\n".join(lines)


def export_schedule_to_xer(db: Session, external_schedule_id: int, include_approved_actuals: bool = True) -> tuple[str, dict]:
    service = XERExportService(db)
    return service.export_schedule(external_schedule_id, include_approved_actuals)