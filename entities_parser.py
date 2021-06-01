import re
from parsimonious.grammar import Grammar
from parsimonious.grammar import NodeVisitor
from textwrap import indent


class EntitiesSyntaxError(Exception):
    pass


entity_grammar = Grammar(
    r"""
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
"""
)


class EntityVisitor(NodeVisitor):
    def parse(self, text):
        """Initialize private fields before parsing"""
        self.version = None
        self.hierarchy_version = None
        return super().parse(text)

    def visit_DOCUMENT(self, node, visited_children):
        _, entities = visited_children
        # print("")
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
        return nodename.text, {"__layername__": string}

    def visit_ENTITYDEF_BLOCK(self, node, visited_children):
        nodename, _, varname, _, assignments, _ = visited_children
        return f"{nodename.text} {varname}", dict(assignments)

    def visit_ASSIGNMENT(self, node, visited_children):
        varname, _, value = visited_children
        return varname[0], value[0]

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
            return int(float(node.text))
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
        if not clsname or f"""class = "{clsname}";""" in segment:
            segment_count += 1
            yield "entity {" + re.sub(r"//.*$", "", segment)
    if clsname:
        print(f"{segment_count} instances of {clsname} found")


def parse_entities(filename, class_filter=""):
    # with Pool(processes=mp.cpu_count()) as pool:
    #   data = pool.map(ev.parse, generate_entity_segments(filename, class_filter))
    data = map(ev.parse, generate_entity_segments(filename, class_filter))
    return data


def generate_entity(parsed_entity: dict, depth=0) -> str:
    """
    Converts a parsed event back to .entities
    shoutout to Chrispy
    :param parsed_entity:
    :param depth:
    :return:
    """
    s = ""
    NO_EQUALS = ("entityDef", "layers")
    if depth == 0:
        s += "entity {\n\t"
    item_index = 0
    do_item_numbering = False
    for key, val in parsed_entity.items():
        if do_item_numbering or key == "num":
            do_item_numbering = True
            if key == "num":
                val = len(parsed_entity) - 1
            else:
                key = f"item[{item_index}]"
                item_index += 1
            if item_index >= len(parsed_entity) - 1:
                item_index = 0
                do_item_numbering = False

        if isinstance(val, dict):
            s += key
            if not key.startswith(NO_EQUALS):
                s += " ="
            s += " {\n" + generate_entity(val, depth + 1) + "}\n"
        else:
            multiline = False
            if isinstance(val, bool):
                val = "true" if val else "false"
            elif isinstance(val, str):
                # if string is multiline, 'unpack' the string
                multiline = "\n" in val
                if not multiline:
                    val = f'"{val}"'
            s += f"{key} = {str(val)}"
            if not multiline:
                s += ";\n"

    return indent(s, "\t") if depth > 0 else s + "}\n"


def minify(filename):
    with open(filename, "r") as fp:
        s = fp.read()
    result = s.replace("\t", "").replace("\n", "")
    with open(filename, "w") as fp:
        s = fp.write(result)


def unminify(filename):
    with open(filename, "r") as fp:
        s = fp.read()

    # add newlines
    s = s.replace("{", "{\n")
    s = s.replace("}", "}\n")
    s = s.replace(";", ";\n")

    # add tabs (state machine moment)
    result = ""
    indent_level = 0
    for line in s.splitlines():
        if "}" in line:
            indent_level -= 1
        result += indent_level * "\t" + line + "\n"
        if "{" in line:
            indent_level += 1
    with open(filename, "w") as fp:
        fp.write(result)


# quick-n-dirty punctuation check
# TODO: make less bad
def verify_file(filename):
    print("Checking file...")
    error_found = False
    depth = 0
    layers_line = False
    last_entity_line = 0
    with open(filename) as fp:
        for i, line in enumerate(fp.readlines()):
            if "{" in line:
                depth += line.count("{")
            if "}" in line:
                depth -= 1
            if line.strip() == "entity {":
                if depth != 1:
                    print(f"Unmatched braces in entity starting at line {i+1}")
                    return True
                last_entity_line = i
            if layers_line:
                layers_line = False
                continue
            if i < 2 or not line.strip() or line.lstrip().startswith("//"):
                continue
            if line.strip().startswith("layers"):
                layers_line = True
            if not line.rstrip().endswith(("{", "}", ";")):
                print(f"Missing punctuation on line {i+1}")
                print(f"line {i+1}: {line}")
                error_found = True
    if depth != 0:
        print(f"Unmatched braces detected! Depth = {depth}")
        return True
    if not error_found:
        print("No problems found!")
    return error_found


def list_checkpoints(filename):
    cps = []
    print("\nCHECKPOINTS:")
    with open(filename) as fp:
        for line in fp.readlines():
            if "playerSpawnSpot = " in line:
                name = (
                    line.replace("playerSpawnSpot = ", "").strip().strip(";").strip('"')
                )
                cps += [name]
    for name in cps:
        print(name)
    print("")
