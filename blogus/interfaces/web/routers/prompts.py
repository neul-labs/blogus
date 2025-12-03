"""
FastAPI router for prompt operations.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..container import get_container, WebContainer
from ....application.dto import (
    AnalyzePromptRequest, AnalyzePromptResponse,
    ExecutePromptRequest, ExecutePromptResponse,
    GenerateTestRequest, GenerateTestResponse,
    PromptDto
)
from ....shared.exceptions import BlogusError, ValidationError, ResourceNotFoundError


router = APIRouter(prefix="/prompts", tags=["prompts"])


# =============================================================================
# Request Models
# =============================================================================

class CreatePromptRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=100000)
    description: str = Field("", max_length=500)
    goal: Optional[str] = Field(None, max_length=1000)
    category: str = Field("general", max_length=50)
    tags: Optional[List[str]] = Field(None)
    author: str = Field("unknown", max_length=100)


class UpdatePromptRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1, max_length=100000)
    description: Optional[str] = Field(None, max_length=500)
    goal: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = Field(None)
    author: Optional[str] = Field(None, max_length=100)


class AnalyzePromptRequestModel(BaseModel):
    prompt_text: Optional[str] = Field(None, max_length=100000)
    prompt_id: Optional[str] = Field(None)
    judge_model: str = Field(...)
    goal: Optional[str] = Field(None, max_length=1000)


class ExecutePromptRequestModel(BaseModel):
    prompt_text: Optional[str] = Field(None, max_length=100000)
    prompt_id: Optional[str] = Field(None)
    target_model: str = Field(...)
    variables: Optional[Dict[str, str]] = Field(None)


class GenerateTestRequestModel(BaseModel):
    prompt_text: Optional[str] = Field(None, max_length=100000)
    prompt_id: Optional[str] = Field(None)
    judge_model: str = Field(...)
    goal: Optional[str] = Field(None, max_length=1000)


class MultiModelExecuteRequest(BaseModel):
    prompt_text: Optional[str] = Field(None, max_length=100000)
    prompt_id: Optional[str] = Field(None)
    models: List[str] = Field(..., min_length=1, max_length=10)
    variables: Optional[Dict[str, str]] = Field(None)


class MultiModelCompareRequest(BaseModel):
    prompt_text: Optional[str] = Field(None, max_length=100000)
    prompt_id: Optional[str] = Field(None)
    models: List[str] = Field(..., min_length=1, max_length=10)
    goal: Optional[str] = Field(None, max_length=1000)
    reference_output: Optional[str] = Field(None, max_length=100000)
    variables: Optional[Dict[str, str]] = Field(None)
    include_llm_assessment: bool = Field(True)


# =============================================================================
# Response Models
# =============================================================================

class PromptResponse(BaseModel):
    id: str
    name: str
    description: str
    content: str
    goal: Optional[str] = None
    category: str
    tags: List[str]
    author: str
    version: int
    variables: List[str]
    is_template: bool
    usage_count: int
    created_at: str
    updated_at: str


class PromptListResponse(BaseModel):
    prompts: List[PromptResponse]
    total: int


class AnalysisResponse(BaseModel):
    prompt_id: str
    goal_alignment: int
    effectiveness: int
    suggestions: List[str]
    status: str
    inferred_goal: Optional[str] = None


class FragmentResponse(BaseModel):
    text: str
    fragment_type: str
    goal_alignment: int
    improvement_suggestion: str


class AnalyzePromptResponse(BaseModel):
    analysis: AnalysisResponse
    fragments: List[FragmentResponse]


class ExecutePromptResponse(BaseModel):
    result: str
    model_used: str
    duration: float
    prompt_id: Optional[str] = None


class TestCaseResponse(BaseModel):
    input_variables: dict
    expected_output: str
    goal_relevance: int


class GenerateTestResponse(BaseModel):
    test_case: TestCaseResponse
    prompt_id: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def prompt_to_response(prompt) -> PromptResponse:
    """Convert domain Prompt to API response."""
    return PromptResponse(
        id=prompt.id.value,
        name=prompt.name,
        description=prompt.description,
        content=prompt.content,
        goal=prompt.goal,
        category=prompt.category,
        tags=list(prompt.tags),
        author=prompt.author,
        version=prompt.version,
        variables=prompt.variables,
        is_template=prompt.is_template,
        usage_count=prompt.usage_count,
        created_at=prompt.created_at.isoformat(),
        updated_at=prompt.updated_at.isoformat()
    )


async def get_prompt_text(
    container: WebContainer,
    prompt_text: Optional[str],
    prompt_id: Optional[str]
) -> tuple[str, Optional[str], Optional[str]]:
    """Get prompt text from either direct text or prompt_id. Returns (text, goal, prompt_id)."""
    if prompt_id:
        prompt_dto = await container.get_prompt_service().get_prompt(prompt_id)
        if not prompt_dto:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
        return prompt_dto.text, prompt_dto.goal, prompt_id
    elif prompt_text:
        return prompt_text, None, None
    else:
        raise HTTPException(status_code=400, detail="Either prompt_text or prompt_id is required")


# =============================================================================
# CRUD Endpoints
# =============================================================================

@router.post("/", response_model=PromptResponse)
async def create_prompt(
    request: CreatePromptRequest,
    container: WebContainer = Depends(get_container)
):
    """Create a new prompt."""
    try:
        prompt = await container.get_prompt_service().create_prompt(
            name=request.name,
            content=request.content,
            description=request.description,
            goal=request.goal,
            category=request.category,
            tags=request.tags,
            author=request.author
        )
        # Get the full prompt object
        from ....domain.models.prompt import PromptId
        full_prompt = await container.get_prompt_service()._repository.find_by_id(PromptId(prompt.id))
        return prompt_to_response(full_prompt)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=PromptListResponse)
async def list_prompts(
    category: Optional[str] = None,
    has_variables: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    container: WebContainer = Depends(get_container)
):
    """List all prompts with optional filtering."""
    try:
        from ....domain.models.prompt import PromptId
        prompts = await container.get_prompt_service()._repository.find_all(
            category=category,
            has_variables=has_variables,
            limit=limit,
            offset=offset
        )
        return PromptListResponse(
            prompts=[prompt_to_response(p) for p in prompts],
            total=len(prompts)
        )
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str,
    container: WebContainer = Depends(get_container)
):
    """Get a prompt by ID."""
    try:
        from ....domain.models.prompt import PromptId
        prompt = await container.get_prompt_service()._repository.find_by_id(PromptId(prompt_id))
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
        return prompt_to_response(prompt)
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    request: UpdatePromptRequest,
    container: WebContainer = Depends(get_container)
):
    """Update a prompt. Updates content will increment version."""
    try:
        from ....domain.models.prompt import PromptId
        prompt = await container.get_prompt_service()._repository.find_by_id(PromptId(prompt_id))
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")

        # Update content if provided (increments version)
        if request.content is not None:
            prompt.update_content(request.content)

        # Update metadata
        prompt.update_metadata(
            name=request.name,
            description=request.description,
            goal=request.goal,
            category=request.category,
            tags=set(request.tags) if request.tags is not None else None,
            author=request.author
        )

        # Save changes
        await container.get_prompt_service()._repository.save(prompt)
        return prompt_to_response(prompt)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    container: WebContainer = Depends(get_container)
):
    """Delete a prompt."""
    try:
        from ....domain.models.prompt import PromptId
        deleted = await container.get_prompt_service()._repository.delete(PromptId(prompt_id))
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
        return {"message": f"Prompt {prompt_id} deleted"}
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Analysis & Testing Endpoints
# =============================================================================

@router.post("/analyze", response_model=AnalyzePromptResponse)
async def analyze_prompt(
    request: AnalyzePromptRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Analyze a prompt for effectiveness and goal alignment."""
    try:
        prompt_text, stored_goal, pid = await get_prompt_text(
            container, request.prompt_text, request.prompt_id
        )
        goal = request.goal or stored_goal

        app_request = AnalyzePromptRequest(
            prompt_text=prompt_text,
            judge_model=request.judge_model,
            goal=goal
        )
        response = await container.get_prompt_service().analyze_prompt(app_request)

        return AnalyzePromptResponse(
            analysis=AnalysisResponse(
                prompt_id=pid or response.analysis.prompt_id,
                goal_alignment=response.analysis.goal_alignment,
                effectiveness=response.analysis.effectiveness,
                suggestions=response.analysis.suggestions,
                status=response.analysis.status,
                inferred_goal=response.analysis.inferred_goal
            ),
            fragments=[
                FragmentResponse(
                    text=f.text,
                    fragment_type=f.fragment_type,
                    goal_alignment=f.goal_alignment,
                    improvement_suggestion=f.improvement_suggestion
                )
                for f in response.fragments
            ]
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=ExecutePromptResponse)
async def execute_prompt(
    request: ExecutePromptRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Execute a prompt with a target LLM."""
    try:
        prompt_text, _, pid = await get_prompt_text(
            container, request.prompt_text, request.prompt_id
        )

        # Render variables if provided
        if request.variables and pid:
            from ....domain.models.prompt import PromptId
            prompt = await container.get_prompt_service()._repository.find_by_id(PromptId(pid))
            if prompt:
                prompt_text = prompt.render(request.variables)
                prompt.increment_usage()
                await container.get_prompt_service()._repository.save(prompt)

        app_request = ExecutePromptRequest(
            prompt_text=prompt_text,
            target_model=request.target_model
        )
        response = await container.get_prompt_service().execute_prompt(app_request)

        return ExecutePromptResponse(
            result=response.result,
            model_used=response.model_used,
            duration=response.duration,
            prompt_id=pid
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=GenerateTestResponse)
async def generate_test(
    request: GenerateTestRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Generate a test case for a prompt."""
    try:
        prompt_text, stored_goal, pid = await get_prompt_text(
            container, request.prompt_text, request.prompt_id
        )
        goal = request.goal or stored_goal

        app_request = GenerateTestRequest(
            prompt_text=prompt_text,
            judge_model=request.judge_model,
            goal=goal
        )
        response = await container.get_prompt_service().generate_test_case(app_request)

        return GenerateTestResponse(
            test_case=TestCaseResponse(
                input_variables=response.test_case.input_variables,
                expected_output=response.test_case.expected_output,
                goal_relevance=response.test_case.goal_relevance
            ),
            prompt_id=pid
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Multi-Model Execution & Comparison Endpoints
# =============================================================================

@router.post("/execute/multi")
async def execute_multi_model(
    request: MultiModelExecuteRequest,
    container: WebContainer = Depends(get_container)
):
    """Execute a prompt across multiple LLM models in parallel."""
    try:
        prompt_text, _, pid = await get_prompt_text(
            container, request.prompt_text, request.prompt_id
        )

        result = await container.get_prompt_service().execute_multi_model(
            prompt_text=prompt_text,
            models=request.models,
            prompt_id=pid,
            variables=request.variables
        )

        # Increment usage if using saved prompt
        if pid:
            from ....domain.models.prompt import PromptId
            prompt = await container.get_prompt_service()._repository.find_by_id(PromptId(pid))
            if prompt:
                prompt.increment_usage()
                await container.get_prompt_service()._repository.save(prompt)

        return {
            "prompt_id": pid or result.prompt_id.value,
            "prompt_text": result.prompt_text,
            "total_duration_ms": result.total_duration_ms,
            "executions": [
                {
                    "id": e.id.value,
                    "model": e.model,
                    "output": e.output,
                    "latency_ms": e.latency_ms,
                    "success": e.success,
                    "error": e.error
                }
                for e in result.executions
            ]
        }

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.post("/execute/compare")
async def execute_and_compare(
    request: MultiModelCompareRequest,
    container: WebContainer = Depends(get_container)
):
    """Execute a prompt across multiple models and compare outputs."""
    try:
        prompt_text, stored_goal, pid = await get_prompt_text(
            container, request.prompt_text, request.prompt_id
        )
        goal = request.goal or stored_goal

        result = await container.get_prompt_service().execute_and_compare(
            prompt_text=prompt_text,
            models=request.models,
            prompt_id=pid,
            goal=goal,
            reference_output=request.reference_output,
            variables=request.variables,
            include_llm_assessment=request.include_llm_assessment
        )

        # Increment usage if using saved prompt
        if pid:
            from ....domain.models.prompt import PromptId
            prompt = await container.get_prompt_service()._repository.find_by_id(PromptId(pid))
            if prompt:
                prompt.increment_usage()
                await container.get_prompt_service()._repository.save(prompt)

        # Override prompt_id in result if we have one
        if pid:
            result["prompt_id"] = pid

        return result

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/models/available")
async def get_available_models(
    container: WebContainer = Depends(get_container)
):
    """Get list of available LLM models for execution."""
    try:
        models = container.get_prompt_service().get_available_models()
        return {"models": models}
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))
