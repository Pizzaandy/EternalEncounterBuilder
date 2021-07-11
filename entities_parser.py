import re
from parsimonious.grammar import Grammar
from parsimonious.grammar import NodeVisitor
from textwrap import indent
import multiprocessing as mp


class EntitiesSyntaxError(Exception):
    pass


entity_grammar = Grammar(
    r"""
    #DOCUMENT = VERSION_LINES? ENTITY*

    #VERSION_LINES = "Version" SPACE INTEGER SPACE "HierarchyVersion" SPACE INTEGER SPACE
    ENTITY        = "entity" LBRACE ENTITY_PROPS* RBRACE
    ENTITY_PROPS  = (ENTITYDEF_BLOCK / LAYERS_BLOCK / ASSIGNMENT)

    ENTITYDEF_BLOCK = "entityDef" SPACE VARNAME LBRACE ASSIGNMENT* RBRACE
    LAYERS_BLOCK    = "layers" LBRACE LAYERS_STRING RBRACE
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
    LAYERS_STRING = ~r'[\s\w/"]+'
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
        _, _, strings, _ = visited_children
        # print(f"strings is {strings}")
        lines = strings.splitlines()
        lines = [
            line.replace("\t", "").replace(" ", "") for line in lines if line.strip()
        ]
        return "layers", {f"__layername_{idx}__": s for idx, s in enumerate(lines)}

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

    def visit_LAYERS_STRING(self, node, visited_children):
        # print(str(node.text))
        return str(node.text)

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


LINE_PATTERN = re.compile(r"//(.*)(?=[\r\n]+)")


def strip_comments(s):
    s += "\n"
    return re.sub(LINE_PATTERN, "", s)


ENTITY_SPLIT_PATTERN = re.compile(r"^entity {", flags=re.MULTILINE)


def generate_entity_segments(filename, class_filter="", version_numbers=False):
    with open(filename) as fp:
        segments = re.split(ENTITY_SPLIT_PATTERN, fp.read())
    # skip first segment with version numbers in it, remove comments
    segment_count = 0
    start_index = 0 if version_numbers else 1
    for i, segment in enumerate(segments[start_index:]):
        segment = strip_comments(segment)
        # filter class name
        if i == 0 and version_numbers:
            yield segment
            continue
        if not class_filter or f"""class = "{class_filter}";""" in segment:
            segment_count += 1
            yield "entity {" + re.sub(r"//.*$", "", segment)
    if class_filter:
        print(f"{segment_count} instances of {class_filter} found")


def parse_entities(filename, class_filter=""):
    with mp.Pool(processes=mp.cpu_count() - 2) as pool:
        data = pool.map(
            parse_entity, generate_entity_segments(filename, class_filter=class_filter)
        )
    # data = map(ev.parse, generate_entity_segments(filename, class_filter))
    return data


def parse_entity(entity: str):
    try:
        return ev.parse(entity)
    except Exception as e:
        print(f"ERROR: unable to parse entity:\n{entity}")
        return {}
