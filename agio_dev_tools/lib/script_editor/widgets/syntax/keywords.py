"""Python keywords and syntax definitions for syntax highlighting."""

SYNTAX = {
    "extension": ["py", "pyw"],
    "comment": ["#"],
    "string": ['"', "'"],
    "operators": [
        "=",
        "!=", "<", ">",
        "\\+", "-", "\\*", "/", "%",
        "\\^", "\\|", "&",
    ],
    "keywords": [
        "and", "assert", "break", "continue", "del",
        "elif", "else", "except", "finally", "for",
        "from", "global", "if", "import", "in",
        "is", "lambda", "not", "or", "pass",
        "raise", "return", "try", "while", "yield",
        "None", "True", "False",
        "with", "as",
    ],
    "definition": ["class", "def", "async", "await"],
    "boolean": ["True", "False"],
    "extras": [
        "abs", "all", "any", "basestring", "bin", "bool", "bytearray",
        "callable", "chr", "classmethod", "cmp", "compile", "complex",
        "delattr", "dict", "dir", "divmod", "enumerate", "eval", "exec",
        "execfile", "file", "filter", "float", "format", "frozenset",
        "getattr", "globals", "hasattr", "hash", "help", "hex", "id",
        "input", "int", "isinstance", "issubclass", "iter", "len", "list",
        "locals", "long", "map", "max", "memoryview", "min", "next",
        "object", "oct", "open", "ord", "pow", "property", "range",
        "raw_input", "reduce", "reload", "repr", "reversed", "round",
        "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum",
        "super", "tuple", "type", "unichr", "unicode", "vars", "xrange",
        "zip", "apply", "buffer", "coerce", "intern",
    ],
    "braces": ['\\{', '\\}', '\\(', '\\)', '\\[', '\\]'],
}
