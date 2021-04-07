#from eternalevents import *
import eternalevents as ee
#from eternalevents import ebl_to_event, encounter_spawn_names
import sys
import json
import re
import time
import pprint
from multiprocessing import Pool
import multiprocessing as mp
from parsimonious.grammar import Grammar
from parsimonious.grammar import NodeVisitor
import chevron
from textwrap import dedent, indent

def str_to_class(classname):
    return getattr(ee, classname)

def get_event_args(classname):
    return [i for i in classname.__dict__.keys() if not i.startswith('__') and not i.startswith('args')]

entity_grammar = Grammar(r"""
    #DOCUMENT = VERSION_LINES? ENTITY*
    
    #VERSION_LINES = "Version" SPACE INTEGER SPACE "HierarchyVersion" SPACE INTEGER SPACE
    ENTITY        = "entity" LBRACE ENTITY_PROPS* RBRACE
    ENTITY_PROPS  = (ENTITYDEF_BLOCK / LAYERS_BLOCK / ASSIGNMENT)
    
    ENTITYDEF_BLOCK = "entityDef" SPACE VARNAME LBRACE ASSIGNMENT* RBRACE
    LAYERS_BLOCK    = "layers" LBRACE STRING RBRACE
    ASSIGNMENT      = VARIABLE EQUALS (OBJECT / LITERAL)
 
    OBJECT     = LBRACE ASSIGNMENT+ RBRACE
    LITERAL    = (NUMBER / STRING / NULL / BOOL) SEMICOLON
    
    VARIABLE = (INDEXED / VARNAME)
    INDEXED    = VARNAME "[" INTEGER "]"
 
    LBRACE    = SPACE? "{" SPACE?
    RBRACE    = SPACE? "}" SPACE?
    EQUALS    = SPACE? "=" SPACE?
    SEMICOLON = SPACE? ";" SPACE?
 
    VARNAME = ~r"\w+"
    STRING  = '"' ~r"[^\"]*" '"'
    NUMBER  = ~r"[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?"
    INTEGER = ~r"[-]?\d+"
    BOOL    = "true" / "false"
    NULL    = "NULL"
    SPACE   = ~r"\s+"
""")



ebl_grammar = Grammar(r"""
    DOCUMENT = (STATEMENTS)*
    STATEMENTS = SPACE? (EVENT / WAVE / WAITFORBLOCK / WAITFOR)
    
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
        
    LBRACE    = SPACE? "{" SPACE?
    RBRACE    = SPACE? "}" SPACE?
    LBRACKET  = SPACE? "[" SPACE?
    RBRACKET  = SPACE? "]" SPACE?
    LPARENTHESES  = SPACE? "(" SPACE?
    RPARENTHESES  = SPACE? ")" SPACE?
    LPARENCHAR = "("
    RPARENCHAR = ")"
    
    SPACE = ~r"\s+"
    STRING = ~r"[\w/]+"
    NUMBER = ~r"[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?"
    BOOL = "true" / "false"
""")

waitFor_keywords = {
    "all": "ENCOUNTER_LOGICAL_OP_AND",
    "any": "ENCOUNTER_LOGICAL_OP_OR"
}



class EntityVisitor(NodeVisitor):
    def parse(self, text):
        """ Initialize private fields before parsing """
        self.version = None
        self.hierarchy_version = None
        return super().parse(text)
 
    def visit_DOCUMENT(self, node, visited_children):
        _, entities = visited_children
        #print("")
        return entities
    
    def visit_VERSION_LINES(self, node, visited_children):
        _, _, version, _, _, _, hierarchy_version, _ = visited_children
        self.version = version
        self.hierarchy_version = hierarchy_version
        print(f"Version:{version}, HierarchyVersion:{hierarchy_version}")
 
    def visit_ENTITY(self, node, visited_children):
        nodename, _, props, _ = visited_children
        return dict(props)
 
    def visit_ENTITY_PROPS(self, node, visited_children):
        return visited_children[0]
 
    def visit_LAYERS_BLOCK(self, node, visited_children):
        nodename, _, string, _ = visited_children
        return (nodename.text, string)
    
    def visit_ENTITYDEF_BLOCK(self, node, visited_children):
        nodename, _, varname, _, assignments, _ = visited_children
        return (f"{nodename.text} {varname}", dict(assignments))
 
    def visit_ASSIGNMENT(self, node, visited_children):
        varname, _, value = visited_children
        return (varname[0], value[0])
 
    def visit_OBJECT(self, node, visited_children):
        _, assignments, _ = visited_children
        return dict(assignments)
 
    def visit_LITERAL(self, node, visited_children):
        literal, _ = visited_children
        return literal[0]
 
    def visit_INDEXED(self, node, visited_children):
        varname, _, index, _ = visited_children
        return f"{varname}[{index}]"
    
    def visit_VARNAME(self, node, visited_children):
        return str(node.text)
    
    def visit_STRING(self, node, visited_children):
        _, string, _ = visited_children
        return str(string.text)
    
    def visit_NUMBER(self, node, visited_children):
        return float(node.text)
    
    def visit_INTEGER(self, node, visited_children):
        return int(node.text)
    
    def visit_BOOL(self, node, visited_children):
        return node.text == "true"
 
    def visit_NULL(self, node, visited_children):
        return None
    
    def generic_visit(self, node, visited_children):
        return visited_children or node


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
    
    def visit_BOOL(self, node, visited_children):
        return node.text == "true"
    
    def generic_visit(self, node, visited_children):
        return visited_children or node


ev = EntityVisitor()
ev.grammar = entity_grammar

def strip_comments(string):
    pattern = r"//(.*)[\r\n]+"
    return re.sub(pattern, "", string)

def generate_entity_segments(filename):
    with open(filename) as fp:
        segments = re.split(r"^entity {", fp.read(), flags=re.MULTILINE)
    # skip first segment with version numbers in it, remove comments
    segment_count = 0
    for segment in segments[1:]:
        segment = strip_comments(segment)
        # handle encounters only for now
        if '''inherit = "target/spawn";''' in segment:
            segment_count += 1
            yield "entity {" + re.sub(r"//.*$", "", segment)
            
    print(f"{segment_count} targets found")

def convert_entities_file(filename):
    tic = time.time()
    data = []
    if __name__ == '__main__':
        print("Start processing")
        with Pool(processes=mp.cpu_count()) as pool:
            data = pool.map(ev.parse, generate_entity_segments(filename))
         
        print(f"Done processing in {time.time()-tic:.1f} seconds")
        with open('testoutput.json', 'w') as fp:
            json.dump(data, fp, indent = 4)
    return data


ebl = EBLVisitor()
ebl.grammar = ebl_grammar

# Splits EBL file into segments at <ENCOUNTER headers>
def generate_EBL_segments(filename):
    with open(filename) as fp:
        segments = re.split(r"^<ENCOUNTER", fp.read(), flags=re.MULTILINE)
    # skip first segment with version numbers in it, remove comments
    for segment in segments[0:]:
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
                "event":"waitMultipleConditions",
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

def compile_EBL(filename):    
    tic = time.time()
    encounters = map(ebl.parse, generate_EBL_segments(filename))
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
