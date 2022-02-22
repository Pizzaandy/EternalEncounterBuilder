import entities_parser as parser
from pyperclip3 import copy

fp = r"C:\AndyStuff\DoomModding\_MYMODS_\__ENTITIES__\e6m3_mcity_horde.entities"
res = ""

if __name__ == "__main__":
    entities = parser.find_entities(fp, class_filter="idAI2")
    for entity in entities:
        if "bounty" in entity:
            res += entity
    copy(res)