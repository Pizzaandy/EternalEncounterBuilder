from eternalevents import *
import json
import re
import time
import pprint
from multiprocessing import Pool
import multiprocessing as mp
from parsimonious.grammar import Grammar
from parsimonious.grammar import NodeVisitor

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


ev = EntityVisitor()
ev.grammar = entity_grammar

def generate_segments(filename):
    with open(filename) as fp:
        segments = re.split(r"^entity {", fp.read(), flags=re.MULTILINE)
    # skip first segment with version numbers in it, remove comments
    for segment in segments[1:]:
        # handle encounters only for now
        if "idEncounterManager" in segment:
            yield "entity {" + re.sub(r"//.*$", "", segment)
 
def convert_entities_file(filename):
    tic = time.time()
    if __name__ == '__main__':
        print("Start processing")
        with Pool(processes=mp.cpu_count()) as pool:
            data = pool.map(ev.parse, generate_segments(filename))
    print(f"Done processing in {time.time()-tic:.1f} seconds")
    return data


#convert_entities_file("example_entities.txt")