"""
FastAPI router for prompt operations.
"""

from typing import List, Optional
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


# Pydantic models for API
class AnalyzePromptRequestModel(BaseModel):
    prompt_text: str = Field(..., min_length=1, max_length=100000)
    judge_model: str = Field(...)
    goal: Optional[str] = Field(None, max_length=1000)


class ExecutePromptRequestModel(BaseModel):
    prompt_text: str = Field(..., min_length=1, max_length=100000)
    target_model: str = Field(...)


class GenerateTestRequestModel(BaseModel):
    prompt_text: str = Field(..., min_length=1, max_length=100000)
    judge_model: str = Field(...)
    goal: Optional[str] = Field(None, max_length=1000)


class CreatePromptRequestModel(BaseModel):
    text: str = Field(..., min_length=1, max_length=100000)
    goal: Optional[str] = Field(None, max_length=1000)


# Response models
class AnalysisResponseModel(BaseModel):
    prompt_id: str
    goal_alignment: int
    effectiveness: int
    suggestions: List[str]
    status: str
    inferred_goal: Optional[str] = None


class FragmentResponseModel(BaseModel):
    text: str
    fragment_type: str
    goal_alignment: int
    improvement_suggestion: str


class AnalyzePromptResponseModel(BaseModel):
    analysis: AnalysisResponseModel
    fragments: List[FragmentResponseModel]


class ExecutePromptResponseModel(BaseModel):
    result: str
    model_used: str
    duration: float


class TestCaseResponseModel(BaseModel):
    input_variables: dict
    expected_output: str
    goal_relevance: int


class GenerateTestResponseModel(BaseModel):
    test_case: TestCaseResponseModel


class PromptResponseModel(BaseModel):
    id: str
    text: str
    goal: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("/analyze", response_model=AnalyzePromptResponseModel)
async def analyze_prompt(
    request: AnalyzePromptRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Analyze a prompt for effectiveness and goal alignment."""
    try:
        # Convert to application DTO
        app_request = AnalyzePromptRequest(
            prompt_text=request.prompt_text,
            judge_model=request.judge_model,
            goal=request.goal
        )

        # Call application service
        response = await container.get_prompt_service().analyze_prompt(app_request)

        # Convert to API response
        return AnalyzePromptResponseModel(
            analysis=AnalysisResponseModel(
                prompt_id=response.analysis.prompt_id,
                goal_alignment=response.analysis.goal_alignment,
                effectiveness=response.analysis.effectiveness,
                suggestions=response.analysis.suggestions,
                status=response.analysis.status,
                inferred_goal=response.analysis.inferred_goal
            ),
            fragments=[
                FragmentResponseModel(
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


@router.post("/execute", response_model=ExecutePromptResponseModel)
async def execute_prompt(
    request: ExecutePromptRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Execute a prompt with a target LLM."""
    try:
        # Convert to application DTO
        app_request = ExecutePromptRequest(
            prompt_text=request.prompt_text,
            target_model=request.target_model
        )

        # Call application service
        response = await container.get_prompt_service().execute_prompt(app_request)

        # Convert to API response
        return ExecutePromptResponseModel(
            result=response.result,
            model_used=response.model_used,
            duration=response.duration
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=GenerateTestResponseModel)
async def generate_test(
    request: GenerateTestRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Generate a test case for a prompt."""
    try:
        # Convert to application DTO
        app_request = GenerateTestRequest(
            prompt_text=request.prompt_text,
            judge_model=request.judge_model,
            goal=request.goal
        )

        # Call application service
        response = await container.get_prompt_service().generate_test_case(app_request)

        # Convert to API response
        return GenerateTestResponseModel(
            test_case=TestCaseResponseModel(
                input_variables=response.test_case.input_variables,
                expected_output=response.test_case.expected_output,
                goal_relevance=response.test_case.goal_relevance
            )
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PromptResponseModel)
async def create_prompt(
    request: CreatePromptRequestModel,
    container: WebContainer = Depends(get_container)
):
    """Create a new prompt."""
    try:
        # Call application service
        prompt_dto = await container.get_prompt_service().create_prompt(
            text=request.text,
            goal=request.goal
        )

        # Convert to API response
        return PromptResponseModel(
            id=prompt_dto.id,
            text=prompt_dto.text,
            goal=prompt_dto.goal,
            created_at=prompt_dto.created_at.isoformat() if prompt_dto.created_at else None,
            updated_at=prompt_dto.updated_at.isoformat() if prompt_dto.updated_at else None
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{prompt_id}", response_model=PromptResponseModel)
async def get_prompt(
    prompt_id: str,
    container: WebContainer = Depends(get_container)
):
    """Get a prompt by ID."""
    try:
        prompt_dto = await container.get_prompt_service().get_prompt(prompt_id)

        if not prompt_dto:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")

        return PromptResponseModel(
            id=prompt_dto.id,
            text=prompt_dto.text,
            goal=prompt_dto.goal,
            created_at=prompt_dto.created_at.isoformat() if prompt_dto.created_at else None,
            updated_at=prompt_dto.updated_at.isoformat() if prompt_dto.updated_at else None
        )

    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[PromptResponseModel])
async def list_prompts(
    container: WebContainer = Depends(get_container)
):
    """List all prompts."""
    try:
        prompts = await container.get_prompt_service().list_prompts()

        return [
            PromptResponseModel(
                id=p.id,
                text=p.text,
                goal=p.goal,
                created_at=p.created_at.isoformat() if p.created_at else None,
                updated_at=p.updated_at.isoformat() if p.updated_at else None
            )
            for p in prompts
        ]

    except BlogusError as e:
        raise HTTPException(status_code=500, detail=str(e))