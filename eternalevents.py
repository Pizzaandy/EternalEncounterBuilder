import chevron
from textwrap import dedent

# bruh
camelcase = lambda test_str: test_str[:1].lower() + test_str[1:] if test_str else ''

# (alias, total_args, optional_args)
event_to_ebl = {}
ebl_to_event = {}


class EternalEvent:
    ev_template = dedent("""\
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
    """)

    decl_template = dedent("""\
        {
                        {{varname}} = {{{value}}}
                    }""")

    def stringify(self):
        items = [
            {
                "index": index,
                "value": (f'"{val[1]}";' if isinstance(val[1], str)
                          and val[1] not in ["NULL", "true", "false"]
                          else f'{val[1]};'),
                "var": var[1]
            }
            for index, (val, var) in enumerate(zip(vars(self).items(), self.args))
        ]
        #print(items)
        name = camelcase(type(self).__name__)
        for item in items:
            if item["var"].startswith("decl"):
                varname = item["var"].replace("decl:", "")
                item["var"] = "decl"
                item["value"] = (
                    chevron.render(
                        template=self.decl_template,
                        data={"varname": varname, "value": item["value"]}))

        return chevron.render(
            template=self.ev_template,
            data={"name": name, "items": items, "count": len(items)})

    # def dictify(self):
    #     items = [
    #         {
    #             "index": index,
    #             "value": (f'"{val[1]}";' if isinstance(val[1], str)
    #                       and val[1] not in ["NULL", "true", "false"]
    #                       else f'{val[1]};'),
    #             "var": var[1]
    #         }
    #         for index, (val, var) in enumerate(zip(vars(self).items(), self.args))
    #     ]
    #     #print(items)
    #     name = camelcase(type(self).__name__)
    #     items_dict = {"num": len(items)}
    #     for item in items:
    #         if item["var"].startswith("decl"):
    #             varname = item["var"].replace("decl:", "")
    #             item["var"] = "decl"
    #             item["value"] = {varname: item["value"]}
    #         items_dict[f'item[{item["index"]}]'] = {f'{item["var"]}': f'{item["value"]}'}

    #     return {"eventCall": {"eventDef": name, "args": items_dict}}

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
        default_alias = camelcase(cls.__name__)
        aliases = alias if alias else [camelcase(cls.__name__)]
        if not isinstance(aliases, list):
            aliases = [aliases]
        event_to_ebl[default_alias] = aliases[0]

        for item in aliases:
            ebl_to_event[item] = (cls.__name__, len(args))
        ebl_to_event[default_alias] = (cls.__name__, len(args))

    def __init__(self, *args):
        for init_arg, (cls_name, cls_args) in zip(args, self.args):
            setattr(self, cls_name, init_arg)

    def __str__(cls):
        return cls.stringify()


class MaintainAICount(EternalEvent, alias=["maintainAI", "maintain"]):
    spawnType = "eEncounterSpawnType_t"
    desired_count = "int"
    max_spawn_count = "int"
    min_spawn_delay = "float"
    min_ai_for_respawn = "int"
    spawnGroup = "entity"
    group_level = "string"
    max_spawn_delay = "float"

class StaggeredAISpawn(EternalEvent):
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

class SpawnPossessedAI(EternalEvent, alias=["spawnPossessed","spawnSpirit"]):
    spawnType = "eEncounterSpawnType_t"
    spawnTarget = "entity"
    group_label = "string*"
    spawnTarget2 = "entity"
    spawnType2 = "eEncounterSpawnType_t"
    group_label2 = "string*"
    somebool = "bool"

class SpawnSpirit(EternalEvent):
    spawnTarget = "entity"
    spawnType = "eEncounterSpawnType_t"
    group_label = "string*"
    somebool = "bool"

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

class ClearCombatRoles(EternalEvent):
    spawnType = "eEncounterSpawnType_t"
    group_label = "string*"

class SetFactionRelation(EternalEvent):
    instigatorSpawnType = "eEncounterSpawnType_t"
    groupLabel = "string*"
    targetSpawnType = "eEncounterSpawnType_t"
    relation = "socialEmotion_t"

class ClearFactionOverrides(EternalEvent):
    pass

class ForceChargeOnAllAI(EternalEvent):
    pass

class WaitMulitpleConditions(EternalEvent):
    condition_count = "int"
    logic_operator = "encounterLogicOperator_t"
    disableAIHighlight = "bool"

class Wait(EternalEvent):
    seconds = "float"
    disableAIHighlight = "bool"

class WaitAIHealthLevel(EternalEvent, alias="AIHealthLevel"):
    aiType = "eEncounterSpawnType_t"
    desired_remaing_ai_count = "int"
    group_label = "char*"
    disableAIHighlight = "bool"

class WaitAIRemaining(EternalEvent, alias="AIRemaining"):
    aiType = "eEncounterSpawnType_t"
    desired_count = "int"
    group_label = "string"

class WaitKillCount(EternalEvent, alias="killCount"):
    ai_type = "eEncounterSpawnType_t"
    desired_kill_count = "int"
    group_label = "string*"
    disableAIHighlight = "bool"

class WaitKillCountOrSyncStart(EternalEvent, alias="killCountOrSyncStart"):
    ai_type = "eEncounterSpawnType_t"
    desired_kill_count = "int"
    group_label = "string*"
    disableAIHighlight = "bool"

class WaitRandomKillCount(EternalEvent, alias="randomKillCount"):
    ai_type = "eEncounterSpawnType_t"
    kill_count_min = "int"
    kill_count_max = "int"
    group_label = "string*"
    disableAIHighlight = "bool"

class WaitMaintainComplete(EternalEvent, alias="maintainComplete"):
    aiType = "eEncounterSpawnType_t"
    remaining_spawn_couunt = "int"
    group_label = "string"

class WaitStaggeredSpawnComplete(EternalEvent, alias="staggeredSpawnComplete"):
    aiType = "eEncounterSpawnType_t"
    remaining_spawn_count = "int"
    group_label = "string*"
    disableAIHighlight = "bool"

class WaitForStatCount(EternalEvent, alias="statCount"):
    trackedStat = "gameStat_t"
    stat_hit_count = "int"
    disableAIHighlight = "bool"

class WaitForEventFlag(EternalEvent, alias="Flag"):
    eventFlag = "eEncounterEventFlags_t"
    userFlag = "string*"
    testIfAlreadyRaised = "bool"
    disableAIHighlight = "bool"

class DamageAI(EternalEvent):
    damageType = "decl:damage"
    aiType = "eEncounterSpawnType_t"
    group_label = "string*"

class SetNextScriptIndex(EternalEvent):
    nextScriptIndex = "int"

class ProceedToNextScript(EternalEvent):
    bypassNextWaitForCommit = "bool"
    carryOverExistingUserFlags = "bool"

class DesignerComment(EternalEvent, alias="print"):
    designerComment = "string*"
    printToConsole = "bool"

#events = []
#for line in lines:
    #if line.startswith("Wave"):

#mylist = get_event_args(SpawnAI)
#print(mylist
