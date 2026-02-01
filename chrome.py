import ctypes
import sdl2
import skia
from dom_utils import WIDTH, get_font, linespace
from draw_rect import DrawRect
from draw_line import DrawLine
from draw_outline import DrawOutline
from draw_text import DrawText
from url import URL

class Chrome:
    def __init__(self, browser):
        self.browser = browser
        self.font = get_font(20, "normal", "roman")
        self.font_height = linespace(self.font)
        self.padding = 5
        self.tabbar_top = 0
        self.tabbar_bottom = self.font_height + 2 * self.padding
        plus_width = self.font.measureText("+") * 2 * self.padding
        self.newtab_rect = skia.Rect.MakeLTRB(
            l=self.padding,
            t=self.padding,
            r=self.padding + plus_width,
            b=self.padding + self.font_height
        )
        self.urlbar_top = self.tabbar_bottom
        self.urlbar_bottom = self.urlbar_top + self.font_height + 2 * self.padding
        self.bottom = self.urlbar_bottom
        back_width = self.font.measureText("<") + 2 * self.padding
        self.back_rect = skia.Rect.MakeLTRB(
            l=self.padding,
            t=self.urlbar_top + self.padding,
            r=self.padding + back_width,
            b=self.urlbar_bottom - self.padding,
        )
        self.address_rect = skia.Rect.MakeLTRB(
            self.back_rect.right() + self.padding,
            self.urlbar_top + self.padding,
            WIDTH - self.padding,
            self.urlbar_bottom - self.padding,
        )
        self.focus = None
        self.address_bar = ""

    def tab_rect(self, i):
        tabs_start = self.newtab_rect.right() + self.padding
        tab_width = self.font.measureText("Tab X") + 2 * self.padding
        return skia.Rect.MakeLTRB(
            l=tabs_start + tab_width * i,
            t=self.tabbar_top,
            r=tabs_start + tab_width * (i + 1),
            b=self.tabbar_bottom,
        )

    def paint(self):
        cmds = []
        cmds.append(DrawLine(0, self.bottom, WIDTH, self.bottom, "black", 1))
        cmds.append(DrawOutline(self.newtab_rect, "black", 1))
        cmds.append(
            DrawText(
                x1=self.newtab_rect.left() + self.padding,
                y1=self.newtab_rect.top(),
                text="+",
                font=self.font,
                color="black",
            )
        )
        for i, tab in enumerate(self.browser.tabs):
            bounds = self.tab_rect(i)
            cmds.append(
                DrawLine(bounds.left(), 0, bounds.left(), bounds.bottom(), "black", 1)
            )
            cmds.append(
                DrawLine(bounds.right(), 0, bounds.right(), bounds.bottom(), "black", 1)
            )
            cmds.append(
                DrawText(
                    bounds.left() + self.padding,
                    bounds.top() + self.padding,
                    "Tab {}".format(i),
                    self.font,
                    "black",
                )
            )

            if tab == self.browser.active_tab:
                cmds.append(
                    DrawLine(0, bounds.bottom(), bounds.left(), bounds.bottom(), "black", 1)
                )
                cmds.append(
                    DrawLine(
                        bounds.right(), bounds.bottom(), WIDTH, bounds.bottom(), "black", 1
                    )
                )
        cmds.append(DrawOutline(self.back_rect, "black", 1))
        cmds.append(
            DrawText(
                self.back_rect.left() + self.padding,
                self.back_rect.top(),
                "<",
                self.font,
                "black",
            )
        )
        cmds.append(DrawOutline(self.address_rect, "black", 1))
        if self.focus == "address bar":
            cmds.append(
                DrawText(
                    self.address_rect.left() + self.padding,
                    self.address_rect.top(),
                    self.address_bar,
                    self.font,
                    "black",
                )
            )
            w = self.font.measureText(self.address_bar)
            cmds.append(
                DrawLine(
                    self.address_rect.left() + self.padding + w,
                    self.address_rect.top(),
                    self.address_rect.left() + self.padding + w,
                    self.address_rect.bottom(),
                    "red",
                    1,
                )
            )
        else:
            url = str(self.browser.active_tab.url)
            cmds.append(
                DrawText(
                    self.address_rect.left() + self.padding,
                    self.address_rect.top(),
                    url,
                    self.font,
                    "black",
                )
            )
        return cmds

    def click(self, x, y):
        self.focus = None
        if self.newtab_rect.contains(x, y):
            self.browser.new_tab(URL("https://browser.engineering"))
        elif self.back_rect.contains(x, y):
            self.browser.active_tab.go_back()
        elif self.address_rect.contains(x, y):
            self.focus = "address bar"
            self.address_bar = ""
        else:
            for i, tab in enumerate(self.browser.tabs):
                if self.tab_rect(i).contains(x, y):
                    self.browser.active_tab = tab
                    break

    def keypress(self, char):
        if self.focus == "address bar":
            self.address_bar += char
            return True
        return False

    def enter(self):
        if self.focus == "address bar":
            self.browser.active_tab.load(URL(self.address_bar))
            self.focus = None
            self.browser.focus = None
            return True
        return False

    def blur(self):
        self.focus = None
