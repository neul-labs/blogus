"""
Comparison panel widget for multi-model output display.
"""

from typing import Dict, Any, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static


class ModelColumn(Container):
    """Single column showing one model's output."""

    DEFAULT_CSS = """
    ModelColumn {
        width: 1fr;
        border: round #414868;
        padding: 1;
        margin: 0 1;
    }

    ModelColumn .model-header {
        text-align: center;
        text-style: bold;
        background: #24283b;
        color: #7aa2f7;
        padding: 0 1;
        margin-bottom: 1;
    }

    ModelColumn .model-stats {
        text-align: center;
        color: #565f89;
        margin-bottom: 1;
    }

    ModelColumn .model-output {
        background: #16161e;
        padding: 1;
        height: 1fr;
    }

    ModelColumn.winner {
        border: round #9ece6a;
    }

    ModelColumn.winner .model-header {
        background: #1a2e1a;
        color: #9ece6a;
    }
    """

    def __init__(
        self,
        model_name: str,
        output: str = "",
        time_seconds: float = 0,
        tokens: int = 0,
        is_winner: bool = False,
        id: str | None = None,
    ) -> None:
        """
        Initialize the model column.

        Args:
            model_name: Name of the model
            output: Model's output text
            time_seconds: Response time
            tokens: Token count
            is_winner: Whether this model is the "winner"
            id: Widget ID
        """
        classes = "winner" if is_winner else None
        super().__init__(id=id, classes=classes)
        self.model_name = model_name
        self.output = output
        self.time_seconds = time_seconds
        self.tokens = tokens

    def compose(self) -> ComposeResult:
        """Compose the model column."""
        yield Static(self.model_name, classes="model-header")
        stats = f"{self.time_seconds:.1f}s | {self.tokens} tokens"
        yield Static(stats, classes="model-stats")
        yield Static(self.output or "Waiting...", classes="model-output")

    def update_output(
        self,
        output: str,
        time_seconds: Optional[float] = None,
        tokens: Optional[int] = None,
    ) -> None:
        """
        Update the model output.

        Args:
            output: New output text
            time_seconds: Optional new time
            tokens: Optional new token count
        """
        self.output = output
        if time_seconds is not None:
            self.time_seconds = time_seconds
        if tokens is not None:
            self.tokens = tokens

        try:
            output_widget = self.query_one(".model-output", Static)
            output_widget.update(output)

            stats_widget = self.query_one(".model-stats", Static)
            stats = f"{self.time_seconds:.1f}s | {self.tokens} tokens"
            stats_widget.update(stats)
        except Exception:
            pass


class ComparisonPanel(Container):
    """
    Panel showing multi-model comparison with side-by-side outputs.
    """

    DEFAULT_CSS = """
    ComparisonPanel {
        height: 1fr;
    }

    ComparisonPanel .comparison-container {
        layout: horizontal;
        height: 1fr;
    }

    ComparisonPanel .similarity-bar {
        height: 3;
        background: #24283b;
        padding: 0 2;
        margin-top: 1;
        border: round #414868;
    }

    ComparisonPanel .winner-announcement {
        text-align: center;
        text-style: bold;
        color: #9ece6a;
        background: #1a2e1a;
        padding: 0 2;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        models: list[str],
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Initialize the comparison panel.

        Args:
            models: List of model names to compare
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(id=id, classes=classes)
        self.models = models
        self.results: Dict[str, Dict[str, Any]] = {}

    def compose(self) -> ComposeResult:
        """Compose the comparison panel."""
        with Horizontal(classes="comparison-container"):
            for model in self.models:
                yield ModelColumn(
                    model_name=model,
                    id=f"model-{model.replace('/', '-').replace('.', '-')}",
                )
        yield Static("", classes="similarity-bar", id="similarity")
        yield Static("", classes="winner-announcement", id="winner")

    def update_model(
        self,
        model: str,
        output: str,
        time_seconds: float = 0,
        tokens: int = 0,
    ) -> None:
        """
        Update a single model's output.

        Args:
            model: Model name
            output: Output text
            time_seconds: Response time
            tokens: Token count
        """
        self.results[model] = {
            "output": output,
            "time": time_seconds,
            "tokens": tokens,
        }

        try:
            safe_id = f"model-{model.replace('/', '-').replace('.', '-')}"
            column = self.query_one(f"#{safe_id}", ModelColumn)
            column.update_output(output, time_seconds, tokens)
        except Exception:
            pass

    def set_similarity(self, text: str) -> None:
        """
        Set the similarity display text.

        Args:
            text: Similarity information text
        """
        try:
            widget = self.query_one("#similarity", Static)
            widget.update(text)
        except Exception:
            pass

    def set_winner(self, model: str) -> None:
        """
        Set and highlight the winning model.

        Args:
            model: Name of the winning model
        """
        try:
            # Update winner text
            widget = self.query_one("#winner", Static)
            widget.update(f"Recommended: {model}")

            # Highlight winner column
            safe_id = f"model-{model.replace('/', '-').replace('.', '-')}"
            column = self.query_one(f"#{safe_id}", ModelColumn)
            column.add_class("winner")
        except Exception:
            pass
