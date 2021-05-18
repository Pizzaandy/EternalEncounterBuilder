import eternalevents
import entities_parser as parser
from entities_parser import EntitiesSyntaxError
import compiler_constants as cc

fp = "Test Entities/e5m3_hell.entities"
event_to_ebl = eternalevents.event_to_ebl


blacklist = [
    "ENCOUNTER_DO_NOT_USE_MAX_HEAVY",
    "ENCOUNTER_DO_NOT_USE_MAX_SUPER",
    "ENCOUNTER_DO_NOT_USE_AMBIENT",
]


def snake_to_camel(s):
    return "".join(word.title() for word in s.split("_"))


def format_arg(arg):
    res = ""
    if isinstance(arg, bool):
        arg = "true" if arg else "false"
        return arg

    for word in str(arg).split():
        if word in blacklist:
            continue
        if word.replace("ENCOUNTER_SPAWN_", "") in cc.ENCOUNTER_SPAWN_NAMES:
            word = snake_to_camel(word.replace("ENCOUNTER_SPAWN_", ""))
        res += word + " "
    return res.strip()


def convert_encounter_to_ebl(encounter):
    """
    Don't even look at this
    it's horrific
    :param encounter:
    :return:
    """
    parsed_encounter = parser.ev.parse(encounter)
    try:
        entitydef = ""
        for key in parsed_encounter:
            if key.startswith("entityDef"):
                entitydef = key
        events = parsed_encounter[entitydef]["edit"]["encounterComponent"][
            "entityEvents"
        ]["item[0]"]["events"]
    except KeyError:
        raise EntitiesSyntaxError("encounterComponent events not found")
    res = ""
    last_name = ""
    repeat_count = 0
    wait_block_count = 0
    for key, event in events.items():
        params = []
        if key == "num":
            continue

        # try to find entity name idk
        game_name = ""
        try:
            game_name = event["eventCall"]["eventDef"]
            name = event_to_ebl[game_name]
        except KeyError:
            game_name = game_name if game_name else "name not found"
            print(f"WARNING: unknown event '{game_name}'")
            continue

        if wait_block_count > 0:
            wait_block_count -= 1
            if wait_block_count == 0:
                res += "}\n"
            else:
                res += "\t"
        elif "wait" in game_name and game_name != "wait":
            name = "waitfor " + name
        elif game_name == "wait":
            last_name = name
            res += "waitfor "
            for arg_key, arg in args.items():
                if arg_key == "num":
                    res += str(arg) + " sec\n"
                    break
            continue

        args = event["eventCall"]["args"]
        print(args)

        for arg_key, arg in args.items():
            if arg_key == "num":
                if game_name == "waitMulitpleConditions":
                    wait_block_count = arg
                    res += "waitfor "
                continue
            arg_value = next(iter(arg.items()))[1]
            if game_name == "waitMulitpleConditions":
                if arg_key == "item[1]":
                    res += cc.EBL_WAITFOR_KEYWORDS[arg_value] + " {\n"
                    break
                else:
                    continue
            if isinstance(arg_value, dict):
                arg_value = next(iter(arg_value.items()))[1]
                print(f"found decl = {arg_value}")
            arg_value = format_arg(arg_value)
            params.append(arg_value)

        if game_name == "waitMulitpleConditions":
            continue

        if name != last_name:
            param_line = f'{name}({", ".join(params)})\n'
        else:
            param_line = f'({", ".join(params)})\n'
        if param_line.endswith(", )\n"):
            param_line = param_line.replace(", )\n", ")\n")

        if name == last_name:
            res += param_line
            if repeat_count == 0:
                index = res.rindex(f"{name}(") + len(name)
                res = res[:index] + "\n" + res[index:]
            repeat_count += 1
        else:
            if "wait" in game_name and wait_block_count == 0:
                res += "\n"
            elif repeat_count > 0:
                res += "\n"
            res += param_line
            repeat_count = 0
        last_name = name

    return res


def generate_ebl_file(entities_file, ebl_file):
    encounters = parser.generate_entity_segments(entities_file, "idEncounterManager")
    with open(ebl_file, "w") as f:
        for entity in encounters:
            f.write(convert_encounter_to_ebl(entity))
    # print(event_to_ebl)
