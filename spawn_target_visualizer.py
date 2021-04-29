import entities_parser as parser
import chevron
from textwrap import dedent


marker_template = dedent("""\
entity {
	entityDef marker_{{name}} {
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
""")

def show_spawn_targets(filename):
    generated_string = '''// WARNING: AUTO-GENERATED! Anything past this point will be deleted!\n'''

    idTargets = parser.parse_entities(filename, "idTarget_Spawn")
    positions = []
    count = 0

    for d in idTargets:
        count += 1
        entityDef = [v for k,v in d.items() if k.startswith('entityDef')][0]
        name = [k for k,v in d.items() if k.startswith('entityDef')][0]
        name = name.replace("entityDef ", "")
        pos = entityDef["edit"]["spawnPosition"]
        if all(key in pos for key in ("x", "y", "z")):
            positions.append((pos["x"], pos["y"], pos["z"], name))

    for pos in positions:
        new_daisy = chevron.render(template=marker_template, data={
            "xpos":pos[0],
            "ypos":pos[1],
            "offset_ypos": pos[1] + 0.4,
            "zpos":pos[2],
            "name":pos[3]
        })
        generated_string += "\n" + new_daisy

    print(f"Added visual markers for {count} spawn targets")

    with open(filename, "a") as fp:
        fp.write(generated_string)

