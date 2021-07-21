CACHE_FILE = "cache.txt"
ANIM_OFFSETS_FILE = "anim_offsets.txt"

EBL_HEADERS_REGEX = r"(^REPLACE ENCOUNTER |^REPLACE |^MODIFY COPY |^REMOVE |^TEMPLATE |^MODIFY |^INIT|^ADD)"

# character reserved for spaces in string literals
SPACE_CHAR = "^"

# another reserved character for strings in quotes
LITERAL_CHAR = "$"

# waitFor block arguments
WAITFOR_KEYWORDS = {"all": "ENCOUNTER_LOGICAL_OP_AND", "any": "ENCOUNTER_LOGICAL_OP_OR"}
EBL_WAITFOR_KEYWORDS = {v: k for k, v in WAITFOR_KEYWORDS.items()}

# ENCOUNTER_SPAWN + name
ENCOUNTER_SPAWN_NAMES = [
    "ANY",
    "GENERIC",
    "ARACHNOTRON",
    "ARMORED_BARON",
    "BARON",
    "BLOOD_ANGEL",
    "CACODEMON",
    "CHAINGUN_SOLDIER",
    "CUEBALL",
    "CURSED_PROWLER",
    "CYBER_MANCUBUS",
    "DOOM_HUNTER",
    "DREAD_KNIGHT",
    "GARGOYLE",
    "HELL_KNIGHT",
    "HELL_SOLDIER",
    "IMP",
    "MANCUBUS",
    "MARAUDER",
    "PAIN_ELEMENTAL",
    "PINKY",
    "PROWLER",
    "REVENANT",
    "SHOTGUN_SOLDIER",
    "STONE_IMP",
    "TENTACLE",
    "TYRANT",
    "WHIPLASH",
    "ZOMBIE_MAYKR",
    "ZOMBIE_T1_SCREECHER",
    "ZOMBIE_TIER_1",
    "ZOMBIE_TIER_3",
    "LOST_SOUL",
    "SPECTRE",
    "CARCASS",
    "ARCHVILE",
    "BUFF_POD",
    "SPIRIT",
    "TURRET",
    "SUPER_TENTACLE",
]


# These are the preferred constants
ENCOUNTER_SPAWN_ALIASES = {
    "Any": "ANY",
    "Generic": "GENERIC",
    "Arachnotron": "ARACHNOTRON",
    "ArmoredBaron": "ARMORED_BARON",
    "Spider": "ARACHNOTRON",
    "Baron": "BARON",
    "FireborneBaron": "BARON",
    "BloodAngel": "BLOOD_ANGEL",
    "BloodMaykr": "BLOOD_ANGEL",
    "Cacodemon": "CACODEMON",
    "ChaingunSoldier": "CHAINGUN_SOLDIER",
    "Chaingunner": "CHAINGUN_SOLDIER",
    "RiotSoldier": "CHAINGUN_SOLDIER",
    "Cueball": "CUEBALL",
    "CursedProwler": "CURSED_PROWLER",
    "CyberMancubus": "CYBER_MANCUBUS",
    "DoomHunter": "DOOM_HUNTER",
    "DreadKnight": "DREAD_KNIGHT",
    "Gargoyle": "GARGOYLE",
    "HellKnight": "HELL_KNIGHT",
    "HellSoldier": "HELL_SOLDIER",
    "ZombieMan": "HELL_SOLDIER",
    "Soldier": "HELL_SOLDIER",
    "Imp": "IMP",
    "Mancubus": "MANCUBUS",
    "Marauder": "MARAUDER",
    "PainElemental": "PAIN_ELEMENTAL",
    "Pinky": "PINKY",
    "Prowler": "PROWLER",
    "Revenant": "REVENANT",
    "ShotgunSoldier": "SHOTGUN_SOLDIER",
    "Shotgunner": "SHOTGUN_SOLDIER",
    "ShotgunGuy": "SHOTGUN_SOLDIER",
    "ShieldGuy": "SHOTGUN_SOLDIER",
    "StoneImp": "STONE_IMP",
    "SIMP": "STONE_IMP",
    "Tentacle": "TENTACLE",
    "Tyrant": "TYRANT",
    "Cyberdemon": "TYRANT",
    "Whiplash": "WHIPLASH",
    "ZombieMaykr": "ZOMBIE_MAYKR",
    "MaykrDrone": "ZOMBIE_MAYKR",
    "ZombieT1Screecher": "ZOMBIE_T1_SCREECHER",
    "Screecher": "ZOMBIE_T1_SCREECHER",
    "ZombieTier1": "ZOMBIE_TIER_1",
    "Zombie": "ZOMBIE_TIER_1",
    "ZombieTier3": "ZOMBIE_TIER_3",
    "MechaZombie": "ZOMBIE_TIER_3",
    "LostSoul": "LOST_SOUL",
    "Spectre": "SPECTRE",
    "Carcass": "CARCASS",
    "BigChungus": "CARCASS",
    "Archvile": "ARCHVILE",
    "BuffTotem": "BUFF_POD",
    "BuffPod": "BUFF_POD",
    "Spirit": "SPIRIT",
    "Turret": "TURRET",
    "SuperTentacle": "SUPER_TENTACLE",
}


BASE_ENTITYDEFS = [
    "custom_ai_fodder_imp",
    "custom_ai_fodder_soldier_blaster",
    "custom_ai_fodder_gargoyle",
    "custom_ai_fodder_zombie_tier_3",
    "custom_ai_heavy_hellknight",
    "custom_ai_heavy_revenant",
    "custom_ai_fodder_lostsoul",
    "custom_ai_fodder_soldier_shield",
    "custom_ai_heavy_whiplash",
    "custom_ai_heavy_arachnotron",
    "custom_ai_heavy_cacodemon",
    "custom_ai_ambient_zombie_cueball",
    "custom_ai_fodder_zombie_t1_scientist",
    "custom_ai_heavy_mancubus_fire",
    "custom_ai_ambient_tentacle",
    "custom_ai_fodder_carcass",
    "custom_ai_fodder_prowler",
    "custom_ai_heavy_dreadknight",
    "custom_ai_heavy_mancubus_goo",
    "custom_ai_heavy_painelemental",
    "custom_ai_heavy_pinky",
    "custom_ai_heavy_pinky_spectre",
    "custom_ai_superheavy_archvile",
    "custom_ai_superheavy_baron",
    "custom_ai_superheavy_doom_hunter",
    "custom_ai_superheavy_marauder",
    "custom_ai_superheavy_tyrant",
    "custom_ai_ambient_buffpod",
    "custom_ai_fodder_zombie_maykr",
]


DLC1_ENTITYDEFS = [
    "custom_ai_ambient_turret",
    "custom_ai_heavy_bloodangel",
    "custom_ai_ambient_super_tentacle",
    "custom_ai_ambient_spirit",
]


DLC2_ENTITYDEFS = [
    "custom_ai_superheavy_baron_armored",
    "custom_ai_fodder_prowler_cursed",
    "custom_ai_fodder_imp_stone",
    "custom_ai_fodder_soldier_chaingun",
    "custom_ai_fodder_zombie_t1_screecher",
    "custom_ai_ambient_demonic_trooper",
]


ACTORPOPULATION = [
    "actorpopulation/default/default_no_bosses",
    "actorpopulation/default/dlc1",
    "actorpopulation/default/dlc2",  # dlc2_demonic_soldier
]


NAME_TO_IDAI2 = {
    "ARACHNOTRON": "custom_ai_heavy_arachnotron",
    "ARMORED_BARON": "custom_ai_superheavy_baron_armored",
    "BARON": "custom_ai_superheavy_baron",
    "BLOOD_ANGEL": "custom_ai_heavy_bloodangel",
    "CACODEMON": "custom_ai_heavy_cacodemon",
    "CHAINGUN_SOLDIER": "custom_ai_fodder_soldier_chaingun",
    "CUEBALL": "custom_ai_ambient_zombie_cueball",
    "CURSED_PROWLER": "custom_ai_fodder_prowler_cursed",
    "CYBER_MANCUBUS": "custom_ai_heavy_mancubus_goo",
    "DOOM_HUNTER": "custom_ai_superheavy_doom_hunter",
    "DREAD_KNIGHT": "custom_ai_heavy_dreadknight",
    "GARGOYLE": "custom_ai_fodder_gargoyle",
    "HELL_KNIGHT": "custom_ai_heavy_hellknight",
    "HELL_SOLDIER": "custom_ai_fodder_soldier_blaster",
    "IMP": "custom_ai_fodder_imp",
    "MANCUBUS": "custom_ai_heavy_mancubus_fire",
    "MARAUDER": "custom_ai_superheavy_marauder",
    "PAIN_ELEMENTAL": "custom_ai_heavy_painelemental",
    "PINKY": "custom_ai_heavy_pinky",
    "PROWLER": "custom_ai_fodder_prowler",
    "REVENANT": "custom_ai_heavy_revenant",
    "SHOTGUN_SOLDIER": "custom_ai_fodder_soldier_shield",
    "STONE_IMP": "custom_ai_fodder_imp_stone",
    "TENTACLE": "custom_ai_ambient_tentacle",
    "TYRANT": "custom_ai_superheavy_tyrant",
    "WHIPLASH": "custom_ai_heavy_whiplash",
    "ZOMBIE_MAYKR": "custom_ai_fodder_zombie_maykr",
    "ZOMBIE_T1_SCREECHER": "custom_ai_fodder_zombie_t1_screecher",
    "ZOMBIE_TIER_1": "custom_ai_fodder_zombie_t1_scientist",
    "ZOMBIE_TIER_3": "custom_ai_fodder_zombie_tier_3",
    "LOST_SOUL": "custom_ai_fodder_lostsoul",
    "SPECTRE": "custom_ai_heavy_pinky_spectre",
    "CARCASS": "custom_ai_fodder_carcass",
    "ARCHVILE": "custom_ai_superheavy_archvile",
    "BUFF_POD": "custom_ai_ambient_buffpod",
    "SPIRIT": "custom_ai_ambient_spirit",
    "TURRET": "custom_ai_ambient_turret",
    "SUPER_TENTACLE": "custom_ai_ambient_super_tentacle",
}

NAME_TO_ANIMWEB = {
    "ARACHNOTRON": "arachnotron",
    "ARMORED_BARON": "baron",
    "BARON": "baron",
    "BLOOD_ANGEL": "bloodangel",
    "CACODEMON": "cacodemon",
    "CHAINGUN_SOLDIER": "soldier_chaingun",
    "CUEBALL": "zombie_cueball",
    "CURSED_PROWLER": "prowler",
    "CYBER_MANCUBUS": "mancubus_goo",
    "DOOM_HUNTER": "doomhunter",
    "DREAD_KNIGHT": "dreadknight",
    "GARGOYLE": "gargoyle",
    "HELL_KNIGHT": "hellknight",
    "HELL_SOLDIER": "soldier_blaster",
    "IMP": "imp",
    "MANCUBUS": "mancubus_fire",
    "MARAUDER": "marauder",
    "PAIN_ELEMENTAL": "painelemental",
    "PINKY": "pinky",
    "PROWLER": "prowler",
    "REVENANT": "revenant",
    "SHOTGUN_SOLDIER": "soldier_shield",
    "STONE_IMP": "imp_stone",
    "TENTACLE": "tentacle",
    "TYRANT": "tyrant",
    "WHIPLASH": "whiplash",
    "ZOMBIE_MAYKR": "zombie_maykr",
    "ZOMBIE_T1_SCREECHER": "zombie_t1_screecher",
    "ZOMBIE_TIER_1": "zombie_tier_1",
    "ZOMBIE_TIER_3": "zombie_tier_3",
    "SPECTRE": "pinky",
    "CARCASS": "carcass",
    "ARCHVILE": "archvile",
}

ANIM_TO_OFFSET = {
    "jump_forward_1000_up_1000": (1000, 1000),
    "jump_forward_1000_down_1000": (1000, -1000),
    "jump_forward_500_up_500": (500, 500),
    "jump_forward_500_down_500": (500, -500),
    "jump_forward_300_down_300": (300, -300),
    "jump_forward_300_up_300": (300, 300),
    "jump_forward_100": (100, 0),
    "jump_forward_400": (400, 0),
    "jump_forward_700": (700, 0),
    "jump_forward_1000": (1000, 0),
    "jump_ledge_up_300": (0, 300),
    "ledge_forward_1000_up_1000": (1000, 1000),
    "ledge_down_100": (0, -100),
    "ledge_down_500": (0, -500),
    "ledge_down_1000": (0, -1000),
    "ledge_up_100": (0, 100),
    "ledge_up_500": (0, 500),
    "ledge_up_1000": (0, 1000),
    "rail_up_400": (0, 400),
}

TRAVERSALS_ENEMIES = ["REVENANT", "MARAUDER"]

# larger value = larger offset
# (width_offset, ledge_offset)
NAME_TO_HORIZONTAL_OFFSET = {
    "ARACHNOTRON": (150, 470),
    "ARMORED_BARON": 640,
    "BARON": 610,
    "BLOOD_ANGEL": 150,
    "CHAINGUN_SOLDIER": 200,
    "CUEBALL": 200,
    "CURSED_PROWLER": (450, 100),
    "PROWLER": (250, 100),
    "CYBER_MANCUBUS": 500,
    "DOOM_HUNTER": (450, 200),
    "DREAD_KNIGHT": (390, 20),
    "GARGOYLE": 150,
    "HELL_KNIGHT": 380,
    "HELL_SOLDIER": 200,
    "IMP": 150,
    "MANCUBUS": 470,
    "MARAUDER": (580, 200),
    "PINKY": 145,
    "REVENANT": (285, 100),
    "SHOTGUN_SOLDIER": 200,
    "STONE_IMP": 150,
    "TENTACLE": 0,
    "TYRANT": 500,
    "WHIPLASH": (50, 330),
    "ZOMBIE_MAYKR": 175,
    "ZOMBIE_T1_SCREECHER": (150, 250),
    "ZOMBIE_TIER_1": (150, 250),
    "ZOMBIE_TIER_3": 150,
    "SPECTRE": 145,
    "CARCASS": (300, 170),
    "ARCHVILE": 375,
    "PAIN_ELEMENTAL": 0,
}

ANIM_LIST = [
    "jump_forward_100",
    "jump_forward_1000",
    "jump_forward_1000_down_1000",
    "jump_forward_1000_down_1000_into",
    "jump_forward_1000_down_1000_out",
    "jump_forward_1000_into",
    "jump_forward_1000_out",
    "jump_forward_1000_up_1000",
    "jump_forward_1000_up_1000_into",
    "jump_forward_1000_up_1000_out",
    "jump_forward_100_into",
    "jump_forward_100_out",
    "jump_forward_200",
    "jump_forward_200_into",
    "jump_forward_200_out",
    "jump_forward_300",
    "jump_forward_300_down_300",
    "jump_forward_300_down_300_into",
    "jump_forward_300_down_300_out",
    "jump_forward_300_down_500",
    "jump_forward_300_down_500_into",
    "jump_forward_300_down_500_out",
    "jump_forward_300_into",
    "jump_forward_300_out",
    "jump_forward_300_up_300",
    "jump_forward_300_up_300_into",
    "jump_forward_300_up_300_out",
    "jump_forward_300_up_500_into",
    "jump_forward_300_up_500_out",
    "jump_forward_400",
    "jump_forward_400_into",
    "jump_forward_400_out",
    "jump_forward_500",
    "jump_forward_500_down_300",
    "jump_forward_500_down_300_into",
    "jump_forward_500_down_300_out",
    "jump_forward_500_down_500",
    "jump_forward_500_down_500_into",
    "jump_forward_500_down_500_out",
    "jump_forward_500_into",
    "jump_forward_500_out",
    "jump_forward_500_up_300",
    "jump_forward_500_up_300_into",
    "jump_forward_500_up_300_out",
    "jump_forward_500_up_500",
    "jump_forward_500_up_500_into",
    "jump_forward_500_up_500_out",
    "jump_forward_700",
    "jump_forward_700_into",
    "jump_forward_700_out",
    "ledge_down_100",
    "ledge_down_1000",
    "ledge_down_1000_out",
    "ledge_down_100_out",
    "ledge_down_200",
    "ledge_down_200_out",
    "ledge_down_300",
    "ledge_down_300_out",
    "ledge_down_400",
    "ledge_down_400_out",
    "ledge_down_500",
    "ledge_down_500_out",
    "ledge_down_700",
    "ledge_down_700_out",
    "ledge_up_100",
    "ledge_up_1000",
    "ledge_up_1000_into",
    "ledge_up_1000_out",
    "ledge_up_100_into",
    "ledge_up_100_out",
    "ledge_up_200",
    "ledge_up_200_into",
    "ledge_up_200_out",
    "ledge_up_300",
    "ledge_up_300_into",
    "ledge_up_300_out",
    "ledge_up_400",
    "ledge_up_400_into",
    "ledge_up_400_out",
    "ledge_up_500",
    "ledge_up_500_into",
    "ledge_up_500_out",
    "ledge_up_700",
    "ledge_up_700_into",
    "ledge_up_700_out",
    "rail_down_100",
    "rail_down_1000",
    "rail_down_1000_into",
    "rail_down_1000_out",
    "rail_down_100_into",
    "rail_down_100_out",
    "rail_down_200",
    "rail_down_200_into",
    "rail_down_200_out",
    "rail_down_300",
    "rail_down_300_into",
    "rail_down_300_out",
    "rail_down_400",
    "rail_down_400_into",
    "rail_down_400_out",
    "rail_down_500",
    "rail_down_500_into",
    "rail_down_500_out",
    "rail_down_700",
    "rail_down_700_into",
    "rail_down_700_out",
    "rail_up_100",
    "rail_up_1000",
    "rail_up_1000_into",
    "rail_up_1000_out",
    "rail_up_100_into",
    "rail_up_100_out",
    "rail_up_200",
    "rail_up_200_into",
    "rail_up_200_out",
    "rail_up_300",
    "rail_up_300_into",
    "rail_up_300_out",
    "rail_up_400",
    "rail_up_400_into",
    "rail_up_400_out",
    "rail_up_500",
    "rail_up_500_into",
    "rail_up_500_out",
    "rail_up_700",
    "rail_up_700_into",
    "rail_up_700_out",
]

MAIN_SPAWN_PARENT = """entity {
	entityDef eblmod_main_spawn_parent {
	inherit = "encounter/spawn_group/parent";
	class = "idTarget_Spawn_Parent";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		flags = {
			noFlood = true;
		}
		spawnConditions = {
			maxCount = 0;
			reuseDelaySec = 0;
			doBoundsTest = false;
			boundsTestType = "BOUNDSTEST_NONE";
			fovCheck = 0;
			minDistance = 0;
			maxDistance = 0;
			neighborSpawnerDistance = -1;
			LOS_Test = "LOS_NONE";
			playerToTest = "PLAYER_SP";
			conditionProxy = "";
		}
		spawnEditableShared = {
			groupName = "";
			deathTrigger = "";
			coverRadius = 0;
			maxEnemyCoverDistance = 0;
		}
		entityDefs = {
			num = 0;
		}
		conductorEntityAIType = "SPAWN_AI_TYPE_ANY";
		initialEntityDefs = {
			num = 0;
		}
		spawnPosition = {
			x = 0;
			y = 0;
			z = 0;
		}
		targets = {
			num = 0;
		}
	}
}
}
"""

if __name__ == "__main__":
    # import json
    # for key, val in NAME_TO_HORIZONTAL_OFFSET.items():
    #     if not isinstance(val, tuple):
    #         NAME_TO_HORIZONTAL_OFFSET[key] = (val, 0)
    # with open(ANIM_OFFSETS_FILE, "w") as fp:
    #     fp.write(json.dumps(NAME_TO_HORIZONTAL_OFFSET, indent=4))
    for key, val in ANIM_TO_OFFSET.items():
        print(key)