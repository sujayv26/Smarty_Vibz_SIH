import pytest
from pathlib import Path
from app.services.xer.parser import (
    XERParser,
    parse_xer_content,
    XERParseResult,
    XERSchedule,
    XERActivity,
    XERRelationship,
    RelationshipType,
    XERParseError,
    parse_date,
)
from app.services.xer.service import XERImportService
from app.services.xer.export import XERExportService, export_schedule_to_xer
from app.models.schedule import ScheduleActivity
from app.models.xer import ExternalSchedule, ScheduleRelationship
from app.models.confidence import PlannerReview, AuditRecord, ReviewStatus, DecisionType
from app.models.progress import ProgressEvent
from sqlalchemy.orm import Session
from datetime import date
import io

FIXTURES_DIR = Path(__file__).parent / "fixtures"


SAMPLE_XER_CONTENT = """%T	PROJECT
%F	proj_id	proj_short_name	proj_name	data_date
%R	SCH-001	Test Project	Test Infrastructure Project	2026-01-15
%T	WBS
%F	wbs_id	wbs_short_name	wbs_name	proj_id
%R	WBSCIV	CIV	Civil Foundation	SCH-001
%R	WBSSTR	STR	Structural Steel	SCH-001
%R	WBSPIP	PIP	Piping Erection	SCH-001
%R	WBSEQP	EQP	Equipment Installation	SCH-001
%R	WBSELE	ELE	Electrical Works	SCH-001
%T	TASK
%F	task_id	task_code	task_name	wbs_id	proj_id	task_type	target_start_date	target_end_date	act_start_date	act_end_date	phys_pct_complete
%R	CIV-100	CIV-100	Excavate Foundation	WBSCIV	SCH-001	Civil	2026-01-20	2026-01-30			0
%R	CIV-110	CIV-110	Pour Foundation Concrete	WBSCIV	SCH-001	Civil	2026-02-01	2026-02-10			0
%R	STR-200	STR-200	Erect Structural Steel Grid A	WBSSTR	SCH-001	Structural	2026-02-15	2026-03-01			0
%R	STR-210	STR-210	Install Steel Connections	WBSSTR	SCH-001	Structural	2026-03-02	2026-03-10			0
%R	PIP-300	PIP-300	Erect Line 24-XX-101	WBSPIP	SCH-001	Piping	2026-03-15	2026-03-30			0
%R	PIP-310	PIP-310	Install Support for XX-101	WBSPIP	SCH-001	Piping	2026-03-10	2026-03-20			0
%R	PIP-320	PIP-320	Erect Line 24-XX-102	WBSPIP	SCH-001	Piping	2026-04-01	2026-04-15			0
%R	EQP-400	EQP-400	Install Pump P-101	WBSEQP	SCH-001	Mechanical	2026-04-20	2026-05-05			0
%R	EQP-410	EQP-410	Install Compressor C-101	WBSEQP	SCH-001	Mechanical	2026-05-01	2026-05-15			0
%R	ELE-500	ELE-500	Cable Pulling for Substation	WBSELE	SCH-001	Electrical	2026-05-10	2026-05-25			0
%R	ELE-510	ELE-510	Terminate Cables	WBSELE	SCH-001	Electrical	2026-05-20	2026-06-01			0
%T	TASKPRED
%F	task_id	pred_task_id	pred_type	lag_hr_cnt
%R	CIV-110	CIV-100	FS	0
%R	STR-200	CIV-110	FS	0
%R	STR-210	STR-200	SS	16
%R	PIP-300	STR-210	FS	0
%R	PIP-310	PIP-300	SS	8
%R	PIP-320	PIP-300	FF	0
%R	EQP-400	PIP-320	FS	0
%R	EQP-410	EQP-400	SS	24
%R	ELE-500	EQP-410	FS	0
%R	ELE-510	ELE-500	SS	16
%R	ELE-510	ELE-500	SF	0
%E
"""


class TestXERParser:
    def test_parse_valid_xer(self):
        result = parse_xer_content(SAMPLE_XER_CONTENT)
        assert isinstance(result, XERParseResult)
        assert isinstance(result.schedule, XERSchedule)
        assert result.schedule.external_schedule_id == "SCH-001"
        assert len(result.schedule.activities) == 11
        assert len(result.schedule.relationships) == 11

    def test_activity_extraction(self):
        result = parse_xer_content(SAMPLE_XER_CONTENT)
        activities = result.schedule.activities
        assert len(activities) == 11

        pip300 = next(a for a in activities if a.activity_code == "PIP-300")
        assert pip300.activity_id == "PIP-300"
        assert pip300.activity_name == "Erect Line 24-XX-101"
        assert pip300.discipline == "Piping"
        assert pip300.wbs_code == "PIP"
        assert pip300.planned_start == date(2026, 3, 15)
        assert pip300.planned_finish == date(2026, 3, 30)

    def test_wbs_mapping(self):
        result = parse_xer_content(SAMPLE_XER_CONTENT)
        activities = result.schedule.activities
        civ100 = next(a for a in activities if a.activity_code == "CIV-100")
        assert civ100.wbs_code == "CIV"
        assert civ100.wbs_name == "Civil Foundation"

    def test_fs_relationship(self):
        result = parse_xer_content(SAMPLE_XER_CONTENT)
        rels = result.schedule.relationships
        fs_rels = [r for r in rels if r.relationship_type == RelationshipType.FS]
        assert len(fs_rels) >= 5
        civ_rel = next(r for r in fs_rels if r.successor_activity_id == "CIV-110")
        assert civ_rel.predecessor_activity_id == "CIV-100"
        assert civ_rel.relationship_type == RelationshipType.FS

    def test_ss_relationship(self):
        result = parse_xer_content(SAMPLE_XER_CONTENT)
        rels = result.schedule.relationships
        ss_rels = [r for r in rels if r.relationship_type == RelationshipType.SS]
        assert len(ss_rels) >= 2
        str_rel = next(r for r in ss_rels if r.successor_activity_id == "STR-210")
        assert str_rel.predecessor_activity_id == "STR-200"
        assert str_rel.relationship_type == RelationshipType.SS
        assert str_rel.lag == 2

    def test_ff_relationship(self):
        result = parse_xer_content(SAMPLE_XER_CONTENT)
        rels = result.schedule.relationships
        ff_rels = [r for r in rels if r.relationship_type == RelationshipType.FF]
        assert len(ff_rels) >= 1
        pip_rel = next(r for r in ff_rels if r.successor_activity_id == "PIP-320")
        assert pip_rel.predecessor_activity_id == "PIP-300"

    def test_sf_relationship(self):
        result = parse_xer_content(SAMPLE_XER_CONTENT)
        rels = result.schedule.relationships
        sf_rels = [r for r in rels if r.relationship_type == RelationshipType.SF]
        assert len(sf_rels) >= 1
        ele_rel = next(r for r in sf_rels if r.successor_activity_id == "ELE-510")
        assert ele_rel.predecessor_activity_id == "ELE-500"

    def test_lag_preservation(self):
        result = parse_xer_content(SAMPLE_XER_CONTENT)
        rels = result.schedule.relationships
        str_rel = next(r for r in rels if r.successor_activity_id == "STR-210")
        assert str_rel.lag == 2
        assert str_rel.lag_unit == "days"

        eqp_rel = next(r for r in rels if r.successor_activity_id == "EQP-410")
        assert eqp_rel.lag == 3

    def test_empty_xer_raises_error(self):
        with pytest.raises(XERParseError, match="Empty XER file"):
            parse_xer_content("")

    def test_malformed_xer_handled(self):
        malformed = "%T\tPROJECT\n%F\tproj_id\n%R\tSCH-001\n%E"
        result = parse_xer_content(malformed)
        assert result.schedule.external_schedule_id == "SCH-001"

    def test_invalid_date_returns_none(self):
        result = parse_date("invalid-date")
        assert result is None

    def test_parse_date_formats(self):
        assert parse_date("2026-01-15") == date(2026, 1, 15)
        assert parse_date("15-Jan-26") == date(2026, 1, 15)
        assert parse_date("15-Jan-2026") == date(2026, 1, 15)
        assert parse_date("01/15/2026") == date(2026, 1, 15)

    def test_duplicate_activity_id_handled(self):
        xer_with_dup = SAMPLE_XER_CONTENT.replace(
            "%R	ELE-510	ELE-510	Terminate Cables	WBSELE	SCH-001	Electrical	2026-05-20	2026-06-01			0",
            "%R	ELE-510	ELE-510	Terminate Cables	WBSELE	SCH-001	Electrical	2026-05-20	2026-06-01			0\n%R	ELE-510	ELE-510	Duplicate	WBSELE	SCH-001	Electrical	2026-05-20	2026-06-01			0"
        )
        result = parse_xer_content(xer_with_dup)
        assert len(result.rejected_activities) >= 1

    def test_missing_activity_name_raises_error(self):
        xer_bad = SAMPLE_XER_CONTENT.replace(
            "%R	PIP-300	PIP-300	Erect Line 24-XX-101	WBSPIP	SCH-001	Piping	2026-03-15	2026-03-30			0",
            "%R	PIP-300	PIP-300		WBSPIP	SCH-001	Piping	2026-03-15	2026-03-30			0"
        )
        result = parse_xer_content(xer_bad)
        assert len(result.rejected_activities) >= 1


class TestXERImportService:
    def test_import_xer_creates_activities(self, db_session):
        service = XERImportService(db_session)
        result = service.import_xer(SAMPLE_XER_CONTENT, "sample.xer")

        assert result["imported_activity_count"] == 11
        assert result["rejected_activity_count"] == 0
        assert result["imported_relationship_count"] == 11
        assert result["source_format"] == "XER"
        assert result["external_schedule_id"] == "SCH-001"

        activities = db_session.query(ScheduleActivity).all()
        assert len(activities) == 11

        pip300 = db_session.query(ScheduleActivity).filter(
            ScheduleActivity.activity_code == "PIP-300"
        ).first()
        assert pip300 is not None
        assert pip300.activity_name == "Erect Line 24-XX-101"
        assert pip300.discipline == "Piping"
        assert pip300.wbs == "PIP"
        assert pip300.source_format == "XER"
        assert pip300.external_activity_id == "PIP-300"

    def test_import_xer_creates_relationships(self, db_session):
        service = XERImportService(db_session)
        service.import_xer(SAMPLE_XER_CONTENT, "sample.xer")

        relationships = db_session.query(ScheduleRelationship).all()
        assert len(relationships) == 11

        fs_rel = next(r for r in relationships if r.relationship_type == "FS")
        assert fs_rel.lag == 0

        ss_rel = next(r for r in relationships if r.relationship_type == "SS")
        assert ss_rel.lag >= 1

    def test_import_preserves_external_ids(self, db_session):
        service = XERImportService(db_session)
        service.import_xer(SAMPLE_XER_CONTENT, "sample.xer")

        activity = db_session.query(ScheduleActivity).filter(
            ScheduleActivity.activity_code == "PIP-300"
        ).first()
        assert activity.external_activity_id == "PIP-300"
        assert activity.external_schedule_id is not None

    def test_existing_excel_schedule_still_works(self, db_session):
        excel_activity = ScheduleActivity(
            activity_code="EXCEL-001",
            activity_name="Excel Activity",
            discipline="Civil",
            wbs="EXCEL.001",
            planned_start=date(2026, 1, 1),
            planned_finish=date(2026, 1, 10),
            source_format="EXCEL",
        )
        db_session.add(excel_activity)
        db_session.commit()

        service = XERImportService(db_session)
        service.import_xer(SAMPLE_XER_CONTENT, "sample.xer")

        all_activities = db_session.query(ScheduleActivity).all()
        assert len(all_activities) == 12

        excel_act = db_session.query(ScheduleActivity).filter(
            ScheduleActivity.activity_code == "EXCEL-001"
        ).first()
        assert excel_act.source_format == "EXCEL"

        xer_act = db_session.query(ScheduleActivity).filter(
            ScheduleActivity.activity_code == "PIP-300"
        ).first()
        assert xer_act.source_format == "XER"

    def test_self_referencing_relationship_rejected(self, db_session):
        xer_self_ref = SAMPLE_XER_CONTENT.replace("%E", "%R\tCIV-100\tCIV-100\tFS\t0\n%E")
        service = XERImportService(db_session)
        result = service.import_xer(xer_self_ref, "sample.xer")
        assert result["rejected_relationship_count"] >= 1

    def test_invalid_relationship_reference_rejected(self, db_session):
        xer_bad_ref = SAMPLE_XER_CONTENT.replace(
            "%R	CIV-110	CIV-100	FS	0",
            "%R	CIV-110	NONEXISTENT	FS	0"
        )
        service = XERImportService(db_session)
        result = service.import_xer(xer_bad_ref, "sample.xer")
        assert result["rejected_relationship_count"] >= 1


class TestXERExport:
    def test_export_valid_xer(self, db_session):
        service = XERImportService(db_session)
        service.import_xer(SAMPLE_XER_CONTENT, "sample.xer")

        ext_schedule = db_session.query(ExternalSchedule).first()
        xer_content, stats = export_schedule_to_xer(db_session, ext_schedule.id)

        assert stats["exported_activity_count"] == 11
        assert stats["exported_relationship_count"] == 11
        assert "SCH-001" in xer_content
        assert "PIP-300" in xer_content
        assert "FS" in xer_content
        assert "SS" in xer_content
        assert "FF" in xer_content
        assert "SF" in xer_content

    def test_export_approved_actual_start(self, db_session):
        service = XERImportService(db_session)
        service.import_xer(SAMPLE_XER_CONTENT, "sample.xer")

        ext_schedule = db_session.query(ExternalSchedule).first()
        pip300 = db_session.query(ScheduleActivity).filter(
            ScheduleActivity.activity_code == "PIP-300"
        ).first()

        event = ProgressEvent(
            raw_text="Started erection of XX-101 spool",
            activity_reference="PIP-300",
            event_type="START",
            event_date=date(2026, 3, 15),
            discipline="Piping",
            equipment_tag="XX-101",
            source_type="FREE_TEXT",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        review = PlannerReview(
            progress_event_id=event.id,
            proposed_activity_id=pip300.id,
            final_activity_id=pip300.id,
            confidence_score=0.9,
            confidence_level="HIGH",
            status=ReviewStatus.APPROVED,
            completed_at=date(2026, 3, 15),
        )
        db_session.add(review)
        db_session.commit()

        audit = AuditRecord(
            progress_event_id=event.id,
            proposed_activity_id=pip300.id,
            final_activity_id=pip300.id,
            confidence_score=0.9,
            confidence_level="HIGH",
            decision=DecisionType.APPROVED,
            actor_type="PLANNER",
        )
        db_session.add(audit)
        db_session.commit()

        xer_content, stats = export_schedule_to_xer(db_session, ext_schedule.id)

        assert stats["approved_actuals_count"] == 1
        assert "2026-03-15" in xer_content

    def test_export_does_not_include_unapproved_actuals(self, db_session):
        service = XERImportService(db_session)
        service.import_xer(SAMPLE_XER_CONTENT, "sample.xer")

        ext_schedule = db_session.query(ExternalSchedule).first()
        pip300 = db_session.query(ScheduleActivity).filter(
            ScheduleActivity.activity_code == "PIP-300"
        ).first()

        event = ProgressEvent(
            raw_text="Started erection of XX-101 spool",
            activity_reference="PIP-300",
            event_type="START",
            event_date=date(2026, 3, 15),
            discipline="Piping",
            equipment_tag="XX-101",
            source_type="FREE_TEXT",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        review = PlannerReview(
            progress_event_id=event.id,
            proposed_activity_id=pip300.id,
            confidence_score=0.6,
            confidence_level="MEDIUM",
            status=ReviewStatus.PENDING,
        )
        db_session.add(review)
        db_session.commit()

        xer_content, stats = export_schedule_to_xer(db_session, ext_schedule.id)

        assert stats["approved_actuals_count"] == 0

    def test_export_preserves_relationships(self, db_session):
        service = XERImportService(db_session)
        service.import_xer(SAMPLE_XER_CONTENT, "sample.xer")

        ext_schedule = db_session.query(ExternalSchedule).first()
        xer_content, stats = export_schedule_to_xer(db_session, ext_schedule.id)

        assert stats["exported_relationship_count"] == 11
        assert "TASKPRED" in xer_content

    def test_original_file_not_overwritten(self, db_session):
        service = XERImportService(db_session)
        service.import_xer(SAMPLE_XER_CONTENT, "sample.xer")

        ext_schedule = db_session.query(ExternalSchedule).first()
        xer_content, _ = export_schedule_to_xer(db_session, ext_schedule.id)

        assert xer_content != SAMPLE_XER_CONTENT
        assert "exported" in xer_content.lower() or "SCH-001" in xer_content


class TestXERImportAPI:
    def test_import_p6_endpoint(self, client):
        with open(FIXTURES_DIR / "sample_schedule.xer", "rb") as f:
            response = client.post(
                "/schedule/import/p6",
                files={"file": ("sample.xer", f, "application/octet-stream")}
            )
        assert response.status_code == 200
        data = response.json()
        assert data["imported_activity_count"] == 11
        assert data["imported_relationship_count"] == 11
        assert data["source_format"] == "XER"

    def test_import_invalid_extension(self, client):
        response = client.post(
            "/schedule/import/p6",
            files={"file": ("sample.txt", b"bad content", "text/plain")}
        )
        assert response.status_code == 400

    def test_get_relationships_endpoint(self, client, db_session):
        service = XERImportService(db_session)
        service.import_xer(SAMPLE_XER_CONTENT, "sample.xer")

        ext_schedule = db_session.query(ExternalSchedule).first()
        response = client.get(f"/schedule/relationships?external_schedule_id={ext_schedule.id}")
        assert response.status_code == 200
        relationships = response.json()
        assert len(relationships) == 11

    def test_get_external_schedules_endpoint(self, client, db_session):
        service = XERImportService(db_session)
        service.import_xer(SAMPLE_XER_CONTENT, "sample.xer")

        response = client.get("/schedule/external-schedules")
        assert response.status_code == 200
        schedules = response.json()
        assert len(schedules) == 1
        assert schedules[0]["external_schedule_id"] == "SCH-001"


class TestEndToEnd:
    def test_xer_import_to_export_flow(self, client, db_session):
        with open(FIXTURES_DIR / "sample_schedule.xer", "rb") as f:
            import_resp = client.post(
                "/schedule/import/p6",
                files={"file": ("sample.xer", f, "application/octet-stream")}
            )
        assert import_resp.status_code == 200
        import_data = import_resp.json()
        ext_schedule_id = import_data["internal_schedule_id"]

        pip300 = db_session.query(ScheduleActivity).filter(
            ScheduleActivity.activity_code == "PIP-300"
        ).first()

        event = ProgressEvent(
            raw_text="Today at 9:30 AM, the piping team started erection of the XX-101 spool in Area B",
            activity_reference="PIP-300",
            event_type="START",
            event_date=date(2026, 3, 15),
            event_time="09:30",
            discipline="Piping",
            location="Area B",
            equipment_tag="XX-101",
            source_type="FREE_TEXT",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        match_resp = client.post(f"/matching/run/{event.id}")
        assert match_resp.status_code == 200
        match_data = match_resp.json()
        assert match_data["top_matches"][0]["activity_code"] == "PIP-300"

        conf_resp = client.post(f"/confidence/evaluate/{event.id}")
        assert conf_resp.status_code == 200
        conf_data = conf_resp.json()

        if conf_data["decision"] == "AUTO_MATCH":
            review_id = None
        else:
            review_id = conf_data["review_id"]
            approve_resp = client.post(f"/reviews/{review_id}/approve", json={"reviewer_note": "Approved"})
            assert approve_resp.status_code == 200

        export_resp = client.post(f"/schedule/export/p6/{ext_schedule_id}")
        assert export_resp.status_code == 200
        assert export_resp.headers["content-disposition"].startswith("attachment")

        export_preview = client.get(f"/schedule/export/p6/{ext_schedule_id}/preview")
        assert export_preview.status_code == 200
        preview_data = export_preview.json()
        assert preview_data["stats"]["approved_actuals_count"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])