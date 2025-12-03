"""
FastAPI router for prompt registry operations.
"""

from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..container import get_container, WebContainer
from ....application.dto import (
    RegisterDeploymentRequest, UpdateDeploymentContentRequest,
    UpdateDeploymentModelRequest, SetTrafficConfigRequest,
    ExecuteDeploymentRequest, RollbackDeploymentRequest,
    GetMetricsRequest, CompareVersionsRequest, TrafficRouteDto
)
from ....shared.exceptions import BlogusError, ConfigurationError


router = APIRouter(prefix="/registry", tags=["registry"])


# ==================== Request Models ====================

class RegisterDeploymentRequestModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, pattern=r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$')
    description: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=100000)
    model_id: str = Field(...)
    goal: Optional[str] = Field(None, max_length=1000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1000, ge=1, le=100000)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    fallback_models: Optional[List[str]] = None
    category: str = Field("general", max_length=50)
    tags: Optional[List[str]] = None
    author: str = Field("anonymous", max_length=100)


class UpdateContentRequestModel(BaseModel):
    new_content: str = Field(..., min_length=1, max_length=100000)
    author: str = Field(..., min_length=1, max_length=100)
    change_summary: Optional[str] = Field(None, max_length=500)


class UpdateModelConfigRequestModel(BaseModel):
    model_id: str = Field(...)
    author: str = Field(..., min_length=1, max_length=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=100000)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    fallback_models: Optional[List[str]] = None
    change_summary: Optional[str] = Field(None, max_length=500)


class TrafficRouteModel(BaseModel):
    version: int = Field(..., ge=1)
    weight: int = Field(..., ge=0, le=100)
    model_override: Optional[str] = None


class SetTrafficConfigRequestModel(BaseModel):
    routes: List[TrafficRouteModel]
    shadow_version: Optional[int] = Field(None, ge=1)


class ExecuteRequestModel(BaseModel):
    variables: Optional[Dict[str, str]] = None


class RollbackRequestModel(BaseModel):
    target_version: int = Field(..., ge=1)
    author: str = Field(..., min_length=1, max_length=100)


class SetStatusRequestModel(BaseModel):
    status: str = Field(..., pattern=r'^(active|inactive|archived)$')


# ==================== Response Models ====================

class ModelParametersResponseModel(BaseModel):
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    stop_sequences: Optional[List[str]]


class ModelConfigResponseModel(BaseModel):
    model_id: str
    parameters: Optional[ModelParametersResponseModel]
    fallback_models: Optional[List[str]]


class VersionRecordResponseModel(BaseModel):
    version: int
    content_hash: str
    content: str
    model_configuration: ModelConfigResponseModel
    created_at: str
    created_by: str
    change_summary: Optional[str]


class TrafficRouteResponseModel(BaseModel):
    version: int
    weight: int
    model_override: Optional[str]


class TrafficConfigResponseModel(BaseModel):
    routes: List[TrafficRouteResponseModel]
    shadow_version: Optional[int]


class DeploymentResponseModel(BaseModel):
    id: str
    name: str
    description: str
    content: str
    goal: Optional[str]
    model_configuration: ModelConfigResponseModel
    tags: List[str]
    category: str
    author: str
    version: int
    version_history: List[VersionRecordResponseModel]
    traffic_configuration: Optional[TrafficConfigResponseModel]
    status: str
    is_template: bool
    template_variables: List[str]
    created_at: str
    updated_at: str


class DeploymentSummaryResponseModel(BaseModel):
    id: str
    name: str
    description: str
    model_id: str
    version: int
    status: str
    category: str
    author: str
    tags: List[str]
    is_template: bool
    updated_at: str


class ExecutionResultResponseModel(BaseModel):
    prompt_name: str
    version: int
    model_used: str
    response: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    shadow_response: Optional[str]


class MetricsSummaryResponseModel(BaseModel):
    prompt_name: str
    version: Optional[int]
    total_executions: int
    success_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    total_tokens: int
    total_cost_usd: float
    period_hours: int


# ==================== Helper Functions ====================

def _deployment_dto_to_response(dto) -> DeploymentResponseModel:
    """Convert deployment DTO to response model."""
    return DeploymentResponseModel(
        id=dto.id,
        name=dto.name,
        description=dto.description,
        content=dto.content,
        goal=dto.goal,
        model_configuration=ModelConfigResponseModel(
            model_id=dto.model_config.model_id,
            parameters=ModelParametersResponseModel(
                temperature=dto.model_config.parameters.temperature,
                max_tokens=dto.model_config.parameters.max_tokens,
                top_p=dto.model_config.parameters.top_p,
                frequency_penalty=dto.model_config.parameters.frequency_penalty,
                presence_penalty=dto.model_config.parameters.presence_penalty,
                stop_sequences=dto.model_config.parameters.stop_sequences
            ) if dto.model_config.parameters else None,
            fallback_models=dto.model_config.fallback_models
        ),
        tags=dto.tags,
        category=dto.category,
        author=dto.author,
        version=dto.version,
        version_history=[
            VersionRecordResponseModel(
                version=vr.version,
                content_hash=vr.content_hash,
                content=vr.content,
                model_configuration=ModelConfigResponseModel(
                    model_id=vr.model_config.model_id,
                    parameters=ModelParametersResponseModel(
                        temperature=vr.model_config.parameters.temperature,
                        max_tokens=vr.model_config.parameters.max_tokens,
                        top_p=vr.model_config.parameters.top_p,
                        frequency_penalty=vr.model_config.parameters.frequency_penalty,
                        presence_penalty=vr.model_config.parameters.presence_penalty,
                        stop_sequences=vr.model_config.parameters.stop_sequences
                    ) if vr.model_config.parameters else None,
                    fallback_models=vr.model_config.fallback_models
                ),
                created_at=vr.created_at.isoformat(),
                created_by=vr.created_by,
                change_summary=vr.change_summary
            )
            for vr in dto.version_history
        ],
        traffic_configuration=TrafficConfigResponseModel(
            routes=[
                TrafficRouteResponseModel(
                    version=r.version,
                    weight=r.weight,
                    model_override=r.model_override
                )
                for r in dto.traffic_config.routes
            ],
            shadow_version=dto.traffic_config.shadow_version
        ) if dto.traffic_config else None,
        status=dto.status,
        is_template=dto.is_template,
        template_variables=dto.template_variables,
        created_at=dto.created_at.isoformat(),
        updated_at=dto.updated_at.isoformat()
    )


def _summary_dto_to_response(dto) -> DeploymentSummaryResponseModel:
    """Convert deployment summary DTO to response model."""
    return DeploymentSummaryResponseModel(
        id=dto.id,
        name=dto.name,
        description=dto.description,
        model_id=dto.model_id,
        version=dto.version,
        status=dto.status,
        category=dto.category,
        author=dto.author,
        tags=dto.tags,
        is_template=dto.is_template,
        updated_at=dto.updated_at.isoformat()
    )


# ==================== Deployment Management Endpoints ====================

@router.post("/deployments", response_model=DeploymentResponseModel, status_code=201)
async def register_deployment(
    request: RegisterDeploymentRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Register a new prompt deployment."""
    try:
        app_request = RegisterDeploymentRequest(
            name=request.name,
            description=request.description,
            content=request.content,
            model_id=request.model_id,
            goal=request.goal,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            fallback_models=request.fallback_models,
            category=request.category,
            tags=request.tags,
            author=request.author
        )

        response = await container.get_registry_service().register_deployment(app_request)
        return _deployment_dto_to_response(response.deployment)

    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments", response_model=List[DeploymentSummaryResponseModel])
async def list_deployments(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, pattern=r'^(active|inactive|archived)$'),
    category: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    container: WebContainer = Depends(get_container)
):
    """List all deployments with optional filters."""
    try:
        tags_list = tags.split(",") if tags else None
        deployments = await container.get_registry_service().list_deployments(
            limit=limit,
            offset=offset,
            status=status,
            category=category,
            tags=tags_list
        )
        return [_summary_dto_to_response(d) for d in deployments]

    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments/search", response_model=List[DeploymentSummaryResponseModel])
async def search_deployments(
    query: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    category: Optional[str] = None,
    author: Optional[str] = None,
    container: WebContainer = Depends(get_container)
):
    """Search deployments by various criteria."""
    try:
        tags_list = tags.split(",") if tags else None
        deployments = await container.get_registry_service().search_deployments(
            query=query,
            tags=tags_list,
            category=category,
            author=author
        )
        return [_summary_dto_to_response(d) for d in deployments]

    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments/{name}", response_model=DeploymentResponseModel)
async def get_deployment(
    name: str,
    container: WebContainer = Depends(get_container)
):
    """Get a deployment by name."""
    try:
        deployment = await container.get_registry_service().get_deployment(name)
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Deployment '{name}' not found")
        return _deployment_dto_to_response(deployment)

    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/deployments/{name}/content", response_model=DeploymentResponseModel)
async def update_deployment_content(
    name: str,
    request: UpdateContentRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Update deployment content (creates new version)."""
    try:
        app_request = UpdateDeploymentContentRequest(
            name=name,
            new_content=request.new_content,
            author=request.author,
            change_summary=request.change_summary
        )
        deployment = await container.get_registry_service().update_content(app_request)
        return _deployment_dto_to_response(deployment)

    except ConfigurationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/deployments/{name}/model", response_model=DeploymentResponseModel)
async def update_deployment_model(
    name: str,
    request: UpdateModelConfigRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Update deployment model configuration (creates new version)."""
    try:
        app_request = UpdateDeploymentModelRequest(
            name=name,
            model_id=request.model_id,
            author=request.author,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            fallback_models=request.fallback_models,
            change_summary=request.change_summary
        )
        deployment = await container.get_registry_service().update_model_config(app_request)
        return _deployment_dto_to_response(deployment)

    except ConfigurationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/deployments/{name}/traffic", response_model=DeploymentResponseModel)
async def set_traffic_config(
    name: str,
    request: SetTrafficConfigRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Set traffic routing configuration for A/B testing."""
    try:
        routes = [
            TrafficRouteDto(
                version=r.version,
                weight=r.weight,
                model_override=r.model_override
            )
            for r in request.routes
        ]

        app_request = SetTrafficConfigRequest(
            name=name,
            routes=routes,
            shadow_version=request.shadow_version
        )
        deployment = await container.get_registry_service().set_traffic_config(app_request)
        return _deployment_dto_to_response(deployment)

    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/deployments/{name}/traffic", response_model=DeploymentResponseModel)
async def clear_traffic_config(
    name: str,
    container: WebContainer = Depends(get_container)
):
    """Clear traffic configuration (route 100% to latest version)."""
    try:
        deployment = await container.get_registry_service().clear_traffic_config(name)
        return _deployment_dto_to_response(deployment)

    except ConfigurationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deployments/{name}/rollback", response_model=DeploymentResponseModel)
async def rollback_deployment(
    name: str,
    request: RollbackRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Rollback deployment to a previous version."""
    try:
        app_request = RollbackDeploymentRequest(
            name=name,
            target_version=request.target_version,
            author=request.author
        )
        deployment = await container.get_registry_service().rollback(app_request)
        return _deployment_dto_to_response(deployment)

    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/deployments/{name}/status", response_model=DeploymentResponseModel)
async def set_deployment_status(
    name: str,
    request: SetStatusRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Update deployment status."""
    try:
        deployment = await container.get_registry_service().set_status(name, request.status)
        return _deployment_dto_to_response(deployment)

    except ConfigurationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/deployments/{name}", status_code=204)
async def delete_deployment(
    name: str,
    container: WebContainer = Depends(get_container)
):
    """Delete a deployment."""
    try:
        deleted = await container.get_registry_service().delete_deployment(name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Deployment '{name}' not found")

    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Execution Endpoints ====================

@router.post("/deployments/{name}/execute", response_model=ExecutionResultResponseModel)
async def execute_deployment(
    name: str,
    request: ExecuteRequestModel = None,
    container: WebContainer = Depends(get_container)
):
    """Execute a prompt deployment."""
    try:
        app_request = ExecuteDeploymentRequest(
            name=name,
            variables=request.variables if request else None
        )
        response = await container.get_registry_service().execute(app_request)
        result = response.result

        return ExecutionResultResponseModel(
            prompt_name=result.prompt_name,
            version=result.version,
            model_used=result.model_used,
            response=result.response,
            latency_ms=result.latency_ms,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
            estimated_cost_usd=result.estimated_cost_usd,
            shadow_response=result.shadow_response
        )

    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Metrics Endpoints ====================

@router.get("/deployments/{name}/metrics", response_model=MetricsSummaryResponseModel)
async def get_deployment_metrics(
    name: str,
    version: Optional[int] = Query(None, ge=1),
    period_hours: int = Query(24, ge=1, le=720),
    container: WebContainer = Depends(get_container)
):
    """Get metrics for a deployment."""
    try:
        app_request = GetMetricsRequest(
            name=name,
            version=version,
            period_hours=period_hours
        )
        response = await container.get_registry_service().get_metrics(app_request)
        metrics = response.metrics

        return MetricsSummaryResponseModel(
            prompt_name=metrics.prompt_name,
            version=metrics.version,
            total_executions=metrics.total_executions,
            success_rate=metrics.success_rate,
            avg_latency_ms=metrics.avg_latency_ms,
            p95_latency_ms=metrics.p95_latency_ms,
            total_tokens=metrics.total_tokens,
            total_cost_usd=metrics.total_cost_usd,
            period_hours=metrics.period_hours
        )

    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments/{name}/metrics/compare", response_model=Dict[int, MetricsSummaryResponseModel])
async def compare_version_metrics(
    name: str,
    versions: str = Query(..., description="Comma-separated version numbers"),
    period_hours: int = Query(24, ge=1, le=720),
    container: WebContainer = Depends(get_container)
):
    """Compare metrics across versions."""
    try:
        version_list = [int(v.strip()) for v in versions.split(",")]

        app_request = CompareVersionsRequest(
            name=name,
            versions=version_list,
            period_hours=period_hours
        )
        response = await container.get_registry_service().compare_versions(app_request)

        return {
            version: MetricsSummaryResponseModel(
                prompt_name=metrics.prompt_name,
                version=metrics.version,
                total_executions=metrics.total_executions,
                success_rate=metrics.success_rate,
                avg_latency_ms=metrics.avg_latency_ms,
                p95_latency_ms=metrics.p95_latency_ms,
                total_tokens=metrics.total_tokens,
                total_cost_usd=metrics.total_cost_usd,
                period_hours=metrics.period_hours
            )
            for version, metrics in response.comparisons.items()
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid version format")
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Export/Import Endpoints ====================

class ImportRequestModel(BaseModel):
    content: str = Field(..., description="Content to import (JSON or YAML string)")
    format: str = Field("json", pattern=r'^(json|yaml)$')
    author: str = Field("import", max_length=100)


class ExportResponseModel(BaseModel):
    name: str
    format: str
    content: str


@router.get("/deployments/{name}/export")
async def export_deployment(
    name: str,
    format: str = Query("json", pattern=r'^(json|yaml|markdown)$'),
    include_history: bool = Query(False),
    container: WebContainer = Depends(get_container)
):
    """Export a deployment to JSON, YAML, or Markdown."""
    try:
        exported = await container.get_registry_service().export_deployment(
            name, format, include_history
        )

        # Return appropriate content type
        media_type = {
            "json": "application/json",
            "yaml": "application/x-yaml",
            "markdown": "text/markdown"
        }.get(format, "text/plain")

        from fastapi.responses import Response
        return Response(content=exported, media_type=media_type)

    except ConfigurationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deployments/import", response_model=DeploymentResponseModel, status_code=201)
async def import_deployment(
    request: ImportRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Import a deployment from JSON or YAML."""
    try:
        deployment = await container.get_registry_service().import_deployment(
            request.content, request.format, request.author
        )
        return _deployment_dto_to_response(deployment)

    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))
