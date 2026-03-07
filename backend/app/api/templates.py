"""Template management endpoints."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.template import Template
from app.schemas.template import (
    TemplateCreate,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdate,
)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=TemplateListResponse)
def list_templates(db: Session = Depends(get_db)):
    """List all saved templates."""
    templates = db.query(Template).order_by(Template.created_at.desc()).all()
    return TemplateListResponse(
        templates=[TemplateResponse.model_validate(t) for t in templates]
    )


@router.post("", response_model=TemplateResponse, status_code=201)
def create_template(data: TemplateCreate, db: Session = Depends(get_db)):
    """Create a new template from selections."""
    template = Template(
        name=data.name,
        selections=[s.model_dump() for s in data.selections],
        selection_count=len(data.selections),
        page_count=data.page_count,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return TemplateResponse.model_validate(template)


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: UUID, db: Session = Depends(get_db)):
    """Get a specific template with its selections."""
    template = db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    db: Session = Depends(get_db),
):
    """Update a template (e.g., rename it)."""
    template = db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if data.name is not None:
        template.name = data.name

    db.commit()
    db.refresh(template)
    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}")
def delete_template(template_id: UUID, db: Session = Depends(get_db)):
    """Delete a template."""
    template = db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    db.delete(template)
    db.commit()
    return {"detail": "Template deleted"}


@router.get("/{template_id}/export")
def export_template(template_id: UUID, db: Session = Depends(get_db)):
    """Download a template as a .tabula-template.json file."""
    template = db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    export_data = {
        "name": template.name,
        "page_count": template.page_count,
        "selection_count": template.selection_count,
        "template": template.selections,
    }

    content = json.dumps(export_data, indent=2, ensure_ascii=False)
    filename = f"{template.name}.tabula-template.json"

    return Response(
        content=content.encode("utf-8"),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/import", response_model=TemplateResponse, status_code=201)
async def import_template(file: UploadFile, db: Session = Depends(get_db)):
    """Import a .tabula-template.json file."""
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    # Validate required fields
    if "template" not in data:
        raise HTTPException(
            status_code=400,
            detail="Missing 'template' key in file. Not a valid Tabula template.",
        )

    selections = data["template"]
    required_keys = {"page", "extraction_method", "x1", "y1", "x2", "y2"}
    for sel in selections:
        if not required_keys.issubset(sel.keys()):
            raise HTTPException(
                status_code=400,
                detail=f"Each selection must have keys: {required_keys}",
            )
        # Ensure width/height are present
        if "width" not in sel:
            sel["width"] = sel["x2"] - sel["x1"]
        if "height" not in sel:
            sel["height"] = sel["y2"] - sel["y1"]

    name = data.get("name", file.filename or "Imported template")
    page_count = data.get("page_count", max((s["page"] for s in selections), default=1))

    template = Template(
        name=name,
        selections=selections,
        selection_count=len(selections),
        page_count=page_count,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return TemplateResponse.model_validate(template)
