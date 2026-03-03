# Brownie Browser — Living Documentation

This document describes every entity in the **Brownie** Python browser project.
Its purpose is to serve as a reference for porting the browser to Swift with **zero third-party dependencies**.

> **Swift porting principle:** Every Python third-party library used here has a native Apple-framework equivalent.
> - `tkinter` (GUI + canvas + fonts) → `AppKit` / `CoreGraphics` / `CoreText`
> - `dukpy` (Duktape JavaScript engine) → `JavaScriptCore` (built-in on Apple platforms)
> - `socket` + `ssl` (raw TCP/TLS) → `Network` framework (`NWConnection`) or `URLSession`

---

## Table of Contents

1. [Constants & Configuration](#constants--configuration)
2. [DOM Nodes](#dom-nodes)
   - [Text](#text)
   - [Element](#element)
3. [Network Layer](#network-layer)
   - [URL](#url)
4. [Parsers](#parsers)
   - [HTMLParser](#htmlparser)
   - [CSSParser](#cssparser)
   - [TagSelector](#tagselector)
   - [DescendantSelector](#descendantselector)
5. [Layout Engine](#layout-engine)
   - [DocumentLayout](#documentlayout)
   - [BlockLayout](#blocklayout)
   - [LineLayout](#linelayout)
   - [TextLayout](#textlayout)
   - [InputLayout](#inputlayout)
6. [Paint Commands (Display List)](#paint-commands-display-list)
   - [Rect](#rect)
   - [DrawText](#drawtext)
   - [DrawRect](#drawrect)
   - [DrawLine](#drawline)
   - [DrawOutline](#drawoutline)
7. [Styling Utilities](#styling-utilities)
8. [JavaScript Engine](#javascript-engine)
   - [JSContext](#jscontext)
   - [runtime.js](#runtimejs)
9. [Browser Shell](#browser-shell)
   - [Tab](#tab)
   - [Chrome](#chrome)
   - [Browser](#browser)

---

## Constants & Configuration

**Source:** `dom_utils.py`

| Constant | Value | Description |
|---|---|---|
| `WIDTH` | `800` | Default window width in pixels |
| `HEIGHT` | `600` | Default window height in pixels |
| `HSTEP` | `13` | Horizontal margin/padding step |
| `VSTEP` | `18` | Vertical margin/padding step |
| `SCROLL_STEP` | `100` | Pixels scrolled per key/event |
| `INHERITED_PROPERTIES` | dict | CSS properties that inherit from parent: `font-size` (16px), `font-style` (normal), `font-weight` (normal), `color` (black) |
| `FONTS` | dict | Font cache keyed by `(size, weight, style)` |

**Source:** `url.py`

| Constant | Value | Description |
|---|---|---|
| `COOKIE_JAR` | dict | Global cookie store keyed by hostname; value is `(cookie_string, params_dict)` |

**Source:** `block_layout.py`

| Constant | Value | Description |
|---|---|---|
| `INPUT_WIDTH_PX` | `200` | Fixed pixel width for `<input>` and `<button>` elements |
| `BLOCK_ELEMENTS` | list | HTML tags that trigger block layout mode (e.g. `div`, `p`, `h1`–`h6`, `ul`, `li`, etc.) |

**Swift notes:**
- `WIDTH`/`HEIGHT` become the initial `NSWindow` content size.
- `FONTS` cache maps to a `[FontKey: NSFont]` dictionary.
- `COOKIE_JAR` maps to `HTTPCookieStorage` or a custom `[String: (String, [String:String])]` dict.

---

## DOM Nodes

### Text

**Source:** `text.py`

Represents a text node in the DOM tree (leaf node, no tag).

#### Properties
| Name | Type | Description |
|---|---|---|
| `text` | `str` | The raw text content |
| `children` | `list` | Always empty (leaf node, kept for tree-walk compatibility) |
| `parent` | `Element \| None` | Parent element in the DOM tree |
| `is_focused` | `bool` | Whether this node currently has focus (always `False` for text nodes) |

#### Swift notes
- Model as a `struct` or `final class` conforming to a `DOMNode` protocol.
- `children` can be an empty `[DOMNode]` or omitted entirely for text nodes.

---

### Element

**Source:** `element.py`

Represents an HTML element node in the DOM tree.

#### Properties
| Name | Type | Description |
|---|---|---|
| `tag` | `str` | Lowercase tag name (e.g. `"div"`, `"a"`, `"input"`) |
| `attributes` | `dict[str, str]` | HTML attribute key/value pairs (keys are casefolded) |
| `children` | `list[Text \| Element]` | Ordered child nodes |
| `parent` | `Element \| None` | Parent element |
| `style` | `dict[str, str]` | Computed CSS properties set during the styling pass |
| `is_focused` | `bool` | Whether the element is the focused input |

#### Swift notes
- Model as a `final class` (reference semantics needed — parent/children form a mutable graph).
- `attributes` → `[String: String]`.
- `style` → `[String: String]` (computed, filled by the styling pass).
- Both `Text` and `Element` should conform to a shared `DOMNode` protocol with `parent`, `children`, and `is_focused`.

---

## Network Layer

### URL

**Source:** `url.py`

Parses and resolves URLs, and performs raw HTTP/HTTPS requests over TCP sockets with cookie support.

#### Properties
| Name | Type | Description |
|---|---|---|
| `scheme` | `str` | `"http"` or `"https"` |
| `host` | `str` | Hostname (e.g. `"example.com"`) |
| `port` | `int` | Port number (default 80 for http, 443 for https) |
| `path` | `str` | URL path starting with `/` |

#### Methods

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(url: str)` | Parses a full URL string into its components |
| `request` | `(referrer: URL \| None, payload: str \| None) -> (headers: dict, body: str)` | Opens a raw TCP socket, optionally wraps with TLS, sends HTTP/1.0 GET or POST request, reads and returns response headers and body. Handles `Cookie` and `Set-Cookie` headers via `COOKIE_JAR`. |
| `resolve` | `(url: str) -> URL` | Resolves a relative URL against this URL. Handles absolute URLs, protocol-relative (`//`), root-relative (`/`), and relative paths including `../` traversal. |
| `origin` | `() -> str` | Returns `scheme://host:port` (used for same-origin checks) |
| `__str__` | `() -> str` | Reconstructs the full URL string, omitting default ports |

#### Key behaviours
- Only `http` and `https` schemes are supported (assertion error otherwise).
- Cookie `samesite=lax` enforcement: non-GET cross-origin requests do not send the cookie.
- Asserts no `transfer-encoding` or `content-encoding` in responses (chunked transfer / compression not supported).

#### Swift notes
- Replace raw `socket` + `ssl` with `NWConnection` (Network framework) for full control, or use `URLSession` for simpler cases. Since the goal is zero third-party dependencies, both are native.
- `COOKIE_JAR` → `HTTPCookieStorage.shared` or a custom actor-isolated dictionary.
- `resolve` logic is straightforward string manipulation — port as-is.

---

## Parsers

### HTMLParser

**Source:** `html_parser.py`

A hand-written, forgiving HTML parser that produces a DOM tree of `Text` and `Element` nodes.

#### Properties
| Name | Type | Description |
|---|---|---|
| `body` | `str` | Raw HTML source string |
| `unfinished` | `list[Element]` | Stack of currently open (unfinished) element nodes |

#### Methods

| Method | Description |
|---|---|
| `parse() -> Element` | Main entry point. Iterates through `body` character-by-character, dispatching to `add_text` or `add_tag`. Returns the root node. |
| `add_text(text: str)` | Creates a `Text` node and appends it to the current open element. Skips pure-whitespace text. Calls `implicit_tags(None)` first. |
| `add_tag(tag: str)` | Parses a tag token. Handles closing tags (pop stack), self-closing tags, and opening tags (push stack). Calls `implicit_tags(tag)` first. |
| `get_attributes(text: str) -> (tag, attributes)` | Splits a raw tag string into the tag name and a dict of attributes. Strips surrounding quotes from attribute values. |
| `finish() -> Element` | Closes any remaining open tags and returns the root element from the stack. |
| `implicit_tags(tag: str \| None)` | Inserts implicit `<html>`, `<head>`, or `<body>` tags as needed to maintain a well-formed tree structure. |

#### Class constants
| Constant | Description |
|---|---|
| `SELF_CLOSING_TAGS` | List of void elements: `area`, `base`, `br`, `col`, `embed`, `hr`, `img`, `input`, `link`, `meta`, `param`, `source`, `track`, `wbr` |
| `HEAD_TAGS` | Tags that belong inside `<head>`: `base`, `basefont`, `bgsound`, `noscript`, `link`, `meta`, `title`, `style`, `script` |

#### Swift notes
- Implement as a `struct` or `class` with a character-by-character state machine.
- The implicit tag insertion logic is essential for real-world HTML tolerance.
- No third-party dependencies — pure string parsing.

---

### CSSParser

**Source:** `css_parser.py`

A hand-written CSS parser that produces a list of `(selector, property_dict)` rule tuples.

#### Properties
| Name | Type | Description |
|---|---|---|
| `s` | `str` | Raw CSS source string |
| `i` | `int` | Current character position (cursor) |

#### Methods

| Method | Description |
|---|---|
| `parse() -> list[(selector, dict)]` | Main entry point. Returns a list of `(Selector, {prop: val})` tuples. Skips malformed rules gracefully. |
| `selector() -> TagSelector \| DescendantSelector` | Parses a CSS selector. Supports simple tag selectors and descendant combinators (space-separated tags). |
| `body() -> dict[str, str]` | Parses the `{ prop: val; ... }` block. Skips malformed declarations. |
| `pair() -> (str, str)` | Parses a single `property: value` pair. |
| `word() -> str` | Reads an alphanumeric word (including `#`, `-`, `.`, `%`). |
| `whitespace()` | Advances `i` past whitespace. |
| `literal(char)` | Asserts and consumes a specific character. |
| `ignore_until(chars) -> str \| None` | Skips forward until one of the given characters is found (used for error recovery). |

#### Swift notes
- Implement as a `struct` with a `String.Index` cursor.
- Error recovery via `ignore_until` is important for real-world CSS resilience.

---

### TagSelector

**Source:** `css_parser.py`

Matches a DOM node if it is an `Element` with a specific tag name.

#### Properties
| Name | Type | Description |
|---|---|---|
| `tag` | `str` | The tag name to match (casefolded) |
| `priority` | `int` | Specificity weight = `1` |

#### Methods
| Method | Description |
|---|---|
| `matches(node) -> bool` | Returns `True` if `node` is an `Element` whose `.tag == self.tag` |

---

### DescendantSelector

**Source:** `css_parser.py`

Matches a DOM node if it matches the `descendant` selector AND has an ancestor matching the `ancestor` selector.

#### Properties
| Name | Type | Description |
|---|---|---|
| `ancestor` | `TagSelector \| DescendantSelector` | The ancestor selector |
| `descendant` | `TagSelector \| DescendantSelector` | The descendant selector |
| `priority` | `int` | Sum of ancestor and descendant priorities |

#### Methods
| Method | Description |
|---|---|
| `matches(node) -> bool` | Walks up the parent chain to check ancestor match after confirming descendant match |

#### Swift notes
- Model both selectors as cases of a `CSSSelector` enum, or use a protocol `CSSSelector { func matches(_ node: DOMNode) -> Bool; var priority: Int { get } }`.

---

## Layout Engine

The layout engine transforms the DOM tree into a layout tree. Each layout object calculates its own position (`x`, `y`), `width`, and `height`, then produces paint commands via `paint()`.

**Layout tree hierarchy:**
```
DocumentLayout
  └── BlockLayout          (one per block-level element or inline container)
        └── LineLayout     (one per line of inline content)
              ├── TextLayout   (one per word)
              └── InputLayout  (one per <input> or <button>)
```

---

### DocumentLayout

**Source:** `document_layout.py`

The root of the layout tree. Wraps the entire document in a single top-level block.

#### Properties
| Name | Type | Description |
|---|---|---|
| `node` | `Element` | The root DOM node (typically `<html>`) |
| `parent` | `None` | Always `None` (root node) |
| `children` | `list[BlockLayout]` | Contains exactly one `BlockLayout` child |
| `x`, `y` | `float` | Position: `x = HSTEP`, `y = VSTEP` |
| `width` | `float` | `WIDTH - 2 * HSTEP` |
| `height` | `float` | Set to child's height after layout |

#### Methods
| Method | Description |
|---|---|
| `layout()` | Creates one `BlockLayout` child, sets own dimensions, calls child's `layout()` |
| `paint() -> []` | Returns empty list (document root paints nothing itself) |
| `should_paint() -> bool` | Always `True` |

---

### BlockLayout

**Source:** `block_layout.py`

Lays out a block-level or inline container. Determines layout mode and either recurses into child blocks or builds `LineLayout` / `TextLayout` / `InputLayout` objects.

#### Properties
| Name | Type | Description |
|---|---|---|
| `node` | `Text \| Element` | The DOM node being laid out |
| `parent` | `DocumentLayout \| BlockLayout` | Parent layout object |
| `previous` | `BlockLayout \| None` | Previous sibling layout (used to compute `y`) |
| `children` | `list[BlockLayout \| LineLayout]` | Child layout objects |
| `x`, `y`, `width`, `height` | `float \| None` | Geometry, computed during `layout()` |
| `cursor_x` | `float` | Inline cursor position (used in inline mode) |

#### Methods
| Method | Description |
|---|---|
| `layout()` | Computes position from parent/previous, determines `layout_mode`, creates children, calls their `layout()`, sums height |
| `layout_mode() -> "block" \| "inline"` | Returns `"block"` if any child is a block element, `"inline"` if node has children or is an input, otherwise `"block"` |
| `recurse(node)` | Walks the DOM subtree in inline mode, calling `word()` for text nodes and `input()` for input/button elements |
| `word(node, word)` | Creates a `TextLayout` in the current `LineLayout`, wrapping to a new line if needed |
| `input(node)` | Creates an `InputLayout` in the current `LineLayout`, wrapping if needed |
| `new_line()` | Appends a new `LineLayout` to `children` and resets `cursor_x` |
| `flush()` | No-op placeholder (kept for API compatibility) |
| `open_tag(tag)` / `close_tag(tag)` | Handle inline style changes (italic, bold, size) — **currently unused** in the inline-via-CSS path |
| `paint() -> list[DrawRect]` | Returns a `DrawRect` command if `background-color` is set |
| `self_rect() -> Rect` | Returns a `Rect` for the block's bounding box |
| `should_paint() -> bool` | `False` for `<input>` and `<button>` nodes (handled by `InputLayout`) |

---

### LineLayout

**Source:** `line_layout.py`

Represents one line of inline content. Computes baseline alignment across all words on the line.

#### Properties
| Name | Type | Description |
|---|---|---|
| `node` | `Element` | The containing block's DOM node |
| `parent` | `BlockLayout` | Parent block layout |
| `previous` | `LineLayout \| None` | Previous line (used to compute `y`) |
| `children` | `list[TextLayout \| InputLayout]` | Inline items on this line |
| `x`, `y`, `width`, `height` | `float` | Computed during `layout()` |

#### Methods
| Method | Description |
|---|---|
| `layout()` | Sets `x`/`width` from parent; stacks below previous line; calls `layout()` on all children; computes baseline from max ascent; positions each child's `y`; computes height from max ascent + max descent × 1.25 |
| `paint() -> []` | Returns empty list |
| `should_paint() -> bool` | Always `True` |

#### Swift notes
- Font metrics (`ascent`, `descent`, `linespace`) map to `NSFont.ascender`, `NSFont.descender`, `NSFont.leading`.

---

### TextLayout

**Source:** `text_layout.py`

Lays out a single word of text within a `LineLayout`.

#### Properties
| Name | Type | Description |
|---|---|---|
| `node` | `Text` | The DOM text node (carries style) |
| `word` | `str` | The single word string |
| `parent` | `LineLayout` | Parent line layout |
| `previous` | `TextLayout \| None` | Previous word on the same line |
| `children` | `list` | Always empty |
| `font` | `tkinter.Font` | Resolved font (set during `layout()`) |
| `x`, `y`, `width`, `height` | `float` | Computed during `layout()` |

#### Methods
| Method | Description |
|---|---|
| `layout()` | Resolves font from node's style (`font-weight`, `font-style`, `font-size`); measures word width via `font.measure(word)`; positions `x` after previous word (with space); sets `height` from `font.metrics("linespace")` |
| `paint() -> [DrawText]` | Returns one `DrawText` command using node's `color` style |
| `should_paint() -> bool` | Always `True` |

#### Swift notes
- `font.measure(word)` → `(word as NSString).size(withAttributes: [.font: nsFont]).width`
- `font.metrics("linespace")` → `nsFont.ascender + abs(nsFont.descender) + nsFont.leading`

---

### InputLayout

**Source:** `input_layout.py`

Lays out an `<input>` or `<button>` element within a `LineLayout`. Fixed width of 200 px.

#### Properties
| Name | Type | Description |
|---|---|---|
| `node` | `Element` | The `<input>` or `<button>` DOM element |
| `parent` | `LineLayout` | Parent line layout |
| `previous` | `TextLayout \| InputLayout \| None` | Previous inline sibling |
| `children` | `list` | Always empty |
| `font` | `tkinter.Font` | Resolved font (set during `layout()`) |
| `x`, `y`, `width`, `height` | `float \| None` | Geometry |

#### Methods
| Method | Description |
|---|---|
| `layout()` | Resolves font; sets `width = INPUT_WIDTH_PX (200)`; positions `x` after previous; computes `height` from linespace |
| `paint() -> list` | Draws background rect (if any), text content (`value` attr for `<input>`, text child for `<button>`), and a cursor line if `node.is_focused` |
| `self_rect() -> Rect` | Returns bounding `Rect` |
| `should_paint() -> bool` | Always `True` |

---

## Paint Commands (Display List)

Paint commands are produced by layout objects and collected into a **display list** (`Tab.display_list`). Each command has a `rect` property and an `execute(scroll, canvas)` method.

### Rect

**Source:** `rect.py`

A simple axis-aligned rectangle used as the bounding box for all paint commands.

#### Properties
| Name | Type | Description |
|---|---|---|
| `left` | `float` | Left edge x-coordinate |
| `top` | `float` | Top edge y-coordinate |
| `right` | `float` | Right edge x-coordinate |
| `bottom` | `float` | Bottom edge y-coordinate |

#### Methods
| Method | Description |
|---|---|
| `contains_point(x, y) -> bool` | Returns `True` if `(x, y)` falls within the rect (exclusive right/bottom) |

#### Swift notes
- Maps directly to `CGRect`. `contains_point` → `CGRect.contains(CGPoint)`.

---

### DrawText

**Source:** `draw_text.py`

Renders a string of text at a given position.

#### Properties
| Name | Type | Description |
|---|---|---|
| `rect` | `Rect` | Bounding box computed from font measurements |
| `text` | `str` | The text to draw |
| `font` | `tkinter.Font` | The font |
| `color` | `str` | CSS color string |

#### `execute(scroll, canvas)`
Calls `canvas.create_text(x, y - scroll, text, font, anchor="nw", fill=color)`.

#### Swift notes
- `NSAttributedString(string: text, attributes: [.font: nsFont, .foregroundColor: nsColor]).draw(at: CGPoint(x: rect.left, y: rect.top - scroll))`

---

### DrawRect

**Source:** `draw_rect.py`

Fills a rectangle with a solid color (no outline).

#### Properties
| Name | Type | Description |
|---|---|---|
| `rect` | `Rect` | The rectangle to fill |
| `color` | `str` | Fill color |

#### `execute(scroll, canvas)`
Calls `canvas.create_rectangle(...)` with `width=0` (no border).

#### Swift notes
- `NSColor(named: color)?.setFill(); NSBezierPath(rect: cgRect).fill()`

---

### DrawLine

**Source:** `draw_line.py`

Draws a straight line between two points.

#### Properties
| Name | Type | Description |
|---|---|---|
| `rect` | `Rect` | `left/top` = start point, `right/bottom` = end point |
| `color` | `str` | Line color |
| `thickness` | `int` | Line width in pixels |

#### `execute(scroll, canvas)`
Calls `canvas.create_line(x1, y1-scroll, x2, y2-scroll, fill, width)`.

#### Swift notes
- `let path = NSBezierPath(); path.move(to:); path.line(to:); path.lineWidth = thickness; color.setStroke(); path.stroke()`

---

### DrawOutline

**Source:** `draw_outline.py`

Draws a rectangle border (outline only, no fill).

#### Properties
| Name | Type | Description |
|---|---|---|
| `rect` | `Rect` | The rectangle to outline |
| `color` | `str` | Border color |
| `thickness` | `int` | Border width |

#### `execute(scroll, canvas)`
Calls `canvas.create_rectangle(...)` with `width=thickness, outline=color`.

#### Swift notes
- `NSColor(named: color)?.setStroke(); let path = NSBezierPath(rect: cgRect); path.lineWidth = CGFloat(thickness); path.stroke()`

---

## Styling Utilities

**Source:** `dom_utils.py`

These free functions implement the CSS cascade and are called by `Tab.render()`.

### `style(node, rules)`

Applies CSS rules to a DOM node (and recursively to all its children).

**Algorithm:**
1. Initialise `node.style` with inherited values from parent (or `INHERITED_PROPERTIES` defaults).
2. Apply matching stylesheet rules in order (rules must be pre-sorted by `cascade_priority`).
3. Apply inline `style=""` attribute overrides via `CSSParser.body()`.
4. Resolve percentage `font-size` values against the parent's computed pixel size.
5. Recurse into all children.

### `cascade_priority(rule) -> int`
Key function for `sorted()`. Returns `selector.priority` from a `(selector, body)` rule tuple.

### `paint_tree(layout_object, display_list)`
Recursively walks the layout tree. If `layout_object.should_paint()` is `True`, extends `display_list` with the result of `layout_object.paint()`. Then recurses into children.

### `tree_to_list(tree, list) -> list`
Flattens any tree (DOM or layout) into a list via pre-order depth-first traversal. Used for hit-testing and DOM queries.

### `get_font(size, weight, style) -> tkinter.Font`
Returns a cached `tkinter.Font`. Cache key is `(size, weight, style)`.

#### Swift notes
- `get_font` → a `FontCache` singleton keyed by `(Int, NSFont.Weight, Bool)` returning `NSFont`.
- `style()` and `paint_tree()` become methods on a `StyleEngine` and `PaintEngine` type, or free functions in a utility module.

---

## JavaScript Engine

### JSContext

**Source:** `js_context.py`

Bridges the browser's Python state with a Duktape JavaScript interpreter. Exposes DOM APIs to JavaScript via exported Python functions.

#### Properties
| Name | Type | Description |
|---|---|---|
| `tab` | `Tab` | The owning tab (gives access to the DOM, URL, etc.) |
| `interp` | `dukpy.JSInterpreter` | The JavaScript interpreter instance |
| `node_to_handle` | `dict[node, int]` | Maps DOM node objects to integer handles |
| `handle_to_node` | `dict[int, node]` | Maps integer handles back to DOM nodes |

#### Exported Python → JS bindings (registered at init)
| JS name | Python function | Description |
|---|---|---|
| `log` | `print` | `console.log` implementation |
| `querySelectorAll` | `self.querySelectorAll` | CSS selector query |
| `getAttribute` | `self.getAttribute` | Get attribute by handle |
| `innerHTML_set` | `self.innerHTML_set` | Set innerHTML by handle |
| `XMLHttpRequest_send` | `self.XMLHttpRequest_send` | Synchronous XHR |

#### Methods
| Method | Description |
|---|---|
| `run(script, code)` | Evaluates JavaScript source `code`. Catches `JSRuntimeError` and prints it. |
| `querySelectorAll(selector_text)` | Parses CSS selector, walks DOM via `tree_to_list`, returns list of integer handles for matching nodes |
| `get_handle(elt) -> int` | Returns or creates an integer handle for a DOM node |
| `getAttribute(handle, attr) -> str` | Returns the attribute value for the node identified by `handle` |
| `dispatch_event(type, elt) -> bool` | Fires a DOM event on a node. Returns `True` if default action should proceed. |
| `innerHTML_set(handle, s)` | Parses `s` as HTML, replaces `elt.children` with the new nodes, re-renders the tab |
| `XMLHttpRequest_send(method, url, body) -> str` | Performs a synchronous HTTP request from JavaScript. Enforces CSP and same-origin policy. |

#### Swift notes
- Replace `dukpy` entirely with **JavaScriptCore** (`import JavaScriptCore`).
- `JSContext` (Apple) is the direct equivalent: `context["log"] = ...` to export Swift closures.
- `node_to_handle` / `handle_to_node` maps become `[ObjectIdentifier: Int]` and `[Int: DOMNode]`.
- `dispatch_event` uses `JSContext.evaluateScript(...)`.

---

### runtime.js

**Source:** `runtime.js`

JavaScript runtime shim loaded into every `JSContext` at startup. Provides the browser-side DOM API surface that calls back into Python via `call_python(...)`.

#### Globals defined
| Global | Description |
|---|---|
| `console` | Object with `log(x)` method → `call_python("log", x)` |
| `document` | Object with `querySelectorAll(s)` → returns array of `Node` wrappers |
| `Node(handle)` | Constructor wrapping an integer handle |
| `Node.prototype.getAttribute(attr)` | → `call_python("getAttribute", handle, attr)` |
| `Node.prototype.addEventListener(type, listener)` | Registers an event listener in `LISTENERS` |
| `Node.prototype.dispatchEvent(evt)` | Dispatches stored listeners, returns `evt.do_default` |
| `Node.prototype.innerHTML` (setter) | → `call_python("innerHTML_set", handle, s)` |
| `LISTENERS` | Global object `{handle: {type: [listener, ...]}}` |
| `Event(type)` | Constructor with `type` and `do_default = true` |
| `Event.prototype.preventDefault()` | Sets `do_default = false` |
| `XMLHttpRequest` | Constructor |
| `XMLHttpRequest.prototype.open(method, url, is_async)` | Stores method/url; throws on async |
| `XMLHttpRequest.prototype.send(body)` | → `call_python("XMLHttpRequest_send", method, url, body)` |

#### Swift notes
- With JavaScriptCore, inject this same `runtime.js` string via `jsContext.evaluateScript(runtimeJS)`.
- `call_python` is the Duktape convention; with JSCore replace it with registered Swift blocks:
  `jsContext["log"] = unsafeBitCast({ ... } as @convention(block) (String) -> Void, to: AnyObject.self)`

---

## Browser Shell

### Tab

**Source:** `tab.py`

Represents a single browser tab. Owns the DOM, layout tree, display list, JS context, CSS rules, scroll state, and navigation history.

#### Properties
| Name | Type | Description |
|---|---|---|
| `url` | `URL \| None` | Currently loaded URL |
| `tab_height` | `int` | Available viewport height (window height minus chrome height) |
| `history` | `list[URL]` | Navigation history stack |
| `scroll` | `int` | Current vertical scroll offset in pixels |
| `focus` | `Element \| None` | Currently focused input element |
| `nodes` | `Element` | Root of the DOM tree |
| `document` | `DocumentLayout` | Root of the layout tree |
| `display_list` | `list[DrawCommand]` | Flat list of paint commands |
| `js` | `JSContext` | JavaScript context |
| `rules` | `list[(selector, dict)]` | Active CSS rules (default sheet + linked sheets) |
| `allowed_origins` | `list[str] \| None` | CSP-allowed origins; `None` = no restriction |

#### Methods
| Method | Description |
|---|---|
| `load(url, payload=None)` | Fetches `url`, parses HTML, creates `JSContext`, loads linked CSS and JS, calls `render()`. Parses `Content-Security-Policy` header. |
| `render()` | Runs the style pass (`style()`), builds the layout tree (`DocumentLayout`), and walks it to build `display_list` (`paint_tree()`). |
| `draw(canvas, offset)` | Iterates `display_list`, skips commands outside the viewport, calls `cmd.execute(scroll - offset, canvas)` for visible commands. |
| `click(x, y)` | Hit-tests the layout tree via `tree_to_list`; walks up the DOM from the hit node to find links, inputs, or buttons; dispatches JS events. |
| `submit_form(elt)` | URL-encodes `<input name=... value=...>` fields and POSTs to `form.action`. |
| `scrolldown()` | Increments `scroll` by `SCROLL_STEP`, clamped to max scrollable distance |
| `go_back()` | Pops the history stack and reloads the previous URL |
| `keypress(char)` | Appends `char` to focused input's `value` attribute, fires JS `keydown` event, re-renders |
| `allowed_request(url) -> bool` | Returns `True` if `url.origin()` is in `allowed_origins` (or CSP is not set) |

---

### Chrome

**Source:** `chrome.py`

Renders and handles interaction with the browser UI chrome: tab bar, new-tab button, back button, and address bar.

#### Properties
| Name | Type | Description |
|---|---|---|
| `browser` | `Browser` | Reference to the owning browser |
| `font` | `tkinter.Font` | Font for all chrome text (size 20) |
| `font_height` | `int` | Line height of the chrome font |
| `padding` | `int` | `5` px uniform padding |
| `tabbar_top` | `int` | `0` |
| `tabbar_bottom` | `int` | `font_height + 2 * padding` |
| `urlbar_top` | `int` | `tabbar_bottom` |
| `urlbar_bottom` | `int` | `urlbar_top + font_height + 2 * padding` |
| `bottom` | `int` | `urlbar_bottom` — total height of the chrome area |
| `newtab_rect` | `Rect` | Clickable area for the `+` new-tab button |
| `back_rect` | `Rect` | Clickable area for the `<` back button |
| `address_rect` | `Rect` | Clickable area for the address bar |
| `focus` | `str \| None` | `"address bar"` when address bar is active, else `None` |
| `address_bar` | `str` | Text typed into the address bar |

#### Methods
| Method | Description |
|---|---|
| `paint() -> list[DrawCommand]` | Returns the full display list for the chrome (background, lines, tab labels, back button, address bar with cursor) |
| `tab_rect(i) -> Rect` | Returns the bounding `Rect` for tab `i` in the tab bar |
| `click(x, y)` | Dispatches click to: new-tab button, back button, address bar, or a specific tab |
| `keypress(char) -> bool` | Appends `char` to `address_bar` if focused; returns `True` if consumed |
| `enter()` | Navigates the active tab to `URL(address_bar)` if address bar is focused |
| `blur()` | Clears `focus` |

---

### Browser

**Source:** `browser.py`

Top-level application class. Owns the window, canvas, tab list, and the Chrome UI. Routes user events to the active tab or chrome.

#### Properties
| Name | Type | Description |
|---|---|---|
| `window` | `tkinter.Tk` | The OS window |
| `canvas` | `tkinter.Canvas` | The drawing surface (800 × 600) |
| `tabs` | `list[Tab]` | All open tabs |
| `active_tab` | `Tab \| None` | The currently visible tab |
| `chrome` | `Chrome` | The browser UI chrome |
| `focus` | `str \| None` | `"content"` when page content has focus |

#### Event handlers
| Handler | Trigger | Action |
|---|---|---|
| `handle_down(e)` | `<Down>` arrow key | `active_tab.scrolldown()` + redraw |
| `handle_click(e)` | `<Button-1>` mouse click | Routes to `chrome.click()` or `active_tab.click()` based on y-coordinate |
| `handle_key(e)` | `<Key>` any printable key | Routes to `chrome.keypress()` or `active_tab.keypress()` |
| `handle_enter(e)` | `<Return>` key | `chrome.enter()` + redraw |

#### Methods
| Method | Description |
|---|---|
| `draw()` | Clears canvas, draws the active tab's display list offset by `chrome.bottom`, then draws chrome paint commands |
| `new_tab(url)` | Creates a new `Tab`, loads `url`, sets it as `active_tab`, appends to `tabs`, redraws |

#### Swift notes
- `tkinter.Tk` + `tkinter.Canvas` → `NSWindow` + a custom `NSView` subclass overriding `draw(_:)`.
- Key/mouse event bindings → `NSResponder` overrides (`keyDown`, `mouseDown`, `scrollWheel`).
- `canvas.delete("all")` + redraw pattern → call `setNeedsDisplay(_:)` to invalidate and trigger a redraw cycle.
- `tkinter.mainloop()` → `NSApplication.shared.run()`.

---

## Entity Dependency Graph

```
Browser
├── Chrome
│   ├── Rect
│   ├── DrawRect, DrawLine, DrawOutline, DrawText
│   └── URL
└── Tab
    ├── URL
    ├── HTMLParser
    │   ├── Text
    │   └── Element
    ├── CSSParser
    │   ├── TagSelector
    │   └── DescendantSelector
    ├── DocumentLayout
    │   └── BlockLayout
    │       ├── LineLayout
    │       │   ├── TextLayout  → DrawText
    │       │   └── InputLayout → DrawText, DrawRect, DrawLine
    │       └── DrawRect
    └── JSContext (dukpy → JavaScriptCore)
        ├── CSSParser
        └── HTMLParser
```

---

## Swift Port Quick-Reference

| Python / Library | Swift Native Replacement |
|---|---|
| `tkinter.Tk` | `NSApplication`, `NSWindow` |
| `tkinter.Canvas` | Custom `NSView` subclass + `draw(_:)` |
| `tkinter.font.Font` | `NSFont` |
| `font.measure(text)` | `(text as NSString).size(withAttributes:).width` |
| `font.metrics("ascent")` | `nsFont.ascender` |
| `font.metrics("descent")` | `abs(nsFont.descender)` |
| `font.metrics("linespace")` | `nsFont.ascender + abs(nsFont.descender) + nsFont.leading` |
| `canvas.create_text(...)` | `NSAttributedString.draw(at:)` |
| `canvas.create_rectangle(...)` | `NSBezierPath(rect:).fill()` / `.stroke()` |
| `canvas.create_line(...)` | `NSBezierPath().move(to:).line(to:).stroke()` |
| `socket` + `ssl` | `Network.NWConnection` or `Foundation.URLSession` |
| `dukpy.JSInterpreter` | `JavaScriptCore.JSContext` |
| `tkinter.mainloop()` | `NSApplication.shared.run()` |
| `urllib.parse.quote` | `String.addingPercentEncoding(withAllowedCharacters:)` |
