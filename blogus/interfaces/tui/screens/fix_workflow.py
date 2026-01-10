"""
Fix workflow screen for Blogus TUI demo.

Demonstrates the check -> fix -> lock -> verify workflow.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.reactive import reactive

from ..widgets.diff_view import DiffView


class WorkflowStep(Static):
    """Widget representing a single workflow step."""

    DEFAULT_CSS = """
    WorkflowStep {
        padding: 0 2;
        margin-bottom: 1;
    }

    WorkflowStep.complete {
        color: #9ece6a;
    }

    WorkflowStep.active {
        color: #7aa2f7;
        text-style: bold;
    }

    WorkflowStep.pending {
        color: #565f89;
    }
    """

    def __init__(
        self,
        step_num: int,
        name: str,
        description: str,
        status: str = "pending",
    ) -> None:
        self.step_num = step_num
        self.name = name
        self.description = description
        icon = {"complete": "[x]", "active": "[>]", "pending": "[ ]"}.get(status, "[ ]")
        content = f"{icon} Step {step_num}: {name} - {description}"
        super().__init__(content, classes=status)
        self.status = status

    def set_status(self, status: str) -> None:
        """Update step status."""
        self.remove_class("complete", "active", "pending")
        self.add_class(status)
        self.status = status
        icon = {"complete": "[x]", "active": "[>]", "pending": "[ ]"}.get(status, "[ ]")
        self.update(f"{icon} Step {self.step_num}: {self.name} - {self.description}")


class FixWorkflowScreen(Screen):
    """
    Fix workflow screen - demonstrates version management workflow.

    Shows the check -> fix -> lock -> verify flow with before/after
    diff views for code modifications.
    """

    BINDINGS = [
        Binding("n", "next_screen", "Next", show=True),
        Binding("b", "prev_screen", "Back", show=True),
        Binding("enter", "execute_step", "Execute Step", show=True),
        Binding("a", "run_all", "Run All", show=True),
    ]

    current_step = reactive(0)
    workflow_complete = reactive(False)

    # Example before/after code for demo
    BEFORE_CODE = '''def answer_support_question(question: str) -> str:
    """Answer a customer support question."""
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a helpful support agent.
Answer: {question}"""
            }
        ]
    )
    return response.content[0].text'''

    AFTER_CODE = '''# @blogus:support-qa sha256:e4f5a6b7c8d9
def answer_support_question(question: str) -> str:
    """Answer a customer support question."""
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a helpful support agent.
Answer: {question}"""
            }
        ]
    )
    return response.content[0].text'''

    def compose(self) -> ComposeResult:
        """Compose the fix workflow screen."""
        with Container(classes="main-container"):
            yield Static("Version Management Workflow", classes="title")
            yield Static(
                "Manage prompt versions with check -> fix -> lock -> verify",
                classes="subtitle",
            )

            with Vertical(classes="workflow-steps", id="steps-container"):
                yield WorkflowStep(1, "Check", "Validate prompt versioning", "active")
                yield WorkflowStep(2, "Fix", "Add missing @blogus markers", "pending")
                yield WorkflowStep(3, "Lock", "Update prompts.lock file", "pending")
                yield WorkflowStep(4, "Verify", "Confirm lock file matches", "pending")

            yield Static(
                "[ENTER] Execute Current Step    [A] Run All Steps",
                classes="instructions",
            )

            yield Static("Code Changes:", classes="subtitle")
            yield DiffView(
                before=self.BEFORE_CODE,
                after="(Changes will appear here after Fix step)",
                before_title="BEFORE",
                after_title="AFTER",
                id="diff-view",
            )

            yield Static("", id="step-output", classes="log-panel")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize workflow state."""
        self.current_step = 0
        self._update_steps()

    def _update_steps(self) -> None:
        """Update step status display."""
        steps = self.query("WorkflowStep")
        for i, step in enumerate(steps):
            if i < self.current_step:
                step.set_status("complete")
            elif i == self.current_step:
                step.set_status("active")
            else:
                step.set_status("pending")

    async def action_execute_step(self) -> None:
        """Execute the current workflow step."""
        import asyncio

        if self.workflow_complete:
            self.notify("Workflow already complete!", severity="warning")
            return

        output = self.query_one("#step-output", Static)
        runner = self.app.runner

        step_names = ["Check", "Fix", "Lock", "Verify"]
        current_name = step_names[self.current_step]

        output.update(f"Executing {current_name}...")
        await asyncio.sleep(runner.delay * 2)

        if self.current_step == 0:
            # Check step
            result = runner.run_check()
            untracked = len(result.get("untracked", []))
            if untracked > 0:
                output.update(
                    f"Check complete: Found {untracked} untracked prompt(s)\n"
                    f"Run Fix step to add version markers."
                )
            else:
                output.update("Check complete: All prompts are tracked!")

        elif self.current_step == 1:
            # Fix step
            # In a real scenario, this would call runner.run_fix()
            # For demo, we just show the diff
            diff_view = self.query_one("#diff-view", DiffView)
            diff_view.update_content(self.BEFORE_CODE, self.AFTER_CODE)
            output.update(
                "Fix complete: Added @blogus markers to 2 file(s)\n"
                "  - src/api/support_bot.py\n"
                "  - src/services/reviewer.py"
            )

        elif self.current_step == 2:
            # Lock step
            output.update(
                "Lock complete: Updated .blogus/prompts.lock\n"
                "  - summarize: sha256:a1b2c3...\n"
                "  - code-review: sha256:d4e5f6...\n"
                "  - translate: sha256:g7h8i9...\n"
                "  - support-qa: sha256:e4f5a6... (new)"
            )

        elif self.current_step == 3:
            # Verify step
            output.update(
                "Verify complete: All prompts match lock file!\n"
                "  4 prompt(s) verified\n"
                "  Ready for deployment"
            )
            self.workflow_complete = True

        # Advance to next step
        if self.current_step < 3:
            self.current_step += 1
            self._update_steps()

        runner.state.workflow_step = self.current_step

    async def action_run_all(self) -> None:
        """Run all remaining workflow steps."""
        while not self.workflow_complete:
            await self.action_execute_step()

    def action_next_screen(self) -> None:
        """Go to summary screen."""
        self.app.switch_screen("summary")

    def action_prev_screen(self) -> None:
        """Go back to compare screen."""
        self.app.switch_screen("compare")
