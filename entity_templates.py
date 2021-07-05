import math
import sys
import chevron
from ebl_grammar import EblTypeError


# TODO: move entity templates to another module
class EntityTemplate:
    """
    Handles text templates to be rendered into .entities
    """

    def __init__(self, name, template, args):
        self.name = name
        self.template = template
        self.args = args
        print(f"Template {name} found")

    def modify_args(self, args):
        args = list(args)
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
                args[i] = cls().render(*clsargs)
                print(f"Rendered class {clsname} with args {clsargs}")
        return args

    def render(self, *argv) -> str:
        argv = self.modify_args(argv)
        if len(argv) != len(self.args):
            raise EblTypeError(
                f"Expected {len(self.args)} args in template {self.name}, {len(argv)} given"
            )
        t_data = {}
        for arg_name, arg in zip(self.args, argv):
            t_data[arg_name] = arg
        return chevron.render(template=self.template, data=t_data)


# noinspection PyMissingConstructor
class Vec3(EntityTemplate):
    def __init__(self):
        self.name = "Vec3"
        self.args = ["x", "y", "z"]
        self.template = """{
            x = {{x}};
            y = {{y}};
            z = {{z}};
        }
    """


# noinspection PyMissingConstructor
class pVec3(EntityTemplate):
    def __init__(self):
        self.name = "pVec3"
        self.args = ["x", "y", "z"]
        self.template = """{
            x = {{x}};
            y = {{y}};
            z = {{z}};
        }
    """

    def modify_args(self, args):
        new_args = args[0], args[1], float(args[2]) - 1.67
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
        else:
            return args


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
}
