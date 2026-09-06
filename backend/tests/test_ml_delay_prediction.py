import pytest
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.services.ml_delay_service import DelayPredictionService, DelayPredictionModel
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.schedule import ScheduleActivity
from app.models.wbs_node import WBSNode
from app.models.delay_reason import DelayReason, DelayCategory
from app.models.productivity_benchmark import ProductivityBenchmark
from app.models.progress import ProgressEvent
from app.models.confidence import PlannerReview, ConfidenceLevel, ReviewStatus
from app.models.ingestion_source import IngestionSource
from app.core.security import get_password_hash


class TestDelayPredictionModel:
    """Tests for the ML model class."""
    
    def test_model_initialization(self):
        model = DelayPredictionModel("v1")
        assert model.model_version == "v1"
        assert not model.is_trained
        assert model.feature_names is not None
        assert len(model.feature_names) > 0
    
    def test_model_save_load(self, tmp_path):
        model = DelayPredictionModel("v1")
        model_path = tmp_path / "test_model.pkl"
        
        # Train on dummy data
        import numpy as np
        X = np.random.rand(20, len(model.feature_names))
        y_delay = np.random.randint(0, 2, 20)
        y_delay_days = np.random.rand(20) * 5
        
        # Need at least some positive samples
        y_delay[0] = 1
        y_delay_days[0] = 3.0
        
        from sklearn.preprocessing import StandardScaler
        model.scaler.fit(X)
        X_scaled = model.scaler.transform(X)
        model.classifier.fit(X_scaled, y_delay)
        model.regressor.fit(X_scaled, y_delay_days)
        model.is_trained = True
        
        model.save(model_path)
        assert model_path.exists()
        
        loaded = DelayPredictionModel.load(model_path)
        assert loaded.model_version == "v1"
        assert loaded.is_trained
        assert loaded.feature_names == model.feature_names
    
    def test_predict_untrained_raises(self):
        model = DelayPredictionModel("v1")
        import numpy as np
        X = np.random.rand(1, len(model.feature_names))
        with pytest.raises(ValueError, match="not trained"):
            model.predict(X)
    
    def test_predict_trained(self):
        model = DelayPredictionModel("v1")
        import numpy as np
        X = np.random.rand(20, len(model.feature_names))
        y_delay = np.random.randint(0, 2, 20)
        y_delay_days = np.random.rand(20) * 5
        y_delay[0] = 1
        y_delay_days[0] = 3.0
        
        model.scaler.fit(X)
        X_scaled = model.scaler.transform(X)
        model.classifier.fit(X_scaled, y_delay)
        model.regressor.fit(X_scaled, y_delay_days)
        model.is_trained = True
        
        proba, delay, conf = model.predict(X[:5])
        assert len(proba) == 5
        assert len(delay) == 5
        assert len(conf) == 5
        assert all(0 <= p <= 1 for p in proba)
        assert all(d >= 0 for d in delay)
        assert all(0 <= c <= 1 for c in conf)


class TestDelayPredictionService:
    """Tests for the ML service."""
    
    def _setup_project_with_data(self, db: Session) -> tuple[Project, Organization, User]:
        """Create a project with activities, delays, benchmarks for testing."""
        org = Organization(name="Test Org", slug="test-ml")
        db.add(org)
        db.commit()
        db.refresh(org)

        project = Project(name="Test Project", code="TEST-ML", organization_id=org.id)
        db.add(project)
        db.commit()
        db.refresh(project)

        user = User(
            email="ml@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="ML Test User",
            role=UserRole.PROJECT_CONTROLS,
            organization_id=org.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create activities with actuals (for training)
        activities = []
        for i, (code, name, disc, start_offset, duration, actual_delay) in enumerate([
            ("A-100", "Excavation", "Civil", 0, 10, 5),      # Delayed
            ("A-110", "Foundation", "Civil", 10, 5, 0),       # On time
            ("A-120", "Backfill", "Civil", 15, 8, 3),         # Delayed
            ("B-100", "Steel Erection", "Structural", 20, 10, 2),  # Delayed
            ("B-110", "Connections", "Structural", 30, 5, 0),  # On time
            ("C-100", "Pipe Install", "Piping", 10, 15, 7),    # Delayed
            ("C-110", "Hydrotest", "Piping", 25, 5, 0),        # On time
            ("D-100", "Cable Pull", "Electrical", 15, 10, 1),  # Slight delay
        ]):
            planned_start = date(2026, 1, 1) + timedelta(days=start_offset)
            planned_finish = planned_start + timedelta(days=duration)
            actual_start = planned_start
            actual_finish = planned_finish + timedelta(days=actual_delay)
            
            act = ScheduleActivity(
                organization_id=org.id,
                project_id=project.id,
                activity_code=code,
                activity_name=name,
                discipline=disc,
                wbs=f"{disc[:3].upper()}.{i+1}",
                planned_start=planned_start,
                planned_finish=planned_finish,
                actual_start=actual_start,
                actual_finish=actual_finish,
            )
            db.add(act)
            activities.append(act)
        db.commit()
        for a in activities:
            db.refresh(a)

        # Add WBS nodes
        for act in activities:
            node = WBSNode(
                project_id=project.id,
                activity_code=act.activity_code,
                activity_name=act.activity_name,
                discipline=act.discipline,
                wbs=act.wbs,
                level=2,
                planned_start=act.planned_start,
                planned_finish=act.planned_finish,
                actual_start=act.actual_start,
                actual_finish=act.actual_finish,
            )
            db.add(node)
        db.commit()

        # Add delay reasons
        wbs_nodes = db.query(WBSNode).filter(WBSNode.project_id == project.id).all()
        delay_data = [
            (wbs_nodes[0], DelayCategory.WEATHER, 5, True),
            (wbs_nodes[2], DelayCategory.RESOURCE, 3, False),
            (wbs_nodes[3], DelayCategory.MATERIAL, 2, True),
            (wbs_nodes[5], DelayCategory.DESIGN, 7, True),
            (wbs_nodes[7], DelayCategory.EXTERNAL, 1, False),
        ]
        for wbs, cat, days, critical in delay_data:
            delay = DelayReason(
                project_id=project.id,
                wbs_node_id=wbs.id,
                category=cat,
                description=f"{cat.value} delay",
                impact_days=days,
                is_critical_path=critical,
            )
            db.add(delay)
        db.commit()

        # Add productivity benchmarks
        benchmarks_data = [
            ("Civil", "Excavation", "m3/day", 100, 105, 10, 12, 8.75),
            ("Civil", "Foundation", "m3/day", 200, 190, 5, 6, 31.7),
            ("Structural", "Steel Erection", "ton/day", 50, 48, 10, 12, 4.0),
            ("Piping", "Pipe Install", "m/day", 300, 320, 15, 12, 26.7),
            ("Electrical", "Cable Pull", "m/day", 500, 480, 10, 9, 53.3),
        ]
        for disc, act_type, unit, plan_qty, actual_qty, plan_dur, actual_dur, rate in benchmarks_data:
            bench = ProductivityBenchmark(
                organization_id=org.id,
                project_id=project.id,
                discipline=disc,
                activity_type=act_type,
                unit=unit,
                planned_quantity=plan_qty,
                actual_quantity=actual_qty,
                planned_duration_days=plan_dur,
                actual_duration_days=actual_dur,
                productivity_rate=rate,
                sample_size=3,
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
            )
            db.add(bench)
        db.commit()

        # Add ingestion sources
        for code, name, desc in [("VOICE", "Voice", "Voice"), ("TEXT_DIARY", "Diary", "Diary")]:
            src = IngestionSource(code=code, name=name, description=desc)
            db.add(src)
        db.commit()

        # Add progress events and reviews for confidence
        sources = db.query(IngestionSource).all()
        for i, act in enumerate(activities):
            event = ProgressEvent(
                organization_id=org.id,
                project_id=project.id,
                user_id=user.id,
                raw_text=f"Completed {act.activity_name}",
                activity_reference=act.activity_code,
                event_type="COMPLETE",
                event_date=act.actual_finish,
                discipline=act.discipline,
                source_type=sources[i % len(sources)].code,
                ingestion_source_id=sources[i % len(sources)].id,
            )
            db.add(event)
            db.commit()
            db.refresh(event)

            review = PlannerReview(
                progress_event_id=event.id,
                proposed_activity_id=act.id,
                final_activity_id=act.id,
                confidence_score=0.85 + (i * 0.01),
                confidence_level=ConfidenceLevel.HIGH,
                status=ReviewStatus.APPROVED,
                top_candidates_json='[]',
                score_breakdown_json='{}',
                matching_reasons_json='[]',
                reviewer_note="Approved",
                completed_at=act.actual_finish,
            )
            db.add(review)
        db.commit()

        return project, org, user

    def test_prepare_training_data(self, db_session: Session):
        """Test training data preparation."""
        project, org, user = self._setup_project_with_data(db_session)
        service = DelayPredictionService(db_session)
        
        X, y_delay, y_delay_days = service._prepare_training_data(project.id)
        
        # Should have 8 activities (all with actuals)
        assert len(X) == 8
        assert len(y_delay) == 8
        assert len(y_delay_days) == 8
        assert X.shape[1] == len(service.model.feature_names)
        
        # Should have some delayed and some on-time
        assert sum(y_delay) > 0  # Some delayed
        assert sum(y_delay) < len(y_delay)  # Some on-time
    
    def test_extract_features(self, db_session: Session):
        """Test feature extraction for a WBS node."""
        project, org, user = self._setup_project_with_data(db_session)
        service = DelayPredictionService(db_session)
        
        wbs = db_session.query(WBSNode).filter(WBSNode.project_id == project.id).first()
        features = service._extract_features(wbs, project.id)
        
        assert features
        assert "planned_duration_days" in features
        assert "disc_Civil" in features
        assert "historical_delay_rate" in features
        assert "benchmark_productivity_rate" in features
        assert "float_days" in features
    
    def test_train_insufficient_data(self, db_session: Session):
        """Test training with insufficient data returns failure."""
        org = Organization(name="Test", slug="test-empty")
        db_session.add(org)
        db_session.commit()
        
        project = Project(name="Empty", code="EMPTY", organization_id=org.id)
        db_session.add(project)
        db_session.commit()
        
        service = DelayPredictionService(db_session)
        result = service.train(project.id)
        
        assert result["status"] == "failed"
        assert "Insufficient" in result["error"]
    
    def test_train_success(self, db_session: Session):
        """Test successful training."""
        project, org, user = self._setup_project_with_data(db_session)
        service = DelayPredictionService(db_session)
        
        result = service.train(project.id)
        
        assert result["status"] == "completed"
        assert result["train_samples"] > 0
        assert result["test_samples"] > 0
        assert "auc_roc" in result
        assert "mae_delay_days" in result
        assert service.model.is_trained
        
        # Check training run saved
        training_run = service.get_latest_training_run(project.id)
        assert training_run is not None
        assert training_run.status == "completed"
    
    def test_predict_for_project(self, db_session: Session):
        """Test generating predictions."""
        project, org, user = self._setup_project_with_data(db_session)
        service = DelayPredictionService(db_session)
        
        # First train
        service.train(project.id)
        
        # Add in-progress activity (started but not finished)
        in_progress_act = ScheduleActivity(
            organization_id=org.id,
            project_id=project.id,
            activity_code="NEW-100",
            activity_name="New In Progress",
            discipline="Civil",
            wbs="NEW.1",
            planned_start=date(2026, 1, 1),
            planned_finish=date(2026, 1, 20),
            actual_start=date(2026, 1, 5),
            actual_finish=None,
        )
        db_session.add(in_progress_act)
        db_session.commit()
        db_session.refresh(in_progress_act)
        
        in_progress_wbs = WBSNode(
            project_id=project.id,
            activity_code="NEW-100",
            activity_name="New In Progress",
            discipline="Civil",
            wbs="NEW.1",
            level=2,
            planned_start=date(2026, 1, 1),
            planned_finish=date(2026, 1, 20),
            actual_start=date(2026, 1, 5),
            actual_finish=None,
        )
        db_session.add(in_progress_wbs)
        db_session.commit()
        db_session.refresh(in_progress_wbs)
        
        # Predict
        predictions = service.predict_for_project(project.id)
        
        assert len(predictions) >= 1
        pred = predictions[0]
        assert pred.project_id == project.id
        assert pred.wbs_node_id == in_progress_wbs.id
        assert 0 <= pred.delay_probability <= 1
        assert pred.expected_delay_days >= 0
        assert 0 <= pred.confidence_score <= 1
        assert pred.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert pred.model_version == "v1"
    
    def test_load_model(self, db_session: Session):
        """Test model loading from disk."""
        project, org, user = self._setup_project_with_data(db_session)
        service = DelayPredictionService(db_session)
        
        # Train and save
        service.train(project.id)
        
        # Create new service and load
        new_service = DelayPredictionService(db_session)
        new_service.load_model(project.id)
        
        assert new_service.model.is_trained
        assert new_service.model.model_version == "v1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])