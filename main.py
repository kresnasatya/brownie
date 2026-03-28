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
import sys

import sdl2
import skia
from sdl2.keycode import SDLK_MINUS, SDLK_RCTRL

from browser import Browser
from url import URL


def mainloop(browser):
    event = sdl2.SDL_Event()
    ctrl_down = False
    try:
        while True:
            if sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                if event.type == sdl2.SDL_QUIT:
                    browser.handle_quit()
                    sdl2.SDL_Quit()
                    sys.exit()
                elif event.type == sdl2.SDL_MOUSEBUTTONUP:
                    browser.handle_click(event.button)
                elif event.type == sdl2.SDL_MOUSEMOTION:
                    browser.handle_hover(event.motion)
                elif event.type == sdl2.SDL_KEYDOWN:
                    if ctrl_down:
                        if event.key.keysym.sym == sdl2.SDLK_EQUALS:
                            browser.increment_zoom(True)
                        elif event.key.keysym.sym == sdl2.SDLK_MINUS:
                            browser.increment_zoom(False)
                        elif event.key.keysym.sym == sdl2.SDLK_0:
                            browser.reset_zoom()
                        elif event.key.keysym.sym == sdl2.SDLK_LEFT:
                            browser.go_back()
                        elif event.key.keysym.sym == sdl2.SDLK_l:
                            browser.focus_addressbar()
                        elif event.key.keysym.sym == sdl2.SDLK_d:
                            browser.toggle_dark_mode()
                        elif event.key.keysym.sym == sdl2.SDLK_a:
                            browser.toggle_accessibility()
                        elif event.key.keysym.sym == sdl2.SDLK_t:
                            browser.new_tab()
                        elif event.key.keysym.sym == sdl2.SDLK_TAB:
                            browser.cycle_tabs()
                        elif event.key.keysym.sym == sdl2.SDLK_q:
                            browser.handle_quit()
                            sdl2.SDL_Quit()
                            sys.exit()
                            break
                    elif event.key.keysym.sym == sdl2.SDLK_RETURN:
                        browser.handle_enter()
                    elif event.key.keysym.sym == sdl2.SDLK_TAB:
                        browser.handle_tab()
                    elif event.key.keysym.sym == sdl2.SDLK_DOWN:
                        browser.handle_down()
                    elif (
                        event.key.keysym.sym == sdl2.SDLK_RCTRL
                        or event.key.keysym.sym == sdl2.SDLK_LCTRL
                    ):
                        ctrl_down = True
                elif event.type == sdl2.SDL_KEYUP:
                    if (
                        event.key.keysym.sym == sdl2.SDLK_RCTRL
                        or event.key.keysym.sym == sdl2.SDLK_LCTRL
                    ):
                        ctrl_down = False
                elif event.type == sdl2.SDL_TEXTINPUT:
                    browser.handle_key(event.text.text.decode("utf8"))
            browser.composite_raster_and_draw()
            browser.schedule_animation_frame()
    except KeyboardInterrupt:
        browser.handle_quit()
        sdl2.SDL_Quit()
        sys.exit()


if __name__ == "__main__":
    sdl2.SDL_Init(sdl2.SDL_INIT_EVENTS)
    browser = Browser()
    browser.new_tab(URL(sys.argv[1]))
    mainloop(browser)

"""
To run this program use Python 3:
    uv run -m http.server 8000 -d ./static-site
    uv run main.py http://localhost:8000 # static site

    FOR server side
    uv run server/server8.py # This will run localhost:8080
    uv run main.py http://localhost:8080 # server site
"""
