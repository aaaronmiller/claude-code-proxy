"""
Reports API - Phase 3

Endpoints for report generation, templates, scheduling, and delivery

Author: AI Architect
Date: 2026-01-05
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import sqlite3
import json

from src.core.logging import logger
from src.services.usage.usage_tracker import usage_tracker
from src.services.report_generator import report_generator, ReportTemplate

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────────────────────────────────────

class ReportConfigRequest(BaseModel):
    """Request model for report generation"""
    template_id: str
    start_date: str
    end_date: str
    format: str = "excel"
    brand_logo: Optional[str] = None
    brand_color: str = "#3b82f6"

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATES MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/reports/templates")
async def get_report_templates():
    """Get all report templates"""
    try:
        if not usage_tracker.enabled:
            return {"templates": []}

        templates = report_generator.get_templates()

        return {
            "templates": [{
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "config": t.config,
                "created_at": t.created_at,
                "created_by": t.created_by,
                "is_default": t.is_default
            } for t in templates],
            "count": len(templates)
        }

    except Exception as e:
        logger.error(f"Get templates failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/reports/templates")
async def create_report_template(template_data: Dict[str, Any]):
    """Create a new report template"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        template_id = report_generator.create_template(
            name=template_data.get("name", "Custom Template"),
            description=template_data.get("description", ""),
            config=template_data.get("config", {}),
            created_by=template_data.get("created_by", "web_ui"),
            is_default=template_data.get("is_default", False)
        )

        return {
            "success": True,
            "template_id": template_id,
            "message": "Template created successfully"
        }

    except Exception as e:
        logger.error(f"Create template failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/reports/templates/{template_id}")
async def get_report_template(template_id: str):
    """Get specific report template"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        template = report_generator.get_template(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "config": template.config,
            "created_at": template.created_at,
            "created_by": template.created_by,
            "is_default": template.is_default
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get template failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/reports/templates/{template_id}")
async def delete_report_template(template_id: str):
    """Delete report template"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute("DELETE FROM report_templates WHERE id = ?", (template_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted == 0:
            raise HTTPException(status_code=404, detail="Template not found")

        return {"success": True, "template_id": template_id, "message": "Template deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete template failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# REPORT GENERATION
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/reports/generate")
async def generate_report(report_config: ReportConfigRequest):
    """Generate report in specified format (PDF, Excel, CSV)"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        template_id = report_config.template_id
        start_date = report_config.start_date
        end_date = report_config.end_date
        format_type = report_config.format
        brand_logo = report_config.brand_logo
        brand_color = report_config.brand_color

        # Get template
        template = report_generator.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Generate report
        if format_type == "pdf":
            data = report_generator.generate_pdf(template, start_date, end_date, brand_logo, brand_color)
            media_type = "application/pdf"
            filename = f"{template.name.replace(' ', '_')}_{start_date}_{end_date}.pdf"
        elif format_type == "excel":
            data = report_generator.generate_excel(template, start_date, end_date)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"{template.name.replace(' ', '_')}_{start_date}_{end_date}.xlsx"
        elif format_type == "csv":
            data = report_generator.generate_csv(template, start_date, end_date).encode('utf-8')
            media_type = "text/csv"
            filename = f"{template.name.replace(' ', '_')}_{start_date}_{end_date}.csv"
        else:
            raise HTTPException(status_code=400, detail="Invalid format type")

        return {
            "success": True,
            "template": template.name,
            "format": format_type,
            "size": len(data),
            "filename": filename,
            "download_url": f"/api/reports/download/{template_id}/{format_type}?start={start_date}&end={end_date}",
            "data": data.hex()  # Return as hex for safe transmission
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/reports/download/{template_id}/{format_type}")
async def download_report(template_id: str, format_type: str, start: str = Query(...), end: str = Query(...)):
    """Download generated report file"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        template = report_generator.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if format_type == "pdf":
            data = report_generator.generate_pdf(template, start, end)
            media_type = "application/pdf"
            filename = f"{template.name.replace(' ', '_')}_{start}_{end}.pdf"
        elif format_type == "excel":
            data = report_generator.generate_excel(template, start, end)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"{template.name.replace(' ', '_')}_{start}_{end}.xlsx"
        elif format_type == "csv":
            data = report_generator.generate_csv(template, start, end).encode('utf-8')
            media_type = "text/csv"
            filename = f"{template.name.replace(' ', '_')}_{start}_{end}.csv"
        else:
            raise HTTPException(status_code=400, detail="Invalid format")

        from fastapi.responses import Response
        return Response(content=data, media_type=media_type, headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/reports/generate/preview")
async def preview_report(report_config: Dict[str, Any]):
    """Generate report preview (metadata only, no file)"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        template_id = report_config.get("template_id")
        start_date = report_config.get("start_date")
        end_date = report_config.get("end_date")

        template = report_generator.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        data = report_generator.generate_report_data(template, start_date, end_date)

        return {
            "preview": data,
            "template": template.name,
            "date_range": {"start": start_date, "end": end_date}
        }

    except Exception as e:
        logger.error(f"Preview report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULED REPORTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/reports/schedule")
async def get_scheduled_reports():
    """Get all scheduled reports"""
    try:
        if not usage_tracker.enabled:
            return {"scheduled": []}

        scheduled = report_generator.get_scheduled_reports()

        return {
            "scheduled": scheduled,
            "count": len(scheduled)
        }

    except Exception as e:
        logger.error(f"Get scheduled reports failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/reports/schedule")
async def schedule_report(schedule_config: Dict[str, Any]):
    """Create scheduled report"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        template_id = schedule_config.get("template_id")
        frequency = schedule_config.get("frequency", "weekly")  # daily, weekly, monthly
        recipients = schedule_config.get("recipients", [])
        timezone = schedule_config.get("timezone", "UTC")

        schedule_id = report_generator.schedule_report(
            template_id=template_id,
            frequency=frequency,
            recipients=recipients,
            timezone=timezone
        )

        if not schedule_id:
            raise HTTPException(status_code=400, detail="Failed to create schedule")

        return {
            "success": True,
            "schedule_id": schedule_id,
            "message": f"Report scheduled {frequency}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schedule report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/reports/schedule/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str):
    """Enable/disable scheduled report"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        conn = sqlite3.connect(usage_tracker.db_path)

        # Get current state
        cursor = conn.execute("SELECT is_active FROM scheduled_reports WHERE id = ?", (schedule_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Schedule not found")

        new_state = 1 - row[0]
        cursor.execute("UPDATE scheduled_reports SET is_active = ? WHERE id = ?", (new_state, schedule_id))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "schedule_id": schedule_id,
            "is_active": bool(new_state),
            "message": f"Schedule {'enabled' if new_state else 'disabled'}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Toggle schedule failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# EXECUTION HISTORY
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/reports/history")
async def get_execution_history(limit: int = Query(50, ge=1, le=200)):
    """Get report execution history"""
    try:
        if not usage_tracker.enabled:
            return {"history": []}

        history = report_generator.get_execution_history(limit)

        return {
            "history": history,
            "count": len(history)
        }

    except Exception as e:
        logger.error(f"Get execution history failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULED REPORTS CHECKER (Background Task)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/reports/schedule/check")
async def check_scheduled_reports():
    """Check and execute due scheduled reports (manual trigger)"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        results = report_generator.check_scheduled_reports()

        return {
            "checked": True,
            "reports_processed": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"Check scheduled reports failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/reports/health")
async def reports_health():
    """Check if report generation is available"""
    return {
        "status": "healthy",
        "enabled": usage_tracker.enabled,
        "formats_supported": ["pdf", "excel", "csv"],
        "features": ["templates", "scheduling", "exports", "previews"]
    }