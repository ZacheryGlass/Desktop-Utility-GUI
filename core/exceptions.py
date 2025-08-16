class ScriptError(Exception):
    pass

class ScriptLoadError(ScriptError):
    pass

class ScriptExecutionError(ScriptError):
    pass

class ScriptValidationError(ScriptError):
    pass

class ScriptTimeoutError(ScriptError):
    pass