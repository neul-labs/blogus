"""
FastAPI router for template operations.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..container import get_container, WebContainer
from ....application.dto import (
    CreateTemplateRequest, CreateTemplateResponse,
    RenderTemplateRequest, RenderTemplateResponse,
    TemplateDto
)
from ....shared.exceptions import BlogusError, ValidationError, ResourceNotFoundError


router = APIRouter(prefix="/templates", tags=["templates"])


# Pydantic models for API
class CreateTemplateRequestModel(BaseModel):
    template_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$')
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    content: str = Field(..., min_length=1)
    category: str = Field("general", max_length=50)
    tags: List[str] = Field(default_factory=list)
    author: str = Field("unknown", max_length=100)


class RenderTemplateRequestModel(BaseModel):
    template_id: str = Field(...)
    variables: dict = Field(...)


class UpdateTemplateRequestModel(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None


# Response models
class TemplateResponseModel(BaseModel):
    id: str
    name: str
    description: str
    content: str
    category: str
    tags: List[str]
    author: str
    version: str
    variables: List[str]
    usage_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateTemplateResponseModel(BaseModel):
    template: TemplateResponseModel


class RenderTemplateResponseModel(BaseModel):
    rendered_content: str


class ValidationErrorModel(BaseModel):
    issues: List[str]


@router.post("/", response_model=CreateTemplateResponseModel)
async def create_template(
    request: CreateTemplateRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Create a new template."""
    try:
        # Convert to application DTO
        app_request = CreateTemplateRequest(
            template_id=request.template_id,
            name=request.name,
            description=request.description,
            content=request.content,
            category=request.category,
            tags=request.tags,
            author=request.author
        )

        # Call application service
        response = await container.get_template_service().create_template(app_request)

        # Convert to API response
        return CreateTemplateResponseModel(
            template=_convert_template_dto(response.template)
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=TemplateResponseModel)
async def get_template(
    template_id: str,
    container: WebContainer = Depends(get_container)
):
    """Get a template by ID."""
    try:
        template = await container.get_template_service().get_template(template_id)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        return _convert_template_dto(template)

    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[TemplateResponseModel])
async def list_templates(
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    container: WebContainer = Depends(get_container)
):
    """List templates with optional filtering."""
    try:
        templates = await container.get_template_service().list_templates(category, tag)

        return [_convert_template_dto(template) for template in templates]

    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=TemplateResponseModel)
async def update_template(
    template_id: str,
    request: UpdateTemplateRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Update an existing template."""
    try:
        # Filter out None values
        updates = {k: v for k, v in request.dict().items() if v is not None}

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        # Special handling for content field
        if 'content' in updates:
            updates['template_content'] = updates.pop('content')

        template = await container.get_template_service().update_template(template_id, **updates)

        return _convert_template_dto(template)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    container: WebContainer = Depends(get_container)
):
    """Delete a template."""
    try:
        success = await container.get_template_service().delete_template(template_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        return {"message": f"Template {template_id} deleted successfully"}

    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/render", response_model=RenderTemplateResponseModel)
async def render_template(
    template_id: str,
    request: RenderTemplateRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Render a template with variables."""
    try:
        # Convert to application DTO
        app_request = RenderTemplateRequest(
            template_id=template_id,
            variables=request.variables
        )

        # Call application service
        response = await container.get_template_service().render_template(app_request)

        return RenderTemplateResponseModel(
            rendered_content=response.rendered_content
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/", response_model=List[str])
async def get_categories(
    container: WebContainer = Depends(get_container)
):
    """Get all template categories."""
    try:
        categories = await container.get_template_service().get_categories()
        return categories

    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/", response_model=List[str])
async def get_tags(
    container: WebContainer = Depends(get_container)
):
    """Get all template tags."""
    try:
        tags = await container.get_template_service().get_tags()
        return tags

    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidationErrorModel)
async def validate_template_content(
    content: str = Field(..., min_length=1),
    container: WebContainer = Depends(get_container)
):
    """Validate template content."""
    try:
        issues = await container.get_template_service().validate_template_content(content)

        return ValidationErrorModel(issues=issues)

    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


def _convert_template_dto(template_dto: TemplateDto) -> TemplateResponseModel:
    """Convert TemplateDto to API response model."""
    return TemplateResponseModel(
        id=template_dto.id,
        name=template_dto.name,
        description=template_dto.description,
        content=template_dto.content,
        category=template_dto.category,
        tags=template_dto.tags,
        author=template_dto.author,
        version=template_dto.version,
        variables=template_dto.variables,
        usage_count=template_dto.usage_count,
        created_at=template_dto.created_at.isoformat() if template_dto.created_at else None,
        updated_at=template_dto.updated_at.isoformat() if template_dto.updated_at else None
    )