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

from pydoc import text
import tkinter
from lab01 import show, URL


def lex(body):
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return text


WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()

    def load(self, url):
        body = url.request()
        text = lex(body)
        # self.canvas.create_rectangle(10, 20, 400, 300)
        # self.canvas.create_oval(100, 100, 150, 150)
        # self.canvas.create_text(200, 150, text="Hi!")
        cursor_x, cursor_y = HSTEP, VSTEP
        for c in text:
            self.canvas.create_text(cursor_x, cursor_y, text=c)
            cursor_x += HSTEP
            if cursor_x >= WIDTH - HSTEP:
                cursor_y += VSTEP
                cursor_x = HSTEP


if __name__ == "__main__":
    import sys

    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()

"""
To run this program use Python 3:
    python3 lab02.py https://example.org/
"""
