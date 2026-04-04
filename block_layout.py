import ctypes

import sdl2
import skia

from dom_utils import (
    VSTEP,
    dpx,
    font,
    get_font,
    paint_outline,
    paint_visual_effects,
    tree_to_list,
)
from draw_line import DrawCursor
from draw_rrect import DrawRRect
from element import Element
from iframe_layout import IFRAME_WIDTH_PX, IframeLayout
from image_layout import ImageLayout
from input_layout import InputLayout
from line_layout import LineLayout
from text import Text
from text_layout import TextLayout

INPUT_WIDTH_PX = 200

BLOCK_ELEMENTS = [
    "html",
    "body",
    "article",
    "section",
    "nav",
    "aside",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hgroup",
    "header",
    "footer",
    "address",
    "p",
    "hr",
    "pre",
    "blockquote",
    "ol",
    "ul",
    "menu",
    "li",
    "dl",
    "dt",
    "dd",
    "figure",
    "figcaption",
    "main",
    "div",
    "table",
    "form",
    "fieldset",
    "legend",
    "details",
    "summary",
]


class BlockLayout:
    def __init__(self, node, parent, previous, frame=None):
        self.node = node
        node.layout_object = self
        self.parent = parent
        self.previous = previous
        self.frame = frame
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def __repr__(self):
        return f"BlockLayout({self.node}, mode={self.layout_mode()})"

    def layout(self):
        self.x = self.parent.x
        self.width = self.parent.width
        self.zoom = self.parent.zoom
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        mode = self.layout_mode()
        if mode == "block":
            previous = None
            self.children = []
            for child in self.node.children:
                next = BlockLayout(child, self, previous, self.frame)
                self.children.append(next)
                previous = next
        else:
            self.children = []
            self.new_line()
            self.recurse(self.node)

        for child in self.children:
            child.layout()

        self.height = sum([child.height for child in self.children])

    def self_rect(self):
        return skia.Rect.MakeLTRB(
            l=self.x,
            t=self.y,
            r=self.x + self.width,
            b=self.y + self.height,
        )

    def paint(self):
        cmds = []
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            radius = float(self.node.style.get("border-radius", "0px")[:-2])
            cmds.append(DrawRRect(self.self_rect(), radius, bgcolor))
        return cmds

    def word(self, node, word):
        node_font = font(node.style, self.zoom)
        w = node_font.measureText(word)
        self.add_inline_child(node, w, TextLayout, word)

    def new_line(self):
        self.cursor_x = 0
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)

    def flush(self):
        pass

    def open_tag(self, tag):
        # print("tag: ", tag)
        if tag == "i":
            self.style = "italic"
        elif tag == "em":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "strong":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()

    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "em":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "strong":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP

    def recurse(self, node):
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node, word)
        else:
            if node.tag == "br":
                self.new_line()
            elif node.tag == "input" or node.tag == "button":
                self.input(node)
            elif node.tag == "img":
                self.image(node)
            elif node.tag == "iframe" and "src" in node.attributes:
                self.iframe(node)
            else:
                for child in node.children:
                    self.recurse(child)

    def iframe(self, node):
        if "width" in self.node.attributes:
            w = dpx(int(self.node.attributes["width"]), self.zoom)
        else:
            w = IFRAME_WIDTH_PX + dpx(2, self.zoom)
        self.add_inline_child(node, w, IframeLayout, frame=self.frame)

    def input(self, node):
        w = dpx(INPUT_WIDTH_PX, self.zoom)
        self.add_inline_child(node, w, InputLayout, frame=self.frame)

    def image(self, node):
        w = dpx(node.image.width(), self.zoom)
        if "width" in node.attributes:
            w = dpx(int(node.attributes["width"]), self.zoom)
        self.add_inline_child(node, w, ImageLayout, frame=self.frame)

    def layout_intermediate(self):
        previous = None
        for child in self.node.children:
            next = BlockLayout(child, self, previous, self.frame)
            self.children.append(next)
            previous = next

    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif self.node.children:
            for child in self.node.children:
                if isinstance(child, Text):
                    continue
                if child.tag in BLOCK_ELEMENTS:
                    return "block"
            return "inline"
        elif self.node.tag in ["input", "img", "iframe"]:
            return "inline"
        else:
            return "block"

    def should_paint(self):
        return isinstance(self.node, Text) or (
            self.node.tag not in ["input", "button", "img", "iframe"]
        )

    def paint_effects(self, cmds):
        if self.node.is_focused and "contenteditable" in self.node.attributes:
            text_nodes = [
                t for t in tree_to_list(self, []) if isinstance(t, TextLayout)
            ]
            if text_nodes:
                cmds.append(DrawCursor(text_nodes[-1], text_nodes[-1].width))
            else:
                cmds.append(DrawCursor(self, 0))

        cmds = paint_visual_effects(self.node, cmds, self.self_rect())
        paint_outline(self.node, cmds, self.self_rect(), self.zoom)
        return cmds

    def add_inline_child(self, node, w, child_class, word=None, frame=None):
        if self.cursor_x + w > self.x + self.width:
            self.new_line()
        line = self.children[-1]
        previous_word = line.children[-1] if line.children else None
        if word:
            child = child_class(node, word, line, previous_word)
        elif frame:
            child = child_class(node, line, previous_word, frame)
        else:
            child = child_class(node, line, previous_word)
        line.children.append(child)
        self.cursor_x += w + font(node.style, self.zoom).measureText(" ")
