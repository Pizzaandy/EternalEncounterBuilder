from parsimonious.grammar import Grammar
from parsimonious.grammar import NodeVisitor

grammar = Grammar(r"""
    DOCUMENT = (STATEMENTS)*
    STATEMENTS = SPACE? (EVENT / WAVE / ASSIGNMENT / WAITFORBLOCK / WAITFOR)
    
    ASSIGNMENT = STRING EQUALS (NUMBER / STRING) SPACE?
    
    WAVE = "Wave" SPACE (STRING / NUMBER) LBRACE STATEMENTS* RBRACE
    PARAM_LIST = LBRACKET PARAM_TUPLE* RBRACKET
    PARAM_TUPLE = LPARENTHESES PARAM_LINE RPARENTHESES SPACE? ","? SPACE?
    PARAM_LINE = PARAM+
    PARAM = NULLPARAM / REALPARAM / MULTISTRING
    
    REALPARAM = SPACE? (NUMBER / STRING / MULTISTRING) SPACE? ("," / &RPARENTHESES)
    NULLPARAM = SPACE? ("," / &RPARENCHAR)
    MULTISTRING = (SPACE? STRING)+ SPACE? ("," / &RPARENTHESES)
    
    EVENT = STRING SPACE? LPARENTHESES (PARAM_LIST / PARAM_LINE)? RPARENTHESES
    
    WAITFORBLOCK = "waitFor" SPACE? STRING? LBRACE (EVENT / ASSIGNMENT)* RBRACE
    WAITFOR = "waitFor" SPACE? (EVENT / TIMER) 
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
    
    SPACE = ~r"\s+"
    STRING = ~r"[\w/]+"
    NUMBER = ~r"[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?"
""")

class NodeVisitor(NodeVisitor):
    def visit_DOCUMENT(self, node, visited_children):
        output = []
        event_list = visited_children
        for event in event_list:
            output.append(event)
        return output
    
    def visit_STATEMENTS(self, node, visited_children):
        _, statement = visited_children
        #print("statement: " + str(statement[0]))
        return statement[0]
    
    # ASSIGNMENT = STRING EQUALS (NUMBER / STRING)
    def visit_ASSIGNMENT(self, node, visited_children):
        varname, _, value, _ = visited_children
        return {"variable": varname, "value": value[0]}
    
    def visit_WAVE(self, node, visited_children):
        _, _, varname, _, statements, _ = visited_children
        if not isinstance(statements, list):
            return []
        return statements
    
    def visit_PARAM(self, node, visited_children):
        value = visited_children
        #print(value[0])
        return value[0]
    
    def visit_NULLPARAM(self, node, visited_children):
        return None
    
    def visit_REALPARAM(self, node, visited_children):
        _, value, _, _ = visited_children
        #print(value[0])
        return value[0]
    
    def visit_PARAM_LINE(self, node, visited_children):
        params = visited_children
        #print("param_line:" + str(params))
        return params
    
    def visit_PARAM_TUPLE(self, node, visited_children):
        _, param_line, _, _, _, _ = visited_children
        #print("param_tuple: " + str(param_line))
        return param_line
    
    def visit_PARAM_LIST(self, node, visited_children):
        _, param_tuples, _ = visited_children
        #print("param_list: " + str(param_tuples))
        return param_tuples
    
    def visit_EVENT(self, node, visited_children):
        event_name, _, _, params, _ = visited_children
        #print(params[0])
        if not isinstance(params, list):
            return {"event": str(event_name), "args": []}
        #params.insert(0, "EVENT: " + str(event_name))
        #print("event: " + str(params[0][0]))
        return {"event": str(event_name), "args": params[0][0]}
    
    def visit_WAITFOR(self, node, visited_children):
        _, _, condition = visited_children
        #print("waitFor parsed")
        return {"event": "waitFor", "args": condition[0]}
    
    def visit_WAITFORBLOCK(self, node, visited_children):
        _, _, keyword, _, conditions, _ = visited_children
        if not isinstance(conditions, list):
            return {"event": "waitForBlock", "args": []}
        keyword = keyword if isinstance(keyword, str) else "all"
        #print("waitForBlock parsed")
        return {"event": "waitForBlock", "args": conditions, "keyword": keyword}
    
    def visit_TIMER(self, node, visited_children):
        duration, _, _ = visited_children
        return {"event": "wait", "args": [duration, "false"]}
    
    def visit_STRING(self, node, visited_children):
        return str(node.text)
    
    def visit_MULTISTRING(self, node, visited_children):
        string, _, _ = visited_children
        output_str = ""
        for i, item in enumerate(string):
            output_str += string[i][1] + " "
        #print(output_str)
        return output_str.strip()
    
    def visit_NUMBER(self, node, visited_children):
        if float(node.text).is_integer() and not "." in (node.text):
            return int(node.text)
        else:
            return float(node.text)
    
    def generic_visit(self, node, visited_children):
        return visited_children or node