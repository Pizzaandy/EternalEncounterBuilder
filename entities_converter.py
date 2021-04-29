import eternalevents
import entities_parser as parser
import EBL_compiler as ebl

fp = "Test Entities/e5m3_hell.entities"
event_to_ebl = eternalevents.event_to_ebl

blacklist = [
    "ENCOUNTER_DO_NOT_USE_MAX_HEAVY",
    "ENCOUNTER_DO_NOT_USE_MAX_SUPER",
    "ENCOUNTER_DO_NOT_USE_AMBIENT"
]

def snake_to_camel(s):
    return ''.join(word.title() for word in s.split('_'))


def format_arg(arg):
    res = ""
    if isinstance(arg, bool):
        arg = "true" if arg else "false"
        return arg

    for word in str(arg).split():
        if word in blacklist:
            continue
        if word.replace("ENCOUNTER_SPAWN_", "") in ebl.encounter_spawn_names:
            word = snake_to_camel(word.replace("ENCOUNTER_SPAWN_", ""))
        res += word + " "
    return res.strip()


def convert_to_ebl(events):
    res = ""
    last_name = ""
    repeat_count = 0
    for key, event in events.items():
        params = []
        if key == "num":
            continue
        #print(event["eventCall"]["eventDef"])
        game_name = event["eventCall"]["eventDef"]
        name = event_to_ebl[game_name]
        if "wait" in game_name and game_name != "wait":
            name = "waitFor " + name
        args = event["eventCall"]["args"]
        for key, arg in args.items():
            if key == "num":
                continue
            arg_value = list(arg.values())[0]
            if isinstance(arg_value, dict):
                arg_value = list(arg_value.values())[0]
                print(f"found decl = {arg_value}")
            arg_value = format_arg(arg_value)
            params.append(arg_value)
        if name == last_name:
            res += f'({", ".join(params)})\n'
            if repeat_count == 0:
                index = res.rindex(f"{name}(") + len(name)
                res = res[:index] + "\n" + res[index:]
            repeat_count += 1
        else:
            if "wait" in game_name:
                res += "\n"
            elif repeat_count > 0:
                res += "\n"
            res += f'{name}({", ".join(params)})\n'
            repeat_count = 0
        last_name = name
    return res

