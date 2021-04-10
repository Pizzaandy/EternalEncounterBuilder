import eternalevents as ee
import EBL_grammar as EBL
from textwrap import indent
from dataclasses import dataclass
import re
import time

ebl = EBL.NodeVisitor()
ebl.grammar = EBL.grammar

variables = {}
@dataclass
class EBL_Assignment():
    name: str
    value: str
    
def add_variable(varname, value):
    variables[varname] = value
    print(f"Added variable {varname} = {value}")

waitFor_keywords = {
    "all": "ENCOUNTER_LOGICAL_OP_AND",
    "any": "ENCOUNTER_LOGICAL_OP_OR"
}

encounter_spawn_names = [
    "ANY",
    "GENERIC",
    "ARACHNOTRON",
    "BARON",
    "CACODEMON",
    "CHAINGUN_SOLDIER",
    "CUEBALL",
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
    "TENTACLE",
    "TYRANT",
    "WHIPLASH",
    "ZOMBIE_MAKYR",
    "ZOMBIE_TIER_1",
    "ZOMBIE_TIER_3",
    "LOST_SOUL",
    "SPECTRE",
    "CARCASS",
    "ARCHVILE",
    "BUFF_POD",
    "SPIRIT",
    "TURRET",
    "SUPER_TENTACLE"
]

# ok fine, PascalCase too
encounter_spawn_aliases = {
    "Any": "ANY",
    "Generic": "GENERIC",
    "Arachnotron": "ARACHNOTRON",
    "Baron": "BARON",
    "Cacodemon": "CACODEMON",
    "ChaingunSoldier": "CHAINGUN_SOLDIER",
    "Cueball": "CUEBALL",
    "CyberMancubus": "CYBER_MANCUBUS",
    "DoomHunter": "DOOM_HUNTER",
    "DreadKnight": "DREAD_KNIGHT",
    "Gargoyle": "GARGOYLE",
    "HellKnight": "HELL_KNIGHT",
    "HellSoldier": "HELL_SOLDIER",
    "Imp": "IMP",
    "Mancubus": "MANCUBUS",
    "Marauder": "MARAUDER",
    "PainElemental": "PAIN_ELEMENTAL",
    "Pinky": "PINKY",
    "Prowler": "PROWLER",
    "Revenant": "REVENANT",
    "ShotgunSoldier": "SHOTGUN_SOLDIER",
    "Tentacle": "TENTACLE",
    "Tyrant": "TYRANT",
    "Whiplash": "WHIPLASH",
    "ZombieMakyr": "ZOMBIE_MAKYR",
    "ZombieTier1": "ZOMBIE_TIER_1",
    "ZombieTier3": "ZOMBIE_TIER_3",
    "LostSoul": "LOST_SOUL",
    "Spectre": "SPECTRE",
    "Carcass": "CARCASS",
    "Archvile": "ARCHVILE",
    "BuffPod": "BUFF_POD",
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
# and handles SETTINGS flags
def generate_EBL_segments(filename, format_file = True):
    with open(filename) as fp:
        segments = re.split(r"^REPLACE ENCOUNTER", fp.read(), flags=re.MULTILINE)
    start_index = 0
    if segments[0].startswith("SETTINGS"):
        print("SETTINGS found")
        start_index = 1
        if format_file: 
            format_entities_file(filename, segments[0])
        else:
            print("Settings Ignored lol")
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
            #print("waitForBlock found!")
            #print(data["args"])
            length = len([ev for ev in data["args"] if not "variable" in ev[0]])
           # print(length)
            waitevent =  {
                "event":"waitMulitpleConditions",
                "args":[length, waitFor_keywords[data["keyword"]], "false"]
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

# Format entities file according to SETTINGS flags
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
            
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# The Big One:tm:
def compile_EBL(filename):    
    tic = time.time()
    segments = generate_EBL_segments(filename, format_file = True)
    encounters = map(ebl.parse, segments)
    output_file = open("test_encounter.txt", "w")
    for encounter in list(encounters):
        output_str = ""
        item_index = 0
        events = create_events(encounter)
        #print(events)
        if events is None:
            continue
        for event in events:
            if isinstance(event, EBL_Assignment):
                add_variable(event.name, event.value)
                continue
            event_string = str(event)
            for var, val in variables.items():
                #print(var)
                replace_str = (f'"{var}"' if is_number(str(val))
                               or var in ["NULL","true","false"] else var)
                event_string = event_string.replace(replace_str, str(val))
                #print(event_string)
                
            output_str += (f"item[{item_index}]" + " = {\n" +
                           indent(event_string,"\t") + "}\n")
            item_index += 1
        output_file.write(output_str)
    output_file.close()
    print(f"Done compiling in {time.time()-tic:.1f} seconds")
   
compile_EBL("test_EBL_2.txt")
#print(variables)