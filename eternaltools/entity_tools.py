import chevron
import entities_parser as parser


marker_template = """
entity {
	entityDef mod_marker_{{name}} {
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
entity { 
    entityDef mod_label_{{name}} {
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

Z_LABEL_OFFSET = 0.45


def mark_spawn_targets(filename):
    def is_close(pos1, pos2, min_distance=2):
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        dz = abs(pos1[2] - pos2[2])
        return dx < min_distance and dy < min_distance and dz < min_distance

    generated_string = (
        """\n// AUTO-GENERATED ENTITIES: Anything past this point will be deleted!\n"""
    )

    idTargets = parser.parse_entities(filename, "idTarget_Spawn")
    positions = []
    count = 0

    for target in idTargets:
        count += 1
        entityDef = [v for k, v in target.items() if k.startswith("entityDef")][0]
        name = [k for k, v in target.items() if k.startswith("entityDef")][0]
        name = name.replace("entityDef ", "")
        pos = entityDef["edit"]["spawnPosition"]
        if all(key in pos for key in ("x", "y", "z")):
            positions.append((pos["x"], pos["y"], pos["z"], name))

    nearby_groups = []

    for i, pos in enumerate(positions):
        for j, pos2 in enumerate(positions):
            if i == j:
                continue
            if is_close(pos, pos2):
                no_group = True
                for idx, sublist in enumerate(nearby_groups):
                    if pos in sublist and pos2 not in sublist:
                        nearby_groups[idx].append(pos2)
                        no_group = False
                        break
                    if pos2 in sublist and pos not in sublist:
                        nearby_groups[idx].append(pos)
                        no_group = False
                        break
                    if pos in sublist and pos2 in sublist:
                        break
                if no_group:
                    nearby_groups.append([pos, pos2])

    for pos in positions:
        y_off_scalar = 0
        for idx, group in enumerate(nearby_groups):
            if pos in group:
                y_off_scalar = len(group) - 1
                print(f"{y_off_scalar=}")
                nearby_groups[idx].remove(pos)
                break
        new_daisy = chevron.render(
            template=marker_template,
            data={
                "xpos": pos[0],
                "ypos": pos[1],
                "offset_zpos": pos[2] + Z_LABEL_OFFSET * y_off_scalar,
                "zpos": pos[2],
                "name": pos[3],
            },
        )
        generated_string += "\n" + new_daisy

    # print(f"NEARBY GROUPS: \n {nearby_groups}")

    with open(filename, "a") as fp:
        fp.write(generated_string)

    return f"Added visual markers for {count} spawn targets"
