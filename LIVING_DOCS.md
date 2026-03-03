# Living Documentation - Web Browser Project

This document catalogs all the major entities/components in this Python-based web browser project.

## Overview

This is a web browser built from scratch using Python with graphics and windowing provided by **tkinter**. It implements HTML parsing, CSS parsing, layout engine, JavaScript execution, and basic browser features like tabs, navigation, and form handling.

---

## Core Entities

### 1. URL (`url.py`)
**Purpose**: Handles URL parsing, resolution, and HTTP/HTTPS network requests.

**Responsibilities**:
- Parse URLs into scheme, host, port, and path components
- Make HTTP and HTTPS requests using sockets and SSL
- Handle cookies with SameSite attribute support (Lax policy)
- Resolve relative URLs against a base URL
- Compute URL origins for security checks (CSP, CORS)

**Key Methods**:
- `__init__(url)` - Parse URL string into scheme, host, port, path
- `request(referrer, payload)` - Make HTTP GET/POST request with cookie support
- `resolve(url)` - Resolve relative/absolute URLs against this URL
- `origin()` - Return origin string (`scheme://host:port`)
- `__str__()` - Stringify URL, omitting default ports

**Module-level state**:
- `COOKIE_JAR` - Global dict mapping host → (cookie, params)

---

### 2. HTMLParser (`html_parser.py`)
**Purpose**: Parse HTML text into a DOM tree of Element and Text nodes.

**Responsibilities**:
- Tokenize HTML into tags and text by scanning character by character
- Handle self-closing tags (br, img, input, link, meta, etc.)
- Build proper parent-child relationships via an `unfinished` stack
- Insert implicit tags (html, head, body) when missing
- Parse tag attributes (key=value and bare key forms)
- Skip comment/doctype tags (starting with `!`)

**Key Methods**:
- `parse()` - Main parsing entry point; returns root DOM node
- `add_text(text)` - Create and attach Text nodes (skips whitespace-only text)
- `add_tag(tag)` - Create and attach Element nodes, handle closing/self-closing
- `get_attributes(text)` - Parse tag name and attribute dict from raw tag string
- `implicit_tags(tag)` - Insert missing structural tags as needed
- `finish()` - Close all remaining open tags and return root

**Constants**:
- `SELF_CLOSING_TAGS` - List of void HTML elements
- `HEAD_TAGS` - List of tags that belong in `<head>`

---

### 3. CSSParser (`css_parser.py`)
**Purpose**: Parse CSS text into selectors and style rules.

**Responsibilities**:
- Parse CSS selectors (tag and descendant)
- Parse CSS property-value declarations
- Error recovery: skip malformed rules or declarations
- Compute selector specificity/priority

**Key Methods**:
- `parse()` - Parse full CSS stylesheet; returns list of `(selector, body)` tuples
- `selector()` - Parse a single selector
- `body()` - Parse CSS rule body `{ prop: val; ... }`
- `word()` - Read an alphanumeric/symbol token
- `literal(c)` - Assert and consume a specific character
- `pair()` - Parse one `property: value` declaration
- `whitespace()` - Skip whitespace
- `ignore_until(chars)` - Error recovery: skip to next delimiter

**Classes**:
- `TagSelector` - Matches elements by tag name; priority = 1
- `DescendantSelector` - Matches descendant relationships; priority = sum of ancestor + descendant

---

### 4. Element (`element.py`)
**Purpose**: Represents an HTML element node in the DOM tree.

**Attributes**:
- `tag` - Tag name string
- `attributes` - Dict of attribute key-value pairs
- `children` - List of child nodes (Element or Text)
- `parent` - Parent node reference
- `style` - Dict of computed CSS properties
- `is_focused` - Boolean, set to True when the element has input focus

---

### 5. Text (`text.py`)
**Purpose**: Represents a text node in the DOM tree.

**Attributes**:
- `text` - Text content string
- `children` - Always empty list (text nodes have no children)
- `parent` - Parent node reference
- `is_focused` - Boolean (always False for text nodes)

---

### 6. Rect (`rect.py`)
**Purpose**: Axis-aligned rectangle utility used throughout layout and paint.

**Attributes**: `left`, `top`, `right`, `bottom`

**Key Methods**:
- `contains_point(x, y)` - True if point is inside the rectangle

---

### 7. DocumentLayout (`document_layout.py`)
**Purpose**: Root layout node for the entire document.

**Responsibilities**:
- Create a single `BlockLayout` child for the HTML root element
- Set document-level dimensions from `WIDTH`, `HSTEP`, `VSTEP` constants
- Root of the layout tree

**Key Methods**:
- `layout()` - Initialize dimensions and trigger child layout
- `paint()` - Returns empty list (no painting at document level)
- `should_paint()` - Always True

---

### 8. BlockLayout (`block_layout.py`)
**Purpose**: Layout block-level elements and inline content.

**Responsibilities**:
- Determine layout mode: block (vertical stacking) or inline (line wrapping)
- In block mode: create `BlockLayout` children for each DOM child
- In inline mode: recursively walk inline content and build lines
- Handle `<br>` by starting a new line
- Handle `<input>` and `<button>` via `InputLayout`
- Paint background colors

**Key Methods**:
- `layout()` - Compute x, y, width, height; recurse into children
- `layout_mode()` - Return `"block"` or `"inline"` based on node content
- `recurse(node)` - Walk inline DOM content, dispatching to `word()` or `input()`
- `word(node, word)` - Add a word to the current line, wrapping if needed
- `new_line()` - Start a new `LineLayout`
- `input(node)` - Add an `InputLayout` to the current line
- `paint()` - Emit `DrawRect` for non-transparent background-color
- `self_rect()` - Return a `Rect` for this block's bounding box
- `should_paint()` - False for `<input>` and `<button>` (painted by InputLayout)

**Constants**:
- `BLOCK_ELEMENTS` - List of HTML tags that trigger block layout mode
- `INPUT_WIDTH_PX = 200` - Fixed width for input/button elements

**Note**: `open_tag()`, `close_tag()`, `flush()`, `layout_intermediate()` methods exist in the file but are unused remnants of an earlier implementation.

---

### 9. LineLayout (`line_layout.py`)
**Purpose**: Represents a single line of inline content.

**Responsibilities**:
- Hold `TextLayout` and `InputLayout` children
- Compute line height using font ascent/descent metrics with 1.25× line-height factor
- Position children on a shared baseline

**Key Methods**:
- `layout()` - Compute dimensions and baseline-align all children
- `paint()` - Returns empty list
- `should_paint()` - Always True

---

### 10. TextLayout (`text_layout.py`)
**Purpose**: Layout for a single word within a line.

**Responsibilities**:
- Look up font from node style
- Measure word width with tkinter font metrics
- Position word relative to previous sibling or parent

**Key Methods**:
- `layout()` - Compute font, width, x position, height
- `paint()` - Return `[DrawText(...)]` with the word's color and font
- `should_paint()` - Always True

---

### 11. InputLayout (`input_layout.py`)
**Purpose**: Layout for `<input>` and `<button>` elements.

**Responsibilities**:
- Fixed-width (200px) layout for form controls
- Paint background color if set
- Paint input value text or button label text
- Draw a text cursor line when the element is focused

**Key Methods**:
- `layout()` - Compute font, fixed width, x position, height
- `paint()` - Emit background rect, text, and cursor line if focused
- `self_rect()` - Return bounding `Rect`
- `should_paint()` - Always True

---

### 12. JSContext (`js_context.py`)
**Purpose**: JavaScript execution environment using dukpy.

**Responsibilities**:
- Initialize dukpy `JSInterpreter`
- Load `runtime.js` into the interpreter
- Export Python functions callable from JavaScript
- Bidirectional node handle mapping (Python node ↔ JS integer handle)
- DOM query from JavaScript
- innerHTML mutation from JavaScript
- Synchronous XMLHttpRequest with CSP and CORS enforcement
- Event dispatch from Python to JavaScript listeners

**Key Methods**:
- `run(script, code)` - Execute JavaScript code, catching runtime errors
- `querySelectorAll(selector_text)` - Match nodes and return handle list
- `get_handle(elt)` - Get or create integer handle for a DOM node
- `getAttribute(handle, attr)` - Get attribute value by handle
- `dispatch_event(type, elt)` - Fire event on element; return whether default was prevented
- `innerHTML_set(handle, s)` - Parse HTML fragment and replace element's children

**Exported to JavaScript**:
- `log` → `print`
- `querySelectorAll` → `self.querySelectorAll`
- `getAttribute` → `self.getAttribute`
- `innerHTML_set` → `self.innerHTML_set`
- `XMLHttpRequest_send` → `self.XMLHttpRequest_send`

---

### 13. Tab (`tab.py`)
**Purpose**: Represents a single browser tab containing a loaded web page.

**Responsibilities**:
- Load web pages: fetch HTML, parse DOM, load stylesheets and scripts
- Enforce Content Security Policy (CSP) on stylesheet and script requests
- Apply CSS styles to DOM nodes
- Build and update the layout tree
- Generate display list (paint commands)
- Handle click events (links, inputs, buttons, forms)
- Handle keyboard input to focused elements
- Manage scroll position
- Maintain navigation history

**Key Methods**:
- `load(url, payload)` - Fetch and render a page; initialize JSContext; apply CSP
- `allowed_request(url)` - Check if a request is permitted by CSP
- `render()` - Apply styles, build layout tree, generate display list
- `draw(canvas, offset)` - Execute visible paint commands on tkinter canvas
- `click(x, y)` - Hit-test layout tree and dispatch click to links/inputs/buttons
- `submit_form(elt)` - Serialize form inputs and POST to action URL
- `keypress(char)` - Append character to focused input's value
- `scrolldown()` - Scroll down by `SCROLL_STEP`, clamped to document height
- `go_back()` - Pop history stack and reload previous URL

**State**:
- `url` - Current `URL`
- `tab_height` - Usable height below the browser chrome
- `history` - List of visited `URL` objects
- `focus` - Currently focused DOM element (or None)
- `scroll` - Current scroll position in pixels
- `nodes` - Root DOM node
- `rules` - List of CSS rules (default + page-specific)
- `document` - Root `DocumentLayout`
- `display_list` - List of paint commands
- `js` - `JSContext` instance
- `allowed_origins` - List of permitted origins from CSP header (None = allow all)

---

### 14. Chrome (`chrome.py`)
**Purpose**: Browser chrome UI (address bar, tab bar, navigation buttons).

**Responsibilities**:
- Draw tab bar with tab indicators and active tab highlight
- Draw new-tab (+) button
- Draw back (<) button
- Draw address bar with text cursor when focused
- Handle chrome click events (new tab, back, address bar, tab switching)
- Handle keyboard input in address bar
- Navigate to entered URL on Enter

**Key Methods**:
- `tab_rect(i)` - Compute bounding rect for tab `i`
- `paint()` - Return list of draw commands for all chrome UI elements
- `click(x, y)` - Handle click on chrome area
- `keypress(char)` - Append char to address bar if focused; return True if consumed
- `enter()` - Navigate active tab to address bar URL
- `blur()` - Clear chrome focus

**Layout**:
- Tab bar occupies the top portion
- URL bar below the tab bar (contains back button and address rect)
- `self.bottom` - y coordinate where web content begins

---

### 15. Browser (`browser.py`)
**Purpose**: Main browser application managing the window, tabs, and rendering loop.

**Responsibilities**:
- Create tkinter window and canvas (800×600)
- Bind input events (Down arrow, click, key, Return)
- Manage list of tabs and active tab
- Dispatch events to Chrome or active Tab
- Draw: clear canvas, draw active tab content, draw chrome on top

**Key Methods**:
- `new_tab(url)` - Create and load a new Tab, set as active
- `handle_down(e)` - Scroll active tab down
- `handle_click(e)` - Route click to Chrome or Tab based on y position
- `handle_key(e)` - Route printable key to Chrome or Tab
- `handle_enter(e)` - Commit address bar input
- `draw()` - Clear canvas, draw tab content, draw chrome UI

---

### 16. Paint Commands (`draw_rect.py`, `draw_line.py`, `draw_text.py`, `draw_outline.py`)
**Purpose**: Individual drawing operations executed on a tkinter canvas.

**All commands implement**:
- `execute(scroll, canvas)` - Draw to canvas, adjusting y by scroll offset

**Types**:
- `DrawRect(rect, color)` - Filled rectangle (`canvas.create_rectangle`, no border)
- `DrawLine(x1, y1, x2, y2, color, thickness)` - Straight line (`canvas.create_line`)
- `DrawText(x1, y1, text, font, color)` - Text at position (`canvas.create_text`, anchor NW)
- `DrawOutline(rect, color, thickness)` - Rectangle border/outline (no fill)

---

### 17. DOM Utilities (`dom_utils.py`)
**Purpose**: Shared constants, font cache, and tree-manipulation utilities.

**Constants**:
- `WIDTH = 800`, `HEIGHT = 600` - Window dimensions
- `HSTEP = 13`, `VSTEP = 18` - Horizontal and vertical step sizes
- `SCROLL_STEP = 100` - Pixels per scroll event
- `INHERITED_PROPERTIES` - Default values for inherited CSS properties

**Functions**:
- `get_font(size, weight, style)` - Return cached tkinter font (cache key: (size, weight, style))
- `print_tree(node, indent)` - Debug-print the DOM or layout tree
- `tree_to_list(tree, list)` - Flatten a tree into a pre-order list
- `style(node, rules)` - Apply CSS rules to a node and recurse; resolves percentage font-size
- `cascade_priority(rule)` - Return selector priority for CSS cascade sorting
- `paint_tree(layout_object, display_list)` - Walk layout tree and collect paint commands

---

### 18. Runtime JS (`runtime.js`)
**Purpose**: JavaScript standard library injected into every page's JS context.

**Provides**:
- `console.log(x)` - Calls Python `print` via `call_python("log", x)`
- `document.querySelectorAll(s)` - Returns array of `Node` objects
- `Node(handle)` - Constructor wrapping a Python DOM handle
- `Node.prototype.getAttribute(attr)` - Get element attribute
- `Node.prototype.addEventListener(type, listener)` - Register event listener
- `Node.prototype.dispatchEvent(evt)` - Fire event on node, call listeners
- `Node.prototype.innerHTML` (setter) - Replace element children via `innerHTML_set`
- `Event(type)` - Event constructor with `do_default = true`
- `Event.prototype.preventDefault()` - Set `do_default = false`
- `XMLHttpRequest` - Synchronous XHR (async not supported); `.open()` + `.send(body)`

---

### 19. Default Stylesheet (`browser.css`)
**Purpose**: Built-in browser styles applied to every page before author styles.

**Rules**:
- `pre` → `background-color: gray`
- `a` → `color: blue`
- `i` → `font-style: italic`
- `b` → `font-weight: bold`
- `small` → `font-size: 90%`
- `big` → `font-size: 110%`
- `input` → 16px normal font, `background-color: lightblue`
- `button` → 16px normal font, `background-color: orange`

---

### 20. Entry Point (`main.py`)
**Purpose**: Application entry point.

- Creates a `Browser`, opens the URL passed as `sys.argv[1]`, starts `tkinter.mainloop()`
- Requires Homebrew Python + python-tk on macOS (system Tk is deprecated)

**Run commands**:
```
uv run -m http.server 8000 -d ./static-site
uv run main.py http://localhost:8000   # static site

uv run server/server10.py              # server side (runs on :8080)
uv run main.py http://localhost:8080
```

---

### 21. Test Servers (`server/`)
**Purpose**: Local HTTP servers for testing browser features.

- `server8.py` - Basic form/session server
- `server9.py` - Cross-site scripting / security demo server
- `server10.py` - Content Security Policy demo server (runs on port 8080)

---

## External Dependencies

### Graphics & Windowing
- **tkinter** - Window creation, event handling, canvas drawing, font metrics

### JavaScript
- **dukpy** - Duktape-based JavaScript interpreter

### Network
- **socket** - TCP connections for HTTP
- **ssl** - TLS wrapping for HTTPS

### Standard Library
- **urllib.parse** - URL encoding for form submission

---

## Data Flow

### Loading a Web Page
1. User enters URL or clicks a link
2. `Tab.load()` calls `URL.request()` to fetch HTML
3. `HTMLParser` builds DOM tree (Element + Text nodes)
4. CSP header parsed; `allowed_origins` set
5. Linked stylesheets fetched (if CSP allows) and parsed by `CSSParser`
6. Inline scripts fetched (if CSP allows) and run via `JSContext`
7. `Tab.render()` calls `style()` to apply CSS rules to DOM
8. `DocumentLayout` → `BlockLayout` tree built and laid out
9. `paint_tree()` generates display list of draw commands
10. `Tab.draw()` executes visible commands on tkinter canvas

### Rendering Pipeline
1. **Style** - Apply CSS rules to DOM nodes (cascade, inheritance, inline styles)
2. **Layout** - Compute x, y, width, height for each layout object
3. **Paint** - Generate draw commands (DrawRect, DrawText, DrawLine, DrawOutline)
4. **Draw** - Execute draw commands on tkinter canvas with scroll offset

### Event Handling
1. tkinter delivers input event to `Browser`
2. `Browser` routes to `Chrome` (if y < chrome.bottom) or active `Tab`
3. `Tab.click()` hit-tests layout tree to find clicked element
4. `JSContext.dispatch_event()` fires JS event listeners
5. If not prevented, perform default action (navigate, focus, submit)
6. Call `render()` or `load()` to update display

---

## Architecture Notes

### Threading
- **Single-threaded**: all rendering, event handling, and JS execution runs on the main thread via tkinter's event loop. No background threads.

### Security
- **Content Security Policy (CSP)**: `default-src` directive restricts which origins stylesheets and scripts can be loaded from
- **Cookie SameSite**: Lax policy prevents cookies from being sent on cross-site non-GET requests
- **CORS for XHR**: Cross-origin XHR blocked; both CSP and same-origin checks enforced in `XMLHttpRequest_send`

### Performance
- Font caching in `FONTS` dict keyed by (size, weight, style)
- Display list culled by visible scroll range in `Tab.draw()`

---

## References

This project is based on the "Web Browser Engineering" book:
- Book: [Web Browser Engineering](https://browser.engineering/)
- GitHub: [browserengineering/browser](https://github.com/browserengineering/book)
