import eternalevents
from eternalevents import is_number_or_keyword
import eternaltools
import EBL_grammar as EblGrammar
from EBL_grammar import EblTypeError
import entities_parser as parser
from entities_parser import EntitiesSyntaxError
from textwrap import indent
import chevron
from dataclasses import dataclass
from typing import List
import re
import time
import math
import sys

# EBL = Eternal Builder Language, describes changes to .entities files
ebl = EblGrammar.NodeVisitor()
ebl.grammar = EblGrammar.grammar
blacklist_entities = []

# character reserved for spaces in string literals
SPACE_CHAR = "^"
variables = {}
Settings = ""
templates = {}
debug_vars = True


def debug_print(string):
    if debug_vars:
        print(string)


@dataclass
class Assignment:
    name: str
    value: str


# syntax is object.func(value)
@dataclass
class EntityEdit:
    object: str
    func: str
    value: list


# TODO: move entity templates to another module
class EntityTemplate:
    """
    Handles text templates to be rendered into .entities
    """
    def __init__(self, name, template, args):
        self.name = name
        self.template = template
        self.args = args
        print(f"Template {name} found")

    def modify_args(self, args):
        args = list(args)
        for i, arg in enumerate(args):
            if "[" in arg:
                clsname, clsargs = arg.split("[")
                if clsname not in [cls.__name__ for cls in EntityTemplate.__subclasses__()]:
                    print(f"class {clsname} not found")
                    continue
                clsargs = clsargs.replace("]", "").split()
                clsargs = [arg.strip() for arg in clsargs]
                cls = getattr(sys.modules[__name__], clsname)
                args[i] = cls().render(*clsargs)
                print(f"Rendered class {clsname} with args {clsargs}")
        return args

    def render(self, *argv) -> str:
        argv = self.modify_args(argv)
        if len(argv) != len(self.args):
            raise EblTypeError(f"Expected {len(self.args)} args in template {self.name}, {len(argv)} given")
        t_data = {}
        for arg_name, arg in zip(self.args, argv):
            t_data[arg_name] = arg
        return chevron.render(template=self.template, data=t_data)


# noinspection PyMissingConstructor
class Vec3(EntityTemplate):
    def __init__(self):
        self.name = "Vec3"
        self.args = ["x", "y", "z"]
        self.template = ("""{
            x = {{x}};
            y = {{y}};
            z = {{z}};
        }
    """)


def sin_cos(deg):
    rad = math.degrees(float(deg))
    return math.sin(rad), math.cos(rad)


# noinspection PyMissingConstructor
class Mat3(EntityTemplate):
    def __init__(self):
        self.name = "Mat3"
        self.args = [
            "x1", "y1", "z1",
            "x2", "y2", "z2",
            "x3", "y3", "z3"
        ]
        self.template = ("""{
            mat = {
                mat[0] = {
                    x = {{x1}};
                    y = {{y1}};
                    z = {{z1}};
                }
                mat[1] = {
                    x = {{x2}};
                    y = {{y2}};
                    z = {{z2}};
                }
                mat[2] = {
                    x = {{x3}};
                    y = {{y3}};
                    z = {{z3}};
                }
            }
        }""")

    def modify_args(self, args):
        if len(args) == 3:
            sy, cy = sin_cos(args[0])
            sp, cp = sin_cos(args[1])
            sr, cr = sin_cos(args[2])
            return [
                cp*cy, cp*sy, -sp,
                sr*sp*cy + cr*-sy,  sr*sp*sy + cr*cy, sr*cp,
                cr*sp*cy + -sr*sy, cr*sp*sy + -sr*cy, cr*cp
            ]
        else:
            return args


# noinspection PyMissingConstructor
class Mat2(EntityTemplate):
    def __init__(self):
        self.name = "Mat2"
        self.args = [
            "x1", "y1",
            "x2", "y2"
        ]
        self.template = ("""{
            mat = {
                mat[0] = {
                    x = {{x1}};
                    y = {{y1}};
                }
                mat[1] = {
                    x = {{x2}};
                    y = {{y2}};
                }
            }
        }""")

    def modify_args(self, args):
        if len(args) == 2:
            sy, cy = sin_cos(args[0])
            sp, cp = sin_cos(args[1])
            return [
                cy, sy,
                cp, sp
            ]
        else:
            return args


# these are not technically variables, but go off I guess
def add_variable(varname, value):
    if varname in variables:
        debug_print(f"Modified variable {varname} = {value}")
    else:
        print(f"Added variable {varname} = {value}")

    ignore_quotes = "+" not in value
    new_value = format_args([value], 1)[0]
    variables[varname] = concat_strings(new_value, ignore_quotes)
    debug_print(f'''Concatenated strings in assignment {varname} = {variables[varname]}''')
    return True


WAITFOR_KEYWORDS = {
    "all": "ENCOUNTER_LOGICAL_OP_AND",
    "any": "ENCOUNTER_LOGICAL_OP_OR"
}


# ENCOUNTER_SPAWN + name
ENCOUNTER_SPAWN_NAMES = [
    "ANY",
    "GENERIC",
    "ARACHNOTRON",
    "ARMORED_BARON",
    "BARON",
    "BLOOD_ANGEL",
    "CACODEMON",
    "CHAINGUN_SOLDIER",
    "CUEBALL",
    "CURSED_PROWLER",
    "CYBER_MANCUBUS",
    "DOOM_HUNTER",
    "DREAD_KNIGHT",
    "GARGOYLE",
    "HELL_KNIGHT",
    "HELL_SOLDIER",
    "IMP",
    "MANCUBUS",
    "MARAUDER",
    "PAIN_ELEMENTAL",
    "PINKY",
    "PROWLER",
    "REVENANT",
    "SHOTGUN_SOLDIER",
    "STONE_IMP",
    "TENTACLE",
    "TYRANT",
    "WHIPLASH",
    "ZOMBIE_MAYKR",
    "ZOMBIE_T1_SCREECHER",
    "ZOMBIE_TIER_1",
    "ZOMBIE_TIER_3",
    "LOST_SOUL",
    "SPECTRE",
    "CARCASS",
    "ARCHVILE",
    "BUFF_POD",
    "SPIRIT",
    "TURRET",
    "SUPER_TENTACLE",
]

# These are the preferred constants
ENCOUNTER_SPAWN_ALIASES = {
    "Any": "ANY",
    "Generic": "GENERIC",
    "Arachnotron": "ARACHNOTRON",
    "ArmoredBaron": "ARMORED_BARON",
    "Spider": "ARACHNOTRON",
    "Baron": "BARON",
    "FireborneBaron": "BARON",
    "BloodAngel": "BLOOD_ANGEL",
    "BloodMaykr": "BLOOD_ANGEL",
    "Cacodemon": "CACODEMON",
    "ChaingunSoldier": "CHAINGUN_SOLDIER",
    "Chaingunner": "CHAINGUN_SOLDIER",
    "RiotSoldier": "CHAINGUN_SOLDIER",
    "Cueball": "CUEBALL",
    "CursedProwler": "CURSED_PROWLER",
    "CyberMancubus": "CYBER_MANCUBUS",
    "DoomHunter": "DOOM_HUNTER",
    "DreadKnight": "DREAD_KNIGHT",
    "Gargoyle": "GARGOYLE",
    "HellKnight": "HELL_KNIGHT",
    "HellSoldier": "HELL_SOLDIER",
    "ZombieMan": "HELL_SOLDIER",
    "Imp": "IMP",
    "Mancubus": "MANCUBUS",
    "Marauder": "MARAUDER",
    "PainElemental": "PAIN_ELEMENTAL",
    "Pinky": "PINKY",
    "Prowler": "PROWLER",
    "Revenant": "REVENANT",
    "ShotgunSoldier": "SHOTGUN_SOLDIER",
    "Shotgunner": "SHOTGUN_SOLDIER",
    "ShotgunGuy": "SHOTGUN_SOLDIER",
    "ShieldGuy": "SHOTGUN_SOLDIER",
    "StoneImp": "STONE_IMP",
    "SIMP": "STONE_IMP",
    "Tentacle": "TENTACLE",
    "Tyrant": "TYRANT",
    "Cyberdemon": "TYRANT",
    "Whiplash": "WHIPLASH",
    "ZombieMaykr": "ZOMBIE_MAYKR",
    "MaykrDrone": "ZOMBIE_MAYKR",
    "ZombieT1Screecher": "ZOMBIE_T1_SCREECHER",
    "Screecher": "ZOMBIE_T1_SCREECHER",
    "ZombieTier1": "ZOMBIE_TIER_1",
    "Zombie": "ZOMBIE_TIER_1",
    "ZombieTier3": "ZOMBIE_TIER_3",
    "MechaZombie": "ZOMBIE_TIER_3",
    "LostSoul": "LOST_SOUL",
    "Spectre": "SPECTRE",
    "Carcass": "CARCASS",
    "BigChungus": "CARCASS",
    "Archvile": "ARCHVILE",
    "BuffPod": "BUFF_POD",
    "BuffTotem": "BUFF_POD",
    "Spirit": "SPIRIT",
    "Turret": "TURRET",
    "SuperTentacle": "SUPER_TENTACLE",
}


BASE_ENTITYDEFS = [
    "custom_ai_fodder_imp",
    "custom_ai_fodder_soldier_blaster",
    "custom_ai_fodder_gargoyle",
    "custom_ai_fodder_zombie_tier_3",
    "custom_ai_heavy_hellknight",
    "custom_ai_heavy_revenant",
    "custom_ai_fodder_lostsoul",
    "custom_ai_fodder_soldier_shield",
    "custom_ai_heavy_whiplash",
    "custom_ai_heavy_arachnotron",
    "custom_ai_heavy_cacodemon",
    "custom_ai_ambient_zombie_cueball",
    "custom_ai_fodder_zombie_t1_scientist",
    "custom_ai_heavy_mancubus_fire",
    "custom_ai_ambient_tentacle",
    "custom_ai_fodder_carcass",
    "custom_ai_fodder_prowler",
    "custom_ai_heavy_dreadknight",
    "custom_ai_heavy_mancubus_goo",
    "custom_ai_heavy_painelemental",
    "custom_ai_heavy_pinky",
    "custom_ai_heavy_pinky_spectre",
    "custom_ai_superheavy_archvile",
    "custom_ai_superheavy_baron",
    "custom_ai_superheavy_doom_hunter",
    "custom_ai_superheavy_marauder",
    "custom_ai_superheavy_tyrant",
    "custom_ai_ambient_buffpod",
    "custom_ai_fodder_zombie_maykr",
]


DLC1_ENTITYDEFS = [
    "custom_ai_ambient_turret",
    "custom_ai_heavy_bloodangel",
    "custom_ai_ambient_super_tentacle",
    "custom_ai_ambient_spirit",
]


DLC2_ENTITYDEFS = [
    "custom_ai_superheavy_baron_armored",
    "custom_ai_fodder_prowler_cursed",
    "custom_ai_fodder_imp_stone",
    "custom_ai_fodder_soldier_chaingun",
    "custom_ai_fodder_zombie_t1_screecher",
    "custom_ai_ambient_demonic_trooper",
]


def list_entitydefs(entitydefs: list) -> str:
    res = f"num = {len(entitydefs)};\n"
    for i, name in enumerate(entitydefs):
        res += f'item[{i}] = {{\n\tname = "{name}";\n}}\n'
    return res


def list_targets(entitydefs: list) -> str:
    res = f"num = {len(entitydefs)};\n"
    for i, name in enumerate(entitydefs):
        res += f'item[{i}] = "{name}";\n'
    return res


def str_to_class(classname):
    return getattr(eternalevents, classname)


def get_event_args(classname):
    return ([i for i in classname.__dict__.keys()
             if not i.startswith('__')
             and not i.startswith('args')])


def strip_comments(s):
    pattern = r"//(.*)(?=[\r\n]+)"
    return re.sub(pattern, "", s)


EBL_HEADERS_REGEX = r"(^REPLACE ENCOUNTER|^REPLACE |^ADD |^REMOVE |^TEMPLATE |^MODIFY )"


def generate_ebl_segments(filename):
    """
    Splits an EBL file into segments at headers
    returns a tuple with EBL code and encounter name
    :param filename:
    :return:
    """
    with open(filename) as fp:
        segments = re.split(EBL_HEADERS_REGEX, fp.read(), flags=re.MULTILINE)

    if segments[0].startswith("SETTINGS"):
        print("SETTINGS header found!")
        # Settings = segments[0]
    else:
        print("No SETTINGS found")

    # handle variables at top of document
    for line in segments[0].splitlines():
        if line.count('=') == 1:
            var = line.split("=")
            add_variable(var[0].strip(), var[1].strip())

    # yield tuples containing name, header command, and body text
    cmd = ""
    for i, segment in enumerate(segments[1:]):
        if i % 2 == 0:
            cmd = segment.strip()
            continue
        name = segment.split("\n")[0].strip()
        if not name:
            raise EblTypeError(f"No entity name specified in header {cmd}")
        segment = "\n".join(segment.split("\n")[1:])
        yield name, (cmd, strip_comments(segment))


# Handles variables and fills in missing arguments
def format_args(args: list, arg_count) -> list:
    for i, arg in enumerate(args):
        if isinstance(arg, str):
            args[i] = ""
            arg = arg.replace(SPACE_CHAR, SPACE_CHAR + " ").split()
            for word in arg:
                old_word = word
                word = word.replace("^", "")
                if word in ENCOUNTER_SPAWN_NAMES:
                    args[i] += "ENCOUNTER_SPAWN_" + word + " "
                elif word in ENCOUNTER_SPAWN_ALIASES:
                    args[i] += ("ENCOUNTER_SPAWN_" +
                                ENCOUNTER_SPAWN_ALIASES[word] + " ")
                else:
                    args[i] += old_word + " "
            args[i] = args[i].strip()
        if arg is None:
            args[i] = ""
    while len(args) < arg_count:
        args += [""]
    return args


# Consumes parsed EBL and generates a list of EternalEvents
# TODO: use the structural pattern matching feature when it comes out lol
def create_events(data) -> list:
    if isinstance(data, list):
        output = []
        for item in data:
            event = create_events(item)
            output += event  # if event is not None else []
        return output

    if isinstance(data, dict):
        if "variable" in data:
            return [Assignment(data["variable"], data["value"])]

        if "function" in data:
            print(f"function value is {data['value']}")
            return [EntityEdit(data["object"], data["function"], data["value"])]

        if data["event"] == "waitForBlock":
            event_count = len([ev for ev in data["args"] if "variable" not in ev[0]])
            waitevent = {
                "event": "waitMulitpleConditions",
                "args": [event_count, WAITFOR_KEYWORDS[data["keyword"]], "false"]
            }
            return create_events([waitevent] + data["args"])

        if data["event"] == "waitFor":
            return create_events(data["args"])

        if data["event"] in eternalevents.ebl_to_event:
            cls_name, arg_count = eternalevents.ebl_to_event[data["event"]]
            event_cls = str_to_class(cls_name)
        else:
            raise EblTypeError(f'''Undefined event {data["event"]}!''')

        args_list = data["args"]

        # Assume nested argument list means a list of parameters
        if any(isinstance(i, list) for i in args_list):
            result = []
            for args in args_list:
                args = format_args(args, arg_count)
                result += [event_cls(*args)]
            return result
        else:
            args_list = format_args(args_list, arg_count)
            return [event_cls(*args_list)]

    return data


# TODO: this is just dumb, find a better way
def get_dlc_level(filename) -> int:
    """
    Checks dlc level of file by checking first 50 lines for keywords
    :param filename:
    :return dlc_level:
    """
    head = ""
    with open(filename) as fp:
        for i in range(1, 50):
            head += fp.readline()

    if "dlc2" in head:
        dlc_level = 2
    elif "dlc1" in head:
        dlc_level = 1
    else:
        dlc_level = 0
    print(f"DLC Level: {dlc_level}")
    return dlc_level


def add_idai2s(filename, dlc_level):
    file = open(filename, "a")

    with open("idAI2_base.txt", "r") as fp_base:
        print("Added base game idAI2s")
        file.write(fp_base.read())

    if dlc_level >= 2:
        with open("idAI2_dlc2.txt") as fp_dlc2:
            file.write(fp_dlc2.read())
        print("Added DLC2 idAI2s")

    if dlc_level >= 1:
        with open("idAI2_dlc1.txt") as fp_dlc1:
            file.write(fp_dlc1.read())
        print("Added DLC1 idAI2s")

    file.close()


# cringe
def rreplace(s, old, new, occurrence=0):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def concat_strings(s, is_expression=False):
    """
    Okay this function is really nasty
    If I ever find a reason to change it I will lol

    Manipulates string by:
    a) replacing variable names with corresponding values
    b) handling the + operator and concatenating strings
    :param s:
    :param is_expression: whether all of s must be matched if there is no + in string
    :return modified_string:
    """
    items = variables.items()
    sorted_variables = sorted(items, key=lambda x: len(x[0]), reverse=True)

    if "+" not in s:
        for var, val in sorted_variables:
            if is_expression:
                # only replace entire expression if match
                if len(var) == len(s.strip()):
                    s = s.replace(f'{var}', str(val))
                    break
            else:
                # replace all instances of substring in quotes
                if not is_number_or_keyword(s):
                    val = f'"{val}"'
                s = s.replace(f'"{var}"', str(val))
        return s.replace(SPACE_CHAR, " ").replace("$", "")

    result = ""
    segments = s.split("+")
    for i, seg in enumerate(segments):
        seg = seg.lstrip() if i > 0 else seg
        seg = seg.rstrip() if i < len(segments)-1 else seg
        potential_matches = re.findall(r'[$^\w]+', seg)
        first_match = potential_matches[0] if i > 0 else None
        last_match = potential_matches[-1] if i < len(segments)-1 else None

        for j, match in enumerate([first_match, last_match]):
            if not match:
                continue
            for var, val in sorted_variables:
                if len(var) < len(match.strip()):
                    continue
                if match.strip() == var:
                    val = format_args([val], 1)[0]
                    if j == 0:
                        seg = seg.replace(match, str(val), 1)
                    else:
                        seg = rreplace(seg, match, str(val), 1)
                    debug_print(f"matched variable '{match}' and substituted '{str(val)}'")
                    debug_print(f"seg is now '{seg}'")

        result += seg
    return result.replace(SPACE_CHAR, " ").replace("$", "")


def compile_ebl_encounter(s) -> str:
    """
    Compiles EBL to encounterComponent events
    :param s:
    :return events:
    """
    result = ""
    item_index = 0
    events = create_events(ebl.parse(s))
    if events is None:
        return result

    result += f"num = {len(events)};\n"
    for event in events:
        if isinstance(event, Assignment):
            add_variable(event.name, event.value)
            continue
        event_string = concat_strings(str(event))
        result += (f"item[{item_index}]" + " = {\n" +
                   indent(event_string, "\t") + "}\n")
        item_index += 1

    return result


ACTORPOPULATION = [
    "actorpopulation/default/default_no_bosses",
    "actorpopulation/default/dlc1",
    "actorpopulation/default/dlc2_demonic_soldier",
]


# TODO: actual error handling
def replace_encounter(encounter: str, events: str, dlc_level: int) -> str:
    """
    Modifies encounter entity with list of eternalevents
    :param encounter:
    :param events:
    :param dlc_level:
    :return new_entity_string:
    """
    entity = parser.ev.parse(encounter)
    entity_events = "{\n" + indent(events, "\t") + "}\n"
    entitydef = ""
    for key in entity:
        if key.startswith("entityDef"):
            entitydef = key
    if not entitydef:
        raise EntitiesSyntaxError("No entityDef component!")
    try:
        entity[entitydef]["edit"]["encounterComponent"]["entityEvents"]["item[0]"]["events"] = entity_events
        entity[entitydef]["edit"]["aiTypeDefAssignments"] = ACTORPOPULATION[dlc_level]
        # print(f"changed aiTypeDefAssignments to {actorpopulation[dlc_level]}")
    except KeyError:
        print("ERROR: Unable to replace encounter")
        print(entity[entitydef]["edit"])
    return parser.generate_entity(entity)


def edit_entity_fields(base_entity: str, edits: str) -> str:
    """
    Edits specific fields in the given entity
    :param base_entity:
    :param edits:
    :return edited_entity:
    """
    entity = parser.ev.parse(base_entity)
    entitydef = ""
    for key in entity:
        if key.startswith("entityDef"):
            entitydef = key
    if not entitydef:
        # This should never happen when modifying a base entities file
        raise EntitiesSyntaxError("No entityDef component!")

    entity_edits = ebl.parse(edits)
    for entity_edit in create_events(entity_edits):
        if type(entity_edit) is not EntityEdit:
            if type(entity_edit) is Assignment:
                add_variable(entity_edit.name, entity_edit.value)
                continue
            else:
                raise EblTypeError("All lines under MODIFY header must be EntityEdits or Assignments")
        func = entity_edit.func
        values = entity_edit.value
        path = entity_edit.object
        keys = path.split("/")

        print(f"values is {values}")
        for value in values:
            dic = entity[entitydef]

            if func in ["append", "add", "update", "set"]:
                if not 2 >= len(value) >= 1:
                    raise EblTypeError(f'Edit function "{func}" takes one or two arguments')
                for key in keys:
                    dic = dic.setdefault(key, {})
                print(dic)
                if len(value) == 2:
                    if isinstance(value[1], str):
                        value[1] = concat_strings(value[1], is_expression=True)
                    dic[concat_strings(value[0])] = value[1]
                else:
                    dic = value[0]

            if func in ["remove", "pop", "delete"]:
                if len(value) != 1:
                    raise EblTypeError(f'Edit function "{func}" takes one argument')
                value = concat_strings(value[0], is_expression=True)
                for key in keys:
                    dic = dic[key]
                for key, val in dic.items():
                    debug_print(f"Checking value '{value}' against '{val}'")
                    if val == value:
                        debug_print("Matched!")
                        dic.pop(key)
                        break

    return parser.generate_entity(entity)


def add_entitydefs(spawn_target: str, entitydefs: List[str]) -> str:
    """
    Add custom idAI2s to the given spawn target
    :param spawn_target:
    :param entitydefs:
    :return modified_spawn_target:
    """
    entity = parser.ev.parse(spawn_target)
    entitydef = ""
    for key in entity:
        if key.startswith("entityDef"):
            entitydef = key
    if not entitydef:
        print("ERROR: no entityDef component!")
        return spawn_target

    existing_entitydefs = entity[entitydef]["edit"]["entityDefs"]
    existing_entitydefs.pop('num')

    # add existing entitydefs to end of list
    if len(existing_entitydefs) > 0:
        names = []
        for assignment in list(existing_entitydefs.values()):
            names += list(assignment.values())
        entitydefs = entitydefs + names
    try:
        spawn_editable = entity[entitydef]["edit"]["spawnEditable"]
    except KeyError:
        pass
    else:
        # TODO: adjust spawn target formatting to preserve intro animations
        if not spawn_editable["spawnAnim"]:
            entity[entitydef]["edit"]["spawnEditable"]["aiStateOverride"] = 'AIOVERRIDE_TELEPORT'

    listed_targets = list_targets(entitydefs)
    targets = "{\n" + indent(listed_targets, "\t") + "}\n"
    entity[entitydef]["edit"]["targets"] = targets

    listed_entitydefs = list_entitydefs(entitydefs)
    entitydefs = "{\n" + indent(listed_entitydefs, "\t") + "}\n"
    entity[entitydef]["edit"]["entityDefs"] = entitydefs

    return parser.generate_entity(entity)


def modify_entity(name, entity: str, params, dlc_level) -> str:
    """
    Applies changes to entity with given parameters
    :param name:
    :param entity:
    :param params:
    :param dlc_level:
    :return modified_entity:
    """
    cmd, text = params
    if cmd == "REPLACE ENCOUNTER":
        print(f"Replaced encounter {name}")
        return replace_encounter(entity, text, dlc_level)
    if cmd == "REPLACE":
        print(f"Replaced entity {name}")
        return text
    if cmd == "REMOVE":
        print(f"Removed entity {name}")
        return ""
    if cmd == "MODIFY":
        return edit_entity_fields(entity, text)


# Apply all changes in ebl_file to base_file and output to modded_file
def apply_ebl(
    ebl_file,
    base_file,
    modded_file,
    compress_file=True,
    show_spawn_targets=False,
    generate_traversals=True
):
    """
    Applies all changes in an EBL file to a copy of a vanilla entities file
    :param ebl_file: EBL file describing all file changes
    :param base_file: The vanilla entities file to modify
    :param modded_file: The output file path
    :param compress_file: Whether the output file should be compressed
    :param show_spawn_targets: Whether visual spawn target markers should be added to the file
    :param generate_traversals: Whether traversal info should be added to the file
    :return success:
    """
    tic = time.time()
    modified_count = 0
    total_count = 0

    eternaltools.decompress(base_file)
    dlc_level = get_dlc_level(base_file)

    # Add entitydefs with appropriate DLC level
    entitydefs = BASE_ENTITYDEFS
    if dlc_level >= 2:
        entitydefs += DLC2_ENTITYDEFS
    if dlc_level >= 1:
        entitydefs += DLC1_ENTITYDEFS

    # get all file deltas
    segments = generate_ebl_segments(ebl_file)
    deltas = dict(segments)
    added_entities = []

    # find + store templates
    for key, val in deltas.items():
        if val[0] == "TEMPLATE":
            t_name, t_args = key.split("(", 1)
            t_args = re.findall(r'([^(,)]+)(?!.*\()', t_args)
            t_args = [arg.strip() for arg in t_args]
            # print(f"t_args is {t_args}")
            templates[t_name] = EntityTemplate(t_name, val[1], t_args)

    # compile EBL segments to eternalevents and add new entities
    for key, val in deltas.items():
        if val[0] == "REPLACE ENCOUNTER":
            deltas[key] = (val[0], compile_ebl_encounter(val[1]))
            # debug_print(f"Compiling encounter starting with: {val[1].splitlines()[1:3]}")

        if val[0] == "ADD":
            entity = ""
            is_template = False
            for template in templates.keys():
                if key.replace(" ", "").startswith(template + "("):
                    # find all comma-delimited arguments
                    args = re.findall(r'([^(,)]+)(?!.*\()', key)
                    args = [arg.strip() for arg in args]
                    entity = templates[template].render(*args)
                    is_template = True
                    print(f"Added new instance of {key}")
            if not is_template:
                entity = val[1].strip()
                print(f"Added entity {key}")
            added_entities += [entity.strip()]

    # get vanilla entities from base file
    entities = parser.generate_entity_segments(base_file, version_numbers=True)

    with open(modded_file, "w") as fp:
        # iterate vanilla entities, apply changes, then write to output file
        for entity in entities:
            total_count += 1
            for name, params in deltas.items():
                if f"entityDef {name} {{" in entity:
                    print(f"Found entity {name}")
                    entity = modify_entity(name, entity, params, dlc_level)
                    modified_count += 1
                    break
            if ('class = "idTarget_Spawn";' in entity
                    or 'class = "idTarget_Spawn_Parent";' in entity):
                entity = add_entitydefs(entity, entitydefs)
                modified_count += 1
            fp.write(entity)
        fp.write("\n")
        # iterate added entities, apply changes, then write to output file
        for new_entity in added_entities:
            if ('class = "idTarget_Spawn";' in new_entity
                    or 'class = "idTarget_Spawn_Parent";' in new_entity):
                new_entity = add_entitydefs(new_entity, entitydefs)
            fp.write(new_entity + "\n")

    add_idai2s(modded_file, dlc_level)

    if show_spawn_targets:
        print("Adding spawn target markers...")
        eternaltools.mark_spawn_targets(modded_file)

    if generate_traversals:
        print("Generating traversal info...")
        eternaltools.generate_traversals(modded_file, dlc_level)

    parser.verify_file(modded_file)
    parser.list_checkpoints(modded_file)

    if compress_file:
        eternaltools.compress(modded_file)

    print(f"{modified_count} entities out of {total_count-1} modified!")
    print(f"Done processing in {time.time() - tic:.1f} seconds")
    debug_print(variables)
    return True
