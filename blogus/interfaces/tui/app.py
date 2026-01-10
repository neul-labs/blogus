"""
Main Textual application for the Blogus TUI demo.

A visually impressive interactive demo showcasing Blogus capabilities
for conference presentations and talks.
"""

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding

from .demo_runner import DemoRunner
from .screens.welcome import WelcomeScreen
from .screens.scan import ScanScreen
from .screens.analyze import AnalyzeScreen
from .screens.compare import CompareScreen
from .screens.fix_workflow import FixWorkflowScreen
from .screens.dashboard import DashboardScreen
from .screens.summary import SummaryScreen


class BlogusDemoApp(App):
    """
    Blogus TUI Demo Application.

    An interactive terminal-based demo that showcases Blogus capabilities
    including prompt scanning, analysis, multi-model comparison, and
    version management workflow.
    """

    TITLE = "Blogus Demo"
    SUB_TITLE = "package.lock for AI prompts"
    CSS_PATH = "styles/demo.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True, priority=True),
        Binding("d", "dashboard", "Dashboard", show=True),
        Binding("escape", "back", "Back", show=False),
        Binding("?", "help", "Help", show=True),
    ]

    SCREENS = {
        "welcome": WelcomeScreen,
        "scan": ScanScreen,
        "analyze": AnalyzeScreen,
        "compare": CompareScreen,
        "fix": FixWorkflowScreen,
        "dashboard": DashboardScreen,
        "summary": SummaryScreen,
    }

    def __init__(
        self,
        demo_path: Optional[Path] = None,
        speed: str = "normal",
    ):
        """
        Initialize the demo app.

        Args:
            demo_path: Path to the demo project (auto-created if None)
            speed: Animation speed ('slow', 'normal', 'fast')
        """
        super().__init__()
        self.demo_path = demo_path
        self.speed = speed
        self._runner: Optional[DemoRunner] = None

    @property
    def runner(self) -> DemoRunner:
        """Get or create the demo runner."""
        if self._runner is None:
            if self.demo_path is None:
                from .demo_data.setup import setup_demo_project

                self.demo_path = setup_demo_project()
            self._runner = DemoRunner(self.demo_path, self.speed)
        return self._runner

    def on_mount(self) -> None:
        """Called when app is mounted - show welcome screen."""
        self.push_screen("welcome")

    def action_dashboard(self) -> None:
        """Switch to dashboard screen."""
        self.switch_screen("dashboard")

    def action_back(self) -> None:
        """Go back to previous screen."""
        if len(self.screen_stack) > 1:
            self.pop_screen()

    def action_help(self) -> None:
        """Show help information."""
        self.notify(
            "Navigation: [n]ext [b]ack [d]ashboard [q]uit",
            title="Keyboard Shortcuts",
            timeout=5,
        )

    def goto_screen(self, screen_name: str) -> None:
        """
        Navigate to a specific screen.

        Args:
            screen_name: Name of the screen to navigate to
        """
        if screen_name in self.SCREENS:
            self.switch_screen(screen_name)

    def next_in_flow(self, current: str) -> None:
        """
        Go to the next screen in the guided flow.

        Args:
            current: Current screen name
        """
        flow = ["welcome", "scan", "analyze", "compare", "fix", "summary"]
        try:
            idx = flow.index(current)
            if idx < len(flow) - 1:
                self.switch_screen(flow[idx + 1])
        except ValueError:
            pass

    def prev_in_flow(self, current: str) -> None:
        """
        Go to the previous screen in the guided flow.

        Args:
            current: Current screen name
        """
        flow = ["welcome", "scan", "analyze", "compare", "fix", "summary"]
        try:
            idx = flow.index(current)
            if idx > 0:
                self.switch_screen(flow[idx - 1])
        except ValueError:
            pass


def run_demo(demo_path: Optional[Path] = None, speed: str = "normal") -> None:
    """
    Run the Blogus TUI demo.

    Args:
        demo_path: Optional path to demo project
        speed: Animation speed ('slow', 'normal', 'fast')
    """
    app = BlogusDemoApp(demo_path=demo_path, speed=speed)
    app.run()
