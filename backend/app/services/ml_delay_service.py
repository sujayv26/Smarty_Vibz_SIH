import json
import pickle
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

# ML imports - using scikit-learn for baseline model
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

from app.models.delay_prediction import DelayPrediction, ModelTrainingRun
from app.models.delay_reason import DelayReason, DelayCategory
from app.models.productivity_benchmark import ProductivityBenchmark
from app.models.schedule import ScheduleActivity
from app.models.wbs_node import WBSNode
from app.models.progress import ProgressEvent
from app.models.confidence import PlannerReview, ReviewStatus
from app.models.delay_impact import DelayImpact
from app.database import SessionLocal

logger = logging.getLogger(__name__)

# Use local directory for model storage, fallback to /app/models/ml for production
MODEL_DIR = Path("./models/ml")
try:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    # Fallback for read-only filesystems (e.g., test environments)
    MODEL_DIR = Path("./ml_models")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_NAMES = [
    # Activity features
    "planned_duration_days",
    "is_milestone",
    "is_unplanned",
    "wbs_level",
    # Discipline encoding (one-hot)
    "disc_Civil", "disc_Structural", "disc_Mechanical", 
    "disc_Electrical", "disc_Piping", "disc_Instrumentation", "disc_Architectural",
    # Historical performance
    "historical_delay_rate",
    "historical_avg_delay_days",
    "historical_critical_path_rate",
    # Productivity benchmarks
    "benchmark_productivity_rate",
    "benchmark_variance",
    # Schedule context
    "days_to_planned_start",
    "days_to_planned_finish",
    "float_days",
    "is_critical_path",
    # Delay history
    "recent_delay_count",
    "recent_delay_days",
    # Matching confidence
    "avg_confidence_score",
    "review_rate",
]

DISCIPLINES = ["Civil", "Structural", "Mechanical", "Electrical", "Piping", "Instrumentation", "Architectural"]


class DelayPredictionModel:
    """ML model for delay prediction - uses RandomForest for both classification and regression."""
    
    def __init__(self, model_version: str = "v1"):
        self.model_version = model_version
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        self.regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
        self.scaler = StandardScaler()
        self.feature_names = FEATURE_NAMES
        self.is_trained = False
    
    def save(self, path: Path):
        """Save model to disk."""
        model_data = {
            "classifier": self.classifier,
            "regressor": self.regressor,
            "scaler": self.scaler,
            "feature_names": FEATURE_NAMES,
            "model_version": self.model_version,
            "is_trained": self.is_trained,
        }
        with open(path, "wb") as f:
            pickle.dump(model_data, f)
    
    @classmethod
    def load(cls, path: Path) -> "DelayPredictionModel":
        """Load model from disk."""
        with open(path, "rb") as f:
            model_data = pickle.load(f)
        model = cls(model_data["model_version"])
        model.classifier = model_data["classifier"]
        model.regressor = model_data["regressor"]
        model.scaler = model_data["scaler"]
        model.feature_names = model_data["feature_names"]
        model.is_trained = model_data["is_trained"]
        return model
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Predict delay probability, expected delay days, and confidence.
        Returns: (delay_probability, expected_delay_days, confidence_score)
        """
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        
        # Classification: delay probability
        delay_proba = self.classifier.predict_proba(X_scaled)[:, 1]
        
        # Regression: expected delay days (only for delayed samples)
        expected_delay = self.regressor.predict(X_scaled)
        expected_delay = np.maximum(expected_delay, 0)  # No negative delays
        
        # Confidence: based on classifier probability margin
        proba_all = self.classifier.predict_proba(X_scaled)
        confidence = np.max(proba_all, axis=1)
        
        return delay_proba, expected_delay, confidence


class DelayPredictionService:
    """Service for training and serving delay predictions."""
    
    def __init__(self, db: Session, model_version: str = "v1"):
        self.db = db
        self.model_version = model_version
        self.model = DelayPredictionModel(model_version)
    
    def _extract_features(self, wbs_node: WBSNode, project_id: int) -> Dict[str, float]:
        """Extract features for a WBS node."""
        activity = self.db.query(ScheduleActivity).filter(
            ScheduleActivity.project_id == project_id,
            ScheduleActivity.activity_code == wbs_node.activity_code
        ).first()
        
        if not activity:
            return {}
        
        features = {}
        
        # Activity features
        features["planned_duration_days"] = (activity.planned_finish - activity.planned_start).days
        features["is_milestone"] = float(wbs_node.is_milestone)
        features["is_unplanned"] = float(wbs_node.is_unplanned)
        features["wbs_level"] = float(wbs_node.level)
        
        # Discipline one-hot
        for disc in DISCIPLINES:
            features[f"disc_{disc}"] = 1.0 if wbs_node.discipline == disc else 0.0
        
        # Historical performance from delay_reasons
        delays = self.db.query(DelayReason).filter(
            DelayReason.wbs_node_id == wbs_node.id
        ).all()
        
        if delays:
            features["historical_delay_rate"] = len(delays) / max(1, features["planned_duration_days"] / 7)  # per week
            features["historical_avg_delay_days"] = np.mean([d.impact_days for d in delays])
            features["historical_critical_path_rate"] = np.mean([float(d.is_critical_path) for d in delays])
            features["recent_delay_count"] = len([d for d in delays if d.created_at > datetime.utcnow() - timedelta(days=90)])
            features["recent_delay_days"] = sum(d.impact_days for d in delays if d.created_at > datetime.utcnow() - timedelta(days=90))
        else:
            features["historical_delay_rate"] = 0.0
            features["historical_avg_delay_days"] = 0.0
            features["historical_critical_path_rate"] = 0.0
            features["recent_delay_count"] = 0
            features["recent_delay_days"] = 0.0
        
        # Productivity benchmarks
        benchmarks = self.db.query(ProductivityBenchmark).filter(
            ProductivityBenchmark.project_id == project_id,
            ProductivityBenchmark.discipline == wbs_node.discipline
        ).all()
        
        if benchmarks:
            features["benchmark_productivity_rate"] = np.mean([b.productivity_rate for b in benchmarks if b.productivity_rate])
            planned_durs = [b.planned_duration_days for b in benchmarks if b.planned_duration_days]
            actual_durs = [b.actual_duration_days for b in benchmarks if b.actual_duration_days]
            if planned_durs and actual_durs:
                features["benchmark_variance"] = np.mean([(a - p) / p for a, p in zip(actual_durs, planned_durs) if p > 0])
            else:
                features["benchmark_variance"] = 0.0
        else:
            features["benchmark_productivity_rate"] = 1.0
            features["benchmark_variance"] = 0.0
        
        # Schedule context
        today = date.today()
        features["days_to_planned_start"] = max(0, (wbs_node.planned_start - today).days)
        features["days_to_planned_finish"] = max(0, (wbs_node.planned_finish - today).days)
        
        # Float days (from delay_impact or computed)
        impacts = self.db.query(DelayImpact).filter(
            DelayImpact.impacted_wbs_node_id == wbs_node.id
        ).all()
        if impacts:
            features["float_days"] = float(min(i.remaining_float_days for i in impacts if i.remaining_float_days is not None))
            features["is_critical_path"] = float(any(i.is_critical_path for i in impacts))
        else:
            # Estimate from schedule position
            features["float_days"] = 5.0
            features["is_critical_path"] = 0.0
        
        # Matching confidence from reviews
        reviews = self.db.query(PlannerReview).join(
            ProgressEvent, PlannerReview.progress_event_id == ProgressEvent.id
        ).filter(
            ProgressEvent.project_id == project_id,
            ProgressEvent.activity_reference == wbs_node.activity_code
        ).all()
        
        if reviews:
            features["avg_confidence_score"] = np.mean([r.confidence_score for r in reviews])
            features["review_rate"] = len([r for r in reviews if r.status != ReviewStatus.APPROVED]) / len(reviews)
        else:
            features["avg_confidence_score"] = 0.85
            features["review_rate"] = 0.0
        
        return features
    
    def _prepare_training_data(self, project_id: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Prepare training data from historical records."""
        # Get all WBS nodes with actual start/finish
        wbs_nodes = self.db.query(WBSNode).filter(
            WBSNode.project_id == project_id,
            WBSNode.actual_start != None,
            WBSNode.actual_finish != None
        ).all()
        
        X_list = []
        y_delay_list = []  # Binary: was delayed?
        y_delay_days_list = []  # Continuous: how many days delayed?
        
        for wbs in wbs_nodes:
            features = self._extract_features(wbs, project_id)
            if not features:
                continue
            
            # Ensure all features present
            feature_vector = [features.get(name, 0.0) for name in self.model.feature_names]
            X_list.append(feature_vector)
            
            # Target: was there a delay?
            planned_duration = (wbs.planned_finish - wbs.planned_start).days
            actual_duration = (wbs.actual_finish - wbs.actual_start).days
            delay_days = max(0, actual_duration - planned_duration)
            
            y_delay_list.append(1 if delay_days > 0 else 0)
            y_delay_days_list.append(delay_days)
        
        if not X_list:
            return np.array([]), np.array([]), np.array([])
        
        return np.array(X_list), np.array(y_delay_list), np.array(y_delay_days_list)
    
    def train(self, project_id: int = None) -> Dict[str, Any]:
        """Train the model and save it."""
        start_time = datetime.utcnow()
        
        if project_id:
            X, y_delay, y_delay_days = self._prepare_training_data(project_id)
        else:
            # Global model: combine data from all projects
            projects = self.db.query(WBSNode.project_id).distinct().all()
            X_all, y_delay_all, y_delay_days_all = [], [], []
            for (pid,) in projects:
                X_p, y_d_p, y_dd_p = self._prepare_training_data(pid)
                if len(X_p) > 0:
                    X_all.append(X_p)
                    y_delay_all.append(y_d_p)
                    y_delay_days_all.append(y_dd_p)
            if X_all:
                X = np.vstack(X_all)
                y_delay = np.hstack(y_delay_all)
                y_delay_days = np.hstack(y_delay_days_all)
            else:
                X, y_delay, y_delay_days = np.array([]), np.array([]), np.array([])
        
        if len(X) < 5:
            logger.warning(f"Insufficient training data: {len(X)} samples")
            return {"status": "failed", "error": "Insufficient training data", "train_samples": len(X)}
        
        # Split data
        X_train, X_test, y_delay_train, y_delay_test, y_days_train, y_days_test = train_test_split(
            X, y_delay, y_delay_days, test_size=0.2, random_state=42, stratify=y_delay
        )
        
        # Scale features
        X_train_scaled = self.model.scaler.fit_transform(X_train)
        X_test_scaled = self.model.scaler.transform(X_test)
        
        # Train classifier
        self.model.classifier.fit(X_train_scaled, y_delay_train)
        
        # Train regressor (only on delayed samples)
        delay_mask_train = y_delay_train == 1
        if np.sum(delay_mask_train) > 5:
            self.model.regressor.fit(X_train_scaled[delay_mask_train], y_days_train[delay_mask_train])
        else:
            # Fallback: train on all data
            self.model.regressor.fit(X_train_scaled, y_days_train)
        
        self.model.is_trained = True
        
        # Evaluate
        delay_proba = self.model.classifier.predict_proba(X_test_scaled)[:, 1]
        delay_pred = self.model.classifier.predict(X_test_scaled)
        expected_delay = self.model.regressor.predict(X_test_scaled)
        expected_delay = np.maximum(expected_delay, 0)
        
        metrics = {
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "auc_roc": roc_auc_score(y_delay_test, delay_proba) if len(np.unique(y_delay_test)) > 1 else 0.5,
            "auc_pr": average_precision_score(y_delay_test, delay_proba) if len(np.unique(y_delay_test)) > 1 else 0.0,
            "mae_delay_days": mean_absolute_error(y_days_test, expected_delay),
            "rmse_delay_days": np.sqrt(mean_squared_error(y_days_test, expected_delay)),
        }
        
        # Feature importance
        importance = dict(zip(self.model.feature_names, self.model.classifier.feature_importances_))
        metrics["feature_importance"] = json.dumps(importance)
        
        # Save model
        model_path = MODEL_DIR / f"delay_model_{self.model.model_version}_{project_id or 'global'}.pkl"
        self.model.save(model_path)
        
        # Save training run
        training_run = ModelTrainingRun(
            model_version=self.model.model_version,
            project_id=project_id,
            train_samples=len(X_train),
            test_samples=len(X_test),
            auc_roc=metrics["auc_roc"],
            auc_pr=metrics["auc_pr"],
            mae_delay_days=metrics["mae_delay_days"],
            rmse_delay_days=metrics["rmse_delay_days"],
            feature_importance=metrics["feature_importance"],
            hyperparameters=json.dumps({
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "min_samples_leaf": 2,
            }),
            feature_list=json.dumps(self.model.feature_names),
            status="completed",
            started_at=start_time,
            completed_at=datetime.utcnow(),
        )
        self.db.add(training_run)
        self.db.commit()
        
        logger.info(f"Training completed: {metrics}")
        return {"status": "completed", **metrics}
    
    def predict_for_project(self, project_id: int) -> List[DelayPrediction]:
        """Generate predictions for all in-progress activities in a project."""
        if self.model is None or not self.model.is_trained:
            self.load_model(project_id)
        
        if self.model is None or not self.model.is_trained:
            logger.warning(f"No trained model for project {project_id}")
            return []
        
        # Get in-progress activities (started but not finished)
        wbs_nodes = self.db.query(WBSNode).filter(
            WBSNode.project_id == project_id,
            WBSNode.actual_start != None,
            WBSNode.actual_finish == None
        ).all()
        
        if not wbs_nodes:
            return []
        
        X_list = []
        node_ids = []
        for wbs in wbs_nodes:
            features = self._extract_features(wbs, project_id)
            if not features:
                continue
            feature_vector = [features.get(name, 0.0) for name in self.model.feature_names]
            X_list.append(feature_vector)
            node_ids.append(wbs.id)
        
        if not X_list:
            return []
        
        X = np.array(X_list)
        delay_proba, expected_delay, confidence = self.model.predict(X)
        
        predictions = []
        for i, (node_id, proba, exp_delay, conf) in enumerate(zip(node_ids, delay_proba, expected_delay, confidence)):
            # Determine risk level
            if proba >= 0.7 and exp_delay >= 5:
                risk = "CRITICAL"
            elif proba >= 0.5 or exp_delay >= 3:
                risk = "HIGH"
            elif proba >= 0.3 or exp_delay >= 1:
                risk = "MEDIUM"
            else:
                risk = "LOW"
            
            pred = DelayPrediction(
                project_id=project_id,
                wbs_node_id=node_id,
                model_version=self.model.model_version,
                delay_probability=float(proba),
                expected_delay_days=float(exp_delay),
                confidence_score=float(conf),
                risk_level=risk,
                feature_importance=self.model.feature_names[i] if i < len(self.model.feature_names) else "",
                features_json=json.dumps(dict(zip(self.model.feature_names, X_list[i]))),
                prediction_date=date.today(),
                valid_until=date.today() + timedelta(days=7),
            )
            predictions.append(pred)
        
        # Bulk upsert
        for pred in predictions:
            existing = self.db.query(DelayPrediction).filter(
                DelayPrediction.project_id == pred.project_id,
                DelayPrediction.wbs_node_id == pred.wbs_node_id
            ).first()
            if existing:
                existing.delay_probability = pred.delay_probability
                existing.expected_delay_days = pred.expected_delay_days
                existing.confidence_score = pred.confidence_score
                existing.risk_level = pred.risk_level
                existing.feature_importance = pred.feature_importance
                existing.features_json = pred.features_json
                existing.prediction_date = pred.prediction_date
                existing.valid_until = pred.valid_until
                existing.updated_at = datetime.utcnow()
            else:
                self.db.add(pred)
        
        self.db.commit()
        return predictions
    
    def load_model(self, project_id: int = None):
        """Load trained model from disk."""
        model_path = MODEL_DIR / f"delay_model_{self.model_version}_{project_id or 'global'}.pkl"
        if model_path.exists():
            self.model = DelayPredictionModel.load(model_path)
            logger.info(f"Loaded model from {model_path}")
        else:
            # Try global model
            global_path = MODEL_DIR / f"delay_model_{self.model_version}_global.pkl"
            if global_path.exists():
                self.model = DelayPredictionModel.load(global_path)
                logger.info(f"Loaded global model from {global_path}")
            else:
                self.model = DelayPredictionModel(self.model_version)
                logger.warning(f"No model found, created new untrained model")
    
    def get_latest_training_run(self, project_id: int = None) -> Optional[ModelTrainingRun]:
        """Get the latest training run."""
        query = self.db.query(ModelTrainingRun).filter(
            ModelTrainingRun.model_version == self.model_version
        )
        if project_id:
            query = query.filter(ModelTrainingRun.project_id == project_id)
        return query.order_by(ModelTrainingRun.started_at.desc()).first()


def get_delay_prediction_service(db: Session = None, model_version: str = "v1") -> DelayPredictionService:
    """Factory function to get service instance."""
    if db is None:
        db = SessionLocal()
    return DelayPredictionService(db, model_version)