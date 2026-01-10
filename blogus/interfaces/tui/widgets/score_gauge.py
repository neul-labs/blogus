"""
Animated score gauge widget for Blogus TUI demo.
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, ProgressBar
from textual.reactive import reactive


class ScoreGauge(Container):
    """
    Widget displaying an animated score gauge (0-10 scale).

    Shows a label, progress bar, and numeric value with color coding
    based on the score level.
    """

    DEFAULT_CSS = """
    ScoreGauge {
        height: 5;
        border: round #414868;
        padding: 0 1;
        margin: 0 1;
    }

    ScoreGauge .label {
        text-align: center;
        text-style: bold;
        color: #a9b1d6;
    }

    ScoreGauge .value {
        text-align: center;
        text-style: bold;
    }

    ScoreGauge.high {
        border: round #9ece6a;
    }

    ScoreGauge.high .value {
        color: #9ece6a;
    }

    ScoreGauge.medium {
        border: round #e0af68;
    }

    ScoreGauge.medium .value {
        color: #e0af68;
    }

    ScoreGauge.low {
        border: round #f7768e;
    }

    ScoreGauge.low .value {
        color: #f7768e;
    }

    ScoreGauge ProgressBar {
        padding: 0;
    }
    """

    score = reactive(0.0)

    def __init__(
        self,
        label: str,
        score: float = 0.0,
        max_score: float = 10.0,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Initialize the score gauge.

        Args:
            label: Label text shown above the gauge
            score: Initial score value
            max_score: Maximum score value (default 10)
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(id=id, classes=classes)
        self.label_text = label
        self.score = score
        self.max_score = max_score

    def compose(self) -> ComposeResult:
        """Compose the score gauge."""
        yield Static(self.label_text, classes="label")
        yield ProgressBar(total=self.max_score, show_eta=False, show_percentage=False)
        yield Static(f"{self.score:.1f}/{self.max_score:.0f}", classes="value")

    def on_mount(self) -> None:
        """Update progress bar on mount."""
        self._update_display()

    def watch_score(self, score: float) -> None:
        """React to score changes."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the display based on current score."""
        # Update progress bar
        try:
            progress = self.query_one(ProgressBar)
            progress.progress = self.score
        except Exception:
            pass

        # Update value text
        try:
            value = self.query_one(".value", Static)
            value.update(f"{self.score:.1f}/{self.max_score:.0f}")
        except Exception:
            pass

        # Update color class based on score
        self.remove_class("high", "medium", "low")
        ratio = self.score / self.max_score
        if ratio >= 0.7:
            self.add_class("high")
        elif ratio >= 0.4:
            self.add_class("medium")
        else:
            self.add_class("low")

    async def animate_to(self, target: float, duration: float = 1.0) -> None:
        """
        Animate the score to a target value.

        Args:
            target: Target score value
            duration: Animation duration in seconds
        """
        import asyncio

        steps = 20
        step_duration = duration / steps
        start = self.score
        delta = (target - start) / steps

        for i in range(steps):
            self.score = start + delta * (i + 1)
            await asyncio.sleep(step_duration)

        self.score = target
