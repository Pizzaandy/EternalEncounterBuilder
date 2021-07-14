import chevron
import entities_parser as parser
import re
from textwrap import indent
from typing import Tuple, Dict, Any
import hashlib
import json
import ebl_compiler as compiler

NO_EQUALS = ("entityDef ", "layers")


def generate_entity(parsed_entity: dict, depth=0) -> str:
    """
    Converts a parsed event back to .entities -- shoutout to Chrispy
    :param parsed_entity:
    :param depth:
    :return:
    """
    s = ""
    if depth == 0:
        s += "entity {\n"
    item_index = 0
    do_item_numbering = False

    first_key = list(parsed_entity.keys())[0]
    if first_key.startswith("__unique"):
        updict = {"num": 0}
        old_dict = parsed_entity
        parsed_entity = {**updict, **old_dict}
        print("updated dict with __unique key")

    for key, val in parsed_entity.items():
        if do_item_numbering or key == "num":
            do_item_numbering = True
            if key == "num":
                val = len(parsed_entity) - 1
            else:
                key = f"item[{item_index}]"
                item_index += 1
            if item_index >= len(parsed_entity) - 1:
                item_index = 0
                do_item_numbering = False

        if isinstance(val, dict):
            if depth == 0:
                s += "\t"
            s += key
            if not key.startswith(NO_EQUALS):
                s += " ="
            if key == "layers":
                block = indent(generate_entity(val, depth + 1), "\t") + "\t"
            else:
                block = generate_entity(val, depth + 1)
            s += " {\n" + block + "}\n"
        else:
            multiline = False
            # special case for layernames xd
            is_layername = key.startswith("__layername")
            if val is None:
                val = "NULL"
            elif isinstance(val, bool):
                val = "true" if val else "false"
            elif isinstance(val, str):
                # if string is multiline, 'unpack' the string
                # otherwise, enclose in quotes
                multiline = "\n" in val
                if not multiline and not is_layername:
                    val = f'"{val}"'

            if is_layername:
                s += str(val) + "\n"
            else:
                s += f"{key} = {str(val)}"
                if not multiline:
                    s += ";\n"

    return indent(s, "\t") if depth > 0 else s + "}\n"


def minify(filename):
    with open(filename, "r") as fp:
        version_lines = "".join([next(fp) for x in range(2)])
        s = fp.read().removeprefix(version_lines)
    result = version_lines + "\n" + s.replace("\t", "").replace("\n", "")
    with open(filename, "w") as fp:
        s = fp.write(result)


def unminify(filename):
    with open(filename, "r") as fp:
        s = fp.read()

    # add newlines
    s = s.replace("{", "{\n")
    s = s.replace("}", "}\n")
    s = s.replace(";", ";\n")

    # add tabs (state machine moment)
    result = ""
    indent_level = 0
    for line in s.splitlines():
        if "}" in line:
            indent_level -= 1
        result += indent_level * "\t" + line + "\n"
        if "{" in line:
            indent_level += 1
    with open(filename, "w") as fp:
        fp.write(result)


def format_entities(filename):
    minify(filename)
    unminify(filename)


# quick-n-dirty punctuation check
# TODO: make less bad
def verify_file(filename) -> str:
    def strip_comments(s):
        pattern = r"//(.*)(?=[\r\n]+)"
        return re.sub(pattern, "", s)

    print("Checking file...")
    error_found = False
    depth = 0
    layers_block = False
    last_entity_line = 0
    with open(filename) as fp:
        for i, line in enumerate(fp.readlines()):
            line = strip_comments(line)
            if "{" in line:
                depth += line.count("{")
            if "}" in line:
                depth -= 1
                layers_block = False
            if line.strip() == "entity {":
                if depth != 1:
                    print(
                        f"Unmatched braces in entity starting at line {last_entity_line + 1}"
                    )
                    return f"Unmatched braces in entity starting at line {last_entity_line + 1}"
                last_entity_line = i
            if layers_block:
                continue
            if i < 2 or not line.strip() or line.lstrip().startswith("//"):
                continue
            if line.strip().startswith("layers"):
                layers_block = True
            if not line.rstrip().endswith(("{", "}", ";")):
                print(f"Missing punctuation on line {i + 1}")
                print(f"line {i + 1}: {line}")
                return f"Missing punctuation on line {i + 1}"
    if depth != 0:
        print(f"Unmatched braces detected! Depth = {depth}")
        return f"Unmatched braces detected! Depth = {depth}"
    if not error_found:
        return "No problems found!"


def list_checkpoints(filename) -> list:
    cps = []
    with open(filename) as fp:
        for line in fp.readlines():
            if "playerSpawnSpot = " in line:
                name = (
                    line.replace("playerSpawnSpot = ", "").strip().strip(";").strip('"')
                )
                cps += [name]
    return cps


POINT_MARKER = """entity {
	entityDef mod_visualize_marker_{{name}} {
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		renderModelInfo = {
			model = "art/pickups/health/vial.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			emissiveScale = 100;
			scale = {
				x = 0.7;
				y = 0.7;
				z = 0.7;
			}
		}
		spawn_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ITEMS_SPAWNED";
				increase = 1;
			}
		}
		equipOnPickup = false;
		isStatic = true;
		canBePossessed = false;
		spawnPosition = {
			x = {{xpos}};
			y = {{ypos}};
			z = {{zpos}};
		}
	}
}
}
"""

TEXT_LABEL = """entity { 
    entityDef mod_visualize_label_{{name}} {
    class = "idGuiEntity_Text";
    expandInheritance = false;
    poolCount = 0;
    poolGranularity = 2;
    networkReplicated = false;
    disableAIPooling = false;
    edit = {
        billboard = true;
        flags = {
            noknockback = false;
        }
        renderModelInfo = {
            model = "editors/models/gui_text.lwo";
            scale = {
                x = 4;
                y = 4;
                z = 4;
            }
        }
        clipModelInfo = {
            type = "CLIPMODEL_NONE";
        }
        swf = "swf/guientity/generic_text.swf";
        spawnOrientation = {
            mat = {
                mat[0] = {
                    x = 0.099308;
                    y = -0.994933;
                    z = 0.015707;
                }
                mat[1] = {
                    x = 0.995056;
                    y = 0.099320;
                    z = 0.000000;
                }
                mat[2] = {
                    x = -0.001560;
                    y = 0.015629;
                    z = 0.999877;
                }
            }
        }
        spawnPosition = {
			x = {{xpos}};
			y = {{ypos}};
			z = {{offset_zpos}};
		}
        swfScale = 0.02;
        headerText = {
            text = "{{name}}";
            color = {
                r = 1;
                g = 1;
                b = 1;
            }
            relativeWidth = 6;
            alignment = "SWF_ET_ALIGN_CENTER";
        }
    }
}
}
"""

marker_template = POINT_MARKER + "\n" + TEXT_LABEL

Z_LABEL_OFFSET = 0.45

# this function is now coupled with the ebl_compiler module. Oops!
def mark_spawn_targets(filename, spawn_target_hashes=None) -> Tuple[int, str]:
    def is_close(pos_1, pos_2, min_distance=1):
        dx = abs(pos_1[0] - pos_2[0])
        dy = abs(pos_1[1] - pos_2[1])
        dz = abs(pos_1[2] - pos_2[2])
        return (dx < min_distance) and (dy < min_distance) and (dz < min_distance)

    generated_string = (
        """\n// AUTO-GENERATED ENTITIES: Anything past this point will be deleted!\n"""
    )
    if spawn_target_hashes:
        targets_hash = hashlib.md5(str(spawn_target_hashes).encode()).hexdigest()
        if targets_hash in compiler.ebl_cache:
            try:
                cached_markers, count = compiler.ebl_cache[targets_hash]
            except ValueError:
                pass
            else:
                with open(filename, "a") as fp:
                    fp.write(cached_markers)
                compiler.new_ebl_cache[targets_hash] = cached_markers, count
                return count

    id_targets = parser.parse_entities(filename, "idTarget_Spawn")
    positions = []
    count = 0
    for target in id_targets:
        count += 1
        entityDef = [v for k, v in target.items() if k.startswith("entityDef")][0]
        name = [k for k, v in target.items() if k.startswith("entityDef")][0]
        name = name.replace("entityDef ", "")
        pos = entityDef["edit"]["spawnPosition"]
        if all(key in pos for key in ("x", "y", "z")):
            positions.append((pos["x"], pos["y"], pos["z"], name))

    nearby_groups = []

    for i, pos1 in enumerate(positions):
        for j, pos2 in enumerate(positions):
            if i == j:
                continue
            if is_close(pos1, pos2):
                no_group = True
                for idx, sublist in enumerate(nearby_groups):
                    if pos1 in sublist and pos2 not in sublist:
                        nearby_groups[idx].append(pos2)
                        no_group = False
                        break
                    if pos2 in sublist and pos1 not in sublist:
                        nearby_groups[idx].append(pos1)
                        no_group = False
                        break
                    if pos1 in sublist and pos2 in sublist:
                        break
                if no_group:
                    nearby_groups.append([pos1, pos2])

    # print(f"{nearby_groups=}")
    for pos in positions:
        y_off_scalar = 0
        for idx, group in enumerate(nearby_groups):
            if pos in group:
                nearby_groups[idx].remove(pos)
                y_off_scalar = len(group)
                # print(f"{y_off_scalar=}")
                break
        new_daisy = chevron.render(
            template=marker_template,
            data={
                "xpos": pos[0],
                "ypos": pos[1],
                "offset_zpos": pos[2] + (Z_LABEL_OFFSET * y_off_scalar),
                "zpos": pos[2],
                "name": pos[3],
            },
        )
        generated_string += "\n" + new_daisy
    if spawn_target_hashes:
        compiler.new_ebl_cache[targets_hash] = (generated_string, count)
    with open(filename, "a") as fp:
        fp.write(generated_string)

    return count
