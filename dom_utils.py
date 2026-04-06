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

import ctypes

import sdl2
import skia

from blend import Blend
from css_parser import CSSParser
from draw_outline import DrawOutline
from draw_rrect import DrawRRect
from element import Element
from numeric_animation import NumericAnimation
from protected_field import ProtectedField
from transform import Transform, map_translation

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18

SCROLL_STEP = 100

FONTS = {}

REFRESH_RATE_SEC = 0.033


def get_font(size, weight, style):
    key = (weight, style)
    if key not in FONTS:
        if weight == "bold":
            skia_weight = skia.FontStyle.kBold_Weight
        else:
            skia_weight = skia.FontStyle.kNormal_Weight
        if style == "italic":
            skia_style = skia.FontStyle.kItalic_Slant
        else:
            skia_style = skia.FontStyle.kUpright_Slant
        skia_width = skia.FontStyle.kNormal_Width
        style_info = skia.FontStyle(skia_weight, skia_width, skia_style)
        font = skia.Typeface("Arial", style_info)
        FONTS[key] = font
    return skia.Font(FONTS[key], size)


def linespace(font):
    metrics = font.getMetrics()
    return metrics.fDescent - metrics.fAscent


def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


def tree_to_list(tree, list):
    list.append(tree)
    children = tree.children
    if isinstance(children, ProtectedField):
        children = children.get()
    for child in tree.children:
        tree_to_list(child, list)
    return list


INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
}

CSS_PROPERTIES = {
    "font-size": "inherit",
    "font-weight": "inherit",
    "font-style": "inherit",
    "color": "inherit",
    "opacity": "1.0",
    "transition": "",
    "transform": "none",
    "mix-blend-mode": None,
    "border-radius": "0px",
    "overflow": "visible",
    "outline": "none",
    "background-color": "transparent",
    "image-rendering": "auto",
}


def style(node, rules, frame):
    needs_style = any([field.dirty for field in node.style.values()])
    if needs_style:
        old_style = dict(
            [(property, field.value) for property, field in node.style.items()]
        )
        new_style = CSS_PROPERTIES.copy()

        node.style.set(new_style)
        for property, default_value in INHERITED_PROPERTIES.items():
            if node.parent:
                parent_field = node.parent.style[property]
                parent_value = parent_field.read(notify=node.style[property])
                new_style[property] = parent_value
            else:
                new_style[property] = default_value
        for media, selector, body in rules:
            if media:
                if (media == "dark") != frame.tab.dark_mode:
                    continue
            if not selector.matches(node):
                continue
            for property, value in body.items():
                new_style[property] = value
        if isinstance(node, Element) and "style" in node.attributes:
            pairs = CSSParser(node.attributes["style"]).body()
            for property, value in pairs.items():
                new_style[property] = value
        if new_style["font-size"].endswith("%"):
            if node.parent:
                parent_field = node.parent.style["font-size"]
                parent_font_size = parent_field.read(notify=node.style["font-size"])
            else:
                parent_font_size = INHERITED_PROPERTIES["font-size"]
            node_pct = float(new_style["font-size"][:-1]) / 100
            parent_px = float(parent_font_size[:-2])
            new_style["font-size"] = str(node_pct * parent_px) + "px"

        if old_style:
            transitions = diff_styles(old_style, new_style)
            for property, (old_value, new_value, num_frames) in transitions.items():
                if property == "opacity":
                    frame.set_needs_render()
                    animation = NumericAnimation(old_value, new_value, num_frames)
                    node.animations[property] = animation
                    new_style[property] = animation.animate()

        for property, field in node.style.items():
            field.set(new_style[property])

    for child in node.children:
        style(child, rules, frame)


def cascade_priority(rule):
    media, selector, body = rule
    return selector.priority


def paint_visual_effects(node, cmds, rect):
    opacity = float(node.style["opacity"].get())
    blend_mode = node.style["mix-blend-mode"].get()
    translation = parse_transform(node.style["transform"].get())

    if node.style["overflow"].get() == "clip":
        border_radius = float(node.style["border-radius"].get()[:-2])
        if not blend_mode:
            blend_mode = "source-over"
        cmds = [
            Blend(
                1.0,
                "source-over",
                cmds
                + [
                    Blend(
                        1.0,
                        "destination-in",
                        [DrawRRect(rect, border_radius, "white")],
                        None,
                    )
                ],
                node,
            )
        ]

    blend_op = Blend(opacity, blend_mode, cmds, node)
    node.blend_op = blend_op
    return [Transform(translation, rect, node, [blend_op])]


def add_parent_pointers(nodes, parent=None):
    for node in nodes:
        node.parent = parent
        add_parent_pointers(node.children, node)


def parse_transition(value):
    properties = {}
    if not value:
        return properties
    if item in value.split(","):
        property, duration = item.split(" ", 1)
        frames = int(float(duration[:-1]) / REFRESH_RATE_SEC)
        properties[property] = frames
    return properties


def diff_styles(old_style, new_style):
    transitions = {}
    for property, num_frames in parse_transition(new_style.get("transitions")).items():
        if property not in old_style:
            continue
        if property not in new_style:
            continue
        old_value = old_value[property]
        new_value = new_style[property]
        if old_value == new_value:
            continue
        transitions[property] = (old_value, new_value, num_frames)
    return transitions


def parse_transform(transform_str):
    if transform_str.find("translate(") < 0:
        return None
    # paren is parentheses
    left_paren = transform_str.find("(")
    right_paren = transform_str.find(")")
    (x_px, y_px) = transform_str[left_paren + 1 : right_paren].split(",")
    return (float(x_px[:-2]), float(y_px[:-2]))


def absolute_bounds_for_obj(obj):
    rect = skia.Rect.MakeXYWH(obj.x, obj.y, obj.width, obj.height)
    cur = obj.node
    while cur:
        rect = map_translation(rect, parse_transform(cur.style.get("transform", "")))
        cur = cur.parent
    return rect


def local_to_absolute(display_item, rect):
    while display_item.parent:
        rect = display_item.parent.map(rect)
        display_item = display_item.parent
    return rect


def absolute_to_local(display_item, rect):
    parent_chain = []
    while display_item.parent:
        parent_chain.append(display_item.parent)
        display_item = display_item.parent
    for parent in reversed(parent_chain):
        rect = parent.unmap(rect)
    return rect


def dpx(css_px, zoom):
    return css_px * zoom


def is_focusable(node):
    if get_tabindex(node) < 0:
        return False
    elif "tabindex" in node.attributes:
        return True
    elif "contenteditable" in node.attributes:
        return True
    else:
        return node.tag in ["input", "button", "a"]


def get_tabindex(node):
    tabindex = int(node.attributes.get("tabindex", "9999999"))
    return 9_999_999 if tabindex == 0 else tabindex


def paint_outline(node, cmds, rect, zoom):
    outline = parse_outline(node.style.get("outline"))
    if not outline:
        return
    thickness, color = outline
    cmds.append(DrawOutline(rect, color, dpx(thickness, zoom)))


def parse_outline(outline_str):
    if not outline_str:
        return None
    values = outline_str.split(" ")
    if len(values) != 3:
        return None
    if values[1] != "solid":
        return None
    return int(values[0][:-2]), values[2]


def speak_text(text):
    print("SPEAK:", text)


def font(css_style, zoom, notify):
    weight = css_style["font-weight"].read(notify)
    variant = css_style["font-style"].read(notify)
    size = None
    try:
        size = float(css_style["font-size"].read(notify)[:-2]) * 0.75
    except ValueError:
        size = 16
    font_size = dpx(size, zoom)
    return get_font(font_size, weight, variant)


def dirty_style(node):
    for property, value in node.style.items():
        value.mark()
