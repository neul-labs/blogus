"""
Compare screen for Blogus TUI demo.

Demonstrates multi-model comparison with side-by-side outputs.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.reactive import reactive

from ..widgets.comparison_panel import ComparisonPanel


class CompareScreen(Screen):
    """
    Compare screen - demonstrates multi-model prompt comparison.

    Executes the same prompt across multiple LLM models and shows
    outputs side-by-side with timing and similarity information.
    """

    BINDINGS = [
        Binding("n", "next_screen", "Next", show=True),
        Binding("b", "prev_screen", "Back", show=True),
        Binding("c", "run_comparison", "Compare", show=True),
        Binding("d", "dashboard", "Dashboard", show=True),
    ]

    is_comparing = reactive(False)
    comparison_complete = reactive(False)

    # Models to compare (using cheaper/faster models for demo)
    DEMO_MODELS = ["gpt-4o-mini", "gpt-3.5-turbo"]

    def compose(self) -> ComposeResult:
        """Compose the compare screen."""
        with Container(classes="main-container"):
            yield Static("Multi-Model Comparison", classes="title")
            yield Static(
                "Compare the same prompt across different LLM models",
                classes="subtitle",
            )

            yield Static("Test Prompt:", classes="subtitle")
            yield Static(
                "Explain the concept of recursion in programming in 2-3 sentences.",
                id="test-prompt",
                classes="prompt-content",
            )

            yield Static(
                "[C] Run Comparison    [N] Next    [B] Back",
                classes="instructions",
            )

            yield ComparisonPanel(
                models=self.DEMO_MODELS,
                id="comparison-panel",
            )

        yield Footer()

    async def action_run_comparison(self) -> None:
        """Run the multi-model comparison."""
        if self.is_comparing:
            return

        self.is_comparing = True
        self.comparison_complete = False

        panel = self.query_one("#comparison-panel", ComparisonPanel)

        # Reset panel
        for model in self.DEMO_MODELS:
            panel.update_model(model, "Generating...", 0, 0)

        test_prompt = "Explain the concept of recursion in programming in 2-3 sentences."

        try:
            runner = self.app.runner

            def on_model_complete(model: str, output: str):
                """Called when each model completes."""
                result = runner.state.comparison_results.get(test_prompt[:50], {})
                model_data = result.get("models", {}).get(model, {})
                panel.update_model(
                    model,
                    output[:300] + ("..." if len(output) > 300 else ""),
                    model_data.get("time", 0),
                    model_data.get("tokens", 0),
                )

            results = await runner.run_comparison(
                test_prompt,
                models=self.DEMO_MODELS,
                callback=on_model_complete,
            )

            if "error" not in results:
                # Find fastest model as "winner"
                models_data = results.get("models", {})
                if models_data:
                    fastest = min(
                        models_data.items(),
                        key=lambda x: x[1].get("time", float("inf")),
                    )
                    panel.set_winner(fastest[0])

                    # Show similarity info
                    panel.set_similarity(
                        f"Comparison complete - {len(models_data)} models evaluated"
                    )

                self.notify("Comparison complete!", title="Success")
            else:
                self.notify(f"Comparison failed: {results['error']}", severity="error")

            self.comparison_complete = True

        except Exception as e:
            self.notify(f"Comparison failed: {e}", severity="error")

        finally:
            self.is_comparing = False

    def action_next_screen(self) -> None:
        """Go to fix workflow screen."""
        self.app.switch_screen("fix")

    def action_prev_screen(self) -> None:
        """Go back to analyze screen."""
        self.app.switch_screen("analyze")

    def action_dashboard(self) -> None:
        """Go to dashboard."""
        self.app.switch_screen("dashboard")
