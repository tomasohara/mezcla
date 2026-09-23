#! /usr/bin/env python3

"""
Clipboard button module

Provides a minimalist, frameless PyQt5 window with a single button.
The window takes a string via command-line argument. When clicked, 
the text is copied to the system clipboard and the application stays open 
to allow multiple clicks. It is intended for quick, temporary copy-paste 
utility tasks (similar in spirit to xmessage).

Change facilitated by Antigravity using model Gemini 3.1 Pro (Low).

Sample usage:
   ./clipboard_button.py "2026-09-21"
"""

# Standard modules
import sys
from typing import Optional

# Installed modules
# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtCore import Qt
# pylint: enable=no-name-in-module

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system

# Constants
TL = debug.TL
TEXT_ARG = "text"


class ClipboardButton(QPushButton): # pylint: disable=too-few-public-methods
    """UI class for the minimalist clipboard button"""

    def __init__(self, text: str):
        """Initialize the minimalist UI button"""
        super().__init__(text)
        self._text = text

        # Apply minimalist frameless window hint similar to xmessage
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.clicked.connect(self.on_click)

    def on_click(self) -> None:
        """Copies text to the clipboard upon button click"""
        debug.trace(TL.USUAL, f"Button clicked, copying text: {self._text}")
        QApplication.clipboard().setText(self._text)
        debug.assertion(QApplication.clipboard().text() == self._text)


class ClipboardButtonApp(Main):
    """Script input processing class for minimalist clipboard button"""
    text_arg: str = ""
    button: Optional[ClipboardButton] = None

    def setup(self) -> None:
        """Check results of command line processing"""
        debug.trace(TL.VERBOSE, f"ClipboardButtonApp.setup(): self={self}")

        val = self.get_parsed_argument(TEXT_ARG, self.text_arg)
        if val is not None:
            self.text_arg = str(val)

    def run_main_step(self) -> None:
        """Main processing step"""
        debug.trace(TL.DETAILED, f"ClipboardButtonApp.run_main_step(): self={self}")

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        self.button = ClipboardButton(self.text_arg)
        self.button.show()

        # Start event loop
        app.exec_()


#-------------------------------------------------------------------------------

def main() -> None:
    """Entry point"""
    debug.trace(TL.DETAILED, f"main(): script={system.real_path(__file__)}")

    app = ClipboardButtonApp(
        description=__doc__.format(script=gh.basename(__file__)),
        skip_input=True,
        manual_input=True,
        positional_arguments=[TEXT_ARG]
    )
    app.run()


#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
