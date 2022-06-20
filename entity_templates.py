import math
import sys
import chevron
from ebl_grammar import EblTypeError
import re
import ast


def render_subtemplate(subtemplate):
    try:
        clsname, clsargs = subtemplate.split("[")
    except ValueError:
        raise EblTypeError(f"Subtemplate parsing error -- check your commas")
    if clsname not in [cls.__name__ for cls in EntityTemplate.__subclasses__()]:
        print(f"class {clsname} not found")
    clsargs = clsargs.replace("]", "").split()
    clsargs = [str(evaluate_arithmetic(arg.strip())) for arg in clsargs]
    cls = getattr(sys.modules[__name__], clsname)
    return cls().render(*clsargs), (cls(), clsargs)


def evaluate_arithmetic(expression):
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return expression  # not a Python expression
    if not all(
        isinstance(
            node,
            (
                ast.Expression,
                ast.UnaryOp,
                ast.unaryop,
                ast.BinOp,
                ast.operator,
                ast.Num,
            ),
        )
        for node in ast.walk(tree)
    ):
        return expression  # not a mathematical expression (numbers and operators)
    return eval(compile(tree, filename="", mode="eval"))


# TODO: move entity templates to another module
class EntityTemplate:
    """
    Handles text templates to be rendered into .entities
    """

    def __init__(self, name, template, args, arg_expressions={}):
        self.name = name
        self.template = template
        self.args = args
        self.arg_expressions = arg_expressions

    def modify_args(self, args):
        args = list(args)
        added_args = {}
        for i, arg in enumerate(args):
            if "[" in arg:
                args[i], (cls, subargs) = render_subtemplate(arg)
                if self is not None:
                    added_args.update(
                        {
                            f"{self.args[i]}.{arg_name}": arg_value
                            for arg_name, arg_value in zip(cls.args, subargs)
                        }
                    )
        return args, added_args

    def render(self, *argv) -> str:
        try:
            argv, added_args = self.modify_args(argv)
        except ValueError:
            argv = self.modify_args(argv)
            added_args = {}
        # print(f"{added_args=}")
        if len(argv) != len(self.args):
            raise EblTypeError(
                f"Expected {len(self.args)} args in template {self.name}, {len(argv)} given:\n"
                + ", ".join(argv)
            )

        params = {name: val for name, val in zip(self.args, argv)}

        sorted_params = params
        sorted_params.update(added_args)

        sorted_params = sorted(
            sorted_params.items(), key=lambda x: len(x[0]), reverse=True
        )

        expressions = re.findall(r"{{(.*?)}}", self.template)
        modified_template = self.template + "\n"
        for idx, expr in enumerate(expressions):
            original_expr = expr
            if "[" in original_expr:
                pass
            elif not any(c in expr for c in "+-/*."):
                continue
            for arg_name, arg_value in sorted_params:
                if arg_name in expr:
                    expr = expr.replace(arg_name, arg_value)
            new_key = f"__unique_{idx}__"
            modified_template = modified_template.replace(
                "{{" + original_expr + "}}", "{{" + new_key + "}}"
            )
            if "[" in original_expr:
                params[new_key], _ = render_subtemplate(expr)
            else:
                params[new_key] = evaluate_arithmetic(expr)

        return chevron.render(template=modified_template, data=params)


# noinspection PyMissingConstructor
class Vec3(EntityTemplate):
    def __init__(self):
        self.name = "Vec3"
        self.args = ["x", "y", "z"]
        self.template = "{x = {{x}}; y = {{y}}; z = {{z}};}"

    def modify_args(self, args):
        if len(args) == 1:
            return args[0], args[0], args[0]
        else:
            return args


DOOMGUY_HEIGHT = 1.67

# noinspection PyMissingConstructor
class pVec3(EntityTemplate):
    def __init__(self):
        self.name = "pVec3"
        self.args = ["x", "y", "z"]
        self.template = "{x = {{x}}; y = {{y}}; z = {{z}};}"

    def modify_args(self, args):
        new_args = args[0], args[1], float(args[2]) - DOOMGUY_HEIGHT
        return new_args


def sin_cos(deg):
    rad = math.radians(float(deg))
    return math.sin(rad), math.cos(rad)


# noinspection PyMissingConstructor
class Mat3(EntityTemplate):
    def __init__(self):
        self.name = "Mat3"
        self.args = ["x1", "y1", "z1", "x2", "y2", "z2", "x3", "y3", "z3"]
        self.template = """{
            mat = {
                mat[0] = {
                    x = {{x1}};
                    y = {{y1}};
                    z = {{z1}};
                }
                mat[1] = {
                    x = {{x2}};
                    y = {{y2}};
                    z = {{z2}};
                }
                mat[2] = {
                    x = {{x3}};
                    y = {{y3}};
                    z = {{z3}};
                }
            }
        }"""

    def modify_args(self, args):
        if len(args) == 3:
            sy, cy = sin_cos(args[0])
            sp, cp = sin_cos(args[1])
            sr, cr = sin_cos(args[2])
            return_modified = True
        elif len(args) == 1:
            sy, cy = sin_cos(args[0])
            sp, cp = sin_cos(0)
            sr, cr = sin_cos(0)
            return_modified = True
        else:
            return args

        if return_modified:
            return [
                cp * cy,
                cp * sy,
                -sp,
                sr * sp * cy + cr * -sy,
                sr * sp * sy + cr * cy,
                sr * cp,
                cr * sp * cy + -sr * sy,
                cr * sp * sy + -sr * cy,
                cr * cp,
            ]


# noinspection PyMissingConstructor
class Mat3New(EntityTemplate):
    def __init__(self):
        self.name = "Mat3New"
        self.args = ["x1", "y1", "z1", "x2", "y2", "z2", "x3", "y3", "z3"]
        self.template = """{
            mat = {
                mat[0] = {
                    x = {{x1}};
                    y = {{y1}};
                    z = {{z1}};
                }
                mat[1] = {
                    x = {{x2}};
                    y = {{y2}};
                    z = {{z2}};
                }
                mat[2] = {
                    x = {{x3}};
                    y = {{y3}};
                    z = {{z3}};
                }
            }
        }"""

    def modify_args(self, args):
        if len(args) == 3:
            sy, cy = sin_cos(args[1])
            sp, cp = sin_cos(args[0])
            sr, cr = sin_cos(args[2])
            return_modified = True
        elif len(args) == 1:
            sy, cy = sin_cos(args[0])
            sp, cp = sin_cos(0)
            sr, cr = sin_cos(0)
            return_modified = True
        else:
            return args

        if return_modified:
            return [
                cp * cy,
                cp * sy,
                -sp,
                sr * sp * cy + cr * -sy,
                sr * sp * sy + cr * cy,
                sr * cp,
                cr * sp * cy + sr * sy,
                cr * sp * sy + -sr * cy,
                cr * cp,
            ]


# noinspection PyMissingConstructor
class Mat2(EntityTemplate):
    def __init__(self):
        self.name = "Mat2"
        self.args = ["x1", "y1", "x2", "y2"]
        self.template = """{
            mat = {
                mat[0] = {
                    x = {{x1}};
                    y = {{y1}};
                }
                mat[1] = {
                    x = {{x2}};
                    y = {{y2}};
                }
            }
        }"""

    def modify_args(self, args):
        if len(args) == 2:
            sy, cy = sin_cos(args[0])
            sp, cp = sin_cos(args[1])
            return [cy, sy, cp, sp]
        elif len(args) == 1:
            angle = args[0]
            sy, cy = sin_cos(angle)
            sp, cp = 0, 1
            return [cy, sy, cp, sp]
        else:
            return args


class Color(EntityTemplate):
    def __init__(self):
        self.name = "Color"
        self.args = ["r", "g", "b"]
        self.template = """color = {r = {{r}}; g = {{g}}; b = {{b}};}"""


# TODO: put built-in templates into a text file
BUILTIN_TEMPLATES = {
    "SpawnTarget": EntityTemplate(
        "SpawnTarget",
        """entity {
	entityDef {{name}} {
	inherit = "target/spawn";
	class = "idTarget_Spawn";
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
		spawnEditable = {
			spawnAt = "";
			copyTargets = false;
			additionalTargets = {
				num = 0;
			}
			overwriteTraversalFlags = true;
			traversalClassFlags = "CLASS_A";
			combatHintClass = "CLASS_ALL";
			spawnAnim = "";
			aiStateOverride = "AIOVERRIDE_DEFAULT";
			initialTargetOverride = "";
		}
		portal = "";
		targetSpawnParent = "";
		disablePooling = false;
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "AirTarget": EntityTemplate(
        "AirTarget",
        """entity {
	entityDef {{name}} {
	inherit = "target/spawn";
	class = "idTarget_Spawn";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_AIR_TARGET
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
			num = 3;
			item[0] = {
				name = "custom_ai_heavy_painelemental";
			}
			item[1] = {
				name = "custom_ai_heavy_cacodemon";
			}
			item[2] = {
				name = "custom_ai_fodder_lostsoul";
			}
		}
		conductorEntityAIType = "SPAWN_AI_TYPE_ANY";
		initialEntityDefs = {
			num = 0;
		}
		spawnEditable = {
			spawnAt = "";
			copyTargets = false;
			additionalTargets = {
				num = 0;
			}
			overwriteTraversalFlags = true;
			traversalClassFlags = "CLASS_A";
			combatHintClass = "CLASS_ALL";
			spawnAnim = "";
			aiStateOverride = "AIOVERRIDE_TELEPORT";
			initialTargetOverride = "";
		}
		portal = "";
		targetSpawnParent = "";
		disablePooling = false;
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		targets = {
		    num = 2;
		    item[0] = "custom_ai_heavy_painelemental";
			item[1] = "custom_ai_heavy_cacodemon";
		}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "HordeBountyTarget": EntityTemplate(
        "HordeBountyTarget",
        """entity {
	entityDef {{name}} {
	inherit = "target/spawn";
	class = "idTarget_Spawn";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_BOUNTY_TARGET
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
			num = 32;
			item[0] = {
				name = "ai_ai_bounty_ambient_zombie_cueball_1";
			}
			item[1] = {
				name = "ai_ai_bounty_fodder_carcass_1";
			}
			item[2] = {
				name = "ai_ai_bounty_fodder_zombie_tier_1_1";
			}
			item[3] = {
				name = "ai_ai_bounty_fodder_zombie_tier_3_1";
			}
			item[4] = {
				name = "ai_ai_bounty_fodder_imp_1";
			}
			item[5] = {
				name = "ai_ai_bounty_fodder_imp_stone_1";
			}
			item[6] = {
				name = "ai_ai_bounty_fodder_prowler_1";
			}
			item[7] = {
				name = "ai_ai_bounty_fodder_gargoyle_1";
			}
			item[8] = {
				name = "ai_ai_bounty_fodder_soldier_blaster_1";
			}
			item[9] = {
				name = "ai_ai_bounty_fodder_soldier_shield_1";
			}
			item[10] = {
				name = "ai_ai_bounty_fodder_soldier_chaingun_1";
			}
			item[11] = {
				name = "ai_ai_bounty_heavy_hellknight_1";
			}
			item[12] = {
				name = "ai_ai_bounty_heavy_dreadknight_1";
			}
			item[13] = {
				name = "ai_ai_bounty_heavy_pinky_1";
			}
			item[14] = {
				name = "ai_ai_bounty_heavy_pinky_spectre_1";
			}
			item[15] = {
				name = "ai_ai_bounty_heavy_arachnotron_1";
			}
			item[16] = {
				name = "ai_ai_bounty_heavy_cacodemon_1";
			}
			item[17] = {
				name = "ai_ai_bounty_heavy_painelemental_1";
			}
			item[18] = {
				name = "ai_ai_bounty_heavy_revenant_1";
			}
			item[19] = {
				name = "ai_ai_bounty_heavy_bloodangel_1";
			}
			item[20] = {
				name = "ai_ai_bounty_heavy_mancubus_fire_1";
			}
			item[21] = {
				name = "ai_ai_bounty_heavy_mancubus_goo_1";
			}
			item[22] = {
				name = "ai_ai_bounty_heavy_whiplash_1";
			}
			item[23] = {
				name = "ai_ai_bounty_superheavy_baron_1";
			}
			item[24] = {
				name = "ai_ai_bounty_superheavy_baron_armored_1";
			}
			item[25] = {
				name = "ai_ai_bounty_superheavy_doom_hunter_1";
			}
			item[26] = {
				name = "ai_ai_bounty_superheavy_marauder_1";
			}
			item[27] = {
				name = "ai_ai_bounty_superheavy_archvile_1";
			}
			item[28] = {
				name = "ai_ai_bounty_superheavy_tyrant_1";
			}
			item[29] = {
				name = "ai_ai_bounty_fodder_prowler_cursed_1";
			}
			item[30] = {
				name = "ai_ai_bounty_fodder_zombie_maykr_1";
			}
			item[31] = {
				name = "ai_ai_bounty_ambient_turretl_1";
			}
		}
		conductorEntityAIType = "SPAWN_AI_TYPE_ANY";
		initialEntityDefs = {
			num = 0;
		}
		spawnEditable = {
			spawnAt = "";
			copyTargets = false;
			additionalTargets = {
				num = 0;
			}
			overwriteTraversalFlags = true;
			traversalClassFlags = "CLASS_A";
			combatHintClass = "CLASS_ALL";
			spawnAnim = "";
			aiStateOverride = "AIOVERRIDE_TELEPORT";
			initialTargetOverride = "";
		}
		portal = "";
		targetSpawnParent = "";
		disablePooling = false;
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		targets = {
			num = 32;
			item[0] = "ai_ai_bounty_ambient_zombie_cueball_1";
			item[1] = "ai_ai_bounty_fodder_carcass_1";
			item[2] = "ai_ai_bounty_fodder_zombie_tier_1_1";
			item[3] = "ai_ai_bounty_fodder_zombie_tier_3_1";
			item[4] = "ai_ai_bounty_fodder_imp_1";
			item[5] = "ai_ai_bounty_fodder_imp_stone_1";
			item[6] = "ai_ai_bounty_fodder_prowler_1";
			item[7] = "ai_ai_bounty_fodder_gargoyle_1";
			item[8] = "ai_ai_bounty_fodder_soldier_blaster_1";
			item[9] = "ai_ai_bounty_fodder_soldier_shield_1";
			item[10] = "ai_ai_bounty_fodder_soldier_chaingun_1";
			item[11] = "ai_ai_bounty_heavy_hellknight_1";
			item[12] = "ai_ai_bounty_heavy_dreadknight_1";
			item[13] = "ai_ai_bounty_heavy_pinky_1";
			item[14] = "ai_ai_bounty_heavy_pinky_spectre_1";
			item[15] = "ai_ai_bounty_heavy_arachnotron_1";
			item[16] = "ai_ai_bounty_heavy_cacodemon_1";
			item[17] = "ai_ai_bounty_heavy_painelemental_1";
			item[18] = "ai_ai_bounty_heavy_revenant_1";
			item[19] = "ai_ai_bounty_heavy_bloodangel_1";
			item[20] = "ai_ai_bounty_heavy_mancubus_fire_1";
			item[21] = "ai_ai_bounty_heavy_mancubus_goo_1";
			item[22] = "ai_ai_bounty_heavy_whiplash_1";
			item[23] = "ai_ai_bounty_superheavy_baron_1";
			item[24] = "ai_ai_bounty_superheavy_baron_armored_1";
			item[25] = "ai_ai_bounty_superheavy_doom_hunter_1";
			item[26] = "ai_ai_bounty_superheavy_marauder_1";
			item[27] = "ai_ai_bounty_superheavy_archvile_1";
			item[28] = "ai_ai_bounty_superheavy_tyrant_1";
			item[29] = "ai_ai_bounty_fodder_prowler_cursed_1";
			item[30] = "ai_ai_bounty_fodder_zombie_maykr_1";
			item[31] = "ai_ai_bounty_ambient_turretl_1";
		}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "MeathookNode": EntityTemplate(
        "MeathookNode",
        """entity { 
	entityDef {{name}}_target_ai_proxy_meathook {
	class = "idTarget_SmartAIProxy";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		flags = {
			noFlood = true;
		}
		targetingDecl = "target_aiproxy_meathook";
		distanceOverride = 33;
		spawnPosition = {{position}}
		renderModelInfo = {
			scale = {
				x = 1.000000;
				y = 1.000000;
				z = 1.000000;
			}
		}
	}
}
}
entity {
	entityDef {{name}}_target_ai_proxy_handler {
	inherit = "target/proxy_handler";
	class = "idTargetableProxyHandler";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		cooldownDuration = {{cooldown}};
		connectSound = "play_meat_hook_lock_in";
		ambientLoopSound = "play_meathook_sphere_amb_loop";
		oneSidedActiveModel = "art/kit/gameplay/meathook_traversal_a.lwo";
		oneSidedInactiveModel = "art/kit/gameplay/meathook_traversal_b.lwo";
		allSidedActiveModel = "art/kit/gameplay/meathook_traversal_c.lwo";
		allSidedInactiveModel = "art/kit/gameplay/meathook_traversal_d.lwo";
		oneSidedActiveFXModel = "art/kit/gameplay/meathook_traversal_a_rings.lwo";
		oneSidedInactiveFXModel = "art/kit/gameplay/meathook_traversal_b_rings.lwo";
		allSidedActiveFXModel = "art/kit/gameplay/meathook_traversal_c_rings.lwo";
		allSidedInactiveFXModel = "art/kit/gameplay/meathook_traversal_d_rings.lwo";
		renderModelInfo = {
			model = "art/kit/gameplay/meatHook_traversal_placeholder.lwo";
			scale = {
				x = 1.000000;
				y = 1.000000;
				z = 1.000000;
			}
		}
		clipModelInfo = {
			clipModelName = "maps/prefabs/gameplay/meathook_target/target_proxy_handler_2";
		}
		proxyList = {
			num = 1;
			item[0] = {
				proxyEntity = "{{name}}_target_ai_proxy_meathook";
				proxyTagName = "{{name}}_target_ai_proxy_meathook";
			}
		}
		isOmnidirectional = true;
		spawnOrientation = {{orientation}}
		spawnPosition = {{position}}
	}
}
}
""",
        ["name", "position", "orientation", "cooldown"],
    ),
    "Portal": EntityTemplate(
        "Portal",
        """entity {
    entityDef {{open_portal_name}} {
    inherit = "func/emitter";
    class = "idParticleEmitter";
    expandInheritance = false;
    poolCount = 0;
    poolGranularity = 2;
    networkReplicated = false;
    disableAIPooling = false;
    edit = {
        flags = {
            canBecomeDormant = true;
        }
        dormancy = {
            delay = 5;
            distance = 78.029007;
        }
        fadeIn = 0;
        fadeOut = 1.7;
        spawnPosition = {{position}}
        spawnOrientation = {{orientation}}
        renderModelInfo = { 
            {{color}} 
            scale = {
				x = {{scale}};
				y = {{scale}};
				z = {{scale}};
			}
        }
        startOff = true;
        particleSystem = "map_e2m2_base/portal_opening_white";
    }
}
}
entity {
    entityDef {{close_portal_name}} {
    inherit = "func/emitter";
    class = "idParticleEmitter";
    expandInheritance = false;
    poolCount = 0;
    poolGranularity = 2;
    networkReplicated = false;
    disableAIPooling = false;
    edit = {
        flags = {
            canBecomeDormant = true;
        }
        dormancy = {
            delay = 5;
            distance = 78.029007;
        }
        fadeIn = 0;
        fadeOut = 0;
        spawnPosition = {{position}}
        spawnOrientation = {{orientation}}
        renderModelInfo = {
            sortBias = 1;
            {{color}} 
            scale = {
				x = {{scale}};
				y = {{scale}};
				z = {{scale}};
			}
		}
        startOff = true;
        particleSystem = "map_e2m2_base/portal_closing_white";
    }
}
}
""",
        [
            "open_portal_name",
            "close_portal_name",
            "position",
            "orientation",
            "color",
            "scale",
        ],
    ),
    "SpawnGroup": EntityTemplate(
        "SpawnGroup",
        """entity {
	entityDef {{name}} {
	inherit = "encounter/spawn_group/zone";
	class = "idTargetSpawnGroup";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		spawnPosition = {
			x = 0;
			y = 0;
			z = 0;
		}
		renderModelInfo = {
			model = NULL;
		}
		clipModelInfo = {
			clipModelName = "CLIPMODEL_NONE";
		}
		spawners = {
			num = 0;
		}
		targetSpawnParent = "";
	}
}
}""",
        ["name"],
    ),
    "PointLabel": EntityTemplate(
        "PointLabel",
        """entity {
	entityDef {{name}} {
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
		spawnPosition = {{position}}
	}
}
}
entity { 
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
        spawnPosition = {{position}}
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
""",
        ["name", "position"],
    ),
    "PointLabelFinal": EntityTemplate(
        "PointLabelFinal",
        """entity {
	entityDef {{name}} {
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
		spawnPosition = {{position}}
	}
}
}
entity { 
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
        spawnPosition = {{position}}
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
""",
        ["name", "position"],
    ),
    "Encounter": EntityTemplate(
        "Encounter",
        """entity {
	entityDef {{name}} {
	inherit = "encounter/manager";
	class = "idEncounterManager";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		enableAIHighlightOnFinish = true;
		disabledAITypeForHighlight = "AI_MONSTER_SPECTRE AI_MONSTER_BUFF_POD AI_MONSTER_TENTACLE";
		playerMetricDef = "encounter/player_metrics";
		chargeCombatGrouping = "encounter/combat_role/charge_command";
		aiTypeDefAssignments = "actorpopulation/default/dlc2";
		aiTypePrintStrings = {
			num = 43;
			item[0] = {
				aiType = "ENCOUNTER_SPAWN_ZOMBIE_TIER_1";
				singularStringId = "#str_swf_actor_display_name_zombie";
				pluralStringId = "#str_swf_actor_display_name_zombies";
			}
			item[1] = {
				aiType = "ENCOUNTER_SPAWN_ZOMBIE_T1_SCREECHER";
				singularStringId = "#str_swf_actor_display_name_screecher_zombie";
				pluralStringId = "#str_swf_actor_display_name_screecher_zombies";
			}
			item[2] = {
				aiType = "ENCOUNTER_SPAWN_ZOMBIE_TIER_3";
				singularStringId = "#str_swf_actor_display_name_zombie";
				pluralStringId = "#str_swf_actor_display_name_zombies";
			}
			item[3] = {
				aiType = "ENCOUNTER_SPAWN_ZOMBIE_MAYKR";
				singularStringId = "#str_swf_actor_display_name_maykr_zombie";
				pluralStringId = "#str_swf_actor_display_name_maykr_zombies";
			}
			item[4] = {
				aiType = "ENCOUNTER_SPAWN_IMP";
				singularStringId = "#str_swf_actor_display_name_imp";
				pluralStringId = "#str_swf_actor_display_name_imps";
			}
			item[5] = {
				aiType = "ENCOUNTER_SPAWN_STONE_IMP";
				singularStringId = "#str_swf_actor_display_name_stone_imp";
				pluralStringId = "#str_swf_actor_display_name_stone_imps";
			}
			item[6] = {
				aiType = "ENCOUNTER_SPAWN_GARGOYLE";
				singularStringId = "#str_swf_actor_display_name_gargoyle";
				pluralStringId = "#str_swf_actor_display_name_gargoyles";
			}
			item[7] = {
				aiType = "ENCOUNTER_SPAWN_PROWLER";
				singularStringId = "#str_swf_actor_display_name_prowler";
				pluralStringId = "#str_swf_actor_display_name_prowlers";
			}
			item[8] = {
				aiType = "ENCOUNTER_SPAWN_CURSED_PROWLER";
				singularStringId = "#str_swf_actor_display_name_prowler";
				pluralStringId = "#str_swf_actor_display_name_prowlers";
			}
			item[9] = {
				aiType = "ENCOUNTER_SPAWN_HELL_SOLDIER";
				singularStringId = "#str_swf_actor_display_name_hell_soldier";
				pluralStringId = "#str_swf_actor_display_name_hell_soldiers";
			}
			item[10] = {
				aiType = "ENCOUNTER_SPAWN_SHOTGUN_SOLDIER";
				singularStringId = "#str_swf_actor_display_name_shotgun_soldier";
				pluralStringId = "#str_swf_actor_display_name_shotgun_soldiers";
			}
			item[11] = {
				aiType = "ENCOUNTER_SPAWN_CHAINGUN_SOLDIER";
				singularStringId = "#str_swf_actor_display_name_chaingun_soldier";
				pluralStringId = "#str_swf_actor_display_name_chaingun_soldiers";
			}
			item[12] = {
				aiType = "ENCOUNTER_SPAWN_CARCASS";
				singularStringId = "#str_swf_actor_display_name_carcass";
				pluralStringId = "#str_swf_actor_display_name_carcasses";
			}
			item[13] = {
				aiType = "ENCOUNTER_DO_NOT_USE_MAX_COMMON";
				singularStringId = "#str_swf_actor_display_name_lost_soul";
				pluralStringId = "#str_swf_actor_display_name_lost_souls";
			}
			item[14] = {
				aiType = "ENCOUNTER_SPAWN_HELL_KNIGHT";
				singularStringId = "#str_swf_actor_display_name_hellknight";
				pluralStringId = "#str_swf_actor_display_name_hellknights";
			}
			item[15] = {
				aiType = "ENCOUNTER_SPAWN_DREAD_KNIGHT";
				singularStringId = "#str_swf_actor_display_name_dread_knight";
				pluralStringId = "#str_swf_actor_display_name_dread_knights";
			}
			item[16] = {
				aiType = "ENCOUNTER_SPAWN_PINKY";
				singularStringId = "#str_swf_actor_display_name_pinky";
				pluralStringId = "#str_swf_actor_display_name_pinkies";
			}
			item[17] = {
				aiType = "ENCOUNTER_SPAWN_SPECTRE";
				singularStringId = "#str_swf_actor_display_name_spectre";
				pluralStringId = "#str_swf_actor_display_name_spectres";
			}
			item[18] = {
				aiType = "ENCOUNTER_SPAWN_CACODEMON";
				singularStringId = "#str_swf_actor_display_name_cacodemon";
				pluralStringId = "#str_swf_actor_display_name_cacodemons";
			}
			item[19] = {
				aiType = "ENCOUNTER_SPAWN_PAIN_ELEMENTAL";
				singularStringId = "#str_swf_actor_display_name_pain_elemental";
				pluralStringId = "#str_swf_actor_display_name_pain_elementals";
			}
			item[20] = {
				aiType = "ENCOUNTER_SPAWN_MANCUBUS";
				singularStringId = "#str_swf_actor_display_name_mancubus";
				pluralStringId = "#str_swf_actor_display_name_mancubi";
			}
			item[21] = {
				aiType = "ENCOUNTER_SPAWN_CYBER_MANCUBUS";
				singularStringId = "#str_swf_actor_display_name_cyber_mancubus";
				pluralStringId = "#str_swf_actor_display_name_cyber_mancubi";
			}
			item[22] = {
				aiType = "ENCOUNTER_SPAWN_ARACHNOTRON";
				singularStringId = "#str_swf_actor_display_name_arachnotron";
				pluralStringId = "#str_swf_actor_display_name_arachnotrons";
			}
			item[23] = {
				aiType = "ENCOUNTER_SPAWN_REVENANT";
				singularStringId = "#str_swf_actor_display_name_revenant";
				pluralStringId = "#str_swf_actor_display_name_revenants";
			}
			item[24] = {
				aiType = "ENCOUNTER_SPAWN_BLOOD_ANGEL";
				singularStringId = "#str_swf_actor_display_name_blood_angel";
				pluralStringId = "#str_swf_actor_display_name_blood_angels";
			}
			item[25] = {
				aiType = "ENCOUNTER_DO_NOT_USE_MAX_HEAVY";
				singularStringId = "#str_swf_actor_display_name_whiplash";
				pluralStringId = "#str_swf_actor_display_name_whiplashes";
			}
			item[26] = {
				aiType = "ENCOUNTER_SPAWN_DOOM_HUNTER";
				singularStringId = "#str_swf_actor_display_name_doom_hunter";
				pluralStringId = "#str_swf_actor_display_name_doom_hunters";
			}
			item[27] = {
				aiType = "ENCOUNTER_SPAWN_MARAUDER";
				singularStringId = "#str_swf_actor_display_name_marauder";
				pluralStringId = "#str_swf_actor_display_name_marauders";
			}
			item[28] = {
				aiType = "ENCOUNTER_SPAWN_BARON";
				singularStringId = "#str_swf_actor_display_name_baron";
				pluralStringId = "#str_swf_actor_display_name_barons";
			}
			item[29] = {
				aiType = "ENCOUNTER_SPAWN_ARMORED_BARON";
				singularStringId = "#str_swf_actor_display_name_armored_baron";
				pluralStringId = "#str_swf_actor_display_name_armored_barons";
			}
			item[30] = {
				aiType = "ENCOUNTER_SPAWN_ARCHVILE";
				singularStringId = "#str_swf_actor_display_name_archvile";
				pluralStringId = "#str_swf_actor_display_name_archviles";
			}
			item[31] = {
				aiType = "ENCOUNTER_DO_NOT_USE_MAX_SUPER";
				singularStringId = "#str_swf_actor_display_name_tyrant";
				pluralStringId = "#str_swf_actor_display_name_tyrants";
			}
			item[32] = {
				aiType = "ENCOUNTER_SPAWN_GLADIATOR";
				singularStringId = "#str_swf_actor_display_name_gladiator";
				pluralStringId = "#str_swf_actor_display_name_gladiators";
			}
			item[33] = {
				aiType = "ENCOUNTER_SPAWN_ICON_OF_SIN";
				singularStringId = "#str_swf_actor_display_name_icon_of_sin";
				pluralStringId = "#str_swf_actor_display_name_icon_of_sin(s)";
			}
			item[34] = {
				aiType = "ENCOUNTER_SPAWN_MAYKR_ANGEL";
				singularStringId = "#str_swf_actor_display_name_maykr_angel";
				pluralStringId = "#str_swf_actor_display_name_maykr_angels";
			}
			item[35] = {
				aiType = "ENCOUNTER_DO_NOT_USE_AMBIENT";
				singularStringId = "#str_swf_actor_display_name_maykr_samuel_boss";
				pluralStringId = "#str_swf_actor_display_name_maykr_samuel_bosses";
			}
			item[36] = {
				aiType = "ENCOUNTER_SPAWN_CUEBALL";
				singularStringId = "#str_swf_actor_display_name_cueball";
				pluralStringId = "#str_swf_actor_display_name_cueballs";
			}
			item[37] = {
				aiType = "ENCOUNTER_SPAWN_BUFF_POD";
				singularStringId = "#str_swf_actor_display_name_buffpod";
				pluralStringId = "#str_swf_actor_display_name_buffpods";
			}
			item[38] = {
				aiType = "ENCOUNTER_SPAWN_SUPER_TENTACLE";
				singularStringId = "#str_swf_actor_display_name_super_tentacle";
				pluralStringId = "#str_swf_actor_display_name_super_tentacles";
			}
			item[39] = {
				aiType = "ENCOUNTER_SPAWN_TENTACLE";
				singularStringId = "#str_swf_actor_display_name_tentacle";
				pluralStringId = "#str_swf_actor_display_name_tentacles";
			}
			item[40] = {
				aiType = "ENCOUNTER_SPAWN_SPIRIT";
				singularStringId = "#str_swf_actor_display_name_spirit";
				pluralStringId = "#str_swf_actor_display_name_spirits";
			}
			item[41] = {
				aiType = "ENCOUNTER_SPAWN_TURRET";
				singularStringId = "#str_swf_actor_display_name_turret";
				pluralStringId = "#str_swf_actor_display_name_turrets";
			}
			item[42] = {
				aiType = "ENCOUNTER_SPAWN_DEMONIC_TROOPER";
				singularStringId = "#str_swf_actor_display_name_demonic_soldier";
				pluralStringId = "#str_swf_actor_display_name_demonic_soldiers";
			}
		}
		spawnPosition = {
			x = 0;
			y = 0;
			z = 0;
		}
		combatRatingScale = "COMBAT_RATING_SCALE_IGNORE";
		encounterComponent = {
			entityEvents = {
				num = 1;
				item[0] = {
					entity = "{{name}}";
					events = {
						num = 0;
					}
				}
			}
		}
		commitTriggers = {
			num = 1;
			item[0] = "{{flag}}";
		}
		exitTriggers = {
			num = 0;
		}
		userFlagTriggers = {
			num = 0;
		}
		allowSlayerUnknownUI = true;
	}
}
}
""",
        ["name", "flag"],
    ),
    "EncounterTrigger": EntityTemplate(
        "EncounterTrigger",
        """entity {
	entityDef {{name}} {
	inherit = "encounter/trigger/commit";
	class = "idEncounterTrigger_Commit";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		renderModelInfo = {
			model = NULL;
		}
		clipModelInfo = {
		    size = {{scale}}
			clipModelName = "{{clipmodel}}";
		}
		dormancy = {
			allowDistanceDormancy = false;
			allowDormancy = false;
			allowPvsDormancy = false;
		}
	}
}
}
""",
        ["name", "position", "orientation", "scale", "clipmodel"],
    ),
    "EncounterTriggerUser": EntityTemplate(
        "EncounterTriggerUser",
        """entity {
	entityDef {{name}} {
	inherit = "encounter/trigger/user_flag";
	class = "idEncounterTrigger_RaiseUserFlag";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		renderModelInfo = {
			model = NULL;
		}
		clipModelInfo = {
		    size = {{scale}}
			clipModelName = "{{clipmodel}}";
		}
		userFlag = "{{user_flag}}";
	}
}
}
""",
        ["name", "position", "orientation", "scale", "clipmodel", "user_flag"],
    ),
    "EncounterTriggerExit": EntityTemplate(
        "EncounterTriggerExit",
        """entity {
	entityDef {{name}} {
	inherit = "encounter/trigger/exit";
	class = "idEncounterTrigger_Exit";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		renderModelInfo = {
			model = NULL;
		}
		clipModelInfo = {
		    size = {{scale}}
			clipModelName = "{{clipmodel}}";
		}
		dormancy = {
			allowDistanceDormancy = false;
			allowDormancy = false;
			allowPvsDormancy = false;
		}
		resetScriptOnExit = false;
		triggerOnce = false;
		forceAIToFlee = {{force_ai_to_flee}};
		despawn = {{force_ai_to_flee}};
		removeFlag = "RMV_NEVER";
	}
}
}
""",
        ["name", "position", "orientation", "scale", "clipmodel", "force_ai_to_flee"],
    ),
    "ArmorSmall": EntityTemplate(
        "ArmorSmall",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/armor/small";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		renderModelInfo = {
			model = "art/pickups/armor/pickup_shard_01.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			scale = {
				x = 1.5;
				y = 1.5;
				z = 1.5;
			}
			emissiveScale = 0.5;
		}
		spawn_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ITEMS_SPAWNED";
				increase = 1;
			}
		}
		equipOnPickup = true;
		lootStyle = "LOOT_TOUCH";
		triggerDef = "trigger/props/pickup";
		isStatic = true;
		canBePossessed = true;
		removeFlag = "RMV_CHECKPOINT_ALLOW_MS";
		difficultyScaleType = "DST_PICKUP";
		pickup_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ARMOR_PICKUP";
				increase = 1;
			}
		}
		useableComponentDecl = "armor/sp_armor_5";
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		dormancy = {
			playerDistance = 10;
			playerRearwardDistance = 10;
		}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "ArmorMedium": EntityTemplate(
        "ArmorMedium",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/armor/medium";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = true;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		renderModelInfo = {
			model = "art/pickups/armor/pickup_helm_01.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			scale = {
				x = 1.5;
				y = -1.5;
				z = 1.5;
			}
			emissiveScale = 0.5;
		}
		spawn_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ITEMS_SPAWNED";
				increase = 1;
			}
		}
		equipOnPickup = true;
		lootStyle = "LOOT_TOUCH";
		triggerDef = "trigger/props/pickup";
		isStatic = true;
		canBePossessed = true;
		removeFlag = "RMV_CHECKPOINT_ALLOW_MS";
		difficultyScaleType = "DST_PICKUP";
		pickup_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ARMOR_PICKUP";
				increase = 1;
			}
		}
		useableComponentDecl = "armor/sp_armor_25";
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		dormancy = {
			playerDistance = 10;
			playerRearwardDistance = 10;
		}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "ArmorLarge": EntityTemplate(
        "ArmorLarge",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/armor/large";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = true;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		renderModelInfo = {
			model = "art/pickups/armor/pickup_armor_01.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			scale = {
				x = 2;
				y = -2;
				z = 2;
			}
			emissiveScale = 0.5;
		}
		spawn_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ITEMS_SPAWNED";
				increase = 1;
			}
		}
		equipOnPickup = true;
		lootStyle = "LOOT_TOUCH";
		triggerDef = "trigger/props/armor_large";
		isStatic = true;
		canBePossessed = true;
		removeFlag = "RMV_CHECKPOINT_ALLOW_MS";
		difficultyScaleType = "DST_PICKUP";
		pickup_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ARMOR_PICKUP";
				increase = 1;
			}
		}
		useableComponentDecl = "armor/sp_armor_50";
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		dormancy = {
			playerDistance = 10;
			playerRearwardDistance = 10;
		}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "HealthSmall": EntityTemplate(
        "HealthSmall",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/health/small";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		renderModelInfo = {
			model = "art/pickups/health/vial.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			emissiveScale = 2;
			scale = {
				x = 1.79999995;
				y = 1.79999995;
				z = 1.79999995;
			}
		}
		spawn_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ITEMS_SPAWNED";
				increase = 1;
			}
		}
		equipOnPickup = true;
		lootStyle = "LOOT_TOUCH";
		triggerDef = "trigger/props/pickup";
		isStatic = true;
		canBePossessed = true;
		removeFlag = "RMV_CHECKPOINT_ALLOW_MS";
		difficultyScaleType = "DST_PICKUP";
		pickup_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_HEALTH_PICKUP";
				increase = 1;
			}
		}
		useableComponentDecl = "health/sp_health_small";
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		dormancy = {
			playerDistance = 10;
			playerRearwardDistance = 10;
		}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "HealthMedium": EntityTemplate(
        "HealthMedium",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/health/medium";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = true;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		renderModelInfo = {
			model = "art/pickups/health/health_pack_mid_a.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			emissiveScale = 0.5;
			scale = {
				x = 1.75;
				y = 1.75;
				z = 1.75;
			}
		}
		spawn_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ITEMS_SPAWNED";
				increase = 1;
			}
		}
		equipOnPickup = true;
		lootStyle = "LOOT_TOUCH";
		triggerDef = "trigger/props/pickup";
		isStatic = true;
		canBePossessed = true;
		removeFlag = "RMV_CHECKPOINT_ALLOW_MS";
		difficultyScaleType = "DST_PICKUP";
		pickup_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_HEALTH_PICKUP";
				increase = 1;
			}
		}
		useableComponentDecl = "health/sp_health_medium";
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		dormancy = {
			playerDistance = 10;
			playerRearwardDistance = 10;
		}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "HealthLarge": EntityTemplate(
        "HealthLarge",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/health/large";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = true;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		renderModelInfo = {
			model = "art/pickups/health/health_pack_big_a.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			emissiveScale = 0.5;
			scale = {
				x = 1.75;
				y = 1.75;
				z = 1.75;
			}
		}
		spawn_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ITEMS_SPAWNED";
				increase = 1;
			}
		}
		equipOnPickup = true;
		lootStyle = "LOOT_TOUCH";
		triggerDef = "trigger/props/pickup";
		isStatic = true;
		canBePossessed = true;
		removeFlag = "RMV_CHECKPOINT_ALLOW_MS";
		difficultyScaleType = "DST_PICKUP";
		pickup_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_HEALTH_PICKUP";
				increase = 1;
			}
		}
		useableComponentDecl = "health/sp_health_large";
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		dormancy = {
			playerDistance = 10;
			playerRearwardDistance = 10;
		}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "AmmoBullets": EntityTemplate(
        "AmmoBullets",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/ammo/bullets";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		renderModelInfo = {
			model = "art/pickups/ammo/ammo_bullet_02.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			emissiveScale = 0.2;
			scale = {
				x = 1.25;
				y = 1.25;
				z = 1.25;
			}
		}
		spawn_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ITEMS_SPAWNED";
				increase = 1;
			}
		}
		equipOnPickup = true;
		lootStyle = "LOOT_TOUCH";
		triggerDef = "trigger/props/pickup";
		isStatic = false;
		canBePossessed = true;
		removeFlag = "RMV_CHECKPOINT_ALLOW_MS";
		flags = {
			canBecomeDormant = true;
		}
		fxDecl = "pickups/ammo_bullets";
		difficultyScaleType = "DST_PICKUP";
		updateFX = true;
		pickup_statIncreases = {
			num = 2;
			item[0] = {
				stat = "STAT_AMMO_PICKUP";
				increase = 1;
			}
			item[1] = {
				stat = "STAT_PLACED_AMMO_PICKUP";
				increase = 1;
			}
		}
		useableComponentDecl = "propitem/ammo/heavy_cannon";
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "AmmoShells": EntityTemplate(
        "AmmoShells",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/ammo/shells";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		renderModelInfo = {
			model = "art/pickups/ammo/ammo_shotgun_01.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			emissiveScale = 0.2;
			scale = {
				x = 1.39999998;
				y = 1.39999998;
				z = 1.39999998;
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
		lootStyle = "LOOT_TOUCH";
		triggerDef = "trigger/props/pickup";
		isStatic = false;
		canBePossessed = true;
		removeFlag = "RMV_CHECKPOINT_ALLOW_MS";
		flags = {
			canBecomeDormant = true;
		}
		fxDecl = "pickups/ammo_shotgun";
		difficultyScaleType = "DST_PICKUP";
		updateFX = true;
		pickup_statIncreases = {
			num = 2;
			item[0] = {
				stat = "STAT_AMMO_PICKUP";
				increase = 1;
			}
			item[1] = {
				stat = "STAT_PLACED_AMMO_PICKUP";
				increase = 1;
			}
		}
		useableComponentDecl = "propitem/ammo/shotgun_10";
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "AmmoCells": EntityTemplate(
        "AmmoCells",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/ammo/cells";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		renderModelInfo = {
			model = "art/pickups/ammo/ammo_energy_01.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			emissiveScale = 0.5;
			scale = {
				x = 1.25;
				y = 1.25;
				z = 1.25;
			}
		}
		spawn_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ITEMS_SPAWNED";
				increase = 1;
			}
		}
		equipOnPickup = true;
		lootStyle = "LOOT_TOUCH";
		triggerDef = "trigger/props/pickup";
		isStatic = false;
		canBePossessed = true;
		removeFlag = "RMV_CHECKPOINT_ALLOW_MS";
		flags = {
			canBecomeDormant = true;
		}
		fxDecl = "pickups/ammo_cell";
		difficultyScaleType = "DST_PICKUP";
		updateFX = true;
		pickup_statIncreases = {
			num = 2;
			item[0] = {
				stat = "STAT_AMMO_PICKUP";
				increase = 1;
			}
			item[1] = {
				stat = "STAT_PLACED_AMMO_PICKUP";
				increase = 1;
			}
		}
		useableComponentDecl = "propitem/ammo/plasma_rifle";
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "AmmoRocket": EntityTemplate(
        "AmmoRocket",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/ammo/rockets_single";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		renderModelInfo = {
			model = "art/pickups/ammo/ammo_rocket_01.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			emissiveScale = 0.2;
			scale = {
				x = 1.5;
				y = 1.5;
				z = 1.5;
			}
		}
		spawn_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ITEMS_SPAWNED";
				increase = 1;
			}
		}
		equipOnPickup = true;
		lootStyle = "LOOT_TOUCH";
		triggerDef = "trigger/props/pickup";
		isStatic = false;
		canBePossessed = true;
		removeFlag = "RMV_CHECKPOINT_ALLOW_MS";
		flags = {
			canBecomeDormant = true;
		}
		fxDecl = "pickups/ammo_rocket_single";
		difficultyScaleType = "DST_INVALID";
		updateFX = true;
		pickup_statIncreases = {
			num = 2;
			item[0] = {
				stat = "STAT_AMMO_PICKUP";
				increase = 1;
			}
			item[1] = {
				stat = "STAT_PLACED_AMMO_PICKUP";
				increase = 1;
			}
		}
		useableComponentDecl = "propitem/ammo/rocket_launcher_1";
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "DashRefill": EntityTemplate(
        "DashRefill",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/dash_refill";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = true;
	disableAIPooling = false;
	edit = {
		soundOffset = {
			z = 1;
		}
		renderModelInfo = {
			model = "art/pickups/dash_recharge_a.lwo";
			noAmbient = true;
			contributesToLightProbeGen = false;
			scale = {
				x = 0.25;
				y = 0.25;
				z = 0.25;
			}
			emissiveScale = 1;
		}
		fxDecl = "gameplay/dash_activate";
		useableComponentDecl = "propitem/player/fill_dash_meter";
		thinkComponentDecl = "bob_seek";
		hideOnUse = true;
		timeUntilRespawnMS = {{respawn_time}};
		triggerDef = "trigger/props/megahealth";
		sound_spawn = "play_pickup_loop_03";
		sound_stop = "stop_pickup_loop_03";
		updateFX = true;
		spawnPosition = {{position}}
	}
}
}
""",
        ["name", "position", "respawn_time"],
    ),
    "Trigger": EntityTemplate(
        "Trigger",
        """entity {
	entityDef {{name}} {
	inherit = "trigger/trigger";
	class = "idTrigger";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		spawnPosition = {{position}}
		targets = {
			num = 0;
		}
		renderModelInfo = {
			model = NULL;
		}
		clipModelInfo = {
		    size = {{scale}}
			clipModelName = "{{clipmodel}}";
		}
		triggerOnce = {{trigger_once}};
	}
}
}
""",
        ["name", "position", "orientation", "scale", "clipmodel", "trigger_once"],
    ),
    "ShowTarget": EntityTemplate(
        "ShowTarget",
        """entity {
	entityDef {{name}} {
	inherit = "target/show";
	class = "idTarget_Show";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		flags = {
			noFlood = true;
		}
		reuseable = true;
		spawnPosition = {x = 0; y = 0; z = 0;}
		targets = {
			num = 1;
			item[0] = "{{target}}";
		}
	}
}
}
""",
        ["name", "target"],
    ),
    "HideTarget": EntityTemplate(
        "HideTarget",
        """entity {
	entityDef {{name}} {
	inherit = "target/hide";
	class = "idTarget_Hide";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		flags = {
			noFlood = true;
		}
		reuseable = true;
		spawnPosition = {x = 0; y = 0; z = 0;}
		targets = {
			num = 1;
			item[0] = "{{target}}";
		}
	}
}
}
""",
        ["name", "target"],
    ),
    "RemoveTarget": EntityTemplate(
        "RemoveTarget",
        """entity {
	entityDef {{name}} {
	inherit = "target/remove";
	class = "idTarget_Remove";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		flags = {
			noFlood = true;
		}
		spawnPosition = {x = 0; y = 0; z = 0;}
		whenToSave = "SGT_NO_SAVE";
		targets = {
			num = 1;
			item[0] = "{{target}}";
		}
	}
}
}
""",
        ["name", "target"],
    ),
    "TargetCount": EntityTemplate(
        "TargetCount",
        """entity {
	entityDef {{name}} {
	inherit = "target/relay";
	class = "idTarget_Count";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		flags = {
			noFlood = true;
			canBecomeDormant = false;
		}
		spawnPosition = {x = 0; y = 0; z = 0;}
		networkSerializeTransforms = false;
		count = 1;
		targets = {
			num = 0;
		}
		repeat = true;
		dormancy = {
			allowDistanceDormancy = false;
			allowDormancy = false;
			allowPvsDormancy = false;
		}
	}
}
}
""",
        ["name"],
    ),
    "SoundEntity": EntityTemplate(
        "SoundEntity",
        """entity {
	entityDef {{name}} {
	inherit = "sound/soundentity";
	class = "idSoundEntity";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		temporarySoundEvent = true;
		soundOcclusionBypass = true;
		spawnPosition = {x = 0; y = 0; z = 0;}
		startEvents = {
			num = 1;
			item[0] = "{{sound}}";
		}
		stopEvents = {
			num = 1;
			item[0] = "{{sound}}";
		}
	}
}
}
""",
        ["name", "sound"],
    ),
    "Checkpoint": EntityTemplate(
        "Checkpoint",
        """entity {
	entityDef {{activate_name}} {
	inherit = "target/change_layer";
	class = "idTarget_LayerStateChange";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		flags = {
			noFlood = true;
		}
		spawnPosition = {{position}}
		checkpointName = "{{spawnpoint_name}}_cp";
		delayCheckPointSec = 0.5;
		playerSpawnSpot = "{{spawnpoint_name}}";
		mapTipGroup = "MAPTIP_CHECKPOINT_1";
	}
}
}
entity {
	entityDef {{spawnpoint_name}} {
	inherit = "player/start";
	class = "idPlayerStart";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		flags = {
			noFlood = true;
		}
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		targets = {
			num = 0;
		}
	}
}
}
""",
        ["spawnpoint_name", "activate_name", "position", "orientation"],
    ),
    "GasCan": EntityTemplate(
        "GasCan",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/ammo/gas";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		renderModelInfo = {
			model = "art/pickups/ammo/ammo_chainsaw_01.lwo";
			contributesToLightProbeGen = false;
			ignoreDesaturate = true;
			emissiveScale = 0.2;
			scale = {
				x = 2;
				y = 2;
				z = 2;
			}
		}
		spawn_statIncreases = {
			num = 1;
			item[0] = {
				stat = "STAT_ITEMS_SPAWNED";
				increase = 1;
			}
		}
		equipOnPickup = true;
		lootStyle = "LOOT_TOUCH";
		triggerDef = "trigger/props/pickup";
		isStatic = false;
		canBePossessed = true;
		removeFlag = "RMV_CHECKPOINT_ALLOW_MS";
		flags = {
			canBecomeDormant = true;
		}
		fxDecl = "pickups/ammo_gas";
		difficultyScaleType = "DST_PICKUP";
		updateFX = true;
		pickup_statIncreases = {
			num = 2;
			item[0] = {
				stat = "STAT_AMMO_PICKUP";
				increase = 1;
			}
			item[1] = {
				stat = "STAT_PLACED_AMMO_PICKUP";
				increase = 1;
			}
		}
		useableComponentDecl = "propitem/ammo/chainsaw_fuel";
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
	}
}
}
""",
        ["name", "position", "orientation"],
    ),
    "BloodPunchRefill": EntityTemplate(
        "BloodPunchRefill",
        """entity {
	entityDef {{name}} {
	inherit = "pickup/blood_punch_refill";
	class = "idProp2";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = true;
	disableAIPooling = false;
	edit = {
	    //#EBL_IS_PICKUP
		whenToSave = "SGT_CHECKPOINT";
		renderModelInfo = {
			model = "art/pickups/bloodPunch_recharge_a.lwo";
			noAmbient = true;
			contributesToLightProbeGen = false;
		}
		fxDecl = "gameplay/blood_punch_refill";
		useableComponentDecl = "propitem/player/fill_blood_punch";
		thinkComponentDecl = "bob_rotate_slow";
		hideOnUse = true;
		triggerDef = "trigger/props/dash_refill";
		sound_spawn = "play_steam_explosion_small";
		updateFX = true;
		spawnPosition = {{position}}
	}
}
}
""",
        ["name", "position"],
    ),
    "EnableTarget": EntityTemplate(
        "EnableTarget",
        """entity {
	entityDef {{name}} {
	inherit = "target/enable_target";
	class = "idTarget_EnableTarget";
	expandInheritance = false;
	poolCount = 0;
	poolGranularity = 2;
	networkReplicated = false;
	disableAIPooling = false;
	edit = {
		flags = {
			noFlood = true;
		}
		enableFlag = {{enable}};
		spawnPosition = {
			x = 1;
			y = 1;
			z = 1;
		}
		targets = {
			num = 0;
		}
	}
}
}
""",
        ["name", "enable"],
    ),
}

if __name__ == "__main__":
    """Generate list of built-in templates"""
    for key, template in BUILTIN_TEMPLATES.items():
        s = (
            f"{key}({template.args})".replace("'", "")
            .replace("[", "")
            .replace("]", "")
            .replace("position", "position(Vec3)")
            .replace("orientation", "orientation(Mat3)")
            .replace("scale", "scale(Vec3)")
        )
        print(s)
    for key, template in BUILTIN_TEMPLATES.items():
        print(key)
