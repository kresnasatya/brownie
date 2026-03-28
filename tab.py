import ctypes
import math
import urllib.parse

import skia

from accessibility_node import AccessibilityNode
from commit_data import CommitData
from css_parser import CSSParser
from document_layout import DocumentLayout
from dom_utils import (
    INHERITED_PROPERTIES,
    SCROLL_STEP,
    VSTEP,
    WIDTH,
    absolute_bounds_for_obj,
    cascade_priority,
    dpx,
    get_tabindex,
    is_focusable,
    style,
    tree_to_list,
)
from element import Element
from html_parser import HTMLParser
from iframe_layout import IframeLayout
from js_context import JSContext
from task import Task
from task_runner import TaskRunner
from text import Text
from url import URL

DEFAULT_STYLE_SHEET = CSSParser(open("browser.css").read()).parse()

BROKEN_IMAGE = skia.Image.open("Broken_Image.png")


class Tab:
    def __init__(self, browser, tab_height):
        self.url = ""
        self.tab_height = tab_height
        self.history = []
        self.focus = None
        self.focused_frame = None
        self.needs_raf_callbacks = False
        self.needs_paint = False
        self.browser = browser
        self.task_runner = TaskRunner(self)
        self.task_runner.start_thread()
        self.composited_updates = []
        self.zoom = 1.0
        self.dark_mode = browser.dark_mode
        self.needs_focus_scroll = False
        self.needs_accessibility = False
        self.accessibility_tree = None
        self.root_frame = None
        self.window_id_to_frame = {}
        self.origin_to_js = {}

    def set_dark_mode(self, val):
        self.dark_mode = val
        self.set_needs_render()

    def click(self, x, y):
        self.render()
        self.root_frame.click(x, y)

    def load(self, url, payload=None):
        self.loaded = False
        self.history.append(url)
        self.task_runner.clear_pending_tasks()  # NOTE: I don't know why this line doesn't mentioned in book. But, in GitHub repo it shows.
        self.root_frame = Frame(self, None, None)
        self.root_frame.load(url, payload)
        self.root_frame.frame_width = WIDTH
        self.root_frame.frame_height = self.tab_height
        self.loaded = True

    def get_js(self, url):
        origin = url.origin()
        if origin not in self.origin_to_js:
            self.origin_to_js[origin] = JSContext(self, origin)
        return self.origin_to_js[origin]

    def clamp_scroll(self, scroll):
        height = math.ceil(self.document.height + 2 * VSTEP)
        maxscroll = height - self.tab_height
        return max(0, min(scroll, maxscroll))

    def allowed_request(self, url):
        return self.allowed_origins == None or url.origin() in self.allowed_origins

    def set_needs_render(self):
        self.needs_style = True
        self.browser.set_needs_animation_frame(self)

    def set_needs_layout(self):
        self.needs_layout = True
        self.browser.set_needs_animation_frame(self)

    def set_needs_paint(self):
        self.needs_paint = True
        self.browser.set_needs_animation_frame(self)

    def set_needs_render_all_frames(self):
        for id, frame in self.window_id_to_frame.items():
            frame.set_needs_render()

    def render(self):
        self.browser.measure.time("render")

        for id, frame in self.window_id_to_frame.items():
            if frame.loaded:
                frame.render()

        if self.needs_accessibility:
            self.accessibility_tree = AccessibilityNode(self.root_frame.nodes)
            self.accessibility_tree.build()
            self.needs_accessibility = False
            self.needs_paint = True

        if self.needs_paint:
            self.display_list = []
            paint_tree(self.root_frame.document, self.display_list)
            self.needs_paint = False

        self.browser.measure.stop("render")

    def draw(self, canvas, offset):
        for cmd in self.display_list:
            if cmd.rect.top > self.scroll + self.tab_height:
                continue
            if cmd.rect.bottom < self.scroll:
                continue
            cmd.execute(self.scroll - offset, canvas)

    def raster(self, canvas):
        for cmd in self.display_list:
            cmd.execute(canvas)

    def scrolldown(self):
        frame = self.focused_frame or self.root_frame
        frame.scrolldown()
        self.needs_accessibility = True
        self.set_needs_paint()

    def enter(self):
        if self.focus:
            frame = self.focused_frame or self.root_frame
            frame.activate_element(self.focus)

    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()
            back = self.history.pop()
            self.load(back)

    def keypress(self, char):
        if self.focus and self.focus.tag == "input":
            if "value" not in self.focus.attributes:
                self.activate_element(self.focus)
            if self.js.dispatch_event("keydown", self.focus):
                return
            self.focus.attributes["value"] += char
            self.set_needs_render()

    def zoom_by(self, increment):
        if increment > 0:
            self.zoom *= 1.1
            self.scroll *= 1.1
        else:
            self.zoom *= 1 / 1.1
            self.scroll *= 1 / 1.1
        self.scroll_changed_in_tab = True
        self.set_needs_render_all_frames()

    def reset_zoom(self):
        self.scroll_changed_in_tab = True
        self.scroll /= self.zoom
        self.zoom = 1
        self.scroll_changed_in_tab = True
        self.set_needs_render_all_frames()

    def run_animation_frame(self, scroll):
        if not self.root_frame:
            return
        if not self.root_frame.scroll_changed_in_frame:
            self.root_frame.scroll = scroll

        needs_composite = False
        for window_id, frame in self.window_id_to_frame.items():
            if not frame.loaded:
                continue

            self.browser.measure.time("script-runRAFHandlers")
            frame.js.dispatch_RAF(frame.window_id)
            self.browser.measure.stop("script-runRAFHandlers")

            for node in tree_to_list(frame.nodes, []):
                for property_name, animation in node.animations.items():
                    value = animation.animate()
                    if value:
                        node.style[property_name] = value
                        self.composited_updates.append(node)
                        self.set_needs_paint()

            if frame.needs_style or frame.needs_layout:
                needs_composite = True

        self.render()

        if self.focus and self.focused_frame.needs_focus_scroll:
            self.focused_frame.scroll_to(self.focus)
            self.focused_frame.needs_focus_scroll = False

        for window_id, frame in self.window_id_to_frame.items():
            if frame == self.root_frame:
                continue
            if frame.scroll_changed_in_frame:
                needs_composite = True
                frame.scroll_changed_in_frame = False

        scroll = None
        if self.root_frame.scroll_changed_in_frame:
            scroll = self.root_frame.scroll

        composited_updates = None
        if not needs_composite:
            composited_updates = {}
            for node in self.composited_updates:
                composited_updates[node] = node.blend_op
        self.composited_updates = []

        root_frame_focused = (
            not self.focused_frame or self.focused_frame == self.root_frame
        )
        commit_data = CommitData(
            self.root_frame.url,
            scroll,
            root_frame_focused,
            math.ceil(self.root_frame.document.height),
            self.display_list,
            composited_updates,
            self.accessibility_tree,
            self.focus,
        )
        self.display_list = None
        self.root_frame.scroll_changed_in_frame = False

        self.browser.commit(self, commit_data)

    def advance_tab(self):
        frame = self.focused_frame or self.root_frame
        frame.advance_tab()

    def focus_element(self, node):
        if node and node != self.focus:
            self.needs_focus_scroll = True
        if self.focus:
            self.focus.is_focused = False
        self.focus = node
        if node:
            node.is_focused = True

    def post_message(self, message, target_window_id):
        frame = self.window_id_to_frame[target_window_id]
        frame.js.dispatch_post_message(message, target_window_id)


class Frame:
    def __init__(self, tab, parent_frame, frame_element) -> None:
        self.tab = tab
        self.parent_frame = parent_frame
        self.frame_element = frame_element
        self.needs_style = False
        self.needs_layout = False

        self.document = None
        self.scroll = 0
        self.scroll_changed_in_frame = True
        self.needs_focus_scroll = False
        self.nodes = None
        self.url = None
        self.js = None
        self.loaded = False

        self.frame_width = 0
        self.frame_height = 0

        self.window_id = len(self.tab.window_id_to_frame)
        self.tab.window_id_to_frame[self.window_id] = self

    def set_needs_render(self):
        self.needs_style = True
        self.tab.needs_accessibility = True
        self.tab.set_needs_paint()

    def set_needs_layout(self):
        self.needs_layout = True
        self.tab.needs_accesibility = True
        self.tab.set_needs_paint()

    def render(self):
        if self.needs_style:
            INHERITED_PROPERTIES["color"] = "black"
            if self.tab.dark_mode:
                INHERITED_PROPERTIES["color"] = "white"
            style(self.nodes, sorted(self.rules, key=cascade_priority), self)
            self.needs_layout = True
            self.needs_style = False

        if self.needs_layout:
            self.document = DocumentLayout(self.nodes, self)
            self.document.layout(self.frame_width, self.tab.zoom)
            self.tab.needs_accessibility = True
            self.needs_paint = True
            self.needs_layout = False

    def load(self, url, payload=None):
        self.loaded = False
        self.zoom = 1
        self.scroll = 0
        self.scroll_changed_in_frame = True
        headers, body = url.request(self.url, payload)
        body = body.decode("utf8", "replace")
        self.url = url

        self.allowed_origins = None
        if "content-security-policy" in headers:
            csp = headers["content-security-policy"].split()
            if len(csp) > 0 and csp[0] == "default-src":
                self.allowed_origins = csp[1:]

        self.nodes = HTMLParser(body).parse()

        self.rules = DEFAULT_STYLE_SHEET.copy()
        links = [
            node.attributes["href"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "link"
            and node.attributes.get("rel") == "stylesheet"
            and "href" in node.attributes
        ]
        for link in links:
            style_url = url.resolve(link)
            if not self.allowed_request(style_url):
                print("Blocked style", link, "due to CSP")
                continue
            try:
                header, body = style_url.request(url)
            except:
                continue
            self.rules.extend(CSSParser(body.decode("utf8", "response")).parse())

        if self.js:
            self.js.discarded = True
        self.js = self.tab.get_js(url)
        self.js.add_window(self)
        scripts = [
            node.attributes["src"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "script"
            and "src" in node.attributes
        ]
        for script in scripts:
            script_url = url.resolve(script)
            if not self.allowed_request(script_url):
                print("Blocked script", script, "due to CSP")
                continue
            try:
                header, body = script_url.request(url)
            except:
                continue
            body = body.decode("utf8", "replace")
            task = Task(self.js.run, script_url, body, self.window_id)
            self.tab.task_runner.schedule_task(task)

        images = [
            node
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element) and node.tag == "img"
        ]
        for img in images:
            try:
                src = img.attributes.get("src", "")
                image_url = url.resolve(src)
                assert self.allowed_request(image_url), (
                    "Block load of " + str(image_url) + " due to CSP"
                )
                header, body = image_url.request(url)
                img.encoded_data = body
                data = skia.Data.MakeWithoutCopy(body)
                img.image = skia.Image.MakeFromEncoded(data)
                assert img.image, "Failed to recognize format for " + str(image_url)
            except Exception as e:
                print("Image", img.attributes.get("src", ""), "crashed", e)
                img.image = BROKEN_IMAGE

        iframes = [
            node
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "iframe"
            and "src" in node.attributes
        ]
        for iframe in iframes:
            document_url = url.resolve(iframe.attributes["src"])
            if not self.allowed_request(document_url):
                print("Blocked iframe", document_url, "due to CSP")
                iframe.frame = None
                continue
            iframe.frame = Frame(self.tab, self, iframe)
            task = Task(iframe.frame.load, document_url)
            self.tab.task_runner.schedule_task(task)

        self.set_needs_render()
        self.loaded = True

    def click(self, x, y):
        self.focus_element(None)
        y += self.scroll
        loc_rect = skia.Rect.MakeXYWH(x, y, 1, 1)
        objs = [
            obj
            for obj in tree_to_list(self.document, [])
            if absolute_bounds_for_obj(obj).intersects(loc_rect)
        ]
        if not objs:
            return
        elt = objs[-1].node
        if elt and self.js.dispatch_event("click", elt, self.window_id):
            return
        while elt:
            if isinstance(elt, Text):
                pass
            elif elt.tag == "iframe":
                if not elt.layout_object:
                    return
                abs_bounds = absolute_bounds_for_obj(elt.layout_object)
                border = dpx(1, elt.layout_object.zoom)
                new_x = x - abs_bounds.left() - border
                new_y = y - abs_bounds.top() - border
                elt.frame.click(new_x, new_y)
                return
            elif is_focusable(elt):
                self.focus_element(elt)
                self.activate_element(elt)
                self.set_needs_render()
                return
            elt = elt.parent

    def focus_element(self, node):
        if node and node != self.tab.focus:
            self.needs_focus_scroll = True
        if self.tab.focus:
            self.tab.focus.is_focused = False
        if self.tab.focused_frame and self.tab.focused_frame != self:
            self.tab.focused_frame.set_needs_render()
        self.tab.focus = node
        self.tab.focused_frame = self
        if node:
            node.is_focused = True
        self.set_needs_render()

    def activate_element(self, elt):
        if elt.tag == "input":
            elt.attributes["value"] = ""
            self.set_needs_render()
        elif elt.tag == "a" and "href" in elt.attributes:
            url = self.url.resolve(elt.attributes["href"])
            self.load(url)
        elif elt.tag == "button":
            while elt:
                if elt.tag == "from" and "action" in elt.attributes:
                    self.submit_form(elt)
                elt = elt.parent

    def submit_form(self, elt):
        if self.js.dispatch_event("submit", elt):
            return
        inputs = [
            node
            for node in tree_to_list(elt, [])
            if isinstance(node, Element)
            and node.tag == "input"
            and "name" in node.attributes
        ]

        body = ""
        for input in inputs:
            name = input.attributes["name"]
            value = input.attributes.get("value", "")
            name = urllib.parse.quote(name)
            value = urllib.parse.quote(value)
            body += "&" + name + "=" + value
        body = body[1:]

        url = self.url.resolve(elt.attributes["action"])
        self.load(url, body)

    def keypress(self, char):
        if self.focus and self.focus.tag == "input":
            if "value" not in self.focus.attributes:
                self.activate_element(self.focus)
            if self.js.dispatch_event("keydown", self.focus):
                return
            self.focus.attributes["value"] += char
            self.set_needs_render()

    def scrolldown(self):
        self.scroll = self.clamp_scroll(self.scroll + SCROLL_STEP)

    def clamp_scroll(self, scroll):
        height = math.ceil(self.document.height + 2 * VSTEP)
        maxscroll = height - self.frame_height
        return max(0, min(scroll, maxscroll))

    def scroll_to(self, elt):
        assert not (self.needs_style or self.needs_layout)
        objs = [
            obj for obj in tree_to_list(self.document, []) if obj.node == self.tab.focus
        ]
        if not objs:
            return
        obj = objs[0]

        if self.scroll < obj.y < self.scroll + self.frame_height:
            return

        new_scroll = obj.y - SCROLL_STEP
        self.scroll = self.clamp_scroll(new_scroll)
        self.scroll_changed_in_frame = True
        self.tab.set_needs_paint()

    def advance_tab(self):
        focusable_nodes = [
            node
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element) and is_focusable(node)
        ]
        focusable_nodes.sort(key=get_tabindex)
        print(focusable_nodes)

        idx = 0
        if self.tab.focus in focusable_nodes:
            idx = focusable_nodes.index(self.tab.focus) + 1

        if idx < len(focusable_nodes):
            self.focus_element(focusable_nodes[idx])
        else:
            self.focus_element(None)
            self.tab.browser.focus_addressbar()
        self.set_needs_render()

    def allowed_request(self, url):
        return self.allowed_origins == None or url.origin() in self.allowed_origins


def paint_tree(layout_object, display_list):
    cmds = layout_object.paint()

    if (
        isinstance(layout_object, IframeLayout)
        and layout_object.node.frame
        and layout_object.node.frame.loaded
    ):
        paint_tree(layout_object.node.frame.document, cmds)
    else:
        for child in layout_object.children:
            paint_tree(child, cmds)

    cmds = layout_object.paint_effects(cmds)
    display_list.extend(cmds)
