from pathlib import Path
import shutil
import subprocess
import entities_parser as parser
import chevron


def is_binary(filename):
    try:
        with open(filename, "tr") as check_file:  # try to open file in text mode
            check_file.read()
            return False
    except:  # if fail, then file is non-text (binary)
        return True


def decompress(input_path, output_path="", exe="idFileDeCompressor.exe"):
    new_path = True
    if not Path(exe).exists():
        print("ERROR: idFileDeCompressor not in folder!")
        return False
    if Path(input_path).suffix != ".entities":
        print("ERROR: Input path is not an .entities file!")
        return False
    if not is_binary(input_path):
        print("File is already decompressed!")
        if output_path:
            shutil.copy(input_path, output_path)
        return True
    if not output_path:
        new_path = False
        output_path = input_path
    p = subprocess.run([exe, "-d", input_path, output_path])
    if p.stderr:
        print(f"STINKY: {p.stderr}")
        return False
    if new_path:
        print(f"Decompressed {Path(input_path).name} to {Path(output_path).name}")
    else:
        print(f"Decompressed {Path(input_path).name}")
    return True


def compress(input_path, output_path="", exe="idFileDeCompressor.exe"):
    new_path = True
    if not Path(exe).exists():
        print("ERROR: idFileDeCompressor not in folder!")
        return None
    if Path(input_path).suffix != ".entities":
        print("ERROR: Input path is not an .entities file!")
        return False
    if is_binary(input_path):
        print("File is already compressed!")
        if output_path:
            shutil.copy(input_path, output_path)
        return True
    if not output_path:
        new_path = False
        output_path = input_path
    p = subprocess.run([exe, "-c", input_path, output_path])
    if p.stderr:
        print(f"ERROR: {p.stderr}")
        return False
    if new_path:
        print(f"Compressed {Path(input_path).name} to {Path(output_path).name}")
    else:
        print(f"Compressed {Path(input_path).name}")
    return True


base_enemies = [
    "arachnotron",
    "archvile",
    "baron",
    "carcass",
    "doom_hunter",
    "dreadknight",
    "gargoyle",
    "hellknight",
    "imp",
    "mancubus",
    "marauder",
    "marauder_wolf",
    "pinky",
    "prowler",
    "revenant",
    "soldier",
    "tyrant",
    "whiplash",
    "zombie_maykr",
    "zombie",
    "zombie_t3",
]

dlc1_enemies = ["bloodangel"]


def generate_traversals(
    input_path,
    dlc_level,
    exe="EternalTraversalInfoGenerator/EternalTraversalInfoGenerator.exe",
):
    if not Path(exe).exists():
        print("ERROR: EternalTraversalInfoGenerator not in folder!")
        return None
    if Path(input_path).suffix != ".entities":
        print("ERROR: Input path is not an .entities file!")
        return False

    enemies = base_enemies
    if dlc_level > 0:
        enemies += dlc1_enemies

    for enemy in enemies:
        p = subprocess.run(
            [exe, input_path, enemy, "generated_traversals"],
            cwd="EternalTraversalInfoGenerator/",
        )
        print(enemy)
        if p.stderr:
            print(f"ERROR: {p.stderr}")
            return False
        file = open(input_path, "a")
        with open("EternalTraversalInfoGenerator/generated_traversals") as info:
            file.writelines(info.readlines()[2:])
        file.write("\n")
        file.close()

    return True


marker_template = """
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
"""


def mark_spawn_targets(filename):
    generated_string = (
        """// WARNING: AUTO-GENERATED! Anything past this point will be deleted!\n"""
    )

    idTargets = parser.parse_entities(filename, "idTarget_Spawn")
    positions = []
    count = 0

    for d in idTargets:
        count += 1
        entityDef = [v for k, v in d.items() if k.startswith("entityDef")][0]
        name = [k for k, v in d.items() if k.startswith("entityDef")][0]
        name = name.replace("entityDef ", "")
        pos = entityDef["edit"]["spawnPosition"]
        if all(key in pos for key in ("x", "y", "z")):
            positions.append((pos["x"], pos["y"], pos["z"], name))

    for pos in positions:
        new_daisy = chevron.render(
            template=marker_template,
            data={
                "xpos": pos[0],
                "ypos": pos[1],
                "offset_ypos": pos[1] + 0.4,
                "zpos": pos[2],
                "name": pos[3],
            },
        )
        generated_string += "\n" + new_daisy

    print(f"Added visual markers for {count} spawn targets")

    with open(filename, "a") as fp:
        fp.write(generated_string)
