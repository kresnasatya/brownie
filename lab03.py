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
import tkinter.font
from lab01 import URL
from lab02 import HSTEP, VSTEP, WIDTH, HEIGHT


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


SCROLL_STEP = 100


def layout(text):
    font = tkinter.font.Font()
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for word in text.split():
        w = font.measure(word)
        if cursor_x + w > WIDTH - HSTEP:
            cursor_y += font.metrics("linespace") * 1.25
            cursor_x = HSTEP
        display_list.append((cursor_x, cursor_y, word))
        cursor_x += w + font.measure(" ")
    return display_list


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)

    def load(self, url):
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, anchor="nw")

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()


if __name__ == "__main__":
    import sys

    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()

"""
To run this program use Python 3:
    python3 lab03.py https://browser.engineering/text.html
"""
