import math
import sys
import chevron
from ebl_grammar import EblTypeError
import re
import ast


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
                clsname, clsargs = arg.split("[")
                if clsname not in [
                    cls.__name__ for cls in EntityTemplate.__subclasses__()
                ]:
                    print(f"class {clsname} not found")
                    continue
                clsargs = clsargs.replace("]", "").split()
                clsargs = [arg.strip() for arg in clsargs]
                cls = getattr(sys.modules[__name__], clsname)
                if self is not None:
                    added_args.update({
                        f"{self.args[i]}.{arg_name}": arg_value
                        for arg_name, arg_value in zip(cls().args, clsargs)
                    })
                args[i] = cls().render(*clsargs)
        return args, added_args

    def render(self, *argv) -> str:
        def evaluate_arithmetic(expression):
            try:
                tree = ast.parse(expression, mode="eval")
            except SyntaxError:
                return None  # not a Python expression
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
                return None  # not a mathematical expression (numbers and operators)
            return eval(compile(tree, filename="", mode="eval"))
        try:
            argv, added_args = self.modify_args(argv)
        except ValueError:
            argv = self.modify_args(argv)
            added_args = {}
        print(f"{added_args=}")
        if len(argv) != len(self.args):
            raise EblTypeError(
                f"Expected {len(self.args)} args in template {self.name}, {len(argv)} given"
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
            if not any(c in expr for c in "+-/*."):
                continue
            original_expr = expr
            print(f"expr {expr} contains math")
            for arg_name, arg_value in sorted_params:
                if arg_name in expr:
                    print(f"{arg_name=}")
                    expr = expr.replace(arg_name, arg_value)
            new_key = f"__unique_{idx}__"
            modified_template = modified_template.replace(
                "{{" + original_expr + "}}", "{{" + new_key + "}}"
            )
            if (new_value := evaluate_arithmetic(expr)) is not None:
                params[new_key] = new_value

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
            sy, cy = sin_cos(args[0])
            sp, cp = 0, 1
            return [cy, sy, cp, sp]
        else:
            return args


class Color(EntityTemplate):
    def __init__(self):
        self.name = "Color"
        self.args = ["r", "g", "b"]
        self.template = """color = {r = {{r}}; g = {{g}}; b = {{b}};}"""


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
        fadeOut = 0;
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
		spawnPosition = {
			x = 0;
			y = 0;
			z = 0;
		}
		combatRatingScale = "COMBAT_RATING_SCALE_SMALL";
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
		triggerOnce = false;
		spawnPosition = {{position}}
		spawnOrientation = {{orientation}}
		renderModelInfo = {
			model = NULL;
		}
		clipModelInfo = {
		    size = {{scale}}
			clipModelName = "{{clipmodel}}";
		}
	}
}
}
""",
        ["name", "position", "orientation", "scale", "clipmodel"],
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
        )
        print(s)
    for key, template in BUILTIN_TEMPLATES.items():
        print(key)
