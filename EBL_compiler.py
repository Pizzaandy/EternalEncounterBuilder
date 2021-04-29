import eternalevents
import EBL_grammar as EBL
import entities_parser as parser
from textwrap import indent
from dataclasses import dataclass
import re
import time
import chevron
import spawn_target_visualizer as visualizer


ebl = EBL.NodeVisitor()
ebl.grammar = EBL.grammar
space_char = "^"
blacklist_entities = []

variables = {}
debug_vars = False
Settings = ""
templates = {}


@dataclass
class EBL_Assignment():
    name: str
    value: str


class EntityTemplate():
    def __init__(self, name, template, args):
        self.name = name
        self.template = template
        self.args = args
        print(f"Template {name} found")

    def render(self, *argv):
        if len(argv) != len(self.args):
            print(f"ERROR: expected {len(self.args)} args in template {self.name}, {len(argv)} given")
            return ""
        t_data = {}
        for arg_name, arg in zip(self.args, argv):
            t_data[arg_name] = arg
        return chevron.render(template=self.template, data=t_data)


def debug_print(string):
    if debug_vars:
        print(string)


# not technically variables
def add_variable(varname, value):
    if varname in variables:
        debug_print(f"Modified variable {varname} = {value}")
    else:
        debug_print(f"Added variable {varname} = {value}")

    minimum_chars = 0
    prefixed = False
    if isinstance(value, str):
        prefixed = "+" in value
        minimum_chars = len(str(value)) if not prefixed else 0

    items = variables.items()
    sorted_variables = sorted(items, key=lambda x: len(x[0]), reverse=True)
    for var, val in sorted_variables:
        if len(var) < minimum_chars:
            continue
        if not isinstance(value, str):
            continue
        val = format_args([val], 1)[0]
        old_value = value
        value = value.replace(f'{var}', str(val))
        if value != old_value:
            debug_print(f"Substituted {var} = {value} into assignment {varname}")
    if prefixed:
        variables[varname] = value.replace("+", "")
        debug_print(f'''Flattened nested prefix {varname} = {value.replace("+","")}''')
        return

    variables[varname] = format_args([value], 1)[0]


waitFor_keywords = {
    "all": "ENCOUNTER_LOGICAL_OP_AND",
    "any": "ENCOUNTER_LOGICAL_OP_OR"
}

# ENCOUNTER_SPAWN + name
encounter_spawn_names = [
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

# These are the REAL constants you should use
encounter_spawn_aliases = {
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

base_entitydefs = [
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

dlc1_entitydefs = [
    "custom_ai_ambient_turret",
    "custom_ai_heavy_bloodangel",
    "custom_ai_ambient_super_tentacle",
    "custom_ai_ambient_spirit",
]

dlc2_entitydefs = [
    "custom_ai_superheavy_baron_armored",
    "custom_ai_fodder_prowler_cursed",
    "custom_ai_fodder_imp_stone",
    "custom_ai_fodder_soldier_chaingun",
    "custom_ai_fodder_zombie_t1_screecher",
    "custom_ai_ambient_demonic_trooper",
]


def list_entitydefs(entitydefs):
    res = f"num = {len(entitydefs)};\n"
    for i, name in enumerate(entitydefs):
        res += f'item[{i}] = {{\n\tname = "{name}";\n}}\n'
    return res


def list_targets(entitydefs):
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


def strip_comments(string):
    pattern = r"//(.*)(?=[\r\n]+)"
    return re.sub(pattern, "", string)


# Splits EBL file into segments at REPLACE ENCOUNTER headers
# and also handles SETTINGS flags
# returns a tuple with EBL code and encounter name

ebl_headers_regex = r"(^REPLACE ENCOUNTER|^REPLACE |^ADD |^REMOVE |^TEMPLATE )"

def generate_EBL_segments(filename):
    with open(filename) as fp:
        segments = re.split(ebl_headers_regex, fp.read(), flags=re.MULTILINE)
    if segments[0].startswith("SETTINGS"):
        # handle assignments written before REPLACE ENCOUNTERs
        print("SETTINGS header found!")
        Settings = segments[0]
        for line in Settings.splitlines():
            if line.count('=') == 1:
                var = line.split("=")
                add_variable(var[0].strip(), var[1].strip())
    else:
        print("No SETTINGS found")
    for i, segment in enumerate(segments[1:]):
        if i % 2 == 0:
            cmd = segment.strip()
            continue
        name = segment.split("\n")[0].strip()
        if not name:
            print("ERROR: No name in header!")
            continue
        segment = "\n".join(segment.split("\n")[1:])
        yield (name, (cmd, strip_comments(segment)))


# Handles macros and fills in missing arguments
def format_args(args, arg_count):
    for i, arg in enumerate(args):
        if isinstance(arg, str):
            args[i] = ""
            arg = arg.replace(space_char, space_char + " ").split()
            for word in arg:
                old_word = word
                word = word.replace("^", "")
                if word in encounter_spawn_names:
                    args[i] += "ENCOUNTER_SPAWN_" + word + " "
                elif word in encounter_spawn_aliases:
                    args[i] += ("ENCOUNTER_SPAWN_" +
                                encounter_spawn_aliases[word] + " ")
                else:
                    args[i] += old_word + " "
            args[i] = args[i].strip()
        if arg is None:
            args[i] = ""
    while len(args) < arg_count:
        args += [""]
    return args


# Consumes a parsed EBL file and generates a list of EternalEvents
def create_events(data):
    if isinstance(data, list):
        output = []
        for item in data:
            event = create_events(item)
            output += event if event is not None else []
        return output

    if isinstance(data, dict):
        if "variable" in data:
            return [EBL_Assignment(data["variable"], data["value"])]

        if data["event"] == "waitForBlock":
            length = len([ev for ev in data["args"] if not "variable" in ev[0]])
            waitevent =  {
                "event": "waitMulitpleConditions",
                "args": [length, waitFor_keywords[data["keyword"]], "false"]
            }
            return create_events([waitevent] + data["args"])

        if data["event"] == "waitFor":
            return create_events(data["args"])

        if data["event"] in eternalevents.ebl_to_event:
            cls_name, arg_count = eternalevents.ebl_to_event[data["event"]]
            event_cls = str_to_class(cls_name)
        else:
            print(f'''ERROR: undefined event {data["event"]}!''')

        args_list = data["args"]

        # Assume nested argument list means a list of parameters
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


# TODO: this is just dumb, find a better way
def is_dlc(filename):
     # check for "dlc1" and "dlc2"
    head = ""
    with open(filename) as fp:
        for i in range(1,50):
            head += fp.readline()
    dlc1 = "dlc1" in head
    dlc2 = "dlc2" in head
    print(f"dlc1: {dlc1}, dlc2: {dlc2}")
    return (dlc1, dlc2)


def add_idAI2s(filename, include_dlc1, include_dlc2):
    file = open(filename, "a")

    with open("idAI2_base.txt", "r") as fp_base:
        print("Added base game idAI2s")
        file.write(fp_base.read())

    if include_dlc2:
        with open("idAI2_dlc1.txt") as fp_dlc1:
            file.write(fp_dlc1.read())
        print("Added DLC1 idAI2s")
        with open("idAI2_dlc2.txt") as fp_dlc2:
            file.write(fp_dlc2.read())
        print("Added DLC2 idAI2s")

    elif include_dlc1:
        with open("idAI2_dlc1.txt") as fp_dlc1:
            file.write(fp_dlc1.read())
        print("Added DLC1 idAI2s")

    file.close()


# SETTINGS flags: (function, parameters)
setting_to_func = {

}


# Read SETTINGS flags and format entities file
# also make sure we don't miss any variables
def apply_settings(filename, settings):
    for line in settings.splitlines():
        if line in setting_to_func:
            func, args = setting_to_func[line]
            func(filename, *args)


# cringe
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# Concatenate strings (jank)
# TODO: make less jank, this is ugly as hell
def concat_strings(event_string):
    output_str = ""
    items = variables.items()
    sorted_variables = sorted(items, key=lambda x: len(x[0]), reverse=True)

    if "+" in event_string:
        segments = event_string.split("+")
        for i, seg in enumerate(segments):
            for var, val in sorted_variables:
                val = format_args([val], 1)[0]
                if ((seg.rstrip().endswith(f'{var}') and i != len(segments)-1)
                or (seg.lstrip().startswith(f'{var}') and i != 0)):
                    seg = seg.replace(f'{var}', str(val))
                if not (is_number(str(val)) or val in ["true", "false"]):
                    debug_print(f'added "" for {var} = {val}')
                    val = f'"{val}"'
                seg = seg.replace(f'"{var}"', str(val))
                if i == len(segments)-1:
                    seg = seg.lstrip()
                elif i == 0:
                    seg = seg.rstrip()
                else:
                    seg = seg.strip()
            output_str += seg
    else:
        for var, val in sorted_variables:
            if not (is_number(str(val)) or val in ["true", "false"]):
                debug_print(f'added "" for {var} = {val}')
                val = f'"{val}"'
            event_string = event_string.replace(f'"{var}"', str(val))
        output_str = event_string

    return output_str.replace(space_char, " ")


# converts EBL string to encounterComponent events
def compile_EBL(s):
    output_str = ""
    item_index = 0
    events = create_events(ebl.parse(s))
    if events is None:
        return output_str
    output_str += f"num = {len(events)};\n"
    for event in events:
        if isinstance(event, EBL_Assignment):
            add_variable(event.name, event.value)
            continue
        event_string = concat_strings(str(event))
        output_str += (f"item[{item_index}]" + " = {\n" +
                       indent(event_string, "\t") + "}\n")
        item_index += 1

    return output_str



actorpopulation = [
    "actorpopulation/default/default_no_bosses",
    "actorpopulation/default/dlc1",
    "actorpopulation/default/dlc2_demonic_soldier",
]


# TODO: actual error handling
def replace_encounter(entity_string, entity_events, dlc_level):
    entity = parser.ev.parse(entity_string)
    entity_events = "{\n" + indent(entity_events, "\t") + "}\n"
    for key in entity:
        if key.startswith("entityDef"):
            entitydef = key
    if not key:
        print("ERROR: no entityDef component!")
        return entity_string
    try:
        entity[entitydef]["edit"]["encounterComponent"]["entityEvents"]["item[0]"]["events"] = entity_events
        entity[entitydef]["edit"]["aiTypeDefAssignments"] = actorpopulation[dlc_level]
        #print(f"changed aiTypeDefAssignments to {actorpopulation[dlc_level]}")
    except:
        print("ERROR: Unable to replace encounter")
        print(entity[entitydef]["edit"])
    return parser.generate_entity(entity)


def add_entitydefs(entity_string, entitydefs):
    # print(entity_string)
    entity = parser.ev.parse(entity_string)
    for key in entity:
        if key.startswith("entityDef"):
            entitydef = key
    if not key:
        print("ERROR: no entityDef component!")
        return entity_string

    old_entitydefs = entity[entitydef]["edit"]["entityDefs"]
    old_entitydefs.pop('num')

    if len(old_entitydefs) > 0:
        names = []
        for assignment in list(old_entitydefs.values()):
            names += list(assignment.values())
        entitydefs = entitydefs + names
    try:
        spawn_editable = entity[entitydef]["edit"]["spawnEditable"]
    except KeyError:
        pass
    else:
        if not spawn_editable["spawnAnim"]:
            entity[entitydef]["edit"]["spawnEditable"]["aiStateOverride"] = "AIOVERRIDE_TELEPORT";

    targets = list_targets(entitydefs)
    entitydefs = list_entitydefs(entitydefs)
    targets = "{\n" + indent(targets, "\t") + "}\n"
    entitydefs = "{\n" + indent(entitydefs, "\t") + "}\n"
    entity[entitydef]["edit"]["entityDefs"] = entitydefs
    entity[entitydef]["edit"]["targets"] = targets
    #print("Added entitydefs")
    return parser.generate_entity(entity)


def modify_entity(name, entity_string, params, dlc_level):
    cmd = params[0]
    text = params[1]
    if cmd == "REPLACE ENCOUNTER":
        print(f"Replaced encounter {name}")
        return replace_encounter(entity_string, text, dlc_level)
    if cmd == "REPLACE":
        print(f"Replaced entity {name}")
        return text
    if cmd == "REMOVE":
        print(f"Removed entity {name}")
        return ""


# Apply all changes in ebl_file to modded_file created from base_file
def apply_EBL(ebl_file, base_file, modded_file, compress_file=True, show_spawn_targets=False):

    # generate segments + format target file
    tic = time.time()
    modified_count = 0
    entity_count = 0
    parser.decompress(base_file)

    # if they ever make more DLC I'll change this shit lol
    dlc1, dlc2 = is_dlc(base_file)
    entitydefs = base_entitydefs
    if dlc2:
        entitydefs += dlc1_entitydefs + dlc2_entitydefs
        dlc_level = 2
    elif dlc1:
        entitydefs += dlc1_entitydefs
        dlc_level = 1

    segments = generate_EBL_segments(ebl_file)
    deltas = dict(segments)
    added_entities = []

    # find templates
    for key, val in deltas.items():
        if val[0] == "TEMPLATE":
            t_name, t_args = key.split("(", 1)
            t_args = t_args.split(",")
            for i, arg in enumerate(t_args):
                t_args[i] = arg.replace(")", "").strip()
            templates[t_name] = EntityTemplate(t_name, val[1], t_args)

    # compile EBL segments to eternalevents and add new entities
    for key, val in deltas.items():
        if val[0] == "REPLACE ENCOUNTER":
            deltas[key] = (val[0], compile_EBL(val[1]))
        if val[0] == "ADD":
            is_template = False
            for t_key in templates.keys():
                if key.startswith(t_key):
                    args = re.findall (r'([^(,)]+)(?!.*\()', key)
                    args = [arg.strip() for arg in args]
                    entity_str = templates[t_key].render(*args)
                    is_template = True
                    print(f"Added new instance of {t_key} with arguments {args}, {key}")
            if not is_template:
                entity_str = val[1].strip()
                print (f"Added entity {key}")
            added_entities += [entity_str.strip()]

    entities = parser.generate_entity_segments(base_file, version_numbers=True)

    with open(modded_file, "w") as fp:

        for entity in entities:
            entity_count += 1
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
        for new_entity in added_entities:
            if ('class = "idTarget_Spawn";' in new_entity
                or 'class = "idTarget_Spawn_Parent";' in new_entity):
                new_entity = add_entitydefs(new_entity, entitydefs)
            fp.write(new_entity + "\n")

    add_idAI2s(modded_file, dlc1, dlc2)
    apply_settings(modded_file, Settings)

    if show_spawn_targets:
        print("Adding spawn target markers...")
        visualizer.show_spawn_targets(modded_file)

    parser.verify_file(modded_file)
    parser.list_checkpoints(modded_file)

    if compress_file:
        parser.compress(modded_file)

    print(f"{modified_count} entities out of {entity_count-1} modified!")
    print(f"Done processing in {time.time() - tic:.1f} seconds")
    print(templates)

