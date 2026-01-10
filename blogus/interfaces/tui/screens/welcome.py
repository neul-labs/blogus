"""
Welcome screen for Blogus TUI demo.

Grand entrance screen with logo, tagline, and navigation instructions.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Center
from textual.screen import Screen
from textual.widgets import Static, Footer

from ..widgets.logo import LogoWidget


class WelcomeScreen(Screen):
    """
    Welcome screen - the grand entrance to the demo.

    Displays the Blogus ASCII logo, tagline, and keyboard navigation hints.
    """

    BINDINGS = [
        Binding("enter", "start_demo", "Start Demo", show=True),
        Binding("space", "jump_dashboard", "Dashboard", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Compose the welcome screen."""
        with Container(id="logo-container"):
            yield LogoWidget(id="logo")
            yield Static(
                "package.lock for AI prompts",
                id="tagline",
            )
            yield Static(
                "Manage, version, and analyze your prompts like code",
                classes="subtitle",
            )
            yield Static("", classes="spacer")
            yield Static(
                "[ENTER] Start Guided Demo    [SPACE] Jump to Dashboard    [Q] Quit",
                id="instructions",
            )
        yield Footer()

    def action_start_demo(self) -> None:
        """Start the guided demo flow."""
        self.app.switch_screen("scan")

    def action_jump_dashboard(self) -> None:
        """Jump directly to dashboard."""
        self.app.switch_screen("dashboard")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
