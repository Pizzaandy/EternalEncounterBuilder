import eternalevents as ee
from parsimonious.grammar import Grammar
from parsimonious.grammar import NodeVisitor
#import chevron
from textwrap import dedent, indent
import re
import time

def str_to_class(classname):
    return getattr(ee, classname)

def get_event_args(classname):
    return [i for i in classname.__dict__.keys() if not i.startswith('__') and not i.startswith('args')]

ebl_grammar = Grammar(r"""
    DOCUMENT = (STATEMENTS)*
    STATEMENTS = SPACE? (EVENT / WAVE / ASSIGNMENT / WAITFORBLOCK / WAITFOR)
    
    ASSIGNMENT = STRING EQUALS (NUMBER / STRING)
    
    WAVE = "Wave" SPACE (STRING / NUMBER) LBRACE STATEMENTS* RBRACE
    PARAM_LIST = LBRACKET PARAM_TUPLE* RBRACKET
    PARAM_TUPLE = LPARENTHESES PARAM_LINE RPARENTHESES SPACE? ","? SPACE?
    PARAM_LINE = PARAM+
    PARAM = NULLPARAM / REALPARAM / MULTISTRING
    
    REALPARAM = SPACE? (NUMBER / STRING / MULTISTRING) SPACE? ("," / &RPARENTHESES)
    NULLPARAM = SPACE? ("," / &RPARENCHAR)
    MULTISTRING = (SPACE? STRING)+ SPACE? ("," / &RPARENTHESES)
    
    EVENT = STRING SPACE? LPARENTHESES (PARAM_LIST / PARAM_LINE)? RPARENTHESES
    
    WAITFORBLOCK = "waitFor" SPACE? STRING? LBRACE (EVENT)* RBRACE
    WAITFOR = "waitFor" SPACE? (EVENT / TIMER) 
    TIMER = NUMBER SPACE? "sec" 
        
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

waitFor_keywords = {
    "all": "ENCOUNTER_LOGICAL_OP_AND",
    "any": "ENCOUNTER_LOGICAL_OP_OR"
}

class EBLVisitor(NodeVisitor):
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
        print("waitFor parsed")
        return {"event": "waitFor", "args": condition[0]}
    
    def visit_WAITFORBLOCK(self, node, visited_children):
        _, _, keyword, _, conditions, _ = visited_children
        if not isinstance(conditions, list):
            return {"event": "waitForBlock", "args": []}
        keyword = keyword if isinstance(keyword,str) else "all"
        print("waitForBlock parsed")
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
        print(output_str)
        return output_str
    
    def visit_NUMBER(self, node, visited_children):
        if float(node.text).is_integer() and not "." in (node.text):
            return int(node.text)
        else:
            return float(node.text)
    
    #def visit_BOOL(self, node, visited_children):
        #return node.text == "true"
    
    def generic_visit(self, node, visited_children):
        return visited_children or node

def strip_comments(string):
    pattern = r"//(.*)[\r\n]+"
    return re.sub(pattern, "", string)


ebl = EBLVisitor()
ebl.grammar = ebl_grammar

# Splits EBL file into segments at REPLACE ENCOUNTER headers
def generate_EBL_segments(filename, format_file = True):
    with open(filename) as fp:
        segments = re.split(r"^REPLACE ENCOUNTER", fp.read(), flags=re.MULTILINE)
    start_index = 0
    if segments[0].startswith("SETTINGS"):
        start_index = 1
        format_entities_file(filename, segments[0])
    for segment in segments[start_index:]:
        segment = "\n".join(segment.split("\n")[1:])
        yield strip_comments(segment)

# Adds "" in place of blank arguments, handles macros, and fills in optional arguments
def format_args(args, arg_count):
    for i, arg in enumerate(args):
        if arg in ee.encounter_spawn_names:
            args[i] = "ENCOUNTER_SPAWN_" + arg
        if arg is None:
            args[i] = ""
    while len(args) < arg_count:
        args += [""]
    return args

# Consumes a parsed EBL file and generate a list of EternalEvents 
def create_events(data):
    if isinstance(data, list):
        output = []
        for item in data:
            output += create_events(item)
        return output
                
    if isinstance(data, dict):
        if data["event"] == "waitForBlock":
            print("waitForBlock found!")
            waitevent =  {
                "event":"waitMulitpleConditions",
                "args":[len(data["args"]), waitFor_keywords[data["keyword"]], "false"]
            }
            return create_events([waitevent] + data["args"])
        
        if data["event"] == "waitFor":
            #print(create_events(data["args"]))
            print("waitFor found!")
            return create_events(data["args"])
        
        if data["event"] in ee.ebl_to_event:
            cls_name, arg_count = ee.ebl_to_event[data["event"]]
            event_cls = str_to_class(cls_name)
        else:
            print(f'''ERROR: undefined event {data["event"]}!''')
        
        args_list = data["args"]

        # Assume nested argument list means parameter tuple
        if any(isinstance(i, list) for i in args_list):
            output = []
            for args in args_list:
                args = format_args(args, arg_count)
                output += [event_cls(*args)]
            return output
        else:
            args_list = format_args(args_list, arg_count)
            return [event_cls(*args_list)]
    return data

def format_targets(filename, do_all):
    if do_all:
        print("FORMATTING ALL TARGETS")
    else:
        print("FORMATTING MODIFIED TARGETS ONLY")
    
setting_to_func = {
    "formatModifiedSpawnTargets": (format_targets, [False]),
    "formatAllSpawnTargets": (format_targets, [True])
}

def format_entities_file(filename, settings):
    for line in settings.splitlines():
        print(line)
        if line in setting_to_func:
            func, args = setting_to_func[line]
            func(filename, *args)

def compile_EBL(filename):    
    tic = time.time()
    segments = generate_EBL_segments(filename, format_file = True)
    encounters = map(ebl.parse, segments)
    output_file = open("test_encounter.txt", "w")
    for encounter in list(encounters):
        output_str = ""
        item_index = 0
        events = create_events(encounter)
        if events is None:
            continue
        for event in events:
            output_str += f"item[{item_index}]" + " = {\n" + indent(str(event),"\t") + "}\n"
            item_index += 1
        output_file.write(output_str)
    output_file.close()
    print(f"Done compiling in {time.time()-tic:.1f} seconds")
   
compile_EBL("test_EBL_2.txt")