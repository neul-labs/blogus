"""
Analyze screen for Blogus TUI demo.

Demonstrates prompt analysis with LLM scoring and suggestions.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static, Footer, Button
from textual.reactive import reactive

from ..widgets.score_gauge import ScoreGauge


class AnalyzeScreen(Screen):
    """
    Analyze screen - demonstrates prompt effectiveness analysis.

    Shows selected prompt content, runs LLM analysis, and displays
    animated score gauges with suggestions.
    """

    BINDINGS = [
        Binding("n", "next_screen", "Next", show=True),
        Binding("b", "prev_screen", "Back", show=True),
        Binding("a", "run_analysis", "Analyze", show=True),
        Binding("j", "next_prompt", "Next Prompt"),
        Binding("k", "prev_prompt", "Prev Prompt"),
    ]

    is_analyzing = reactive(False)
    current_prompt_text = reactive("")

    def compose(self) -> ComposeResult:
        """Compose the analyze screen."""
        with Container(classes="main-container"):
            yield Static("Prompt Analysis", classes="title")

            with Horizontal(classes="horizontal-split"):
                # Left panel - prompt content
                with Vertical(classes="left-panel"):
                    yield Static("Selected Prompt:", classes="subtitle")
                    yield Static(
                        "Loading...",
                        id="prompt-content",
                        classes="prompt-content",
                    )
                    yield Static(
                        "[A] Run Analysis  [J/K] Navigate Prompts",
                        id="prompt-nav-hint",
                        classes="instructions",
                    )

                # Right panel - analysis results
                with Vertical(classes="right-panel"):
                    yield Static("Analysis Results:", classes="subtitle")
                    yield ScoreGauge(
                        label="Goal Alignment",
                        score=0,
                        id="goal-gauge",
                    )
                    yield ScoreGauge(
                        label="Effectiveness",
                        score=0,
                        id="effectiveness-gauge",
                    )
                    yield Static("", id="inferred-goal", classes="subtitle")
                    yield Static("Suggestions:", classes="subtitle")
                    yield Static(
                        "Press [A] to analyze...",
                        id="suggestions",
                        classes="suggestions",
                    )

        yield Footer()

    def on_mount(self) -> None:
        """Load initial prompt on mount."""
        self._load_current_prompt()

    def _load_current_prompt(self) -> None:
        """Load the currently selected prompt."""
        runner = self.app.runner
        prompt = runner.state.selected_prompt

        if prompt:
            content = runner.get_prompt_content(prompt)
            self.current_prompt_text = content

            # Truncate for display
            display_content = content[:500]
            if len(content) > 500:
                display_content += "\n\n... [truncated]"

            try:
                self.query_one("#prompt-content", Static).update(display_content)
            except Exception:
                pass
        else:
            self.query_one("#prompt-content", Static).update(
                "No prompts available. Run scan first."
            )

    async def action_run_analysis(self) -> None:
        """Run analysis on the current prompt."""
        if self.is_analyzing:
            return

        if not self.current_prompt_text:
            self.notify("No prompt to analyze", severity="warning")
            return

        self.is_analyzing = True
        self.query_one("#suggestions", Static).update("Analyzing...")

        try:
            runner = self.app.runner
            result = await runner.run_analysis(self.current_prompt_text)

            if "error" in result and result.get("goal_alignment", 0) == 0:
                self.notify(f"Analysis failed: {result['error']}", severity="error")
                self.query_one("#suggestions", Static).update(
                    f"Error: {result.get('error', 'Unknown error')}"
                )
            else:
                # Animate score gauges
                goal_gauge = self.query_one("#goal-gauge", ScoreGauge)
                effectiveness_gauge = self.query_one("#effectiveness-gauge", ScoreGauge)

                await goal_gauge.animate_to(result.get("goal_alignment", 0))
                await effectiveness_gauge.animate_to(result.get("effectiveness", 0))

                # Update inferred goal
                if result.get("inferred_goal"):
                    self.query_one("#inferred-goal", Static).update(
                        f"Goal: {result['inferred_goal']}"
                    )

                # Update suggestions
                suggestions = result.get("suggestions", [])
                if suggestions:
                    suggestion_text = "\n".join(
                        f"  {i+1}. {s}" for i, s in enumerate(suggestions[:5])
                    )
                else:
                    suggestion_text = "  No suggestions - prompt looks good!"

                self.query_one("#suggestions", Static).update(suggestion_text)
                self.notify("Analysis complete!", title="Success")

        except Exception as e:
            self.notify(f"Analysis failed: {e}", severity="error")
            self.query_one("#suggestions", Static).update(f"Error: {e}")

        finally:
            self.is_analyzing = False

    def action_next_prompt(self) -> None:
        """Select next prompt."""
        self.app.runner.select_next_prompt()
        self._load_current_prompt()
        self._reset_scores()

    def action_prev_prompt(self) -> None:
        """Select previous prompt."""
        self.app.runner.select_prev_prompt()
        self._load_current_prompt()
        self._reset_scores()

    def _reset_scores(self) -> None:
        """Reset score gauges to zero."""
        try:
            self.query_one("#goal-gauge", ScoreGauge).score = 0
            self.query_one("#effectiveness-gauge", ScoreGauge).score = 0
            self.query_one("#inferred-goal", Static).update("")
            self.query_one("#suggestions", Static).update("Press [A] to analyze...")
        except Exception:
            pass

    def action_next_screen(self) -> None:
        """Go to compare screen."""
        self.app.switch_screen("compare")

    def action_prev_screen(self) -> None:
        """Go back to scan screen."""
        self.app.switch_screen("scan")
