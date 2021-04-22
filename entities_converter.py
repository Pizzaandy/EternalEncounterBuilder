import eternalevents
import entities_parser as parser
import EBL_compiler as ebl

fp = "Test Entities/e5m3_hell.entities"
event_to_ebl = eternalevents.event_to_ebl

def snake_to_camel(s):
    return ''.join(word.title() for word in s.split('_'))

def format_arg(arg):
    res = ""
    if isinstance(arg, bool):
        arg = "true" if arg else "false"
        return arg

    for word in str(arg).split():
        if word.replace("ENCOUNTER_SPAWN_", "") in ebl.encounter_spawn_names:
            word = snake_to_camel(word.replace("ENCOUNTER_SPAWN_", ""))
        res += word + " "
    return res.strip()

def convert_to_ebl(events):
    res = ""
    for key, event in events.items():
        params = []
        if key == "num":
            continue
        #print(event["eventCall"]["eventDef"])
        name = event_to_ebl[event["eventCall"]["eventDef"]]
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
        res += f'{name}({", ".join(params)})'
        print(f'{name}({", ".join(params)})')
    return res



if __name__ == "__main__":
    entities = parser.parse_entities(fp, "idEncounterManager")
    res = ""
    for i, entity in enumerate(entities):
        print(f"processing entity {i}")
        for key in entity:
            if key.startswith("entityDef"):
                entitydef = key
                name = key.replace("entityDef ", "")
        if not key or not name:
            print("ERROR: no entityDef found")
        events = entity[entitydef]["edit"]["encounterComponent"]["entityEvents"]["item[0]"]["events"]
        res += "REPLACE ENCOUNTER " + name
        res += convert_to_ebl(events)
    #print(res)
