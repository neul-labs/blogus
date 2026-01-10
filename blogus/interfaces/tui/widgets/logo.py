"""
ASCII logo widget for Blogus TUI demo.
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

BLOGUS_LOGO = r"""
    ____  __    ____  ______  __  _______
   / __ )/ /   / __ \/ ____/ / / / / ___/
  / __  / /   / / / / / __  / / / /\__ \
 / /_/ / /___/ /_/ / /_/ / / /_/ /___/ /
/_____/_____/\____/\____/  \____//____/
"""

BLOGUS_LOGO_SMALL = r"""
 ___  _    ___   ___ _   _ ___
| _ )| |  / _ \ / __| | | / __|
| _ \| |_| (_) | (_ | |_| \__ \
|___/|____\___/ \___|\___/|___/
"""


class LogoWidget(Static):
    """
    Widget displaying the Blogus ASCII logo.
    """

    DEFAULT_CSS = """
    LogoWidget {
        text-align: center;
        color: #7aa2f7;
        text-style: bold;
        padding: 1;
    }
    """

    def __init__(
        self,
        small: bool = False,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Initialize the logo widget.

        Args:
            small: Use smaller logo variant
            id: Widget ID
            classes: CSS classes
        """
        logo = BLOGUS_LOGO_SMALL if small else BLOGUS_LOGO
        super().__init__(logo, id=id, classes=classes)


class LogoContainer(Container):
    """
    Container with logo, tagline, and instructions.
    """

    DEFAULT_CSS = """
    LogoContainer {
        align: center middle;
        height: 100%;
    }
    """

    def __init__(
        self,
        tagline: str = "package.lock for AI prompts",
        instructions: str = "",
        small: bool = False,
    ) -> None:
        """
        Initialize the logo container.

        Args:
            tagline: Text shown below logo
            instructions: Keyboard instructions text
            small: Use smaller logo
        """
        super().__init__()
        self.tagline = tagline
        self.instructions = instructions
        self.small = small

    def compose(self) -> ComposeResult:
        """Compose the logo container."""
        yield LogoWidget(small=self.small, id="logo")
        yield Static(self.tagline, id="tagline")
        if self.instructions:
            yield Static(self.instructions, id="instructions")
