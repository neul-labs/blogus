"""
Dashboard screen for Blogus TUI demo.

Interactive dashboard for exploring prompts and running operations.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Static, DataTable, Footer
from textual.reactive import reactive


class StatCard(Static):
    """Statistics card widget."""

    DEFAULT_CSS = """
    StatCard {
        width: 1fr;
        height: 5;
        border: round #414868;
        background: #24283b;
        padding: 1;
        margin: 0 1;
        text-align: center;
    }

    StatCard .card-value {
        text-style: bold;
        color: #7aa2f7;
    }

    StatCard .card-label {
        color: #a9b1d6;
    }
    """

    def __init__(
        self,
        value: str,
        label: str,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        content = f"[b]{value}[/b]\n{label}"
        super().__init__(content, id=id, classes=classes, markup=True)
        self.value = value
        self.label = label

    def update_value(self, value: str) -> None:
        """Update the card value."""
        self.value = value
        self.update(f"[b]{value}[/b]\n{self.label}")


class DashboardScreen(Screen):
    """
    Dashboard screen - interactive prompt management hub.

    Shows summary statistics, prompt list, and quick action buttons.
    """

    BINDINGS = [
        Binding("s", "run_scan", "Scan", show=True),
        Binding("a", "analyze_selected", "Analyze", show=True),
        Binding("c", "compare_selected", "Compare", show=True),
        Binding("f", "fix_issues", "Fix", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("w", "welcome", "Welcome"),
        Binding("enter", "view_details", "View Details"),
    ]

    selected_row = reactive(0)

    def compose(self) -> ComposeResult:
        """Compose the dashboard screen."""
        with Container(classes="main-container"):
            yield Static("Blogus Dashboard", classes="title")

            with Horizontal(classes="card-container"):
                yield StatCard("0", "Managed", id="managed-card")
                yield StatCard("0", "API Calls", id="calls-card")
                yield StatCard("0", "Untracked", id="untracked-card")

            yield Static(
                "[S] Scan  [A] Analyze  [C] Compare  [F] Fix  [Q] Quit",
                classes="instructions",
            )

            yield Static("Detected Prompts:", classes="subtitle")
            yield DataTable(id="prompts-table")

            yield Static("Activity Log:", classes="subtitle")
            yield Static("Ready for action...", id="activity-log", classes="log-panel")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize dashboard on mount."""
        # Setup table
        table = self.query_one("#prompts-table", DataTable)
        table.add_columns("Name/File", "Type", "API", "Status", "Score")
        table.cursor_type = "row"

        # Load data
        self._refresh_data()

    def _refresh_data(self) -> None:
        """Refresh dashboard data from runner state."""
        runner = self.app.runner
        state = runner.state

        # Update cards
        self.query_one("#managed-card", StatCard).update_value(str(state.managed_count))
        self.query_one("#calls-card", StatCard).update_value(str(state.total_prompts))
        self.query_one("#untracked-card", StatCard).update_value(
            str(state.untracked_count)
        )

        # Update table
        table = self.query_one("#prompts-table", DataTable)
        table.clear()

        for prompt in state.all_prompts:
            # Determine display name
            if prompt.linked_prompt:
                name = prompt.linked_prompt
            elif prompt.variable_name:
                name = prompt.variable_name
            else:
                try:
                    name = prompt.file_path.relative_to(runner.project_path).name
                except ValueError:
                    name = prompt.file_path.name

            # Status
            if prompt.is_versioned:
                status = "[green]tracked[/]"
            else:
                status = "[yellow]untracked[/]"

            # Score (from analysis if available)
            prompt_key = runner.get_prompt_content(prompt)[:50]
            analysis = state.analysis_results.get(prompt_key, {})
            score = analysis.get("effectiveness", "-")
            if isinstance(score, (int, float)):
                score = f"{score}/10"

            table.add_row(
                name,
                prompt.detection_type,
                prompt.api_type or "-",
                status,
                str(score),
            )

        # Update activity log
        if state.demo_actions:
            log_text = "\n".join(f"  - {a}" for a in state.demo_actions[-5:])
            self.query_one("#activity-log", Static).update(log_text)

    async def action_run_scan(self) -> None:
        """Run a new scan."""
        self._log("Running scan...")

        runner = self.app.runner

        def on_detection(prompt):
            self._log(f"Found: {prompt.file_path.name}:{prompt.line_number}")

        await runner.run_scan(callback=on_detection)
        self._refresh_data()
        self._log("Scan complete!")
        self.notify(f"Found {runner.state.total_prompts} prompts")

    def action_analyze_selected(self) -> None:
        """Go to analyze screen for selected prompt."""
        table = self.query_one("#prompts-table", DataTable)
        if table.row_count > 0:
            self.app.runner.state.selected_prompt_index = table.cursor_row
            self.app.switch_screen("analyze")
        else:
            self.notify("No prompts to analyze. Run scan first.", severity="warning")

    def action_compare_selected(self) -> None:
        """Go to compare screen."""
        self.app.switch_screen("compare")

    def action_fix_issues(self) -> None:
        """Go to fix workflow screen."""
        self.app.switch_screen("fix")

    def action_welcome(self) -> None:
        """Go back to welcome screen."""
        self.app.switch_screen("welcome")

    def action_view_details(self) -> None:
        """View details of selected prompt."""
        table = self.query_one("#prompts-table", DataTable)
        if table.row_count > 0:
            row_key = table.cursor_row
            self.app.runner.state.selected_prompt_index = row_key
            self.app.switch_screen("analyze")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def _log(self, message: str) -> None:
        """Add message to activity log."""
        runner = self.app.runner
        runner.state.demo_actions.append(message)
        log = self.query_one("#activity-log", Static)
        log_text = "\n".join(f"  - {a}" for a in runner.state.demo_actions[-5:])
        log.update(log_text)
