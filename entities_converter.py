import eternalevents
import entities_parser as parser
from entities_parser import EntitiesSyntaxError
import compiler_constants as cc
from eternaltools import oodle

fp = "Test Entities/e5m3_hell.entities"
event_to_ebl = eternalevents.event_to_ebl


blacklist = [
    "ENCOUNTER_DO_NOT_USE_MAX_HEAVY",
    "ENCOUNTER_DO_NOT_USE_MAX_SUPER",
    "ENCOUNTER_DO_NOT_USE_AMBIENT",
    "ENCOUNTER_DO_NOT_USE_MAX_COMMON",
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


SPECIAL_CHARS = "():-"


# TODO: rewrite this complete garbage
def convert_encounter_to_ebl(encounter: str):
    """
    Don't even look at this
    it's horrific
    :param encounter:
    :return:
    """
    res = ""
    try:
        parsed_encounter = parser.ev.parse(encounter)
    except Exception as e:
        print(f"WARNING: {e}")
        return ""
    try:
        entitydef = ""
        for key in parsed_encounter:
            if key.startswith("entityDef"):
                entitydef = key
                entity_name = entitydef.replace("entityDef ", "").strip()
        events = parsed_encounter[entitydef]["edit"]["encounterComponent"][
            "entityEvents"
        ]["item[0]"]["events"]
    except KeyError:
        print("WARNING: encounterComponent events not found")
        return ""
        # raise EntitiesSyntaxError("encounterComponent events not found")
    res += f"REPLACE ENCOUNTER {entity_name}\n\n"
    last_name = ""
    repeat_count = 0
    wait_block_count = 0
    wait_newline = ""
    i = 0

    for key, event in events.items():
        # wtf????
        i += 1
        if i == 3:
            wait_newline = "\n"
        params = []
        if key == "num":
            continue

        args = event["eventCall"]["args"]
        print(args)

        # try to find entity's name idk
        game_name = ""
        try:
            game_name = event["eventCall"]["eventDef"]
            name = event_to_ebl[game_name]
        except KeyError:
            game_name = game_name if game_name else "(name not found)"
            print(f"WARNING: unknown event '{game_name}'")
            continue

        if wait_block_count > 0:
            wait_block_count -= 1
            if wait_block_count == 0:
                if name == last_name:
                    wait_block_count += 1
                    if repeat_count == 1:
                        wait_block_count += 3  # what the fuck?
                    res += "\t"
                elif wait_block_count == 0:
                    res += "}\n"
            else:
                res += "\t"
        elif "wait" in game_name and game_name != "wait":
            name = wait_newline + "waitfor " + name
            if wait_block_count > 0:
                res += "\t"

        if game_name == "wait" and wait_block_count == 0:
            last_name = name
            res += wait_newline + "waitfor "
            for arg_key, arg in args.items():
                if arg_key == "item[0]":
                    res += str(arg["float"]) + " sec\n"
                    break
            continue

        for arg_key, arg in args.items():
            if arg_key == "num":
                if game_name == "waitMulitpleConditions":
                    wait_block_count = arg
                    res += wait_newline + "waitfor "
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
            if (
                isinstance(arg_value, str)
                and any(char in arg_value for char in SPECIAL_CHARS)
                and not eternalevents.is_number_or_keyword(arg_value)
            ):
                arg_value = f'"{arg_value}"'
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
                add_tab = "\t" if wait_block_count > 0 else ""
                res = res[:index] + ":\n" + add_tab + res[index:]
            repeat_count += 1
        else:
            # if "wait" in game_name and wait_block_count == 0:
            #      res += "\n"
            # elif repeat_count > 0 and wait_block_count == 0:
            #     res += "\n"
            res += param_line
            repeat_count = 0
        last_name = name

    if wait_block_count > 0:
        res += "}\n"
    return res + "\n\n\n"


def generate_ebl_file(entities_file, ebl_file):
    # oodle.decompress_entities(entities_file)
    encounters = parser.generate_entity_segments(entities_file, "idEncounterManager")
    with open(ebl_file, "w") as f:
        for entity in encounters:
            f.write(convert_encounter_to_ebl(entity))


blacklist = [
    "tutorial",
    "pvp",
    "shell",
]


def generate_for_all_entities(resources_dir, output_dir):
    import os
    from eternaltools import oodle

    for root, dirs, files in os.walk(resources_dir):
        for name in files:
            if name.endswith(".entities"):
                if any(substr in name for substr in blacklist):
                    continue
                fpath = os.path.join(root, name)
                print(f"found {fpath}")
                oodle.decompress_entities(fpath, os.path.join(output_dir, name))

    for root, dirs, files in os.walk(output_dir):
        for file in files:
            fpath = os.path.join(root, file)
            print(f"fpath is {fpath}")
            generate_ebl_file(
                fpath,
                os.path.join(output_dir, str(file).removesuffix(".entities") + ".ebl"),
            )
            print("generating ebl for {file}")

    mydir = os.walk(output_dir)
    for root, dirs, files in mydir:
        for file in files:
            if file.endswith(".ebl"):
                continue
            fpath = os.path.join(root, file)
            print(f"fpath is {fpath}")
            generate_ebl_file(
                fpath,
                os.path.join(output_dir, str(file).removesuffix(".entities") + ".ebl"),
            )
            print("generating ebl for {file}")


if __name__ == "__main__":
    _resources_dir = r"C:\AndyStuff\DoomModding\__RESOURCES__"
    _output_dir = r"C:\AndyStuff\DoomModding\EncounterBuilder\GeneratedEBL"
    generate_for_all_entities(_resources_dir, _output_dir)
