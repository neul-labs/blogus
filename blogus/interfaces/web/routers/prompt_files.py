"""
FastAPI router for .prompt file operations.

Provides REST API access to the file-based prompt system,
including version history and Git-based versioning.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime

from ....domain.services.version_engine import VersionEngine, VersionedPrompt
from ....domain.services.prompt_parser import PromptParser, PromptParseError
from ....domain.services.detection_engine import DetectionEngine


router = APIRouter(prefix="/prompt-files", tags=["prompt-files"])


# =============================================================================
# Request/Response Models
# =============================================================================

class VariableDefinition(BaseModel):
    name: str
    description: str
    required: bool = True
    default: Optional[str] = None
    enum: Optional[List[str]] = None


class ModelConfig(BaseModel):
    id: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class PromptFileMetadata(BaseModel):
    name: str
    description: str
    author: str
    category: str
    tags: List[str]
    model: ModelConfig
    goal: Optional[str] = None
    variables: List[VariableDefinition]


class PromptFileResponse(BaseModel):
    """Response for a single .prompt file."""
    name: str
    file_path: str
    description: str
    category: str
    author: str
    tags: List[str]
    model: ModelConfig
    goal: Optional[str]
    variables: List[VariableDefinition]
    content: str
    content_hash: str
    version: int
    commit_sha: Optional[str]
    is_dirty: bool
    last_modified: str


class PromptFileListResponse(BaseModel):
    """Response for listing .prompt files."""
    prompts: List[PromptFileResponse]
    total: int


class VersionInfo(BaseModel):
    """Version information for a prompt."""
    version: int
    content_hash: str
    commit_sha: Optional[str]
    timestamp: str
    author: str
    message: str
    tag: Optional[str] = None


class VersionHistoryResponse(BaseModel):
    """Response for version history."""
    prompt_name: str
    versions: List[VersionInfo]
    total: int


class CreatePromptFileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    content: str = Field(..., min_length=1)
    category: str = Field("general", max_length=50)
    tags: List[str] = Field(default_factory=list)
    author: str = Field("studio", max_length=100)
    model: ModelConfig = Field(default_factory=ModelConfig)
    goal: Optional[str] = Field(None, max_length=1000)
    variables: List[VariableDefinition] = Field(default_factory=list)


class UpdatePromptFileRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    author: Optional[str] = Field(None, max_length=100)
    model: Optional[ModelConfig] = None
    goal: Optional[str] = Field(None, max_length=1000)
    variables: Optional[List[VariableDefinition]] = None


class RenderPromptRequest(BaseModel):
    variables: Dict[str, str] = Field(default_factory=dict)


class ScanResultResponse(BaseModel):
    """Response for project scan."""
    project_path: str
    scan_time: str
    stats: Dict[str, int]
    prompt_files: List[Dict[str, Any]]
    detections: List[Dict[str, Any]]


# =============================================================================
# Helper Functions
# =============================================================================

def get_version_engine() -> VersionEngine:
    """Get a VersionEngine for the current working directory."""
    return VersionEngine(Path.cwd())


def get_parser() -> PromptParser:
    """Get a PromptParser instance."""
    return PromptParser()


def versioned_prompt_to_response(vp: VersionedPrompt) -> PromptFileResponse:
    """Convert a VersionedPrompt to API response."""
    meta = vp.parsed.metadata
    return PromptFileResponse(
        name=meta.name,
        file_path=str(vp.parsed.file_path) if vp.parsed.file_path else "",
        description=meta.description,
        category=meta.category,
        author=meta.author,
        tags=meta.tags,
        model=ModelConfig(
            id=meta.model.id,
            temperature=meta.model.temperature,
            max_tokens=meta.model.max_tokens
        ),
        goal=meta.goal,
        variables=[
            VariableDefinition(
                name=v.name,
                description=v.description,
                required=v.required,
                default=v.default,
                enum=v.enum
            )
            for v in meta.variables
        ],
        content=vp.parsed.content,
        content_hash=vp.version.content_hash,
        version=vp.version.version,
        commit_sha=vp.version.commit_sha,
        is_dirty=vp.is_dirty,
        last_modified=vp.version.timestamp.isoformat()
    )


# =============================================================================
# List & Get Endpoints
# =============================================================================

@router.get("/", response_model=PromptFileListResponse)
async def list_prompt_files(
    category: Optional[str] = Query(None, description="Filter by category"),
    include_dirty: bool = Query(True, description="Include modified files")
):
    """
    List all .prompt files in the project.

    Returns prompt files with version information from Git.
    """
    try:
        engine = get_version_engine()
        all_prompts = engine.list_prompts()

        # Filter by category if specified
        if category:
            all_prompts = [
                p for p in all_prompts
                if p.parsed.metadata.category.lower() == category.lower()
            ]

        # Filter out dirty if requested
        if not include_dirty:
            all_prompts = [p for p in all_prompts if not p.is_dirty]

        return PromptFileListResponse(
            prompts=[versioned_prompt_to_response(vp) for vp in all_prompts],
            total=len(all_prompts)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}", response_model=PromptFileResponse)
async def get_prompt_file(name: str):
    """
    Get a specific .prompt file by name.

    Returns the prompt with full metadata and version information.
    """
    try:
        engine = get_version_engine()
        vp = engine.get_prompt_by_name(name)

        if not vp:
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        return versioned_prompt_to_response(vp)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/history", response_model=VersionHistoryResponse)
async def get_prompt_history(
    name: str,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get version history for a prompt.

    Returns list of versions with commit information.
    """
    try:
        engine = get_version_engine()
        vp = engine.get_prompt_by_name(name)

        if not vp:
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        history = engine.get_history(vp.parsed.file_path, limit=limit)

        return VersionHistoryResponse(
            prompt_name=name,
            versions=[
                VersionInfo(
                    version=v.version,
                    content_hash=v.content_hash,
                    commit_sha=v.commit_sha,
                    timestamp=v.timestamp.isoformat(),
                    author=v.author,
                    message=v.message,
                    tag=v.tag
                )
                for v in history
            ],
            total=len(history)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/version/{version}", response_model=PromptFileResponse)
async def get_prompt_at_version(name: str, version: int):
    """
    Get a prompt at a specific version.

    Returns the prompt content as it was at the specified version.
    """
    try:
        engine = get_version_engine()
        vp = engine.get_prompt_by_name(name)

        if not vp:
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        parsed = engine.get_prompt_at_version(vp.parsed.file_path, version)

        if not parsed:
            raise HTTPException(status_code=404, detail=f"Version {version} not found")

        # Get version info
        history = engine.get_history(vp.parsed.file_path)
        version_info = next((v for v in history if v.version == version), None)

        meta = parsed.metadata
        return PromptFileResponse(
            name=meta.name,
            file_path=str(vp.parsed.file_path) if vp.parsed.file_path else "",
            description=meta.description,
            category=meta.category,
            author=meta.author,
            tags=meta.tags,
            model=ModelConfig(
                id=meta.model.id,
                temperature=meta.model.temperature,
                max_tokens=meta.model.max_tokens
            ),
            goal=meta.goal,
            variables=[
                VariableDefinition(
                    name=v.name,
                    description=v.description,
                    required=v.required,
                    default=v.default,
                    enum=v.enum
                )
                for v in meta.variables
            ],
            content=parsed.content,
            content_hash=version_info.content_hash if version_info else "",
            version=version,
            commit_sha=version_info.commit_sha if version_info else None,
            is_dirty=False,
            last_modified=version_info.timestamp.isoformat() if version_info else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Create & Update Endpoints
# =============================================================================

@router.post("/", response_model=PromptFileResponse)
async def create_prompt_file(request: CreatePromptFileRequest):
    """
    Create a new .prompt file.

    The file will be created in the prompts/ directory.
    """
    try:
        engine = get_version_engine()
        parser = get_parser()

        # Check if prompt already exists
        existing = engine.get_prompt_by_name(request.name)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Prompt '{request.name}' already exists"
            )

        # Create metadata
        from ....domain.services.prompt_parser import PromptMetadata, ModelConfig as MC, PromptVariable

        metadata = PromptMetadata(
            name=request.name,
            description=request.description,
            author=request.author,
            category=request.category,
            tags=request.tags,
            model=MC(
                id=request.model.id,
                temperature=request.model.temperature,
                max_tokens=request.model.max_tokens
            ),
            goal=request.goal,
            variables=[
                PromptVariable(
                    name=v.name,
                    description=v.description,
                    required=v.required,
                    default=v.default,
                    enum=v.enum
                )
                for v in request.variables
            ]
        )

        # Ensure prompts directory exists
        prompts_dir = engine.prompts_path
        prompts_dir.mkdir(parents=True, exist_ok=True)

        # Write the file
        file_path = prompts_dir / f"{request.name}.prompt"
        parser.write_file(file_path, metadata, request.content)

        # Return the created prompt
        vp = engine.get_versioned_prompt(file_path)
        return versioned_prompt_to_response(vp)

    except HTTPException:
        raise
    except PromptParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{name}", response_model=PromptFileResponse)
async def update_prompt_file(name: str, request: UpdatePromptFileRequest):
    """
    Update an existing .prompt file.

    Updates will be reflected in the file and visible in Git.
    """
    try:
        engine = get_version_engine()
        parser = get_parser()

        vp = engine.get_prompt_by_name(name)
        if not vp:
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        # Build updated metadata
        current = vp.parsed.metadata
        from ....domain.services.prompt_parser import PromptMetadata, ModelConfig as MC, PromptVariable

        # Merge updates with current values
        new_model = current.model
        if request.model:
            new_model = MC(
                id=request.model.id,
                temperature=request.model.temperature,
                max_tokens=request.model.max_tokens
            )

        new_variables = current.variables
        if request.variables is not None:
            new_variables = [
                PromptVariable(
                    name=v.name,
                    description=v.description,
                    required=v.required,
                    default=v.default,
                    enum=v.enum
                )
                for v in request.variables
            ]

        metadata = PromptMetadata(
            name=current.name,
            description=request.description if request.description is not None else current.description,
            author=request.author if request.author is not None else current.author,
            category=request.category if request.category is not None else current.category,
            tags=request.tags if request.tags is not None else current.tags,
            model=new_model,
            goal=request.goal if request.goal is not None else current.goal,
            variables=new_variables
        )

        # Get content (new or current)
        content = request.content if request.content is not None else vp.parsed.content

        # Write updated file
        parser.write_file(vp.parsed.file_path, metadata, content)

        # Return updated prompt
        updated_vp = engine.get_versioned_prompt(vp.parsed.file_path)
        return versioned_prompt_to_response(updated_vp)

    except HTTPException:
        raise
    except PromptParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{name}")
async def delete_prompt_file(name: str):
    """
    Delete a .prompt file.

    Note: This removes the file from disk. Use Git to recover if needed.
    """
    try:
        engine = get_version_engine()
        vp = engine.get_prompt_by_name(name)

        if not vp:
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        # Delete the file
        vp.parsed.file_path.unlink()

        return {"message": f"Prompt '{name}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.post("/{name}/render")
async def render_prompt(name: str, request: RenderPromptRequest):
    """
    Render a prompt with variable substitution.

    Returns the rendered content without executing.
    """
    try:
        engine = get_version_engine()
        parser = get_parser()

        vp = engine.get_prompt_by_name(name)
        if not vp:
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        rendered = parser.render(vp.parsed.content, request.variables)

        return {
            "name": name,
            "version": vp.version.version,
            "rendered_content": rendered,
            "variables_used": list(request.variables.keys())
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/validate")
async def validate_prompt(name: str):
    """
    Validate a .prompt file.

    Checks for parse errors, missing variables, etc.
    """
    try:
        engine = get_version_engine()

        vp = engine.get_prompt_by_name(name)
        if not vp:
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        issues = engine.validate_prompt(vp.parsed.file_path)

        return {
            "name": name,
            "valid": len(issues) == 0,
            "issues": issues
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/marker")
async def get_version_marker(name: str):
    """
    Get the version marker string for embedding in code.

    Returns a marker like: @blogus:prompt-name@v2 sha256:abc123
    """
    try:
        engine = get_version_engine()

        vp = engine.get_prompt_by_name(name)
        if not vp:
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        marker = engine.get_marker_string(vp.parsed.file_path)

        return {
            "name": name,
            "marker": marker,
            "version": vp.version.version,
            "hash": vp.version.content_hash
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Scan Endpoint
# =============================================================================

@router.post("/scan", response_model=ScanResultResponse)
async def scan_project(
    include_python: bool = Query(True),
    include_js: bool = Query(True)
):
    """
    Scan the project for prompts and LLM API calls.

    Returns detected prompts in code with their status.
    """
    try:
        engine = DetectionEngine(Path.cwd())
        result = engine.scan(
            include_python=include_python,
            include_js=include_js,
            include_prompt_files=True
        )

        return ScanResultResponse(
            project_path=str(result.project_path),
            scan_time=result.scan_time.isoformat(),
            stats=result.stats,
            prompt_files=[
                {
                    "name": vp.parsed.metadata.name,
                    "path": str(vp.parsed.file_path),
                    "version": vp.version.version,
                    "hash": vp.version.content_hash,
                    "is_dirty": vp.is_dirty
                }
                for vp in result.prompt_files
            ],
            detections=[
                {
                    "file": str(p.file_path),
                    "line": p.line_number,
                    "type": p.detection_type,
                    "language": p.language,
                    "api": p.api_type,
                    "linked_to": p.linked_prompt,
                    "status": p.status,
                    "hash": p.content_hash
                }
                for p in result.all_prompts
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Git Operations Endpoints
# =============================================================================

class CommitRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class CommitResponse(BaseModel):
    commit_sha: str
    message: str
    files_committed: List[str]


class GitStatusResponse(BaseModel):
    branch: Optional[str]
    head_sha: Optional[str]
    dirty_files: List[Dict[str, Any]]
    total_dirty: int


@router.get("/git/status", response_model=GitStatusResponse)
async def get_git_status():
    """
    Get Git status for prompt files.

    Returns current branch, HEAD SHA, and list of modified prompt files.
    """
    try:
        engine = get_version_engine()
        all_prompts = engine.list_prompts()

        dirty_files = []
        for vp in all_prompts:
            if vp.is_dirty:
                dirty_files.append({
                    "name": vp.parsed.metadata.name,
                    "path": str(vp.parsed.file_path),
                    "status": engine.repo.get_file_status(vp.parsed.file_path).status
                })

        return GitStatusResponse(
            branch=engine.repo.get_current_branch(),
            head_sha=engine.repo.get_head_sha(),
            dirty_files=dirty_files,
            total_dirty=len(dirty_files)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/commit", response_model=CommitResponse)
async def commit_prompt(name: str, request: CommitRequest):
    """
    Commit changes to a specific prompt file.

    Stages and commits the file with the provided message.
    """
    try:
        engine = get_version_engine()
        vp = engine.get_prompt_by_name(name)

        if not vp:
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        if not vp.is_dirty:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt '{name}' has no changes to commit"
            )

        # Stage the file
        engine.repo.add(vp.parsed.file_path)

        # Create commit
        commit_sha = engine.repo.commit(request.message)

        return CommitResponse(
            commit_sha=commit_sha,
            message=request.message,
            files_committed=[str(vp.parsed.file_path)]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/git/commit-all", response_model=CommitResponse)
async def commit_all_prompts(request: CommitRequest):
    """
    Commit all modified prompt files.

    Stages and commits all dirty .prompt files with the provided message.
    """
    try:
        engine = get_version_engine()
        all_prompts = engine.list_prompts()

        # Find dirty files
        dirty_files = [vp for vp in all_prompts if vp.is_dirty]

        if not dirty_files:
            raise HTTPException(
                status_code=400,
                detail="No modified prompt files to commit"
            )

        # Stage all dirty files
        for vp in dirty_files:
            engine.repo.add(vp.parsed.file_path)

        # Create commit
        commit_sha = engine.repo.commit(request.message)

        return CommitResponse(
            commit_sha=commit_sha,
            message=request.message,
            files_committed=[str(vp.parsed.file_path) for vp in dirty_files]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Categories Endpoint
# =============================================================================

@router.get("/categories/list")
async def list_categories():
    """
    Get list of all categories used in prompts.
    """
    try:
        engine = get_version_engine()
        all_prompts = engine.list_prompts()

        categories = set()
        for vp in all_prompts:
            categories.add(vp.parsed.metadata.category)

        return {
            "categories": sorted(categories),
            "total": len(categories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
