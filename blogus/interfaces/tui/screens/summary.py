"""
Summary screen for Blogus TUI demo.

Final screen showing recap of demo actions and call-to-action.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Center
from textual.screen import Screen
from textual.widgets import Static, Footer


class SummaryScreen(Screen):
    """
    Summary screen - demo completion and call-to-action.

    Shows a recap of what was covered in the demo and provides
    getting started commands.
    """

    BINDINGS = [
        Binding("r", "restart", "Restart Demo", show=True),
        Binding("d", "dashboard", "Dashboard", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Compose the summary screen."""
        with Container(classes="summary-container"):
            with Container(classes="summary-box"):
                yield Static("Demo Complete!", classes="summary-title")

                yield Static("", classes="spacer")

                yield Static("What we covered:", classes="subtitle")
                yield Static("", id="summary-items")

                yield Static("", classes="spacer")

                yield Static("Get started:", classes="subtitle")
                with Container(classes="command-box"):
                    yield Static("$ pip install blogus", classes="command")
                    yield Static("$ blogus init", classes="command")
                    yield Static("$ blogus scan", classes="command")

                yield Static("", classes="spacer")

                yield Static(
                    "github.com/terraprompt/blogus",
                    classes="subtitle",
                    id="github-link",
                )

                yield Static("", classes="spacer")

                yield Static(
                    "[R] Restart Demo    [D] Dashboard    [Q] Quit",
                    classes="instructions",
                )

        yield Footer()

    def on_mount(self) -> None:
        """Populate summary with demo actions."""
        runner = self.app.runner
        state = runner.state

        # Build summary items
        items = []

        if state.total_prompts > 0:
            items.append(f"[x] Scanned project - found {state.total_prompts} prompts")
        else:
            items.append("[ ] Scan project for prompts")

        if state.analysis_results:
            items.append(
                f"[x] Analyzed {len(state.analysis_results)} prompt(s) for effectiveness"
            )
        else:
            items.append("[ ] Analyze prompt effectiveness")

        if state.comparison_results:
            items.append(
                f"[x] Compared prompts across {len(state.comparison_results)} model(s)"
            )
        else:
            items.append("[ ] Compare across multiple models")

        if state.workflow_step > 0:
            items.append(f"[x] Completed {state.workflow_step} workflow step(s)")
        else:
            items.append("[ ] Run version management workflow")

        summary_text = "\n".join(f"  {item}" for item in items)
        self.query_one("#summary-items", Static).update(summary_text)

    def action_restart(self) -> None:
        """Restart the demo from the beginning."""
        # Reset state
        runner = self.app.runner
        runner.state.scan_result = None
        runner.state.analysis_results = {}
        runner.state.comparison_results = {}
        runner.state.fixed_files = []
        runner.state.workflow_step = 0
        runner.state.demo_actions = []
        runner.state.selected_prompt_index = 0

        self.app.switch_screen("welcome")

    def action_dashboard(self) -> None:
        """Go to dashboard."""
        self.app.switch_screen("dashboard")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
