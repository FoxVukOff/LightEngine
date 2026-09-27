class ScriptError(Exception):
    pass


def syntax_error(file, line, msg):
    return ScriptError('%s:%d: %s' % (file, line, msg))
