from celery import shared_task
from datetime import datetime
from app.database import SessionLocal
from app.services.ml_delay_service import DelayPredictionService

@shared_task(name="app.workers.ml_retrain.retrain_delay_model")
def retrain_delay_model(project_id: int = None):
    """Periodic task to retrain the delay prediction model."""
    db = SessionLocal()
    try:
        service = DelayPredictionService(db)
        result = service.train(project_id)
        return {
            "status": result.get("status", "completed"),
            "project_id": project_id,
            "train_samples": result.get("train_samples", 0),
            "test_samples": result.get("test_samples", 0),
            "auc_roc": result.get("auc_roc"),
            "mae_delay_days": result.get("mae_delay_days"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@shared_task(name="app.workers.ml_retrain.predict_all_projects")
def predict_all_projects():
    """Generate predictions for all active projects."""
    db = SessionLocal()
    try:
        from app.models.project import Project
        from app.models.wbs_node import WBSNode
        
        projects = db.query(Project).filter(Project.is_active == True).all()
        results = []
        
        for project in projects:
            # Check if project has in-progress activities
            in_progress = db.query(WBSNode).filter(
                WBSNode.project_id == project.id,
                WBSNode.actual_start != None,
                WBSNode.actual_finish == None
            ).count()
            
            if in_progress > 0:
                service = DelayPredictionService(db)
                predictions = service.predict_for_project(project.id)
                results.append({
                    "project_id": project.id,
                    "project_name": project.name,
                    "predictions_generated": len(predictions),
                    "in_progress_activities": in_progress,
                })
        
        return {
            "status": "completed",
            "projects_processed": len(results),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()