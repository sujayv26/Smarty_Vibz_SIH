from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.xer.export import export_schedule_to_xer
from fastapi.responses import StreamingResponse
import io

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.post("/export/p6/{external_schedule_id}", summary="Export schedule to XER format with approved actuals")
async def export_p6_schedule(
    external_schedule_id: int,
    include_approved_actuals: bool = Query(True, description="Include approved actual start/finish dates"),
    db: Session = Depends(get_db)
):
    try:
        xer_content, stats = export_schedule_to_xer(db, external_schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    filename = f"exported_schedule_{external_schedule_id}.xer"
    return StreamingResponse(
        io.BytesIO(xer_content.encode("utf-8")),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/p6/{external_schedule_id}/preview", summary="Preview XER export content and stats")
async def preview_p6_export(
    external_schedule_id: int,
    include_approved_actuals: bool = Query(True),
    db: Session = Depends(get_db)
):
    try:
        xer_content, stats = export_schedule_to_xer(db, external_schedule_id, include_approved_actuals)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export preview failed: {str(e)}")

    return {
        "stats": stats,
        "preview": xer_content[:5000] + ("..." if len(xer_content) > 5000 else ""),
    }