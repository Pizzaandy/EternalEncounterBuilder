import entity_templates
import eternalevents
from pathlib import Path
import json
import hashlib
from eternalevents import is_number_or_keyword
from eternaltools import oodle, entity_tools
from entity_templates import EntityTemplate
import entities_parser as parser
import ebl_grammar
import compiler_constants as cc
from compiler_constants import ANIM_OFFSETS_FILE
from copy import deepcopy
import datetime
import os
import pyperclip3

from textwrap import indent
from dataclasses import dataclass
from typing import List, Union, Tuple
import re
import time
import pprint

from ebl_grammar import EblTypeError
from entities_parser import EntitiesSyntaxError


run_count = 0
horde_index = 0


def reset_all():
    global run_count
    run_count += 1
    global ebl_cache
    global new_ebl_cache
    global variables
    global decorator_changes
    global decorator_entity_names
    global mod_entity_idx
    global Settings
    global spawn_target_hashes
    global horde_index
    mod_entity_idx = 0
    horde_index = 0
    variables = {}
    ebl_cache = {}
    new_ebl_cache = {}
    decorator_changes = []
    decorator_entity_names = {}
    spawn_target_hashes = []
    Settings = {}
    ignored_entities = []


def cache_result():
    global ebl_cache
    global new_ebl_cache

    def decorator(func):
        def new_func(*args):
            keystr = (
                str(args)
                + func.__name__
                + str(variables)
                + str(ignored_entity_names)
                + str(Settings)
            )
            key = hashlib.md5(keystr.encode()).hexdigest()
            try:
                test_keys = ebl_cache.keys()
            except NameError:
                return func(*args)
            if key in ebl_cache:
                # print("found cached result!")
                new_ebl_cache[key] = ebl_cache[key]
                return ebl_cache[key]
            result = func(*args)
            new_ebl_cache[key] = result
            return result

        return new_func

    return decorator


# EBL = Eternal Builder Language, describes changes to .entities files
ebl = ebl_grammar.NodeVisitor()
ebl.grammar = ebl_grammar.grammar
blacklist_entities = []

variables = {}
Settings = {}
spawn_target_hashes = []
templates = entity_templates.BUILTIN_TEMPLATES
decorator_changes = []
decorator_entity_names = {}
ignored_entities = []
ignored_entity_names = []
debug_vars = False

worker_object = None
do_verbose_logging = True


def ui_log(s):
    try:
        worker_object.worker_log(str(s))
    except Exception:
        print(s)


def ui_log_verbose(s):
    if do_verbose_logging:
        ui_log(s)


def debug_print(string):
    if debug_vars:
        ui_log(string)


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


def parse_event(event: str) -> Tuple[str, list]:
    event, _ = event.replace("\n", "").split(")", 1)
    name, args = event.split("(", 1)
    args = re.findall(r"([^(,)]+)(?!.*\()", args)
    args = [arg.strip() for arg in args]
    return name, args


# these are not technically variables, but go off I guess
def add_variable(varname, value):
    if varname in variables:
        debug_print(f"Modified macro {varname} = {value}")
    else:
        ui_log_verbose(f"Added macro {varname} = {value}")

    value = str(value)
    ignore_quotes = "+" not in str(value)
    variables[varname] = concat_strings(format_args(value), ignore_quotes)
    debug_print(
        f"""Concatenated strings in assignment {varname} = {variables[varname]}"""
    )
    return True


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


def get_event_args(event: eternalevents.EternalEvent):
    return [arg for arg in event.__dict__.values()]


LINE_PATTERN = re.compile(r"//(.*)(?=[\r\n]+)")
MULTILINE_PATTERN = re.compile(r"/\*.*?\*/", flags=re.DOTALL)


def strip_comments(s):
    s += "\n"
    s = re.sub(MULTILINE_PATTERN, "", s)
    return re.sub(LINE_PATTERN, "", s).strip()


def split_ebl_at_headers(filename) -> list:
    """
    Splits an EBL file into segments at headers
    returns a list of tuples with EBL code and encounter name
    Also strips comments!
    :param filename:
    :return:
    """
    with open(filename) as fp:
        segments = re.split(
            cc.EBL_HEADERS_REGEX, strip_comments(fp.read()), flags=re.MULTILINE
        )

    if segments[0].startswith("SETTINGS"):
        ui_log("SETTINGS found!")
        global Settings
        for line in segments[0].splitlines():
            if line == "SETTINGS":
                continue
            line = line.strip()
            if line:
                if "=" not in line:
                    continue
                setting, value = line.split("=", 1)
                Settings[setting.strip()] = value.strip()
                ui_log(line)
    else:
        ui_log("No SETTINGS found")

    res = []
    # yield tuples containing name, header command, and body text
    for cmd, body in zip(*[iter(segments[1:])] * 2):
        cmd = cmd.strip()
        name = body.split("\n")[0].strip()
        if not name:
            if cmd == "INIT":
                name = None
            else:
                raise EblTypeError(f"No entity name specified in header {cmd}")
        body = "\n".join(body.split("\n")[1:])
        res += [(name, (cmd, body))]

    modified_segments = res.copy()
    for key, val in res:
        if val[0] == "IMPORT":
            try:
                with open(key) as fp:
                    pass
            except FileNotFoundError:
                ui_log(f"WARNING: Imported file {key} not found!")
                return []
            modified_segments = split_ebl_at_headers(key) + modified_segments
            ui_log(f"Imported {key}")
    res = modified_segments

    return res


def format_args(args, arg_count=-1) -> Union[list, str]:
    """Handles variables and fills in missing arguments"""
    args = args if isinstance(args, list) else [args]
    for idx, arg in enumerate(args):
        if isinstance(arg, str):
            args[idx] = ""
            arg = arg.replace(cc.SPACE_CHAR, cc.SPACE_CHAR + " ").split()
            for word in arg:
                if word.endswith(cc.SPACE_CHAR):
                    suffix = ""
                else:
                    suffix = " "
                old_word = word
                word = word.replace(cc.SPACE_CHAR, "")
                if word in cc.ENCOUNTER_SPAWN_NAMES:
                    args[idx] += "ENCOUNTER_SPAWN_" + word + suffix
                elif word in cc.ENCOUNTER_SPAWN_ALIASES:
                    args[idx] += (
                        "ENCOUNTER_SPAWN_" + cc.ENCOUNTER_SPAWN_ALIASES[word] + suffix
                    )
                else:
                    args[idx] += old_word + suffix
            args[idx] = args[idx].strip()
        if arg is None:
            args[idx] = ""
    while len(args) < arg_count:
        args += [""]
    return args[0] if arg_count == -1 else args


# TODO: use the structural pattern matching feature when it comes out lol
def create_events(data) -> list:
    """
    Consumes parsed EBL and generates a list of EternalEvents
    we do a little recursion
    """
    if isinstance(data, list):
        output = []
        for item in data:
            event = create_events(item)
            output += event
        return output

    if isinstance(data, dict):
        if "variable" in data:
            return [Assignment(data["variable"], data["value"])]

        if "function" in data:
            return [EntityEdit(data["object"], data["function"], data["value"])]

        if data["event"] == "waitForBlock":
            event_count = 0
            for sublist in data["args"]:
                for _ in sublist[0]["args"]:
                    event_count += 1
            waitevent = {
                "event": "waitMulitpleConditions",
                "args": [event_count, cc.WAITFOR_KEYWORDS[data["keyword"]], "false"],
            }
            return create_events([waitevent] + data["args"])

        if data["event"] == "waitFor":
            return create_events(data["args"])

        if data["event"] in eternalevents.ebl_to_event:
            cls_name, arg_count = eternalevents.ebl_to_event[data["event"]]
            event_cls = str_to_class(cls_name)
        else:
            raise EblTypeError(f"""Undefined event {data["event"]}!""")

        # data is event
        # Assume nested argument list means a list of parameters
        args_list = data["args"]
        if any(isinstance(item, list) for item in args_list):
            result = []
            for args in args_list:
                if "decorator" in data and data["decorator"]:
                    args = add_decorator_command(data["decorator"], event_cls(*args))
                args = format_args(args, arg_count)
                result += [event_cls(*args)]
            return result
        else:
            if "decorator" in data and data["decorator"]:
                args_list = add_decorator_command(
                    data["decorator"], event_cls(*args_list)
                )
            args_list = format_args(args_list, arg_count)
            event_cls = event_cls(*args_list)
            return [event_cls]

    return data


mod_entity_idx = 0


def add_decorator_command(
    decorator: str, event_cls: eternalevents.EternalEvent
) -> list:
    """
    Adds a decorator command from an event
    returns a list of modified args based on the event
    :param decorator:
    :param event_cls:
    :return:
    """
    cmds = decorator
    modified_args = get_event_args(event_cls)
    original_event = deepcopy(event_cls)
    global decorator_changes
    global mod_entity_idx

    cmd_list = [cmd.strip() for cmd in cmds.split(";")]
    for cmd in cmd_list:
        cmd_name, _ = cmd.split(" ", 1) if " " in cmd else (cmd.strip(), "")
        is_possessed = False
        # Decide what to do based on event type, then decorator type
        if type(event_cls) in eternalevents.SPAWN_TARGET_EVENTS:
            if type(event_cls) == eternalevents.SpawnSingleAI:
                spawn_type = format_args(event_cls.spawnType)
            elif type(event_cls) == eternalevents.SpawnArchvile:
                spawn_type = "ENCOUNTER_SPAWN_ARCHVILE"
            elif type(event_cls) == eternalevents.SpawnPossessedAI:
                spawn_type = format_args(event_cls.ai_spawnType)
                is_possessed = True
            spawn_type = spawn_type.removeprefix("ENCOUNTER_SPAWN_")

            if cmd_name == "anim":
                old_spawntarget = concat_strings(
                    original_event.spawnTarget, is_expression=True
                )
                new_entity_name = f"eblmod_spawn_target_{mod_entity_idx}"
                event_cls.spawnTarget = new_entity_name
                if is_possessed:
                    event_cls.ai_spawnTarget = new_entity_name
                decorator_changes.append(
                    (
                        old_spawntarget,
                        cmd + " " + spawn_type,
                        new_entity_name,
                    )
                )
            elif cmd_name == "portal":
                pass
        else:
            ui_log(f"WARNING: event {type(event_cls).__name__} has no associated tags")
            return modified_args

    mod_entity_idx += 1
    modified_args = get_event_args(event_cls)
    return modified_args


def apply_decorator_command(
    entity: str,
    cmd: str,
    new_entity_name: str,
) -> Tuple[str, bool, bool]:
    """
    Returns a copy of the given entity with decorator commands applied
    :param entity:
    :param cmd:
    :param new_entity_name:
    :return:
    """

    def sign(num):
        return 1 if num > 0 else -1

    do_not_modify = False
    delete_original = False

    if new_entity_name in decorator_entity_names:
        delete_original = True
        entity = decorator_entity_names[new_entity_name]
        # print(f"existing decorator entity found: {new_entity_name}")

    parsed_entity = parser.parse_entity(entity)
    entitydef = ""
    for key in parsed_entity:
        if key.startswith("entityDef"):
            entitydef = key
    ui_log_verbose(f"Applying '{cmd}' to '{entitydef.removeprefix('entityDef ')}'")

    # original_name = entitydef.removeprefix("entityDef ")

    if not entitydef:
        raise EntitiesSyntaxError("No entityDef component!")

    if " " not in cmd:
        cmd_name = cmd.strip()
        args = []
    else:
        cmd_name, args = cmd.split(" ", 1)
        args = [
            concat_strings(arg.strip(), is_expression=True)
            for arg in args.split()
            if arg.strip()
        ]

    if cmd_name == "anim":
        anim_name, spawn_type = args
        demon_name = cc.NAME_TO_ANIMWEB[spawn_type]
        traversal_s = (
            "traversals" if spawn_type in cc.TRAVERSALS_ENEMIES else "traversal"
        )
        traversal_path = (
            f"animweb/characters/monsters/{demon_name}/{traversal_s}/" + anim_name
        )
        if demon_name == "cacodemon" or demon_name == "painelemental":
            traversal_path = (
                f"animweb/characters/monsters/{demon_name}/spawn/" + anim_name
            )

        if anim_name not in cc.ANIM_TO_OFFSET:
            traversal_path = f"animweb/characters/monsters/{demon_name}/" + anim_name

        parsed_entity[entitydef]["edit"]["spawnEditable"]["spawnAnim"] = traversal_path
        parsed_entity[entitydef]["edit"]["spawnEditable"][
            "aiStateOverride"
        ] = "AIOVERRIDE_PLAY_ENTRANCE_ANIMATION"
        try:
            x_off, y_off = cc.ANIM_TO_OFFSET[anim_name]
        except KeyError:
            ui_log(f"WARNING: anim {anim_name} not recognized")
        x_off, y_off = cc.ANIM_TO_OFFSET.get(anim_name, (0, 0))
        x_off, y_off = -x_off, -y_off
        x, y, z = (
            parsed_entity[entitydef]["edit"]["spawnPosition"].get("x", 0),
            parsed_entity[entitydef]["edit"]["spawnPosition"].get("y", 0),
            parsed_entity[entitydef]["edit"]["spawnPosition"].get("z", 0),
        )
        try:
            forward_cos = parsed_entity[entitydef]["edit"]["spawnOrientation"]["mat"][
                "mat[0]"
            ]["x"]
            forward_sin = parsed_entity[entitydef]["edit"]["spawnOrientation"]["mat"][
                "mat[0]"
            ]["y"]
        except KeyError:
            forward_cos = 1
            forward_sin = 0
        try:
            demon_width, ledge_offset = cc.NAME_TO_HORIZONTAL_OFFSET[spawn_type]
        except TypeError:
            demon_width = cc.NAME_TO_HORIZONTAL_OFFSET[spawn_type]
            ledge_offset = 0
        if "ledge" in anim_name:
            demon_width += ledge_offset
        dx = forward_cos * sign(x_off) * (abs(x_off) + demon_width)
        dy = y_off
        dz = forward_sin * sign(x_off) * (abs(x_off) + demon_width)
        offset_scalar_x = 1 / 100
        offset_scalar_y = 1 / 100
        # Z is up
        parsed_entity[entitydef]["edit"]["spawnPosition"]["x"] = x + (
            dx * offset_scalar_x
        )
        parsed_entity[entitydef]["edit"]["spawnPosition"]["y"] = y + (
            dz * offset_scalar_x
        )
        parsed_entity[entitydef]["edit"]["spawnPosition"]["z"] = z + (
            dy * offset_scalar_y
        )
        # change name
        parsed_entity[f"entityDef {new_entity_name}"] = parsed_entity.pop(entitydef)
    else:
        ui_log(f"ERROR: Tag {cmd_name} is not recognized")

    if not delete_original:
        decorator_entity_names[new_entity_name] = entity_tools.generate_entity(
            parsed_entity
        )

    return entity_tools.generate_entity(parsed_entity), do_not_modify, delete_original


def all_idai2s(*, dlc_level=2) -> List[str]:
    res = ""

    with open("idAI2_base.txt", "r") as fp_base:
        ui_log("Added base game idAI2s")
        res += fp_base.read() + "\n\n"

    if dlc_level >= 2:
        with open("idAI2_dlc2.txt") as fp_dlc2:
            res += fp_dlc2.read() + "\n\n"
        ui_log("Added DLC2 idAI2s")

    if dlc_level >= 1:
        with open("idAI2_dlc1.txt") as fp_dlc1:
            res += fp_dlc1.read() + "\n\n"
        ui_log("Added DLC1 idAI2s")

    segments = re.split(r"^entity {", res, flags=re.MULTILINE)
    result = [segments[0]] + [
        "entity {" + re.sub(r"//.*$", "", segment) for segment in segments[1:]
    ]

    return result


def concat_strings(s, is_expression=False):
    """Warning: hacky
    Manipulates string by:
    a) replacing variable names with corresponding values
    b) handling the + operator and concatenating strings
    :param s:
    :param is_expression: whether all of s must be matched if there is no + in string
    :return modified_string:
    """

    def rreplace(_s: str, old, new, occurrence=0):
        li = _s.rsplit(old, occurrence)
        return new.join(li)

    items = variables.items()
    sorted_variables = sorted(items, key=lambda x: len(x[0]), reverse=True)

    if "+" not in s:
        for var, val in sorted_variables:
            if is_expression:  # only replace entire expression if matched
                if var == s.strip():
                    s = s.replace(f"{var}", str(val))
                    break
            else:  # replace all instances of matches in quotes
                if not is_number_or_keyword(val):
                    val = f'"{val}"'
                s = s.replace(f'"{var}"', str(val))

        return s.replace(cc.SPACE_CHAR, " ").replace(cc.LITERAL_CHAR, "")

    result = ""
    segments = s.split("+")
    for idx, seg in enumerate(segments):
        seg = seg.lstrip() if idx > 0 else seg
        seg = seg.rstrip() if idx < len(segments) - 1 else seg

        potential_matches = re.findall(r"[$^\w]+", seg)
        first_match = potential_matches[0] if idx > 0 else None
        last_match = potential_matches[-1] if idx < len(segments) - 1 else None

        for j, match in enumerate([first_match, last_match]):
            if not match:
                continue
            for var, val in sorted_variables:
                if len(var) < len(match.strip()):
                    continue
                if match.strip() == var:
                    val = format_args(val)
                    if j == 0:
                        seg = seg.replace(match, str(val), 1)
                    else:
                        seg = rreplace(seg, match, str(val), 1)
                    debug_print(
                        f"matched variable '{match}' and substituted '{str(val)}'"
                    )
                    debug_print(f"seg is now '{seg}'")

        result += seg
    return result.replace(cc.SPACE_CHAR, " ").replace(cc.LITERAL_CHAR, "")


@cache_result()
def parse_ebl(s):
    # print(s)

    return ebl.parse(s + "\n")


def compile_ebl(s, vars_only=False) -> str:
    """
    Compiles EBL to encounterComponent events
    :param s:
    :param vars_only:
    :return events:
    """
    event_lists = parse_ebl(s)
    events = []
    if any(isinstance(item, list) for item in event_lists):
        for event_list in event_lists:
            new_events = create_events(event_list)
            if new_events is None:
                continue
            events.append(new_events)
    else:
        events.append(create_events(event_lists))

    rendered_events = []
    for event_list in events:
        item_index = 0
        result = f"num = {len(event_list)};\n"
        for event in event_list:
            if isinstance(event, Assignment):
                add_variable(event.name, event.value)
                continue
            if vars_only:
                continue
            event_string = concat_strings(str(event))
            if isinstance(event_string, list):
                print(f"{event_string=}")
            result += (
                f"item[{item_index}]" + " = {\n" + indent(event_string, "\t") + "}\n"
            )
            item_index += 1
        rendered_events.append(result)
    return rendered_events


@cache_result()
def replace_encounter(encounter: str, events: Union[list, str], dlc_level: int) -> str:
    """
    Modifies encounter entity with list of EternalEvents
    :param encounter:
    :param events:
    :param dlc_level:
    :return new_entity_string:
    """
    entity = parser.parse_entity(encounter)
    entity_events = [
        "{\n" + indent(events_list, "\t") + "}\n" for events_list in events
    ]
    entitydef = ""
    for key in entity:
        if key.startswith("entityDef"):
            entitydef = key
    if not entitydef:
        raise EntitiesSyntaxError("No entityDef component!")
    for idx, script in enumerate(entity_events):
        try:
            dic = entity
            for key in [
                entitydef,
                "edit",
                "encounterComponent",
                "entityEvents",
                f"item[{idx}]",
            ]:
                dic = dic.setdefault(key, {})
            dic["events"] = script
            dic["entity"] = entitydef.removeprefix("entityDef ")
            entity[entitydef]["edit"]["aiTypeDefAssignments"] = cc.ACTORPOPULATION[
                dlc_level
            ]
        except KeyError:
            ui_log(f"ERROR: Unable to replace Script {idx} for encounter")
            ui_log(entity[entitydef]["edit"])
    result = entity_tools.generate_entity(entity)
    return result


@cache_result()
def edit_entity_fields(name: str, base_entity: str, edits: str) -> str:
    """
    Edits specific fields in the given entity
    :param name:
    :param base_entity:
    :param edits:
    :return edited_entity:
    """
    entity = parser.parse_entity(base_entity)
    entitydef = ""
    for key in entity:
        if key.startswith("entityDef"):
            entitydef = f"entityDef {name}"
            entity[entitydef] = entity.pop(key)
            break
    if not entitydef:
        # This should never happen when modifying a base entities file
        raise EntitiesSyntaxError("No entityDef component!")

    entity_edits = parse_ebl(edits)
    for entity_edit in create_events(entity_edits):
        # assignment or function
        if type(entity_edit) is EntityEdit:
            function_name = entity_edit.func
            values = entity_edit.value
            path = entity_edit.object
        elif type(entity_edit) is Assignment:
            function_name = "set"
            values = [[entity_edit.value]]
            # ui_log(values)
            path = entity_edit.name
        else:
            raise EblTypeError(
                "All lines under MODIFY header must be EntityEdits or Assignments"
            )

        keys = path.split("/")
        unique_key_index = 0

        for value in values:
            dic = entity[entitydef]
            if function_name == "add":
                if len(value) != 1:
                    raise EblTypeError(
                        f'Edit function "{function_name}" takes one argument'
                    )
                for key in keys:
                    dic = dic.setdefault(key, {})
                value[0] = concat_strings(value[0], is_expression=True)
                dic[f"__unique_{unique_key_index}__"] = value[0]
                unique_key_index += 1

            if function_name == "set":
                if len(value) != 1:
                    raise EblTypeError(
                        f'Edit function "{function_name}" takes one argument'
                    )
                for key in keys[:-1]:
                    dic = dic.setdefault(key, {})
                if isinstance(value[0], str):
                    modded_val, _ = EntityTemplate.modify_args(None, [value[0]])
                    value[0] = modded_val[0]
                    value[0] = concat_strings(value[0], is_expression=True)
                    try:
                        value[0] = float(value[0])
                    except ValueError:
                        pass
                    if value[0] in ["true", "false"]:
                        value[0] = True if value[0] == "true" else False
                    if value[0] == "NULL":
                        value[0] = None
                try:
                    dic[concat_strings(keys[-1])] = value[0]
                except TypeError:
                    raise EblTypeError(
                        f"value {concat_strings(keys[-1])} does not exist in entity {name}"
                    )

            if function_name == "pop":
                if len(value) != 1:
                    raise EblTypeError(
                        f'Edit function "{function_name}" takes one argument'
                    )
                value = concat_strings(value[0], is_expression=True)
                for key in keys:
                    if key == "":
                        continue
                    dic = dic[key]
                for key, val in dic.items():
                    debug_print(f"Checking value '{value}' against '{val}'")
                    if val == value:
                        debug_print("Matched!")
                        dic.pop(key)
                        break

            if function_name == "delete":
                if len(value) != 1:
                    raise EblTypeError(
                        f'Edit function "{function_name}" takes one argument'
                    )
                value = concat_strings(value[0], is_expression=True)
                for key in keys:
                    if key == "":
                        continue
                    dic = dic[key]
                for key, val in dic.items():
                    debug_print(f"Checking key '{value}' against '{key}'")
                    if key == value:
                        debug_print("Matched!")
                        dic.pop(key)
                        break
    result = entity_tools.generate_entity(entity)
    result += "\n"
    return result


@cache_result()
def format_spawn_target(
    spawn_target: str, entitydefs: List[str], current_horde_index: int
) -> Tuple[str, int]:
    """
    Adds custom idAI2s and applies changes to the given spawn target
    :param spawn_target:
    :param entitydefs:
    :return modified_spawn_target:
    """
    try:
        entity = parser.parse_entity(spawn_target)
    except Exception as e:
        ui_log("ERROR: couldn't parse spawn target")
        ui_log(spawn_target)
        return spawn_target, current_horde_index
    entitydef = ""
    # name = ""
    for idx, key in enumerate(entity):
        if key == "layers":
            entity.pop("layers")
            break
        if idx > 1:
            break
    for key in entity:
        if key.startswith("entityDef"):
            entitydef = key
            # name = entitydef.replace("entityDef", "").strip()
    if not entitydef:
        ui_log("ERROR: no entityDef component!")
        return spawn_target, current_horde_index

    entity_name = entitydef.removeprefix("entityDef ")
    if entity_name in ignored_entity_names:
        return entity_tools.generate_entity(entity), current_horde_index

    if entity_name.startswith("custom_"):
        ui_log(f"Skipping custom spawn target {entity_name}")
        return entity_tools.generate_entity(entity), current_horde_index

    try:
        spawn_editable = entity[entitydef]["edit"]["spawnEditable"]
    except KeyError:
        pass
    else:
        no_spawnanim = not spawn_editable["spawnAnim"]
        no_traversal_override = not spawn_editable["initialTargetOverride"]
        # no_add_targets = spawn_editable["additionalTargets"]["num"] == 0
        if no_spawnanim and no_traversal_override:
            entity[entitydef]["edit"]["spawnEditable"][
                "aiStateOverride"
            ] = "AIOVERRIDE_TELEPORT"

        if not entity_name.startswith("bounty"):
            try:
                entity[entitydef]["edit"]["spawnConditions"]["reuseDelaySec"] = 3
                entity[entitydef]["edit"]["spawnConditions"]["minDistance"] = int(
                    Settings["spawn_min_distance"]
                )
                entity[entitydef]["edit"]["spawnConditions"][
                    "playerToTest"
                ] = "PLAYER_SP"
            except KeyError:
                pass

            try:
                entity[entitydef]["edit"]["spawnConditions"]["maxDistance"] = int(
                    Settings["spawn_max_distance"]
                )
                entity[entitydef]["edit"]["spawnConditions"][
                    "playerToTest"
                ] = "PLAYER_SP"
            except KeyError:
                pass

    listed_targets = list_targets(entitydefs)
    targets = "{\n" + indent(listed_targets, "\t") + "}\n"
    entity[entitydef]["edit"]["targets"] = targets

    listed_entitydefs = list_entitydefs(entitydefs)
    entitydefs = "{\n" + indent(listed_entitydefs, "\t") + "}\n"
    entity[entitydef]["edit"]["entityDefs"] = entitydefs

    global horde_index
    entity_horde = {}
    if (
        "add_horde_bounty_targets" in Settings
        and 'class = "idTarget_Spawn_Parent";' not in spawn_target
    ):
        entity_horde = deepcopy(entity)
        entitydefs = cc.HORDE_ENTITYDEFS_NO_AIR
        if (
            "add_ground_spawns_only" in Settings
            and Settings["add_ground_spawns_only"] == "true"
        ):
            if "//#EBL_IS_AIR_TARGET" not in spawn_target:
                entitydefs = cc.HORDE_ENTITYDEFS_NO_AIR

        # entity_horde[entitydef]["edit"]["targetSpawnParent"] = "ai_encounter_spawn_group_parent_bounty_base"

        current_horde_index += 1

        listed_targets = list_targets(entitydefs)
        targets = "{\n" + indent(listed_targets, "\t") + "}\n"
        entity_horde[entitydef]["edit"]["targets"] = targets

        listed_entitydefs = list_entitydefs(entitydefs)
        entitydefs = "{\n" + indent(listed_entitydefs, "\t") + "}\n"
        entity_horde[entitydef]["edit"]["entityDefs"] = entitydefs
        entity_horde[f"entityDef bounty{horde_index}"] = entity_horde[entitydef]
        del entity_horde[entitydef]

    entity_coin = {}
    if (
        "add_coin_targets" in Settings
        and 'class = "idTarget_Spawn_Parent";' not in spawn_target
    ):
        entity_coin = deepcopy(entity)
        entitydefs = cc.HORDE_COIN
        if (
            "add_ground_spawns_only" in Settings
            and Settings["add_ground_spawns_only"] == "true"
        ):
            if "//#EBL_IS_AIR_TARGET" not in spawn_target:
                entitydefs = cc.HORDE_COIN
        listed_targets = list_targets(entitydefs)
        targets = "{\n" + indent(listed_targets, "\t") + "}\n"
        entity_coin[entitydef]["edit"]["targets"] = targets

        listed_entitydefs = list_entitydefs(entitydefs)
        entitydefs = "{\n" + indent(listed_entitydefs, "\t") + "}\n"
        entity_coin[entitydef]["edit"]["entityDefs"] = entitydefs
        entity_coin[f"entityDef coin{horde_index}"] = entity_coin[entitydef]
        del entity_coin[entitydef]

    result = entity_tools.generate_entity(entity)
    result_horde = entity_tools.generate_entity(entity_horde) if entity_horde else ""
    result_coin = entity_tools.generate_entity(entity_coin) if entity_coin else ""
    return result + result_horde + result_coin, current_horde_index


def apply_entity_changes(name, entity: str, params: tuple[str, str], dlc_level) -> str:
    """
    Applies changes to entity with given parameters
    :param name:
    :param entity:
    :param params: (command, body_text)
    :param dlc_level:
    :return modified_entity:
    """
    cmd, text = params
    if cmd == "REPLACE ENCOUNTER":
        ui_log(f"Replaced encounter {name}")
        return replace_encounter(entity, text, dlc_level)
    elif cmd == "REPLACE":
        ui_log(f"Replaced {name}")
        return text
    elif cmd == "REMOVE":
        ui_log(f"Removed {name}")
        return ""
    elif cmd == "MODIFY COPY":
        try:
            old_name, as_keyword, new_name = name.strip().split()
            if as_keyword != "AS":
                raise ValueError("no as keyword")
        except ValueError:
            ui_log(
                "ERROR: MODIFY COPY requires two names, e.g. MODIFY COPY old_name AS new_name"
            )
            return entity
        ui_log(f"Created copy of {old_name} as {new_name}")
        global entities
        entities.append(edit_entity_fields(new_name, entity, text))
        return entity
    elif cmd == "MODIFY":
        ui_log(f"Modified {name}")
        return edit_entity_fields(name, entity, text)
    else:
        raise EblTypeError(f"Unknown command {cmd}")


entities = []
added_entities = []


# Apply all changes in ebl_file to base_file and output to modded_file
def apply_ebl(
    ebl_file,
    base_file,
    output_folder,
    show_checkpoints=False,
    compress_file=True,
    show_spawn_targets=False,
    generate_traversals=True,
    dlc_level=2,
    output_name_override="",
    do_punctuation_check=False,
):
    """
    Applies all changes in an EBL file to a copy of a vanilla entities file
    :param ebl_file: EBL file describing all file changes
    :param base_file: The vanilla entities file to modify
    :param output_folder: The output folder
    :param show_checkpoints: Whether to log a list of checkpoints
    :param compress_file: Whether the output file should be compressed
    :param show_spawn_targets: Whether visual spawn target markers should be added to the file
    :param generate_traversals: Whether traversal info should be added to the file
    :param dlc_level:
    :return success:
    """
    tic = time.time()
    total_count = 0
    modified_count = 0
    added_count = 0

    global ebl_cache
    global new_ebl_cache
    reset_all()
    global horde_index
    horde_index = 0
    new_ebl_cache["__PREVIOUS_FILES__"] = (base_file, ebl_file, output_folder)

    CACHE_FILE = f"ebl_cache/{Path(ebl_file).stem}_cache.txt"
    try:
        with open(CACHE_FILE, "r") as fp:
            ebl_cache = json.load(fp)
    except (json.JSONDecodeError, FileNotFoundError):
        ui_log(f"Failed to read {CACHE_FILE}, creating new")

    oodle.decompress_entities(base_file)
    try:
        with open(ANIM_OFFSETS_FILE, "r") as fp:
            cc.NAME_TO_HORIZONTAL_OFFSET = json.load(fp)
    except json.JSONDecodeError:
        ui_log(f"WARNING: Failed to decode {ANIM_OFFSETS_FILE}")
    # if dlc_level >= 2:
    #     entitydefs += cc.DLC2_ENTITYDEFS
    # if dlc_level >= 1:
    #     entitydefs += cc.DLC1_ENTITYDEFS

    # 1) Get file deltas
    deltas = split_ebl_at_headers(ebl_file) if ebl_file else []

    # 2) Get vanilla entities from base file
    global entities
    global added_entities
    entities = []
    added_entities = []
    entities = list(parser.generate_entity_segments(base_file, version_numbers=True))
    entities = entities[0:3] + all_idai2s(dlc_level=dlc_level) + entities[3:]

    try:
        base_entitydefs_list = (
            cc.BASE_ENTITYDEFS_NO_AIR_DEMONS
            if Settings["add_ground_spawns_only"] == "true"
            else cc.BASE_ENTITYDEFS
        )
    except KeyError:
        base_entitydefs_list = cc.BASE_ENTITYDEFS
    entitydefs = base_entitydefs_list + cc.DLC1_ENTITYDEFS + cc.DLC2_ENTITYDEFS

    # 3) find + store entity templates
    for key, val in deltas:
        if val[0] == "TEMPLATE":
            # TODO: make a PEG parser for this
            t_name, t_args = parse_event(key)
            templates[t_name] = EntityTemplate(t_name, val[1], t_args)
            ui_log_verbose(f"Template {t_name} found")
        elif val[0] == "INIT":
            compile_ebl(val[1], vars_only=True)
        elif val[0] == "IGNORE":
            ignored_entity_names.append(key)
            ui_log(f"Ignoring entity {key}")

    # 4) Create copies of entities
    break_idx = len(entities)
    for idx, entity in enumerate(entities):
        if idx == break_idx:
            break
        for name, params in deltas:
            cmd, body_text = params
            if cmd != "MODIFY COPY":
                continue
            ident = name.split()[0]
            if f"entityDef {ident} {{" in entity:
                ui_log_verbose(f"Found entity {ident}")
                apply_entity_changes(name, entity, params, dlc_level)
                continue
    entities.append(cc.MAIN_SPAWN_PARENT)

    # 5) initialize variables, add new entities, and compile encounters
    template_added_count = {template: 0 for template in templates.keys()}

    for idx, (key, val) in enumerate(deltas):
        if val[0] == "REPLACE ENCOUNTER":
            try:
                deltas[idx] = key, (val[0], compile_ebl(val[1]))
            except Exception as e:
                raise Exception(e)
                return
        elif val[0] == "ADD":
            is_template = False
            for template in templates.keys():
                if not show_spawn_targets and template == "PointLabel":
                    # print("skipped Pointlabel")
                    continue
                full_text = key + val[1]
                if (
                    full_text.replace(" ", "")
                    .replace("\n", "")
                    .startswith(template + "(")
                ):
                    # TODO: make a PEG parser for this
                    _, args = parse_event(full_text)
                    args = [concat_strings(arg, is_expression=True) for arg in args]
                    rendered_template = templates[template].render(*args)
                    try:
                        pickup_respawn_ms = float(
                            Settings["all_powerups_respawn_time_ms"]
                        )
                        if (
                            pickup_respawn_ms >= 0
                            and "//#EBL_IS_PICKUP" in rendered_template
                        ):
                            rendered_template = rendered_template.replace(
                                "//#EBL_IS_PICKUP",
                                f"timeUntilRespawnMS = {pickup_respawn_ms};",
                            ).replace(
                                """removeFlag = "RMV_CHECKPOINT_ALLOW_MS";""",
                                """removeFlag="RMV_NEVER";""",
                            )
                    except KeyError:
                        pass
                    template_entities = re.split(
                        parser.ENTITY_SPLIT_PATTERN, rendered_template
                    )
                    template_entities = [
                        "entity {\n\t" + strip_comments(segment)
                        for segment in template_entities
                        if segment
                    ]
                    is_template = True
                    template_added_count[template] += 1

                    for template_entity in template_entities:
                        entities.append(template_entity + "\n")

                    if (
                        "//#EBL_IS_AIR_TARGET" in rendered_template
                        or "//#EBL_IS_BOUNTY_TARGET" in rendered_template
                    ):
                        ui_log_verbose(f"Ignoring air target {args[0]}")
                        ignored_entity_names.append(args[0])

            if not is_template:
                entity = val[1].strip()
                ui_log(f"Added entity {key}")
                entities.append(entity + "\n")
            added_count += 1

    for key, val in template_added_count.items():
        if val == 0:
            continue
        add_s = "s" if val > 1 else ""
        ui_log(f"Added {val} instance{add_s} of {key}")

    try:
        output_name_override = Settings["output_filename"]
    except KeyError:
        pass

    entities_name = (
        Path(base_file).name if not output_name_override else output_name_override
    )
    modded_file = str(output_folder) + "/" + entities_name

    # 6) iterate entities, apply changes, then write to output file
    with open(modded_file, "w") as fp:
        for entity in entities:
            total_count += 1
            skip_entity = False
            new_decorator_entities = []
            for target_entity_name, cmd, new_entity_name in decorator_changes:
                if f"entityDef {target_entity_name} {{" in entity:
                    (
                        new_entity,
                        do_not_modify,
                        delete_original,
                    ) = apply_decorator_command(entity, cmd, new_entity_name)
                    if delete_original:
                        new_decorator_entities = []
                        skip_entity = True
                    if do_not_modify:
                        new_decorator_entities.append((new_entity, True))
                    else:
                        new_decorator_entities.append((new_entity, False))

            for decorator_entity, do_not_modify in new_decorator_entities:
                added_count += 1
                if do_not_modify:
                    fp.write(decorator_entity)
                else:
                    entities.append(decorator_entity)
            if skip_entity:
                continue

            # replace encounters first
            for name, params in deltas:
                cmd, _ = params
                if cmd != "REPLACE ENCOUNTER":
                    continue
                ident = name.split()[0]
                if f"entityDef {ident} {{" in entity:
                    ui_log_verbose(f"Found encounter {ident}")
                    entity = apply_entity_changes(name, entity, params, dlc_level)
                    modified_count += 1

            # ...then modify
            for name, params in deltas:
                cmd, _ = params
                if cmd in ["INIT", "MODIFY COPY", "ADD", "IGNORE", "REPLACE ENCOUNTER"]:
                    continue
                ident = name.split()[0]
                if f"entityDef {ident} {{" in entity:
                    ui_log_verbose(f"Found entity {ident}")
                    entity = apply_entity_changes(name, entity, params, dlc_level)
                    modified_count += 1
                    # break
            if (
                'class = "idTarget_Spawn";' in entity
                or 'class = "idTarget_Spawn_Parent";' in entity
            ):
                entity, horde_index = format_spawn_target(
                    entity, entitydefs, horde_index
                )
                global spawn_target_hashes
                spawn_target_hashes.append(hashlib.md5(entity.encode()).hexdigest())
                modified_count += 1
            fp.write(entity)
        fp.write("\n")

        # 7) TODO: remove this part
        #  write ignored entities to output file
        # for new_entity in ignored_entities:
        #     total_count += 1
        #     fp.write(new_entity + "\n")

    if show_spawn_targets:
        ui_log("Adding spawn target markers...")
        target_count = entity_tools.mark_spawn_targets(modded_file, spawn_target_hashes)
        ui_log(f"Added visual markers for {target_count} spawn targets")
        added_count += target_count * 2
        total_count += target_count * 2

    if generate_traversals:
        pass
        # ui_log("Generating traversal info...")
        # entity_tools.generate_traversals(modded_file, dlc_level)
        # TODO: rewrite generate_traversals
        # give sauce proteh >:(

    if show_checkpoints:
        checkpoints = entity_tools.list_checkpoints(modded_file)
        ui_log("\nCHECKPOINTS:")
        for cp in checkpoints:
            ui_log(cp)
        ui_log("\n")

    if do_punctuation_check:
        ui_log(entity_tools.verify_file(modded_file))

    try:
        do_minify = Settings["minify"] == "true"
    except KeyError:
        do_minify = False

    if do_minify:
        ui_log("Minifying file...")
        entity_tools.minify(modded_file)

    if compress_file:
        ui_log("Compressing file...")
        oodle.compress_entities(modded_file)

    with open(CACHE_FILE, "w") as fp:
        fp.write(json.dumps(new_ebl_cache))

    total_count -= 1
    ui_log(f"Added {added_count} new entities")
    ui_log(f"{modified_count} entities out of {total_count} modified!")
    if "add_horde_bounty_targets" in Settings:
        ui_log(f"Horde bounty targets final index: {horde_index}")
    if "add_coin_targets" in Settings:
        ui_log(f"Horde coin targets final index: {horde_index}")
    ui_log(
        f"Done processing in {time.time() - tic:.1f} seconds ({datetime.datetime.now().strftime('%H:%M:%S')})"
    )
    return True
