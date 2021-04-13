import eternalevents as ee
import EBL_grammar as EBL
from textwrap import indent
from dataclasses import dataclass
import re
import time

ebl = EBL.NodeVisitor()
ebl.grammar = EBL.grammar
variables = {}
debug_vars = True


@dataclass
class EBL_Assignment():
    name: str
    value: str


def debug_print(string):
    if debug_vars:
        print(string)


def add_variable(varname, value):
    if varname in variables:
        debug_print(f"Modified variable {varname} = {value}")
    else:
        debug_print(f"Added variable {varname} = {value}")

    minimum_chars = 0
    prefixed = False
    if isinstance(value, str):
        prefixed = "@" in value
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
        variables[varname] = value.replace("@", "")
        debug_print(f'''Flattened nested prefix {varname} = {value.replace("@","")}''')
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
    "ZOMBIE_MAKYR",
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
    "BloodMakyr": "BLOOD_ANGEL",
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
    "ZombieMakyr": "ZOMBIE_MAKYR",
    "MakyrDrone": "ZOMBIE_MAKYR",
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


def str_to_class(classname):
    return getattr(ee, classname)


def get_event_args(classname):
    return ([i for i in classname.__dict__.keys()
             if not i.startswith('__')
             and not i.startswith('args')])


def strip_comments(string):
    pattern = r"//(.*)[\r\n]+"
    return re.sub(pattern, "", string)


# Splits EBL file into segments at REPLACE ENCOUNTER headers
# and also handles SETTINGS flags
def generate_EBL_segments(filename, format_file=True):
    with open(filename) as fp:
        segments = re.split(r"^REPLACE ENCOUNTER", fp.read(), flags=re.MULTILINE)
    start_index = 0
    if segments[0].startswith("SETTINGS"):
        print("SETTINGS header found!")
        start_index = 1
        if format_file:
            format_entities_file(filename, segments[0])
        else:
            print("Settings Ignored lol")
    else:
        print("No SETTINGS found")
    for segment in segments[start_index:]:
        segment = "\n".join(segment.split("\n")[1:])
        yield strip_comments(segment)


# Handles macros and fills in missing arguments
def format_args(args, arg_count):
    for i, arg in enumerate(args):
        if isinstance(arg, str):
            args[i] = ""
            for word in arg.split():
                if word in encounter_spawn_names:
                    args[i] += "ENCOUNTER_SPAWN_" + word + " "
                elif word in encounter_spawn_aliases:
                    args[i] += ("ENCOUNTER_SPAWN_" +
                                encounter_spawn_aliases[word] + " ")
                else:
                    args[i] += word + " "
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
            # print("waitForBlock found!")
            #print(data["args"])
            length = len([ev for ev in data["args"] if not "variable" in ev[0]])
           # print(length)
            waitevent =  {
                "event": "waitMulitpleConditions",
                "args": [length, waitFor_keywords[data["keyword"]], "false"]
            }
            return create_events([waitevent] + data["args"])

        if data["event"] == "waitFor":
            #print(create_events(data["args"]))
            #print("waitFor found!")
            return create_events(data["args"])

        if data["event"] in ee.ebl_to_event:
            cls_name, arg_count = ee.ebl_to_event[data["event"]]
            event_cls = str_to_class(cls_name)
        else:
            print(f'''ERROR: undefined event {data["event"]}!''')

        args_list = data["args"]

        # Assume nested argument list means parameter list
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
        print("Formatting all spawn targets")
    else:
        print("Formatting modified spawn targets")


# SETTINGS flags: (function, parameters)
setting_to_func = {
    "formatModifiedSpawnTargets": (format_targets, [False]),
    "formatAllSpawnTargets": (format_targets, [True])
}


# Read SETTINGS flags and format entities file
# also make sure we don't miss any variables
def format_entities_file(filename, settings):
    for line in settings.splitlines():
        #print(line)
        if line in setting_to_func:
            func, args = setting_to_func[line]
            func(filename, *args)
        # Handle assignments written before REPLACE ENCOUNTERs
        if line.count('=') == 1:
            var = line.split("=")
            add_variable(var[0].strip(), var[1].strip())


# cringe
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# Apply @ prefixes and macro names
def apply_prefixes(event_string):
    output_str = ""
    items = variables.items()
    sorted_variables = sorted(items, key=lambda x: len(x[0]), reverse=True)
    #print(sorted_variables)
    if "@" in event_string:
        segments = event_string.split("@")
        for i, seg in enumerate(segments):
            for var, val in sorted_variables:
                val = format_args([val], 1)[0]
                if ((seg.endswith(f'{var}') and i != len(segments)-1)
                        or (seg.startswith(f'{var}') and i != 0)):
                    seg = seg.replace(f'{var}', str(val))
                if not (is_number(str(val)) or val in ["true", "false"]):
                    debug_print(f'added "" for {var} = {val}')
                    val = f'"{val}"'
                seg = seg.replace(f'"{var}"', str(val))
            output_str += seg
    else:
        for var, val in sorted_variables:
            if not (is_number(str(val)) or val in ["true", "false"]):
                debug_print(f'added "" for {var} = {val}')
                val = f'"{val}"'
            event_string = event_string.replace(f'"{var}"', str(val))
        output_str = event_string
    #print(output_str)
    return output_str


# The Big One:tm:
def compile_EBL(ebl_file):
    tic = time.time()
    segments = generate_EBL_segments(ebl_file, format_file=True)
    encounters = map(ebl.parse, segments)
    output_file = open("test_encounter.txt", "w")
    for encounter in list(encounters):
        output_str = ""
        item_index = 0
        events = create_events(encounter)
        if events is None:
            continue
        for event in events:
            if isinstance(event, EBL_Assignment):
                add_variable(event.name, event.value)
                continue

            event_string = apply_prefixes(str(event))

            output_str += (f"item[{item_index}]" + " = {\n" +
                           indent(event_string, "\t") + "}\n")
            item_index += 1
        output_file.write(output_str)
    output_file.close()
    print(f"Done compiling in {time.time()-tic:.1f} seconds")


compile_EBL("Test EBL Files/test_EBL_3.txt")