import json

import ebl_grammar
from ebl_compiler import apply_ebl
# import entities_converter
# import cProfile
import shutil
import os
from distutils.dir_util import copy_tree

MOD_BUILD_NAME = "ZandyRemix"
MOD_FOLDER_DIR = r"C:\AndyStuff\DoomModding\_MYMODS_\___ZandyRemix"

compress = 0
generate_traversal = 0
show_checkpoints = 0

def list_files(dir):
    r = []
    for root, dirs, files in os.walk(dir):
        for name in files:
            r.append(os.path.join(root, name))
    return r

def build_map(key, showtargets):
    base_file, _, ebl_file, overrides_folder, _ = map_list[key]
    if not os.path.exists(overrides_folder):
        print("Overrides folder not found. Is the folder incorrectly named?")
        return
    apply_ebl(
        ebl_file,
        base_file,
        overrides_folder,
        show_checkpoints,
        compress,
        show_spawn_targets=showtargets,  # show_targets,
        generate_traversals=generate_traversal,
        dlc_level=2,
        output_name_override="e1m4_boss.entities",
        do_punctuation_check=check_punctuation,
    )

    # from eternaltools import oodle

    # test_level = r"C:\Program Files (x86)\Steam\steamapps\common\DOOMEternal\overrides\maps\game\sp\e2m2_base\e2m2_base.entities"
    # test_output = r"C:\Program Files (x86)\Steam\steamapps\common\DOOMEternal\overrides\maps\game\sp\e2m2_base\e2m2_base.ebl"
    # test_level = r"Test Entities/e5m1_spear_decompressed.entities"
    # test_output = r"Test EBL Files/e5m1_generated_ebl"
    # entities_converter.generate_ebl_file(test_level, test_output)


def zip_mod():
    name = MOD_BUILD_NAME
    output_filename = (
        """C:/Program Files (x86)/Steam/steamapps/common/DOOMEternal/Mods/""" + name
    )
    mod_files_dir = MOD_FOLDER_DIR
    print("Zipping mod...")
    shutil.make_archive(output_filename, "zip", mod_files_dir)
    print("done-zo")


def build_all_maps(skip_maps=False):
    dir_name = MOD_FOLDER_DIR
    json_template = r"C:\AndyStuff\DoomModding\__ZandyRemixEBL\map_files_template\EternalMod\assetsinfo\template.json"
    decls_template = r"C:\AndyStuff\DoomModding\__ZandyRemixEBL\map_decls_template"
    for file in list_files(dir_name):
        if file.endswith(".json") and "assetsinfo" in file and "e6m1_cult_horde" not in file:
            with open(file, "w") as fp:
                with open(json_template, "r") as json_fp:
                    fp.write(json_fp.read())
                    print(f"overwriting {fp}")

    starting_inventory_file = r"C:\AndyStuff\DoomModding\_MYMODS_\___ZandyRemix\e1m1_intro_patch3\generated\decls\devinvloadout\devinvloadout\sp\e1m1.decl"
    idx = 0
    with open(starting_inventory_file, "r") as fp:
        data = fp.read()
    with open(starting_inventory_file, "w") as fp:
        for line in data.splitlines():
            newline = line
            if line.strip().startswith("currencyToGive"):
                idx = 0
            if line.strip().startswith("item[") and line.strip().endswith("{"):
                newline = f"\t\t\titem[{idx}] = {{"
                idx += 1
            fp.write(newline + "\n")
    print(f"Updated indices of inventory")

    if skip_maps:
        print("done")
        return

    for base_file, output_folder, ebl_file, _, _ in map_list.values():
        apply_ebl(
            ebl_file,
            base_file,
            output_folder,
            show_checkpoints=False,
            compress_file=True,
            show_spawn_targets=False,
            generate_traversals=generate_traversal,
            dlc_level=2,
            output_name_override="",
            do_punctuation_check=False,
        )
    #zip_mod()

def build_all_overrides():
    for base_file, _, ebl_file, overrides_folder in map_list.values():
        apply_ebl(
            ebl_file,
            base_file,
            overrides_folder,
            show_checkpoints=False,
            compress_file=False,
            show_spawn_targets=False,
            generate_traversals=generate_traversal,
            dlc_level=2,
            output_name_override="",
            do_punctuation_check=check_punctuation,
        )


map_list = {
    "e1m1": (
        r"C:\AndyStuff\DoomModding\_MYMODS_\__ENTITIES__\e1m1_intro_traversals.entities",
        r"C:\AndyStuff\DoomModding\_MYMODS_\___ZandyRemix\e1m1_intro_patch3\maps\game\sp\e1m1_intro",
        r"C:\AndyStuff\DoomModding\__ZandyRemixEBL\e1m1_intro.ebl",
        r"C:\Program Files (x86)\Steam\steamapps\common\DOOMEternal\overrides\maps\game\sp\e1m1_intro",
        ""
    ),
    "e1m2": (
        r"C:\AndyStuff\DoomModding\_MYMODS_\__ENTITIES__\e1m2_battle_traversals.entities",
        r"C:\AndyStuff\DoomModding\_MYMODS_\___ZandyRemix\e1m2_battle_patch3\maps\game\sp\e1m2_battle",
        r"C:\AndyStuff\DoomModding\__ZandyRemixEBL\e1m2_battle.ebl",
        r"C:\Program Files (x86)\Steam\steamapps\common\DOOMEternal\overrides\maps\game\sp\e1m2_battle",
        ""
    )
}

check_punctuation = 0
build_all = 0
do_zip = 0
skip_maps = 0
map_target = "e1m2"
show_targets = 1
if __name__ == "__main__":
    import subprocess

    if build_all == 2:
        build_all_maps(skip_maps)
    elif build_all == 1:
        build_all_overrides()
    else:
        build_map(map_target, show_targets)

    if do_zip:
        zip_mod()
        subprocess.call(["taskkill", "/F", "/IM", "DOOMEternalx64vk.exe"])
        os.startfile(
            r"C:\Program Files (x86)\Steam\steamapps\common\DOOMEternal\EternalModInjector.bat"
        )
