import dukpy

RUNTIME_JS = open("runtime.js").read()

class JSContext:
    def __init__(self):
        self.interp = dukpy.JSInterpreter()
        self.interp.export_function("log", print)
        self.interp.evaljs(RUNTIME_JS)

    def run(self, script, code):
        try:
            return self.interp.evaljs(code)
        except dukpy.JSRuntimeError as e:
            print("Script", script, "crashed", e)
