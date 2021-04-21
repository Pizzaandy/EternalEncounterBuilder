import eternalevents
import json
import re
import time
from multiprocessing import Pool
import multiprocessing as mp
from parsimonious.grammar import Grammar
from parsimonious.grammar import NodeVisitor
from textwrap import indent
import subprocess
from pathlib import Path

def is_binary(filename):
    try:
        with open(filename, 'tr') as check_file:  # try to open file in text mode
            check_file.read()
            return False
    except:  # if fail, then file is non-text (binary)
        return True


def decompress(input_path, output_path, exe="idFileDeCompressor.exe"):
    if not Path(exe).exists():
        print("ERROR: idFileDeCompressor not in folder!")
        return False
    if Path(input_path).suffix != ".entities":
        print("ERROR: Input path is not an .entities file!")
        return False
    if not is_binary(input_path):
        print("File is already decompressed!")
        return False
    p = subprocess.run(['idFileDeCompressor.exe',"-d", input_path, output_path])
    if p.stderr:
        print(f"STINKY: {p.stderr}")
        return False
    print(f"Decompressed {Path(input_path).name} to {Path(output_path).name}")
    return True

def compress(input_path, output_path, exe="idFileDeCompressor.exe"):
    if not Path(exe).exists():
        print("ERROR: idFileDeCompressor not in folder!")
        return None
    if Path(input_path).suffix != ".entities":
        print("ERROR: Input path is not an .entities file!")
        return False
    if is_binary(input_path):
        print("File is already compressed!")
        return False
    p = subprocess.run(['idFileDeCompressor.exe',"-c", input_path, output_path])
    if p.stderr:
        print(f"ERROR: {p.stderr}")
        return False
    print(f"Compressed {Path(input_path).name} to {Path(output_path).name}")
    return True


entity_grammar = Grammar(r"""
    #DOCUMENT = VERSION_LINES? ENTITY*

    #VERSION_LINES = "Version" SPACE INTEGER SPACE "HierarchyVersion" SPACE INTEGER SPACE
    ENTITY        = "entity" LBRACE ENTITY_PROPS* RBRACE
    ENTITY_PROPS  = (ENTITYDEF_BLOCK / LAYERS_BLOCK / ASSIGNMENT)

    ENTITYDEF_BLOCK = "entityDef" SPACE VARNAME LBRACE ASSIGNMENT* RBRACE
    LAYERS_BLOCK    = "layers" LBRACE STRING RBRACE
    ASSIGNMENT      = VARIABLE EQUALS (OBJECT / LITERAL)

    OBJECT     = LBRACE ASSIGNMENT+ RBRACE
    LITERAL    = (NUMBER / INTEGER / STRING / NULL / BOOL) SEMICOLON

    VARIABLE   = (INDEXED / VARNAME)
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
        return (nodename.text, {"__layername__":string})

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
        if float(node.text).is_integer():
            return int(node.text)
        else:
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


def strip_comments(string):
    pattern = r"//(.*)[\r\n]+"
    return re.sub(pattern, "", string)


def generate_entity_segments(filename, clsname="", version_numbers=False):
    with open(filename) as fp:
        segments = re.split(r"^entity {", fp.read(), flags=re.MULTILINE)
    # skip first segment with version numbers in it, remove comments
    segment_count = 0
    start_index = 0 if version_numbers else 1
    for i, segment in enumerate(segments[start_index:]):
        segment = strip_comments(segment)
        # filter class name
        if i == 0 and version_numbers:
            yield segment
            continue
        if not clsname or f'''class = "{clsname}";''' in segment:
            segment_count += 1
            yield "entity {" + re.sub(r"//.*$", "", segment)
    if not clsname:
        clsname = "entity"
    print(f"{segment_count} instances of {clsname} found")


def parse_entities(filename, class_filter):
    tic = time.time()
    print("Start processing")
    with Pool(processes=mp.cpu_count()) as pool:
        data = pool.map(ev.parse, generate_entity_segments(filename, class_filter))
    print(f"Done processing in {time.time()-tic:.1f} seconds")
    return data


# TODO: make Chrispy less mad
# I have hit a new low
def generate_entity(entity_dict, unpack=None):
    no_equals_list = ['entityDef ', 'layers']
    entity_json = json.dumps(entity_dict, indent=4).replace(",", "")
    res = "entity "
    for line in entity_json.splitlines():
        line = line.replace(4*" ", "\t")
        tabs = len(line) - len(line.lstrip("\t"))
        if not line.lstrip().startswith('"entityDef '):
            line = line[1:] if line.startswith("\t") else line
        if ": " in line:
            var, other = tuple(line.split(": "))
            var = var.replace('"', '')
            if unpack and var.strip().startswith(unpack):
                # print("unpacked the string")
                other = bytes(other, "utf-8").decode("unicode_escape").strip('"')
                other = "{\n" + indent(other, tabs*"\t") + (tabs-1)*"\t" + "}"
            elif not "{" in line:
                other += ";"
            if var.lstrip().startswith(tuple(no_equals_list)):
                line = var + " " + other
                #print(var)
            else:
                line = var + " = " + other
            if line.lstrip().startswith("__layername__ = "):
                line = line.replace(";","").replace("__layername__ = ", "")
        res += line + "\n"
    return res

fp = "C:\_DEV\EternalEncounterDesigner\Test Entities\e5m2_earth.entities"

if __name__ == "__main__":
    entities = parse_entities(fp, "idEncounterManager")
    with open('testoutput.json', 'w') as fp:
        json.dump(entities, fp, indent=4)
    my_entity = generate_entity(entities[1])
    with open("test_generated_entity.txt", "w") as fp:
        fp.write(my_entity)
    print("success!")