"""
Diff view widget for showing before/after code changes.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static


class DiffPanel(Container):
    """Single panel showing code (before or after)."""

    DEFAULT_CSS = """
    DiffPanel {
        width: 1fr;
        padding: 1;
        margin: 0 1;
    }

    DiffPanel.before {
        border: round #f7768e;
    }

    DiffPanel.before .panel-header {
        background: #3d1f1f;
        color: #f7768e;
        text-align: center;
        text-style: bold;
        padding: 0 1;
        margin-bottom: 1;
    }

    DiffPanel.after {
        border: round #9ece6a;
    }

    DiffPanel.after .panel-header {
        background: #1a2e1a;
        color: #9ece6a;
        text-align: center;
        text-style: bold;
        padding: 0 1;
        margin-bottom: 1;
    }

    DiffPanel .code-content {
        background: #16161e;
        padding: 1;
    }
    """

    def __init__(
        self,
        title: str,
        content: str,
        panel_type: str = "before",
        id: str | None = None,
    ) -> None:
        """
        Initialize the diff panel.

        Args:
            title: Panel title (e.g., "BEFORE" or "AFTER")
            content: Code content to display
            panel_type: 'before' or 'after' for styling
            id: Widget ID
        """
        super().__init__(id=id, classes=panel_type)
        self.title = title
        self.content = content

    def compose(self) -> ComposeResult:
        """Compose the diff panel."""
        yield Static(self.title, classes="panel-header")
        yield Static(self.content, classes="code-content")


class DiffView(Container):
    """
    Side-by-side diff view showing before and after code.
    """

    DEFAULT_CSS = """
    DiffView {
        layout: horizontal;
        height: 1fr;
    }
    """

    def __init__(
        self,
        before: str,
        after: str,
        before_title: str = "BEFORE",
        after_title: str = "AFTER",
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Initialize the diff view.

        Args:
            before: Code before changes
            after: Code after changes
            before_title: Title for before panel
            after_title: Title for after panel
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(id=id, classes=classes)
        self.before = before
        self.after = after
        self.before_title = before_title
        self.after_title = after_title

    def compose(self) -> ComposeResult:
        """Compose the diff view."""
        yield DiffPanel(self.before_title, self.before, "before", id="diff-before")
        yield DiffPanel(self.after_title, self.after, "after", id="diff-after")

    def update_content(self, before: str, after: str) -> None:
        """
        Update the diff content.

        Args:
            before: New before content
            after: New after content
        """
        self.before = before
        self.after = after
        try:
            before_panel = self.query_one("#diff-before .code-content", Static)
            after_panel = self.query_one("#diff-after .code-content", Static)
            before_panel.update(before)
            after_panel.update(after)
        except Exception:
            pass
