"""
Demo orchestration and state management for the Blogus TUI demo.

Coordinates demo operations with existing Blogus services and manages
shared state across screens.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path
import asyncio

from ...domain.services.detection_engine import DetectionEngine, ScanResult, UnifiedDetectedPrompt


@dataclass
class DemoState:
    """Shared state across demo screens."""

    scan_result: Optional[ScanResult] = None
    selected_prompt_index: int = 0
    analysis_results: Dict[str, dict] = field(default_factory=dict)
    comparison_results: Dict[str, dict] = field(default_factory=dict)
    fixed_files: List[Path] = field(default_factory=list)
    workflow_step: int = 0
    demo_actions: List[str] = field(default_factory=list)

    @property
    def all_prompts(self) -> List[UnifiedDetectedPrompt]:
        """Get all detected prompts."""
        if self.scan_result:
            return self.scan_result.all_prompts
        return []

    @property
    def selected_prompt(self) -> Optional[UnifiedDetectedPrompt]:
        """Get the currently selected prompt."""
        prompts = self.all_prompts
        if prompts and 0 <= self.selected_prompt_index < len(prompts):
            return prompts[self.selected_prompt_index]
        return None

    @property
    def managed_count(self) -> int:
        """Count of managed/versioned prompts."""
        if self.scan_result:
            # Count prompt files + versioned code prompts
            versioned = [p for p in self.scan_result.all_prompts if p.is_versioned]
            return len(self.scan_result.prompt_files) + len(versioned)
        return 0

    @property
    def untracked_count(self) -> int:
        """Count of untracked prompts."""
        if self.scan_result:
            return len(self.scan_result.untracked_prompts)
        return 0

    @property
    def total_prompts(self) -> int:
        """Total prompt count."""
        return len(self.all_prompts)


class DemoRunner:
    """Coordinates demo operations with existing Blogus services."""

    SPEED_DELAYS = {"slow": 0.5, "normal": 0.2, "fast": 0.05}

    def __init__(self, project_path: Path, speed: str = "normal"):
        self.project_path = project_path
        self.delay = self.SPEED_DELAYS.get(speed, 0.2)
        self.state = DemoState()

        # Initialize detection engine
        self.detection_engine = DetectionEngine(project_path)

    async def run_scan(
        self, callback: Optional[Callable[[UnifiedDetectedPrompt], None]] = None
    ) -> ScanResult:
        """
        Run scan with animated progress.

        Args:
            callback: Optional callback called for each detected prompt

        Returns:
            ScanResult with all detected prompts
        """
        result = self.detection_engine.scan(
            include_python=True, include_js=True, include_prompt_files=True
        )
        self.state.scan_result = result
        self.state.demo_actions.append(
            f"Scanned {len(result.all_prompts)} prompts in project"
        )

        # Animate discoveries
        for prompt in result.all_prompts:
            if callback:
                callback(prompt)
            await asyncio.sleep(self.delay)

        return result

    async def run_analysis(
        self, prompt_text: str, goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run prompt analysis using LLM.

        Args:
            prompt_text: The prompt text to analyze
            goal: Optional goal for the prompt

        Returns:
            Analysis results dict
        """
        try:
            from ...interfaces.web.container import get_container
            from ...application.dto import AnalyzePromptRequest

            container = get_container()
            prompt_service = container.get_prompt_service()

            request = AnalyzePromptRequest(
                prompt_text=prompt_text,
                judge_model="gpt-4o-mini",
                goal=goal,
            )

            response = await prompt_service.analyze_prompt(request)

            result = {
                "goal_alignment": response.analysis.goal_alignment,
                "effectiveness": response.analysis.effectiveness,
                "suggestions": response.analysis.suggestions,
                "status": response.analysis.status,
                "inferred_goal": response.analysis.inferred_goal,
                "fragments": [
                    {
                        "text": f.text,
                        "type": f.fragment_type,
                        "goal_alignment": f.goal_alignment,
                        "suggestion": f.improvement_suggestion,
                    }
                    for f in response.fragments
                ],
            }

            self.state.analysis_results[prompt_text[:50]] = result
            self.state.demo_actions.append("Analyzed prompt effectiveness")
            return result

        except Exception as e:
            return {
                "error": str(e),
                "goal_alignment": 0,
                "effectiveness": 0,
                "suggestions": [f"Analysis failed: {e}"],
                "status": "error",
            }

    async def run_comparison(
        self,
        prompt_text: str,
        models: Optional[List[str]] = None,
        callback: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run multi-model comparison.

        Args:
            prompt_text: The prompt to execute
            models: List of model IDs to compare
            callback: Optional callback(model, output) for each completion

        Returns:
            Comparison results dict
        """
        if models is None:
            models = ["gpt-4o-mini", "gpt-3.5-turbo"]

        results = {"models": {}, "similarity": {}}

        try:
            from ...interfaces.web.container import get_container

            container = get_container()
            llm_provider = container.get_llm_provider()

            for model in models:
                try:
                    import time

                    start = time.time()
                    response = await llm_provider.complete(
                        prompt=prompt_text,
                        model=model,
                        max_tokens=500,
                    )
                    elapsed = time.time() - start

                    results["models"][model] = {
                        "output": response.content,
                        "tokens": response.usage.get("total_tokens", 0)
                        if response.usage
                        else 0,
                        "time": round(elapsed, 2),
                    }

                    if callback:
                        callback(model, response.content)

                    await asyncio.sleep(self.delay)

                except Exception as e:
                    results["models"][model] = {
                        "output": f"Error: {e}",
                        "tokens": 0,
                        "time": 0,
                        "error": str(e),
                    }

            self.state.comparison_results[prompt_text[:50]] = results
            self.state.demo_actions.append(
                f"Compared prompt across {len(models)} models"
            )
            return results

        except Exception as e:
            return {"error": str(e), "models": {}}

    def run_check(self) -> Dict[str, Any]:
        """
        Run validation check.

        Returns:
            Check results with issues found
        """
        is_valid, issues = self.detection_engine.validate(strict=False)

        result = {
            "is_valid": is_valid,
            "issues": issues,
            "untracked": [i for i in issues if i.get("type") == "untracked"],
            "outdated": [i for i in issues if i.get("type") == "outdated"],
        }

        return result

    def run_fix(self, link_name: Optional[str] = None) -> List[Path]:
        """
        Add missing @blogus markers.

        Args:
            link_name: Optional name to link all prompts to

        Returns:
            List of modified file paths
        """
        if not self.state.scan_result:
            return []

        untracked = self.state.scan_result.untracked_prompts
        if not untracked:
            return []

        modified = self.detection_engine.add_markers(untracked, link_name)
        self.state.fixed_files = modified
        self.state.demo_actions.append(f"Fixed {len(modified)} untracked prompts")

        return modified

    def get_prompt_content(self, prompt: UnifiedDetectedPrompt) -> str:
        """
        Get the full content of a detected prompt.

        Args:
            prompt: The detected prompt

        Returns:
            Prompt content string
        """
        if prompt.prompt_content:
            return prompt.prompt_content

        # Try to read from file
        try:
            if prompt.file_path.exists():
                content = prompt.file_path.read_text()
                lines = content.split("\n")
                # Get a window around the detection
                start = max(0, prompt.line_number - 3)
                end = min(len(lines), prompt.line_number + 10)
                return "\n".join(lines[start:end])
        except Exception:
            pass

        return f"[Prompt at {prompt.file_path}:{prompt.line_number}]"

    def select_next_prompt(self) -> Optional[UnifiedDetectedPrompt]:
        """Select the next prompt in the list."""
        if self.state.all_prompts:
            self.state.selected_prompt_index = (
                self.state.selected_prompt_index + 1
            ) % len(self.state.all_prompts)
        return self.state.selected_prompt

    def select_prev_prompt(self) -> Optional[UnifiedDetectedPrompt]:
        """Select the previous prompt in the list."""
        if self.state.all_prompts:
            self.state.selected_prompt_index = (
                self.state.selected_prompt_index - 1
            ) % len(self.state.all_prompts)
        return self.state.selected_prompt
