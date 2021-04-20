#from eternalevents import *
import eternalevents as ee
#from eternalevents import ebl_to_event, encounter_spawn_names
import json
import re
import time
from multiprocessing import Pool
import multiprocessing as mp
from parsimonious.grammar import Grammar
from parsimonious.grammar import NodeVisitor
import subprocess
from pathlib import Path

def decompress(input_path, output_path, exe="idFileDeCompressor.exe"):
    if not Path(exe).exists():
        print("ERROR: idFileDeCompressor not in folder!")
        return False
    if Path(input_path).suffix != ".entities":
        print("ERROR: Input path is not an .entities file!")
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
    p = subprocess.run(['idFileDeCompressor.exe',"-c", input_path, output_path])
    if p.stderr:
        print(f"ERROR: {p.stderr}")
        return False
    print(f"Compressed {Path(input_path).name} to {Path(output_path).name}")
    return True


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


def strip_comments(string):
    pattern = r"//(.*)[\r\n]+"
    return re.sub(pattern, "", string)


def generate_entity_segments(filename, clsname="idEncounterManager"):
    with open(filename) as fp:
        segments = re.split(r"^entity {", fp.read(), flags=re.MULTILINE)
    # skip first segment with version numbers in it, remove comments
    segment_count = 0
    for segment in segments[1:]:
        segment = strip_comments(segment)
        # handle encounters only for now
        if f'''class = "{clsname}";''' in segment:
            segment_count += 1
            yield "entity {" + re.sub(r"//.*$", "", segment)

    print(f"{segment_count} instances of {clsname} found!")


def parse_entities(filename, class_filter):
    tic = time.time()
    data = []
    if __name__ == '__main__':
        print("Start processing")
        with Pool(processes=mp.cpu_count()) as pool:
            data = pool.map(ev.parse, generate_entity_segments(filename, class_filter))

        print(f"Done processing in {time.time()-tic:.1f} seconds")
        with open('testoutput.json', 'w') as fp:
            json.dump(data, fp, indent=4)
    return data

fp = 'randomizer_example.txt'
segments = generate_entity_segments(fp, "idAI2")
output_str = ""
names_str = ""
filter_list = ["masterlevel", "_ai_", "cinematic"]
entity_count = 0
for seg in segments:
    name = ""
    skip_segment = False
    for line in seg.splitlines():
        if "entityDef" in line:
            name = line.replace("{", "").replace("entityDef","").strip()
            if name.startswith(tuple(filter_list)):
                skip_segment = True
            new_name = "custom" + name.rstrip("0123456789_").lstrip("gameplay").lstrip("game")
            seg = seg.replace(name, new_name, 1)
            break
    if skip_segment:
        continue
    if name == "":
        print("No entityDef found!")
    names_str += "// " + new_name + "\n"
    output_str += seg + "\n"
    entity_count += 1

output_str = f"// Automatically added {entity_count} idAI2 entities from the base game:\n\n" + names_str + "\n" + output_str
output_file = open("idAI2_base.txt", "w")
output_file.write(output_str)
output_file.close()

print(names_str)

# testing woo
fp1 = r'C:\_DEV\EternalEncounterDesigner\Test Entities\e3m2_hell.entities'
fp2 = r'C:\_DEV\EternalEncounterDesigner\Test Entities\funny_test.entities'
fp3 = r'C:\_DEV\EternalEncounterDesigner\Test Entities\test.entities'

#decompress(fp2, fp3)
