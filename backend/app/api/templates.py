"""Template management endpoints."""

import json
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.template import Template
from app.models.user import User
from app.schemas.template import (
    TemplateCreate,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdate,
)

router = APIRouter(prefix="/templates", tags=["templates"])


def _template_to_response(t: Template) -> TemplateResponse:
    """Convert a Template ORM object to a TemplateResponse."""
    data = TemplateResponse.model_validate(t)
    if t.owner:
        data.owner_username = t.owner.username
    return data


def _check_template_access(template: Template | None, user: User | None) -> Template:
    """Verify template exists and the user has access."""
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    if user is not None and not user.is_admin:
        if template.user_id != user.id and not template.is_shared:
            raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("", response_model=TemplateListResponse)
def list_templates(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """List templates.

    In mono mode: all templates.
    In multi mode: own templates + shared templates.
    Admins see all templates.
    """
    query = db.query(Template)

    if user is not None and not user.is_admin:
        query = query.filter(
            or_(Template.user_id == user.id, Template.is_shared.is_(True))
        )

    templates = query.order_by(Template.created_at.desc()).all()
    return TemplateListResponse(
        templates=[_template_to_response(t) for t in templates]
    )


@router.post("", response_model=TemplateResponse, status_code=201)
def create_template(
    data: TemplateCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Create a new template from selections."""
    template = Template(
        name=data.name,
        selections=[s.model_dump() for s in data.selections],
        selection_count=len(data.selections),
        page_count=data.page_count,
        user_id=user.id if user else None,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _template_to_response(template)


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Get a specific template with its selections."""
    template = _check_template_access(db.get(Template, template_id), user)
    return _template_to_response(template)


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Update a template (e.g., rename it)."""
    template = _check_template_access(db.get(Template, template_id), user)

    # In multi mode, only owner or admin can update
    if user is not None and not user.is_admin and template.user_id != user.id:
        raise HTTPException(status_code=403, detail="Cannot modify shared template")

    if data.name is not None:
        template.name = data.name

    db.commit()
    db.refresh(template)
    return _template_to_response(template)


@router.delete("/{template_id}")
def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Delete a template."""
    template = _check_template_access(db.get(Template, template_id), user)

    # In multi mode, only owner or admin can delete
    if user is not None and not user.is_admin and template.user_id != user.id:
        raise HTTPException(status_code=403, detail="Cannot delete shared template")

    db.delete(template)
    db.commit()
    return {"detail": "Template deleted"}


@router.get("/{template_id}/export")
def export_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Download a template as a .tabula-template.json file."""
    template = _check_template_access(db.get(Template, template_id), user)

    export_data = {
        "name": template.name,
        "page_count": template.page_count,
        "selection_count": template.selection_count,
        "template": template.selections,
    }

    content = json.dumps(export_data, indent=2, ensure_ascii=False)
    filename = f"{template.name}.tabula-template.json"

    # Build safe Content-Disposition header (RFC 5987)
    ascii_name = filename.encode("ascii", "ignore").decode("ascii")
    ascii_name = ascii_name.replace('"', "").replace("\r", "").replace("\n", "")
    encoded = quote(filename, safe="")
    disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}"

    return Response(
        content=content.encode("utf-8"),
        media_type="application/json",
        headers={
            "Content-Disposition": disposition,
        },
    )


@router.post("/import", response_model=TemplateResponse, status_code=201)
async def import_template(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
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
        user_id=user.id if user else None,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _template_to_response(template)


@router.put("/{template_id}/share")
def toggle_share_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    _admin: User | None = Depends(require_admin),
):
    """Toggle a template's shared status (admin only)."""
    template = db.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.is_shared = not template.is_shared
    db.commit()
    return {"is_shared": template.is_shared}
