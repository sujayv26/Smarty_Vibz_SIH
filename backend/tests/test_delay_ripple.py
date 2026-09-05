import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.services.delay_ripple_service import DelayRippleService
from app.models.schedule import ScheduleActivity
from app.models.xer import ScheduleRelationship
from app.models.wbs_node import WBSNode
from app.models.progress import ProgressEvent
from app.models.delay_impact import DelayImpact
from app.models.project import Project
from app.models.organization import Organization


class TestDelayRippleService:
    """Tests for deterministic delay ripple computation."""

    def _setup_project_with_activities(self, db: Session) -> tuple[Project, list[ScheduleActivity]]:
        """Create a test project with activities and relationships."""
        org = Organization(name="Test Org", slug="test-org")
        db.add(org)
        db.commit()
        db.refresh(org)

        project = Project(
            name="Test Project",
            code="TEST-001",
            organization_id=org.id,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # Create activities with a simple chain: A -> B -> C -> D
        activities = []
        for i, (code, name, disc, start_offset, duration) in enumerate([
            ("A-100", "Excavation", "Civil", 0, 5),
            ("A-110", "Foundation Pour", "Civil", 5, 3),
            ("A-120", "Backfill", "Civil", 8, 4),
            ("A-130", "Compaction", "Civil", 12, 2),
        ]):
            act = ScheduleActivity(
                organization_id=org.id,
                project_id=project.id,
                activity_code=code,
                activity_name=name,
                discipline=disc,
                wbs=f"A.{i+1}",
                planned_start=date(2026, 1, 1) + timedelta(days=start_offset),
                planned_finish=date(2026, 1, 1) + timedelta(days=start_offset + duration),
            )
            db.add(act)
            activities.append(act)
        db.commit()
        for a in activities:
            db.refresh(a)

        # Create relationships: FS chain A->B->C->D
        relationships = []
        for i in range(len(activities) - 1):
            rel = ScheduleRelationship(
                predecessor_activity_id=activities[i].id,
                successor_activity_id=activities[i + 1].id,
                relationship_type="FS",
                lag=0,
                lag_unit="days",
            )
            db.add(rel)
            relationships.append(rel)
        db.commit()

        return project, activities

    def _add_wbs_nodes(self, db: Session, project_id: int, activities: list[ScheduleActivity]) -> list[WBSNode]:
        """Add WBS nodes mirroring activities."""
        nodes = []
        for act in activities:
            node = WBSNode(
                project_id=project_id,
                activity_code=act.activity_code,
                activity_name=act.activity_name,
                discipline=act.discipline,
                wbs=act.wbs,
                level=2,
                planned_start=act.planned_start,
                planned_finish=act.planned_finish,
            )
            db.add(node)
            nodes.append(node)
        db.commit()
        for n in nodes:
            db.refresh(n)
        return nodes

    def test_simple_fs_chain_delay_ripple(self, db_session: Session):
        """Test delay propagation through a simple FS chain."""
        project, activities = self._setup_project_with_activities(db_session)
        self._add_wbs_nodes(db_session, project.id, activities)

        service = DelayRippleService(db_session)

        # Create a progress event for the first activity
        event = ProgressEvent(
            organization_id=activities[0].organization_id,
            project_id=project.id,
            raw_text="Excavation delayed by 5 days due to weather",
            activity_reference="A-100",
            event_type="DELAY",
            event_date=date(2026, 1, 1),
            discipline="Civil",
            source_type="TEXT_DIARY",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        # Find WBS node for A-100
        wbs_node = db_session.query(WBSNode).filter(
            WBSNode.project_id == project.id,
            WBSNode.activity_code == "A-100"
        ).first()
        assert wbs_node is not None

        # Compute delay ripple with 5 days delay
        impacts = service.compute_delay_ripple(
            project_id=project.id,
            source_event_id=event.id,
            source_wbs_node_id=wbs_node.id,
            delay_days=5,
        )

        # Should have impacts on all downstream activities
        assert len(impacts) >= 3  # B, C, D

        # Check impact details
        impacted_codes = set()
        for impact in impacts:
            impacted_wbs = db_session.query(WBSNode).filter(WBSNode.id == impact.impacted_wbs_node_id).first()
            if impacted_wbs:
                impacted_codes.add(impacted_wbs.activity_code)
                # All should have 5 days propagated delay (FS chain)
                assert impact.propagated_delay_days == 5
                assert impact.relationship_type == "FS"
                assert impact.path_depth > 0

        assert "A-110" in impacted_codes
        assert "A-120" in impacted_codes
        assert "A-130" in impacted_codes

    def test_ss_relationship_delay_ripple(self, db_session: Session):
        """Test delay propagation through SS relationship."""
        org = Organization(name="Test Org", slug="test-org-ss")
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

        project = Project(name="Test Project", code="TEST-SS", organization_id=org.id)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # Create activities: A starts, B starts 2 days after A (SS with 2 day lag)
        act_a = ScheduleActivity(
            organization_id=org.id, project_id=project.id,
            activity_code="A-100", activity_name="Start Task", discipline="Civil",
            wbs="A.1", planned_start=date(2026, 1, 1), planned_finish=date(2026, 1, 10),
        )
        act_b = ScheduleActivity(
            organization_id=org.id, project_id=project.id,
            activity_code="B-100", activity_name="Parallel Task", discipline="Civil",
            wbs="A.2", planned_start=date(2026, 1, 3), planned_finish=date(2026, 1, 12),
        )
        db_session.add_all([act_a, act_b])
        db_session.commit()
        db_session.refresh(act_a)
        db_session.refresh(act_b)

        rel = ScheduleRelationship(
            predecessor_activity_id=act_a.id,
            successor_activity_id=act_b.id,
            relationship_type="SS",
            lag=2,
            lag_unit="days",
        )
        db_session.add(rel)
        db_session.commit()

        # Add WBS nodes
        for act in [act_a, act_b]:
            node = WBSNode(
                project_id=project.id, activity_code=act.activity_code,
                activity_name=act.activity_name, discipline=act.discipline,
                wbs=act.wbs, level=2,
                planned_start=act.planned_start, planned_finish=act.planned_finish,
            )
            db_session.add(node)
        db_session.commit()

        service = DelayRippleService(db_session)

        event = ProgressEvent(
            organization_id=org.id, project_id=project.id,
            raw_text="Task A delayed by 3 days", activity_reference="A-100",
            event_type="DELAY", event_date=date(2026, 1, 1),
            discipline="Civil", source_type="TEXT_DIARY",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        wbs_a = db_session.query(WBSNode).filter(
            WBSNode.project_id == project.id, WBSNode.activity_code == "A-100"
        ).first()

        impacts = service.compute_delay_ripple(
            project_id=project.id, source_event_id=event.id,
            source_wbs_node_id=wbs_a.id, delay_days=3,
        )

        assert len(impacts) == 1
        impact = impacts[0]
        impacted_wbs = db_session.query(WBSNode).filter(WBSNode.id == impact.impacted_wbs_node_id).first()
        assert impacted_wbs.activity_code == "B-100"
        assert impact.relationship_type == "SS"
        assert impact.lag_days == 2

    def test_critical_path_detection(self, db_session: Session):
        """Test that activities on critical path are flagged correctly."""
        project, activities = self._setup_project_with_activities(db_session)
        self._add_wbs_nodes(db_session, project.id, activities)

        service = DelayRippleService(db_session)

        event = ProgressEvent(
            organization_id=activities[0].organization_id,
            project_id=project.id,
            raw_text="Excavation delayed by 5 days",
            activity_reference="A-100",
            event_type="DELAY",
            event_date=date(2026, 1, 1),
            discipline="Civil",
            source_type="TEXT_DIARY",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        wbs_node = db_session.query(WBSNode).filter(
            WBSNode.project_id == project.id, WBSNode.activity_code == "A-100"
        ).first()

        impacts = service.compute_delay_ripple(
            project_id=project.id, source_event_id=event.id,
            source_wbs_node_id=wbs_node.id, delay_days=5,
        )

        # All activities in a simple chain with no float should be on critical path
        for impact in impacts:
            assert impact.is_critical_path == True
            assert impact.critical_path_exposure == True

    def test_float_consumption(self, db_session: Session):
        """Test float consumption when delay is less than available float."""
        org = Organization(name="Test Org", slug="test-org-float")
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

        project = Project(name="Test Project", code="TEST-FLOAT", organization_id=org.id)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # Create activities with float: A(1-5), B(10-15) with FS, so B has 5 days float
        act_a = ScheduleActivity(
            organization_id=org.id, project_id=project.id,
            activity_code="A-100", activity_name="Task A", discipline="Civil",
            wbs="A.1", planned_start=date(2026, 1, 1), planned_finish=date(2026, 1, 5),
        )
        act_b = ScheduleActivity(
            organization_id=org.id, project_id=project.id,
            activity_code="B-100", activity_name="Task B", discipline="Civil",
            wbs="A.2", planned_start=date(2026, 1, 10), planned_finish=date(2026, 1, 15),
        )
        db_session.add_all([act_a, act_b])
        db_session.commit()
        db_session.refresh(act_a)
        db_session.refresh(act_b)

        rel = ScheduleRelationship(
            predecessor_activity_id=act_a.id,
            successor_activity_id=act_b.id,
            relationship_type="FS",
            lag=0,
            lag_unit="days",
        )
        db_session.add(rel)
        db_session.commit()

        for act in [act_a, act_b]:
            node = WBSNode(
                project_id=project.id, activity_code=act.activity_code,
                activity_name=act.activity_name, discipline=act.discipline,
                wbs=act.wbs, level=2,
                planned_start=act.planned_start, planned_finish=act.planned_finish,
            )
            db_session.add(node)
        db_session.commit()

        service = DelayRippleService(db_session)

        event = ProgressEvent(
            organization_id=org.id, project_id=project.id,
            raw_text="Task A delayed by 2 days", activity_reference="A-100",
            event_type="DELAY", event_date=date(2026, 1, 1),
            discipline="Civil", source_type="TEXT_DIARY",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        wbs_a = db_session.query(WBSNode).filter(
            WBSNode.project_id == project.id, WBSNode.activity_code == "A-100"
        ).first()

        impacts = service.compute_delay_ripple(
            project_id=project.id, source_event_id=event.id,
            source_wbs_node_id=wbs_a.id, delay_days=2,
        )

        assert len(impacts) == 1
        impact = impacts[0]
        # B has 5 days schedule margin, 2 day delay should consume 2 days
        assert impact.float_consumed_days == 2
        assert impact.remaining_float_days == 3  # 5 - 2 = 3
        # B is on CPM critical path (total float = 0) but has schedule margin
        assert impact.is_critical_path == True  # CPM critical path
        # But no critical path exposure because schedule margin remains
        assert impact.critical_path_exposure == False

    def test_float_exhaustion_becomes_critical(self, db_session: Session):
        """Test that consuming all float flags critical path exposure."""
        org = Organization(name="Test Org", slug="test-org-float2")
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

        project = Project(name="Test Project", code="TEST-FLOAT2", organization_id=org.id)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        act_a = ScheduleActivity(
            organization_id=org.id, project_id=project.id,
            activity_code="A-100", activity_name="Task A", discipline="Civil",
            wbs="A.1", planned_start=date(2026, 1, 1), planned_finish=date(2026, 1, 5),
        )
        act_b = ScheduleActivity(
            organization_id=org.id, project_id=project.id,
            activity_code="B-100", activity_name="Task B", discipline="Civil",
            wbs="A.2", planned_start=date(2026, 1, 10), planned_finish=date(2026, 1, 15),
        )
        db_session.add_all([act_a, act_b])
        db_session.commit()
        db_session.refresh(act_a)
        db_session.refresh(act_b)

        rel = ScheduleRelationship(
            predecessor_activity_id=act_a.id,
            successor_activity_id=act_b.id,
            relationship_type="FS",
            lag=0,
            lag_unit="days",
        )
        db_session.add(rel)
        db_session.commit()

        for act in [act_a, act_b]:
            node = WBSNode(
                project_id=project.id, activity_code=act.activity_code,
                activity_name=act.activity_name, discipline=act.discipline,
                wbs=act.wbs, level=2,
                planned_start=act.planned_start, planned_finish=act.planned_finish,
            )
            db_session.add(node)
        db_session.commit()

        service = DelayRippleService(db_session)

        event = ProgressEvent(
            organization_id=org.id, project_id=project.id,
            raw_text="Task A delayed by 5 days", activity_reference="A-100",
            event_type="DELAY", event_date=date(2026, 1, 1),
            discipline="Civil", source_type="TEXT_DIARY",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        wbs_a = db_session.query(WBSNode).filter(
            WBSNode.project_id == project.id, WBSNode.activity_code == "A-100"
        ).first()

        impacts = service.compute_delay_ripple(
            project_id=project.id, source_event_id=event.id,
            source_wbs_node_id=wbs_a.id, delay_days=5,
        )

        assert len(impacts) == 1
        impact = impacts[0]
        # B has 5 days float, 5 day delay should consume all float
        assert impact.float_consumed_days == 5
        assert impact.remaining_float_days == 0
        # When float is exhausted, it becomes critical path exposure
        assert impact.critical_path_exposure == True

    def test_get_delay_impacts_for_event(self, db_session: Session):
        """Test querying delay impacts by event."""
        project, activities = self._setup_project_with_activities(db_session)
        self._add_wbs_nodes(db_session, project.id, activities)

        service = DelayRippleService(db_session)

        event = ProgressEvent(
            organization_id=activities[0].organization_id,
            project_id=project.id,
            raw_text="Excavation delayed by 5 days",
            activity_reference="A-100",
            event_type="DELAY",
            event_date=date(2026, 1, 1),
            discipline="Civil",
            source_type="TEXT_DIARY",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        wbs_node = db_session.query(WBSNode).filter(
            WBSNode.project_id == project.id, WBSNode.activity_code == "A-100"
        ).first()

        service.compute_delay_ripple(
            project_id=project.id, source_event_id=event.id,
            source_wbs_node_id=wbs_node.id, delay_days=5,
        )

        impacts = service.get_delay_impacts_for_event(event.id)
        assert len(impacts) >= 3
        assert all(i.source_event_id == event.id for i in impacts)

    def test_get_delay_impacts_for_activity(self, db_session: Session):
        """Test querying delay impacts affecting a specific activity."""
        project, activities = self._setup_project_with_activities(db_session)
        self._add_wbs_nodes(db_session, project.id, activities)

        service = DelayRippleService(db_session)

        event = ProgressEvent(
            organization_id=activities[0].organization_id,
            project_id=project.id,
            raw_text="Excavation delayed by 5 days",
            activity_reference="A-100",
            event_type="DELAY",
            event_date=date(2026, 1, 1),
            discipline="Civil",
            source_type="TEXT_DIARY",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        wbs_node = db_session.query(WBSNode).filter(
            WBSNode.project_id == project.id, WBSNode.activity_code == "A-100"
        ).first()

        service.compute_delay_ripple(
            project_id=project.id, source_event_id=event.id,
            source_wbs_node_id=wbs_node.id, delay_days=5,
        )

        # Query impacts for B-110
        wbs_b = db_session.query(WBSNode).filter(
            WBSNode.project_id == project.id, WBSNode.activity_code == "A-110"
        ).first()

        impacts = service.get_delay_impacts_for_activity(project.id, wbs_b.id)
        assert len(impacts) == 1
        assert impacts[0].impacted_wbs_node_id == wbs_b.id

    def test_multiple_delay_events_accumulate(self, db_session: Session):
        """Test that multiple delay events create separate impact records."""
        project, activities = self._setup_project_with_activities(db_session)
        self._add_wbs_nodes(db_session, project.id, activities)

        service = DelayRippleService(db_session)

        # First delay event
        event1 = ProgressEvent(
            organization_id=activities[0].organization_id,
            project_id=project.id,
            raw_text="Excavation delayed by 3 days",
            activity_reference="A-100",
            event_type="DELAY",
            event_date=date(2026, 1, 1),
            discipline="Civil",
            source_type="TEXT_DIARY",
        )
        db_session.add(event1)
        db_session.commit()
        db_session.refresh(event1)

        wbs_a = db_session.query(WBSNode).filter(
            WBSNode.project_id == project.id, WBSNode.activity_code == "A-100"
        ).first()

        service.compute_delay_ripple(
            project_id=project.id, source_event_id=event1.id,
            source_wbs_node_id=wbs_a.id, delay_days=3,
        )

        # Second delay event on same activity
        event2 = ProgressEvent(
            organization_id=activities[0].organization_id,
            project_id=project.id,
            raw_text="Excavation delayed by 2 more days",
            activity_reference="A-100",
            event_type="DELAY",
            event_date=date(2026, 1, 3),
            discipline="Civil",
            source_type="TEXT_DIARY",
        )
        db_session.add(event2)
        db_session.commit()
        db_session.refresh(event2)

        service.compute_delay_ripple(
            project_id=project.id, source_event_id=event2.id,
            source_wbs_node_id=wbs_a.id, delay_days=2,
        )

        # Should have impacts from both events
        impacts1 = service.get_delay_impacts_for_event(event1.id)
        impacts2 = service.get_delay_impacts_for_event(event2.id)
        assert len(impacts1) >= 3
        assert len(impacts2) >= 3
        # All impacts should be separate records
        all_impacts = db_session.query(DelayImpact).filter(
            DelayImpact.project_id == project.id
        ).all()
        assert len(all_impacts) >= 6  # 3 per event

    def test_ff_relationship(self, db_session: Session):
        """Test FF (Finish-to-Finish) relationship delay propagation."""
        org = Organization(name="Test Org", slug="test-org-ff")
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

        project = Project(name="Test Project", code="TEST-FF", organization_id=org.id)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        act_a = ScheduleActivity(
            organization_id=org.id, project_id=project.id,
            activity_code="A-100", activity_name="Task A", discipline="Civil",
            wbs="A.1", planned_start=date(2026, 1, 1), planned_finish=date(2026, 1, 10),
        )
        act_b = ScheduleActivity(
            organization_id=org.id, project_id=project.id,
            activity_code="B-100", activity_name="Task B", discipline="Civil",
            wbs="A.2", planned_start=date(2026, 1, 5), planned_finish=date(2026, 1, 15),
        )
        db_session.add_all([act_a, act_b])
        db_session.commit()
        db_session.refresh(act_a)
        db_session.refresh(act_b)

        rel = ScheduleRelationship(
            predecessor_activity_id=act_a.id,
            successor_activity_id=act_b.id,
            relationship_type="FF",
            lag=0,
            lag_unit="days",
        )
        db_session.add(rel)
        db_session.commit()

        for act in [act_a, act_b]:
            node = WBSNode(
                project_id=project.id, activity_code=act.activity_code,
                activity_name=act.activity_name, discipline=act.discipline,
                wbs=act.wbs, level=2,
                planned_start=act.planned_start, planned_finish=act.planned_finish,
            )
            db_session.add(node)
        db_session.commit()

        service = DelayRippleService(db_session)

        event = ProgressEvent(
            organization_id=org.id, project_id=project.id,
            raw_text="Task A delayed by 4 days", activity_reference="A-100",
            event_type="DELAY", event_date=date(2026, 1, 1),
            discipline="Civil", source_type="TEXT_DIARY",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        wbs_a = db_session.query(WBSNode).filter(
            WBSNode.project_id == project.id, WBSNode.activity_code == "A-100"
        ).first()

        impacts = service.compute_delay_ripple(
            project_id=project.id, source_event_id=event.id,
            source_wbs_node_id=wbs_a.id, delay_days=4,
        )

        assert len(impacts) == 1
        impact = impacts[0]
        impacted_wbs = db_session.query(WBSNode).filter(WBSNode.id == impact.impacted_wbs_node_id).first()
        assert impacted_wbs.activity_code == "B-100"
        assert impact.relationship_type == "FF"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])