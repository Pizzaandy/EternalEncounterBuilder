import re
import compiler_constants as cc
from parsimonious.grammar import Grammar
from parsimonious.grammar import NodeVisitor


class EblTypeError(Exception):
    pass


grammar = Grammar(
    r"""
    DOCUMENT = (STATEMENTS)*
    STATEMENTS = SPACE? (ENTITYEDIT / EVENT / WAVE / ASSIGNMENT / WAITFORBLOCK / WAITFOR / DECORATOR)

    ASSIGNMENT = STRING EQUALS (NUMBER / MULTISTRING / ANYSTRING) SPACE?
    ENTITYEDIT = PATHSTRING "." EVENT

    WAVE = "Wave" SPACE (STRING / NUMBER) LBRACE STATEMENTS* RBRACE
    PARAM_LIST = PARAM_TUPLE+
    PARAM_TUPLE = LPARENTHESES PARAM_LINE RPARENTHESES SPACE? ","? SPACE?
    PARAM_LINE = PARAM*
    PARAM = NULLPARAM / REALPARAM / MULTISTRING

    REALPARAM = SPACE? (NUMBER / STRING / MULTISTRING / STRINGLITERAL) SPACE? ("," / &RPARENTHESES)
    NULLPARAM = SPACE? ("," / &RPARENCHAR)
    MULTISTRING = SPACE? (SPACE_NO_NEWLINE? ANYSTRING)+ SPACE_NO_NEWLINE? ("," / &RPARENTHESES / "\n" / &";")
    ANYSTRING = (STRING / STRINGLITERAL)

    DECORATOR = "@" SPACE? MULTISTRING SPACE?
    EVENT = DECORATOR? STRING SPACE? ":"? SPACE? PARAM_LIST

    WAITFORBLOCK = ("waitFor"/"waitfor") SPACE? STRING? LBRACE (EVENT / ASSIGNMENT)* RBRACE
    WAITFOR = ("waitFor"/"waitfor") SPACE? (EVENT / TIMER)
    TIMER = (NUMBER) SPACE? "sec"

    LBRACE        = SPACE? "{" SPACE?
    RBRACE        = SPACE? "}" SPACE?
    LBRACKET      = SPACE? "[" SPACE?
    RBRACKET      = SPACE? "]" SPACE?
    LPARENTHESES  = SPACE? "(" SPACE?
    RPARENTHESES  = SPACE? ")" SPACE?
    LPARENCHAR    = "("
    RPARENCHAR    = ")"
    EQUALS        = SPACE? "=" SPACE?

    SPACE = ~r"[\s;]+"
    SPACE_NO_NEWLINE = ~r"[\t ]+"
    STRING = ~r'[\w/#+-.]+'
    PATHSTRING = ~r'[\w/#+\[\]]+'
    STRINGLITERAL = ~r'"[\t\n\w/#+-. ]*"'
    NUMBER = ~r"[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?"
"""
)


class NodeVisitor(NodeVisitor):
    def visit_DOCUMENT(self, node, visited_children):
        output = []
        event_list = visited_children
        for event in event_list:
            output.append(event)
        return output

    def visit_STATEMENTS(self, node, visited_children):
        _, statement = visited_children
        return statement[0]

    def visit_ASSIGNMENT(self, node, visited_children):
        varname, _, value, _ = visited_children
        return {"variable": varname, "value": value[0]}

    def visit_ENTITYEDIT(self, node, visited_children):
        obj, _, event = visited_children
        return {"object": obj, "function": event["event"], "value": event["args"]}

    def visit_WAVE(self, node, visited_children):
        _, _, varname, _, statements, _ = visited_children
        if not isinstance(statements, list):
            return []
        return statements

    def visit_PARAM(self, node, visited_children):
        value = visited_children
        # print(value[0])
        return value[0]

    def visit_NULLPARAM(self, node, visited_children):
        return None

    def visit_REALPARAM(self, node, visited_children):
        _, value, _, _ = visited_children
        return value[0]

    def visit_PARAM_LINE(self, node, visited_children):
        params = visited_children
        # print("param_line:" + str(params))
        return params

    def visit_PARAM_TUPLE(self, node, visited_children):
        _, param_line, _, _, _, _ = visited_children
        # print("param_tuple: " + str(param_line))
        return param_line

    def visit_PARAM_LIST(self, node, visited_children):
        param_tuples = visited_children
        # print("param_list: " + str(param_tuples))
        return param_tuples

    def visit_DECORATOR(self, node, visited_children):
        _, _, name, _ = visited_children
        return name

    def visit_EVENT(self, node, visited_children):
        decorator, event_name, _, _, _, params = visited_children
        if not isinstance(params, list):
            params = []
            print("This should never happen")
        decorator = decorator[0] if isinstance(decorator, list) else ""
        if decorator:
            print(f"decorator name is '{decorator}'")
        return {"event": str(event_name), "args": params, "decorator": decorator}

    def visit_WAITFOR(self, node, visited_children):
        _, _, condition = visited_children
        return {"event": "waitFor", "args": condition[0]}

    def visit_WAITFORBLOCK(self, node, visited_children):
        _, _, keyword, _, conditions, _ = visited_children
        if not isinstance(conditions, list):
            print("This should never happen")
            conditions = []
        keyword = keyword[0] if isinstance(keyword, list) else "all"
        return {"event": "waitForBlock", "args": conditions, "keyword": keyword}

    # disableAIHighlight = false by default
    def visit_TIMER(self, node, visited_children):
        duration, _, _ = visited_children
        return {"event": "wait", "args": [duration, "false"]}

    def visit_ANYSTRING(self, node, visited_children):
        string = visited_children
        return string[0]

    def visit_STRING(self, node, visited_children):
        return str(node.text)

    def visit_PATHSTRING(self, node, visited_children):
        return str(node.text)

    def visit_STRINGLITERAL(self, node, visited_children):
        expr = str(node.text).replace('"', "").replace(" ", "$^")
        if "$" not in expr:
            expr = expr + "$"
        # print(f"expr is {expr}")
        # print(expr)
        return expr

    def visit_MULTISTRING(self, node, visited_children):
        _, string, _, _ = visited_children
        output_str = ""
        for i, item in enumerate(string):
            output_str += string[i][1] + " "
        if "^" in output_str:
            print(f"multistring with space char: '{output_str.strip()}'")
        return output_str.strip()

    def visit_NUMBER(self, node, visited_children):
        if (
            float(node.text).is_integer()
            and "." not in node.text
            and "+" not in node.text
        ):
            return int(node.text)
        else:
            return float(node.text)

    def generic_visit(self, node, visited_children):
        return visited_children or node


def ebl_syntax_check(filename):
    pass
