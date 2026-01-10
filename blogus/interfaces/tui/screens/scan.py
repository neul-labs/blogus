"""
Scan screen for Blogus TUI demo.

Demonstrates the `blogus scan` capability with animated progress.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Static, DataTable, Footer, ProgressBar
from textual.reactive import reactive


class ScanScreen(Screen):
    """
    Scan screen - demonstrates prompt detection capabilities.

    Shows real-time scanning progress with a file tree and detected prompts.
    """

    BINDINGS = [
        Binding("n", "next_screen", "Next", show=True),
        Binding("b", "prev_screen", "Back", show=True),
        Binding("r", "rescan", "Rescan", show=True),
        Binding("d", "dashboard", "Dashboard", show=True),
    ]

    files_scanned = reactive(0)
    prompts_found = reactive(0)
    untracked_count = reactive(0)
    scan_complete = reactive(False)

    def compose(self) -> ComposeResult:
        """Compose the scan screen."""
        with Container(classes="main-container"):
            yield Static("Scanning Project for Prompts", classes="title")
            yield ProgressBar(id="scan-progress", total=100, show_eta=False)

            with Horizontal(classes="stats-bar"):
                yield Static("Files: 0", id="file-count", classes="stat-box")
                yield Static("Prompts: 0", id="prompt-count", classes="stat-box success")
                yield Static(
                    "Untracked: 0", id="untracked-count", classes="stat-box warning"
                )

            yield Static("Detected Prompts:", classes="subtitle")
            yield DataTable(id="results-table")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize and start scan on mount."""
        # Setup table
        table = self.query_one("#results-table", DataTable)
        table.add_columns("File", "Line", "Type", "API", "Status")
        table.cursor_type = "row"

        # Start scan
        await self.run_scan()

    async def run_scan(self) -> None:
        """Execute scan with visual updates."""
        import asyncio

        runner = self.app.runner
        progress = self.query_one("#scan-progress", ProgressBar)
        table = self.query_one("#results-table", DataTable)

        # Reset state
        self.files_scanned = 0
        self.prompts_found = 0
        self.untracked_count = 0
        self.scan_complete = False
        table.clear()
        progress.progress = 0

        def on_detection(prompt):
            self.prompts_found += 1
            if not prompt.is_versioned:
                self.untracked_count += 1

            # Determine status display
            if prompt.is_versioned:
                if prompt.linked_prompt:
                    status = f"[green]linked:{prompt.linked_prompt}[/green]"
                else:
                    status = "[green]tracked[/green]"
            else:
                status = "[yellow]untracked[/yellow]"

            # Add row to table
            try:
                rel_path = prompt.file_path.relative_to(runner.project_path)
            except ValueError:
                rel_path = prompt.file_path.name

            table.add_row(
                str(rel_path),
                str(prompt.line_number),
                prompt.detection_type,
                prompt.api_type or "-",
                status,
            )

            # Update stats
            self._update_stats()

        # Simulate file scanning progress
        total_steps = 20
        for i in range(total_steps):
            progress.progress = (i + 1) * (100 / total_steps)
            self.files_scanned = (i + 1) * 2
            self._update_stats()
            await asyncio.sleep(runner.delay / 2)

        # Run actual scan with callbacks
        await runner.run_scan(callback=on_detection)

        # Complete
        progress.progress = 100
        self.scan_complete = True
        self._update_stats()

        self.notify(
            f"Found {self.prompts_found} prompts ({self.untracked_count} untracked)",
            title="Scan Complete",
        )

    def _update_stats(self) -> None:
        """Update the statistics display."""
        try:
            self.query_one("#file-count", Static).update(f"Files: {self.files_scanned}")
            self.query_one("#prompt-count", Static).update(
                f"Prompts: {self.prompts_found}"
            )
            self.query_one("#untracked-count", Static).update(
                f"Untracked: {self.untracked_count}"
            )
        except Exception:
            pass

    def action_next_screen(self) -> None:
        """Go to analyze screen."""
        if self.prompts_found > 0:
            self.app.switch_screen("analyze")
        else:
            self.notify("No prompts found to analyze", severity="warning")

    def action_prev_screen(self) -> None:
        """Go back to welcome screen."""
        self.app.switch_screen("welcome")

    async def action_rescan(self) -> None:
        """Rescan the project."""
        await self.run_scan()

    def action_dashboard(self) -> None:
        """Go to dashboard."""
        self.app.switch_screen("dashboard")
