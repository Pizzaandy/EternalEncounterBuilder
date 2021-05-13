EBL_HEADERS_REGEX = r"(^REPLACE ENCOUNTER|^REPLACE |^ADD |^REMOVE |^TEMPLATE |^MODIFY )"

# character reserved for spaces in string literals
SPACE_CHAR = "^"
# another reserved character for strings in quotes
LITERAL_CHAR = "$"


# waitFor block arguments
WAITFOR_KEYWORDS = {"all": "ENCOUNTER_LOGICAL_OP_AND", "any": "ENCOUNTER_LOGICAL_OP_OR"}


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
    "BuffPod": "BUFF_POD",
    "BuffTotem": "BUFF_POD",
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
    "actorpopulation/default/dlc2_demonic_soldier",
]



