import chevron
from textwrap import dedent

# bruh
camelcase = lambda test_str: test_str[:1].lower() + test_str[1:] if test_str else ""

# (alias, total_args, optional_args)
event_to_ebl = {}
ebl_to_event = {}


def is_number_or_keyword(s):
    s = str(s)
    try:
        float(s)
        return True
    except ValueError:
        return s in ["true", "false", "NULL"]


class EternalEvent:

    ev_template = dedent(
        """\
        eventCall = {
            eventDef = "{{name}}";
            args = {
                num = {{count}};
                {{#items}}
                item[{{index}}] = {
                    {{var}} = {{{value}}}
                }
                {{/items}}
            }
        }
    """
    )

    decl_template = "{\n\t\t\t\t{{varname}} = {{{value}}}\n\t\t\t}"

    def stringify(self):
        def format_value(v):
            if is_number_or_keyword(v):
                return f"{v};"
            else:
                return f'"{v}";'

        items = [
            {"index": index, "value": format_value(val[1]), "var": var[1]}
            for index, (val, var) in enumerate(zip(vars(self).items(), self.args))
        ]
        name = camelcase(type(self).__name__)

        for item in items:
            # handle default arguments
            if "=" in item["var"]:
                varname, default_value = item["var"].split("=")
                item["var"] = varname
                if item["value"] == '"";' or not item["value"]:
                    item["value"] = format_value(default_value)

            # render decls
            if item["var"].startswith("decl:"):
                varname = item["var"].replace("decl:", "")
                item["var"] = "decl"
                item["value"] = chevron.render(
                    template=self.decl_template,
                    data={"varname": varname, "value": item["value"]},
                )
        return chevron.render(
            template=self.ev_template,
            data={"name": name, "items": items, "count": len(items)},
        )

    # metaprogramming time
    # TODO: figure out which arguments are *actually* optional
    def __init_subclass__(cls, alias="", **kwargs):
        super().__init_subclass__(**kwargs)
        # initialize fields
        args = []
        optional_args = 0
        for attr, value in cls.__dict__.items():
            if not attr.startswith("__"):
                if value[-1] == "*":
                    value = value.replace("*", "")
                    optional_args += 1
                args.append((attr, value))
        cls.args = args

        # add event class aliases to dicts
        aliases = []
        if alias:
            aliases = alias if isinstance(alias, list) else [alias]
            for item in aliases:
                ebl_to_event[item] = (cls.__name__, len(args))
                # if "wait" not in default_alias and "spawn"  in default_alias:
                #     print(item, end=' ')
        default_alias = camelcase(cls.__name__)
        ebl_to_event[default_alias] = (cls.__name__, len(args))
        event_to_ebl[default_alias] = aliases[0] if aliases else default_alias
        # if "wait" not in default_alias and "spawn"  in default_alias:
        #     print(default_alias, end=' ')


    def __init__(self, *args):
        for init_arg, (cls_name, cls_args) in zip(args, self.args):
            setattr(self, cls_name, init_arg)

    def __str__(self):
        return self.stringify()


class MaintainAICount(EternalEvent, alias=["maintainAI", "maintain"]):
    spawnType = "eEncounterSpawnType_t"
    desired_count = "int"
    max_spawn_count = "int"
    min_spawn_delay = "float"
    min_ai_for_respawn = "int"
    spawnGroup = "entity"
    group_level = "string"
    max_spawn_delay = "float"


class StaggeredAISpawn(EternalEvent, alias="spawnStaggered"):
    spawnType = "eEncounterSpawnType_t"
    spawn_count = "int"
    spawnGroup = "entity*"
    group_label = "string*"
    minSpawnStagger = "float"
    maxSpawnStagger = "float"


class StopMaintainingAICount(EternalEvent, alias=["stopMaintainAI", "stopMaintain"]):
    spawnType = "eEncounterSpawnType_t"
    group_label = "string*"


class SpawnAI(EternalEvent, alias="spawnMultiple"):
    spawnType = "eEncounterSpawnType_t"
    spawn_count = "int"
    spawnGroup = "entity"
    group_label = "string"


class SpawnSingleAI(EternalEvent, alias="spawn"):
    spawnType = "eEncounterSpawnType_t"
    spawnTarget = "entity"
    group_label = "string*"


class SpawnArchvile(EternalEvent):
    spawnTarget = "entity"
    archvileTemplate = "entity*"
    archvile_label = "string*"
    group_label = "string*"


class SpawnPossessedAI(EternalEvent, alias="spawnPossessed"):
    ai_spawnType = "eEncounterSpawnType_t"
    ai_spawnTarget = "entity"
    ai_groupLabel = "string*"
    spawnTarget = "entity"
    spirit_allowedAITypes = "eEncounterSpawnType_t"
    spirit_allowedGroupLabel = "string*"
    spirit_aiTypeExplicitFiltering = "bool=true"


class SpawnSpirit(EternalEvent):
    spawnTarget = "entity"
    allowedAITypes = "eEncounterSpawnType_t"
    allowed_group_label = "string*"
    aiTypeExplicitFiltering = "bool"


class SetMusicState(EternalEvent):
    target = "entity"
    stateDecl = "decl:soundstate"
    designComment = "string"


class MakeAIAwareOfPlayer(EternalEvent, alias="alertAI"):
    allActive = "bool"
    onSpawn = "bool"
    groupLabel = "string*"
    restorePerception = "bool"


class RestoreDefaultPerception(EternalEvent):
    spawnType = "eEncounterSpawnType_t"
    group_label = "string*"


class ActivateTarget(EternalEvent, alias="activate"):
    targetEntity = "entity"
    command = "string"


class ActivateCombatGrouping(EternalEvent):
    combatGrouping = "entity"
    group_label = "string*"
    assignmentDelaySec = "float"


class SetCombatRoles(EternalEvent):
    spawnType = "eEncounterSpawnType_t"
    group_label = "string"
    group_role = "entity"


class ClearCombatRoles(EternalEvent):
    spawnType = "eEncounterSpawnType_t"
    group_label = "string*"


class SetFactionRelation(EternalEvent):
    instigatorSpawnType = "eEncounterSpawnType_t"
    groupLabel = "string*"
    targetSpawnType = "eEncounterSpawnType_t"
    relation = "socialEmotion_t=EMOTION_DESTROY_AT_ALL_COSTS"


class ClearFactionOverrides(EternalEvent):
    pass


class ForceChargeOnAllAI(EternalEvent):
    pass


class WaitMulitpleConditions(EternalEvent):
    condition_count = "int"
    logic_operator = "encounterLogicOperator_t"
    disableAIHighlight = "bool=false"


class Wait(EternalEvent):
    seconds = "float"
    disableAIHighlight = "bool=false"


class WaitAIHealthLevel(EternalEvent, alias=["healthLevel", "AIHealthLevel"]):
    aiType = "eEncounterSpawnType_t"
    desired_remaing_ai_count = "int"
    group_label = "string*"
    disableAIHighlight = "bool=false"


class WaitAIRemaining(EternalEvent, alias="AIRemaining"):
    aiType = "eEncounterSpawnType_t"
    desired_count = "int"
    group_label = "string"


class WaitKillCount(EternalEvent, alias="killCount"):
    ai_type = "eEncounterSpawnType_t"
    desired_kill_count = "int"
    group_label = "string*"
    disableAIHighlight = "bool=false"


class WaitKillCountOrSyncStart(EternalEvent, alias="killCountOrSyncStart"):
    ai_type = "eEncounterSpawnType_t"
    desired_kill_count = "int"
    group_label = "string*"
    disableAIHighlight = "bool=false"


class WaitRandomKillCount(EternalEvent, alias="randomKillCount"):
    ai_type = "eEncounterSpawnType_t"
    kill_count_min = "int"
    kill_count_max = "int"
    group_label = "string*"
    disableAIHighlight = "bool=false"


class WaitMaintainComplete(EternalEvent, alias="maintainComplete"):
    aiType = "eEncounterSpawnType_t"
    remaining_spawn_couunt = "int"
    group_label = "string"


class WaitStaggeredSpawnComplete(EternalEvent, alias="staggeredSpawnComplete"):
    aiType = "eEncounterSpawnType_t"
    remaining_spawn_count = "int"
    group_label = "string*"
    disableAIHighlight = "bool=false"


class WaitForStatCount(EternalEvent, alias="statCount"):
    trackedStat = "gameStat_t"
    stat_hit_count = "int"
    disableAIHighlight = "bool=false"


class WaitForEventFlag(EternalEvent, alias="Flag"):
    eventFlag = "eEncounterEventFlags_t"
    userFlag = "string*"
    testIfAlreadyRaised = "bool"
    disableAIHighlight = "bool=false"


class DamageAI(EternalEvent, alias="damage"):
    damageType = "decl:damage"
    aiType = "eEncounterSpawnType_t"
    group_label = "string*"


class RemoveAI(EternalEvent, alias="remove"):
    aiType = "eEncounterSpawnType_t"
    group_label = "string*"


class SetNextScriptIndex(EternalEvent):
    nextScriptIndex = "int"


class ProceedToNextScript(EternalEvent):
    bypassNextWaitForCommit = "bool"
    carryOverExistingUserFlags = "bool"


class DesignerComment(EternalEvent, alias="print"):
    designerComment = "string*"
    printToConsole = "bool=true"


SPAWN_EVENTS = [SpawnSingleAI, SpawnArchvile, SpawnPossessedAI]
