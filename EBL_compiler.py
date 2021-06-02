import eternalevents
from eternalevents import is_number_or_keyword
from eternaltools import oodle, entity_tools
from entity_templates import EntityTemplate
import entities_parser as parser
import ebl_grammar
import compiler_constants as cc

from textwrap import indent
from dataclasses import dataclass
from typing import List, Union
import re
import time
from copy import deepcopy

from ebl_grammar import EblTypeError
from entities_parser import EntitiesSyntaxError

# EBL = Eternal Builder Language, describes changes to .entities files
ebl = ebl_grammar.NodeVisitor()
ebl.grammar = ebl_grammar.grammar
blacklist_entities = []

variables = {}
Settings = []
templates = {}
decorator_changes = {}
debug_vars = False


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


# these are not technically variables, but go off I guess
def add_variable(varname, value):
    if varname in variables:
        debug_print(f"Modified variable {varname} = {value}")
    else:
        print(f"Added variable {varname} = {value}")

    ignore_quotes = "+" not in value
    new_value = format_args(value)
    variables[varname] = concat_strings(new_value, ignore_quotes)
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


def get_event_args(classname):
    return [
        arg
        for arg in classname.__dict__.keys()
        if not arg.startswith("__") and not arg.startswith("args")
    ]


def strip_comments(s):
    pattern = r"//(.*)(?=[\r\n]+)"
    return re.sub(pattern, "", s)


def generate_ebl_segments(filename):
    """
    Splits an EBL file into segments at headers
    returns a tuple with EBL code and encounter name
    :param filename:
    :return:
    """
    with open(filename) as fp:
        segments = re.split(cc.EBL_HEADERS_REGEX, fp.read(), flags=re.MULTILINE)

    if segments[0].startswith("SETTINGS"):
        print("SETTINGS header found!")
        global Settings
        for line in segments[0].splitlines():
            Settings += [line.strip()]
    else:
        print("No SETTINGS found")

    # handle variables at top of document
    for line in segments[0].splitlines():
        if line.count("=") == 1:
            var = line.split("=")
            add_variable(var[0].strip(), var[1].strip())

    # yield tuples containing name, header command, and body text
    for cmd, body in zip(*[iter(segments[1:])] * 2):
        cmd = cmd.strip()
        name = body.split("\n")[0].strip()
        if not name:
            raise EblTypeError(f"No entity name specified in header {cmd}")
        body = "\n".join(body.split("\n")[1:])
        yield name, (cmd, strip_comments(body))


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
            # print(f"function value is {data['value']}")
            return [EntityEdit(data["object"], data["function"], data["value"])]

        if data["event"] == "waitForBlock":
            event_count = len([ev for ev in data["args"] if "variable" not in ev[0]])
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

        # Assume nested argument list means a list of parameters
        args_list = data["args"]
        if any(isinstance(item, list) for item in args_list):
            result = []
            for args in args_list:
                if "decorator" in data and data["decorator"]:
                    add_decorator_command(data["decorator"], event_cls(*args))
                args = format_args(args, arg_count)
                result += [event_cls(*args)]
            return result
        else:
            if "decorator" in data and data["decorator"]:
                add_decorator_command(data["decorator"], event_cls(*args_list))
            args_list = format_args(args_list, arg_count)
            event_cls = event_cls(*args_list)
            return [event_cls]

    return data


def add_decorator_command(decorator: str, event_cls: eternalevents.EternalEvent):
    entity_name = None
    cmd = decorator
    # parse decorator command
    # (stuff)

    # try to apply decorator command to EternalEvent
    if type(event_cls) in eternalevents.SPAWN_EVENTS:
        entity_name = concat_strings(event_cls.spawnTarget, is_expression=True)

    if entity_name in decorator_changes:
        decorator_changes[entity_name] += [cmd]
    else:
        decorator_changes[entity_name] = [cmd]


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
def rreplace(s: str, old, new, occurrence=0):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def concat_strings(s, is_expression=False):
    """Warning: hacky
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
            if is_expression:  # only replace entire expression if matched
                if len(var) == len(s.strip()):
                    s = s.replace(f"{var}", str(val))
                    break
            else:  # replace all instances of matches in quotes
                if not is_number_or_keyword(s):
                    val = f'"{val}"'
                s = s.replace(f'"{var}"', str(val))

        return s.replace(cc.SPACE_CHAR, " ").replace(cc.LITERAL_CHAR, "")

    result = ""
    segments = s.split("+")
    for idx, seg in enumerate(segments):
        seg = seg.lstrip() if idx > 0 else seg
        seg = seg.rstrip() if idx < len(segments) - 1 else seg

        # find valid string characters near +
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
        if "testing" in seg:
            print(f"bruhhh '{seg}'")
            debug_print(
                f"""bruhhh '{seg.replace(cc.SPACE_CHAR, " ").replace(cc.LITERAL_CHAR, "")}'"""
            )
        result += seg
    return result.replace(cc.SPACE_CHAR, " ").replace(cc.LITERAL_CHAR, "")


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
        result += f"item[{item_index}]" + " = {\n" + indent(event_string, "\t") + "}\n"
        item_index += 1

    return result


def replace_encounter(encounter: str, events: str, dlc_level: int) -> str:
    """
    Modifies encounter entity with list of EternalEvents
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
        entity[entitydef]["edit"]["encounterComponent"]["entityEvents"]["item[0]"][
            "events"
        ] = entity_events
        entity[entitydef]["edit"]["aiTypeDefAssignments"] = cc.ACTORPOPULATION[
            dlc_level
        ]
        # print(f"changed aiTypeDefAssignments to {actorpopulation[dlc_level]}")
    except KeyError:
        print("ERROR: Unable to replace encounter")
        print(entity[entitydef]["edit"])
    return parser.generate_entity(entity)


def edit_entity_fields(name: str, base_entity: str, edits: str) -> str:
    """
    Edits specific fields in the given entity
    :param name:
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
        # assignment or function
        if type(entity_edit) is EntityEdit:
            function_name = entity_edit.func
            values = entity_edit.value
            path = entity_edit.object
        elif type(entity_edit) is Assignment:
            function_name = "set"
            values = [[entity_edit.value]]
            print(values)
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
                ref_dic = deepcopy(dic)
                dic = {"num": len(ref_dic), **ref_dic}
                print(dic, "FUUUUUU why")

            if function_name == "set":
                if len(value) != 1:
                    raise EblTypeError(
                        f'Edit function "{function_name}" takes one argument'
                    )
                for key in keys[:-1]:
                    dic = dic.setdefault(key, {})
                if isinstance(value[0], str):
                    value[0] = concat_strings(value[0], is_expression=True)
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
                    dic = dic[key]
                for key, val in dic.items():
                    debug_print(f"Checking value '{value}' against '{val}'")
                    if val == value:
                        debug_print("Matched!")
                        dic.pop(key)
                        break

    return parser.generate_entity(entity)


def format_spawn_target(spawn_target: str, entitydefs: List[str]) -> str:
    """
    Adds custom idAI2s and applies changes to the given spawn target
    :param spawn_target:
    :param entitydefs:
    :return modified_spawn_target:
    """
    entity = parser.ev.parse(spawn_target)
    entitydef = ""
    # name = ""
    for key in entity:
        if key.startswith("entityDef"):
            entitydef = key
            # name = entitydef.replace("entityDef", "").strip()
    if not entitydef:
        print("ERROR: no entityDef component!")
        return spawn_target

    existing_entitydefs = entity[entitydef]["edit"]["entityDefs"]
    existing_entitydefs.pop("num")

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
        no_spawnanim = not spawn_editable["spawnAnim"]
        no_add_targets = spawn_editable["additionalTargets"]["num"] == 0
        if no_spawnanim and no_add_targets:
            entity[entitydef]["edit"]["spawnEditable"][
                "aiStateOverride"
            ] = "AIOVERRIDE_TELEPORT"

    listed_targets = list_targets(entitydefs)
    targets = "{\n" + indent(listed_targets, "\t") + "}\n"
    entity[entitydef]["edit"]["targets"] = targets

    listed_entitydefs = list_entitydefs(entitydefs)
    entitydefs = "{\n" + indent(listed_entitydefs, "\t") + "}\n"
    entity[entitydef]["edit"]["entityDefs"] = entitydefs

    return parser.generate_entity(entity)


def apply_entity_changes(name, entity: str, params: tuple[str, str], dlc_level) -> str:
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
    elif cmd == "REPLACE":
        print(f"Replaced entity {name}")
        return text
    elif cmd == "REMOVE":
        print(f"Removed entity {name}")
        return ""
    elif cmd == "MODIFY":
        print(f"Modified fields in entity {name}")
        return edit_entity_fields(name, entity, text)
    else:
        raise EblTypeError(f"Unknown command {cmd}")


# Apply all changes in ebl_file to base_file and output to modded_file
def apply_ebl(
    ebl_file,
    base_file,
    modded_file,
    compress_file=True,
    show_spawn_targets=False,
    generate_traversals=True,
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

    oodle.decompress_entities(base_file)
    dlc_level = get_dlc_level(base_file)

    # Add entitydefs with appropriate DLC level
    entitydefs = cc.BASE_ENTITYDEFS
    if dlc_level >= 2:
        entitydefs += cc.DLC2_ENTITYDEFS
    if dlc_level >= 1:
        entitydefs += cc.DLC1_ENTITYDEFS

    # get all file deltas
    segments = generate_ebl_segments(ebl_file)
    deltas = dict(segments)
    added_entities = []

    # find + store entity templates
    for key, val in deltas.items():
        if val[0] == "TEMPLATE":
            # TODO: make a PEG parser for this
            t_name, t_args = key.split("(", 1)
            t_args = re.findall(r"([^(,)]+)(?!.*\()", t_args)
            t_args = [arg.strip() for arg in t_args]
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
                    # TODO: make a PEG parser for this
                    args = re.findall(r"([^(,)]+)(?!.*\()", key)
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
                    entity = apply_entity_changes(name, entity, params, dlc_level)
                    modified_count += 1
                    break
            if (
                'class = "idTarget_Spawn";' in entity
                or 'class = "idTarget_Spawn_Parent";' in entity
            ):
                entity = format_spawn_target(entity, entitydefs)
                modified_count += 1
            fp.write(entity)
        fp.write("\n")
        # iterate added entities, apply changes, then write to output file
        for new_entity in added_entities:
            if (
                'class = "idTarget_Spawn";' in new_entity
                or 'class = "idTarget_Spawn_Parent";' in new_entity
            ):
                new_entity = format_spawn_target(new_entity, entitydefs)
            fp.write(new_entity + "\n")

    add_idai2s(modded_file, dlc_level)

    if show_spawn_targets:
        print("Adding spawn target markers...")
        entity_tools.mark_spawn_targets(modded_file)

    if generate_traversals:
        print("Generating traversal info...")
        # entity_tools.generate_traversals(modded_file, dlc_level)
        # TODO: rewrite generate_traversals
        # give sauce proteh >:(

    parser.verify_file(modded_file)
    parser.list_checkpoints(modded_file)

    if "minify" in Settings:
        print("Minifying modded file...")
        parser.minify(modded_file)

    if compress_file:
        oodle.compress_entities(modded_file)

    print(f"{modified_count} entities out of {total_count-1} modified!")
    print(f"Done processing in {time.time() - tic:.1f} seconds")
    debug_print(variables)
    print(decorator_changes)
    return True
