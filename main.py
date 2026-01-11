"""
To make this program runs well, you need to install separated python & python-tk from the OS itself.
Otherwise you will get the warning message like this:
    DEPRECATION WARNING: The system version of Tk is deprecated and may be removed in a future release. Please don't rely on it. Set TK_SILENCE_DEPRECATION=1 to suppress this warning.
It makes the canvas doesn't showing up rectangle, oval, and text.
To solve this problem, I'm using Homebrew, so the command is this:
    brew install python python-tk
Then, export homebrew bin to PATH in order to make separated python & python-tk is used:
    export PATH="/opt/homebrew/bin:$PATH"
"""

import tkinter

from url import URL
from browser import Browser

if __name__ == "__main__":
    import sys

    Browser().new_tab(URL(sys.argv[1]))
    tkinter.mainloop()

"""
To run this program use Python 3:
    python3 -m http.server 8000 -d ./static-site
    python3 main.py http://localhost:8000
"""
